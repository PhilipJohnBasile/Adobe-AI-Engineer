"""
Unified Notification Service
Provides real implementations for Slack, Microsoft Teams, and Email notifications
"""

import os
import logging
import smtplib
import asyncio
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum
from datetime import datetime

import requests

logger = logging.getLogger(__name__)


class NotificationChannel(Enum):
    """Available notification channels"""
    SLACK = "slack"
    TEAMS = "teams"
    EMAIL = "email"
    WEBHOOK = "webhook"


class NotificationPriority(Enum):
    """Notification priority levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class NotificationResult:
    """Result of a notification attempt"""
    channel: NotificationChannel
    success: bool
    recipient: str
    message_id: Optional[str] = None
    error: Optional[str] = None
    timestamp: datetime = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()


class SlackNotifier:
    """Real Slack notification implementation using Slack API"""

    API_URL = "https://slack.com/api/chat.postMessage"

    def __init__(self):
        self.token = os.getenv('SLACK_BOT_TOKEN')
        self.default_channel = os.getenv('SLACK_CHANNEL', '#alerts')
        self.enabled = bool(self.token)

        if self.enabled:
            logger.info("Slack notifications enabled")
        else:
            logger.warning("Slack notifications disabled - SLACK_BOT_TOKEN not set")

    async def send(
        self,
        message: str,
        channel: str = None,
        title: str = None,
        priority: NotificationPriority = NotificationPriority.MEDIUM,
        fields: Dict[str, str] = None
    ) -> NotificationResult:
        """Send a Slack notification"""
        if not self.enabled:
            return NotificationResult(
                channel=NotificationChannel.SLACK,
                success=False,
                recipient=channel or self.default_channel,
                error="Slack not configured"
            )

        target_channel = channel or self.default_channel

        try:
            # Build Slack Block Kit message for rich formatting
            priority_emoji = {
                NotificationPriority.CRITICAL: "🔴",
                NotificationPriority.HIGH: "🟠",
                NotificationPriority.MEDIUM: "🟡",
                NotificationPriority.LOW: "🟢"
            }.get(priority, "⚪")

            blocks = []

            # Header block
            if title:
                blocks.append({
                    "type": "header",
                    "text": {"type": "plain_text", "text": f"{priority_emoji} {title}", "emoji": True}
                })

            # Main message block
            blocks.append({
                "type": "section",
                "text": {"type": "mrkdwn", "text": message}
            })

            # Fields block (if provided)
            if fields:
                field_elements = [
                    {"type": "mrkdwn", "text": f"*{key}:* {value}"}
                    for key, value in fields.items()
                ]
                blocks.append({
                    "type": "section",
                    "fields": field_elements[:10]  # Slack limit
                })

            # Context block with timestamp
            blocks.append({
                "type": "context",
                "elements": [
                    {"type": "mrkdwn", "text": f"Sent at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"}
                ]
            })

            payload = {
                "channel": target_channel,
                "text": title or message[:100],  # Fallback text
                "blocks": blocks
            }

            headers = {
                "Authorization": f"Bearer {self.token}",
                "Content-Type": "application/json"
            }

            # Send asynchronously
            loop = asyncio.get_running_loop()
            response = await loop.run_in_executor(
                None,
                lambda: requests.post(self.API_URL, json=payload, headers=headers, timeout=30)
            )

            response_data = response.json()

            if response.status_code == 200 and response_data.get("ok"):
                logger.info(f"Slack message sent to {target_channel}")
                return NotificationResult(
                    channel=NotificationChannel.SLACK,
                    success=True,
                    recipient=target_channel,
                    message_id=response_data.get("ts")
                )
            else:
                error_msg = response_data.get("error", "Unknown error")
                logger.error(f"Slack API error: {error_msg}")
                return NotificationResult(
                    channel=NotificationChannel.SLACK,
                    success=False,
                    recipient=target_channel,
                    error=error_msg
                )

        except Exception as e:
            logger.error(f"Failed to send Slack notification: {e}")
            return NotificationResult(
                channel=NotificationChannel.SLACK,
                success=False,
                recipient=target_channel,
                error=str(e)
            )


class TeamsNotifier:
    """Real Microsoft Teams notification implementation using Incoming Webhooks"""

    def __init__(self):
        self.webhook_url = os.getenv('TEAMS_WEBHOOK_URL')
        self.enabled = bool(self.webhook_url)

        if self.enabled:
            logger.info("Teams notifications enabled")
        else:
            logger.warning("Teams notifications disabled - TEAMS_WEBHOOK_URL not set")

    async def send(
        self,
        message: str,
        title: str = None,
        priority: NotificationPriority = NotificationPriority.MEDIUM,
        fields: Dict[str, str] = None
    ) -> NotificationResult:
        """Send a Microsoft Teams notification"""
        if not self.enabled:
            return NotificationResult(
                channel=NotificationChannel.TEAMS,
                success=False,
                recipient="teams_webhook",
                error="Teams not configured"
            )

        try:
            # Color based on priority
            priority_colors = {
                NotificationPriority.CRITICAL: "FF0000",
                NotificationPriority.HIGH: "FFA500",
                NotificationPriority.MEDIUM: "FFFF00",
                NotificationPriority.LOW: "00FF00"
            }
            theme_color = priority_colors.get(priority, "808080")

            # Build MessageCard payload
            facts = []
            if fields:
                facts = [{"name": k, "value": str(v)} for k, v in fields.items()]

            payload = {
                "@type": "MessageCard",
                "@context": "http://schema.org/extensions",
                "themeColor": theme_color,
                "summary": title or message[:100],
                "sections": [{
                    "activityTitle": title or "Notification",
                    "facts": facts,
                    "text": message,
                    "markdown": True
                }]
            }

            # Send asynchronously
            loop = asyncio.get_running_loop()
            response = await loop.run_in_executor(
                None,
                lambda: requests.post(self.webhook_url, json=payload, timeout=30)
            )

            if response.status_code == 200:
                logger.info("Teams message sent successfully")
                return NotificationResult(
                    channel=NotificationChannel.TEAMS,
                    success=True,
                    recipient="teams_webhook"
                )
            else:
                logger.error(f"Teams webhook error: {response.status_code} - {response.text}")
                return NotificationResult(
                    channel=NotificationChannel.TEAMS,
                    success=False,
                    recipient="teams_webhook",
                    error=f"HTTP {response.status_code}"
                )

        except Exception as e:
            logger.error(f"Failed to send Teams notification: {e}")
            return NotificationResult(
                channel=NotificationChannel.TEAMS,
                success=False,
                recipient="teams_webhook",
                error=str(e)
            )


class EmailNotifier:
    """Real email notification implementation using SMTP"""

    def __init__(self):
        self.host = os.getenv('SMTP_HOST', 'smtp.gmail.com')
        self.port = int(os.getenv('SMTP_PORT', 587))
        self.user = os.getenv('SMTP_USER')
        self.password = os.getenv('SMTP_PASSWORD')
        self.from_addr = os.getenv('SMTP_FROM', self.user)
        self.enabled = bool(self.user and self.password)

        if self.enabled:
            logger.info(f"Email notifications enabled via {self.host}:{self.port}")
        else:
            logger.warning("Email notifications disabled - SMTP credentials not set")

    async def send(
        self,
        to: str,
        subject: str,
        body: str,
        html: bool = True,
        priority: NotificationPriority = NotificationPriority.MEDIUM
    ) -> NotificationResult:
        """Send an email notification"""
        if not self.enabled:
            return NotificationResult(
                channel=NotificationChannel.EMAIL,
                success=False,
                recipient=to,
                error="Email not configured"
            )

        try:
            # Build email message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = self.from_addr
            msg['To'] = to

            # Add priority header
            if priority == NotificationPriority.CRITICAL:
                msg['X-Priority'] = '1'
                msg['Importance'] = 'high'
            elif priority == NotificationPriority.HIGH:
                msg['X-Priority'] = '2'
                msg['Importance'] = 'high'

            # Attach body
            content_type = 'html' if html else 'plain'
            msg.attach(MIMEText(body, content_type))

            # Send via SMTP (run in executor to not block)
            loop = asyncio.get_running_loop()
            await loop.run_in_executor(None, self._send_smtp, msg, to)

            logger.info(f"Email sent to {to}")
            return NotificationResult(
                channel=NotificationChannel.EMAIL,
                success=True,
                recipient=to
            )

        except Exception as e:
            logger.error(f"Failed to send email to {to}: {e}")
            return NotificationResult(
                channel=NotificationChannel.EMAIL,
                success=False,
                recipient=to,
                error=str(e)
            )

    def _send_smtp(self, msg: MIMEMultipart, to: str):
        """Send email via SMTP (blocking - run in executor)"""
        with smtplib.SMTP(self.host, self.port) as server:
            server.starttls()
            server.login(self.user, self.password)
            server.send_message(msg)


class NotificationService:
    """
    Unified notification service that manages all notification channels.

    Usage:
        service = NotificationService()

        # Send to specific channel
        await service.send_slack("Alert!", channel="#alerts")
        await service.send_teams("Alert!", title="System Alert")
        await service.send_email("user@example.com", "Subject", "Body")

        # Send to all configured channels
        await service.broadcast("Critical alert!", priority=NotificationPriority.CRITICAL)
    """

    def __init__(self):
        self.slack = SlackNotifier()
        self.teams = TeamsNotifier()
        self.email = EmailNotifier()

        # Track which channels are available
        self.available_channels = []
        if self.slack.enabled:
            self.available_channels.append(NotificationChannel.SLACK)
        if self.teams.enabled:
            self.available_channels.append(NotificationChannel.TEAMS)
        if self.email.enabled:
            self.available_channels.append(NotificationChannel.EMAIL)

        logger.info(f"NotificationService initialized with channels: {[c.value for c in self.available_channels]}")

    async def send_slack(
        self,
        message: str,
        channel: str = None,
        title: str = None,
        priority: NotificationPriority = NotificationPriority.MEDIUM,
        fields: Dict[str, str] = None
    ) -> NotificationResult:
        """Send a Slack notification"""
        return await self.slack.send(message, channel, title, priority, fields)

    async def send_teams(
        self,
        message: str,
        title: str = None,
        priority: NotificationPriority = NotificationPriority.MEDIUM,
        fields: Dict[str, str] = None
    ) -> NotificationResult:
        """Send a Microsoft Teams notification"""
        return await self.teams.send(message, title, priority, fields)

    async def send_email(
        self,
        to: str,
        subject: str,
        body: str,
        html: bool = True,
        priority: NotificationPriority = NotificationPriority.MEDIUM
    ) -> NotificationResult:
        """Send an email notification"""
        return await self.email.send(to, subject, body, html, priority)

    async def broadcast(
        self,
        message: str,
        title: str = None,
        priority: NotificationPriority = NotificationPriority.MEDIUM,
        fields: Dict[str, str] = None,
        email_recipients: List[str] = None,
        channels: List[NotificationChannel] = None
    ) -> List[NotificationResult]:
        """
        Broadcast a notification to multiple channels.

        Args:
            message: The notification message
            title: Optional title/subject
            priority: Notification priority
            fields: Additional fields to include
            email_recipients: List of email addresses (if sending email)
            channels: Specific channels to use (defaults to all available)

        Returns:
            List of NotificationResult for each channel attempt
        """
        results = []
        target_channels = channels or self.available_channels

        tasks = []

        if NotificationChannel.SLACK in target_channels and self.slack.enabled:
            tasks.append(self.send_slack(message, title=title, priority=priority, fields=fields))

        if NotificationChannel.TEAMS in target_channels and self.teams.enabled:
            tasks.append(self.send_teams(message, title=title, priority=priority, fields=fields))

        if NotificationChannel.EMAIL in target_channels and self.email.enabled and email_recipients:
            for recipient in email_recipients:
                tasks.append(self.send_email(recipient, title or "Notification", message, priority=priority))

        if tasks:
            results = await asyncio.gather(*tasks, return_exceptions=True)
            # Convert exceptions to failed results
            results = [
                r if isinstance(r, NotificationResult) else NotificationResult(
                    channel=NotificationChannel.WEBHOOK,
                    success=False,
                    recipient="unknown",
                    error=str(r)
                )
                for r in results
            ]

        return results

    def get_status(self) -> Dict[str, Any]:
        """Get the status of all notification channels"""
        return {
            "slack": {
                "enabled": self.slack.enabled,
                "channel": self.slack.default_channel if self.slack.enabled else None
            },
            "teams": {
                "enabled": self.teams.enabled
            },
            "email": {
                "enabled": self.email.enabled,
                "host": self.email.host if self.email.enabled else None,
                "from": self.email.from_addr if self.email.enabled else None
            },
            "available_channels": [c.value for c in self.available_channels]
        }


# Global singleton instance
_notification_service: Optional[NotificationService] = None


def get_notification_service() -> NotificationService:
    """Get the global notification service instance"""
    global _notification_service
    if _notification_service is None:
        _notification_service = NotificationService()
    return _notification_service


# Convenience functions for simple usage
async def notify_slack(message: str, **kwargs) -> NotificationResult:
    """Send a Slack notification (convenience function)"""
    return await get_notification_service().send_slack(message, **kwargs)


async def notify_teams(message: str, **kwargs) -> NotificationResult:
    """Send a Teams notification (convenience function)"""
    return await get_notification_service().send_teams(message, **kwargs)


async def notify_email(to: str, subject: str, body: str, **kwargs) -> NotificationResult:
    """Send an email notification (convenience function)"""
    return await get_notification_service().send_email(to, subject, body, **kwargs)


async def broadcast(message: str, **kwargs) -> List[NotificationResult]:
    """Broadcast to all channels (convenience function)"""
    return await get_notification_service().broadcast(message, **kwargs)
