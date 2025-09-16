"""
Webhook Notifications System
Provides real-time alerts and notifications for creative automation events
"""

import json
import requests
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, asdict
from enum import Enum
import uuid
import hashlib
import hmac
import logging


class EventType(Enum):
    CAMPAIGN_STARTED = "campaign.started"
    CAMPAIGN_COMPLETED = "campaign.completed"
    CAMPAIGN_FAILED = "campaign.failed"
    BATCH_STARTED = "batch.started"
    BATCH_COMPLETED = "batch.completed"
    BATCH_FAILED = "batch.failed"
    COMPLIANCE_WARNING = "compliance.warning"
    COMPLIANCE_VIOLATION = "compliance.violation"
    COST_THRESHOLD = "cost.threshold"
    SYSTEM_ERROR = "system.error"
    AB_TEST_SIGNIFICANT = "ab_test.significant"
    AB_TEST_COMPLETED = "ab_test.completed"


class Priority(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class WebhookEvent:
    """Represents a webhook event to be sent"""
    event_id: str
    event_type: EventType
    timestamp: str
    priority: Priority
    data: Dict[str, Any]
    retry_count: int = 0
    max_retries: int = 3
    
    def to_payload(self) -> Dict[str, Any]:
        """Convert to webhook payload format"""
        return {
            "event_id": self.event_id,
            "event_type": self.event_type.value,
            "timestamp": self.timestamp,
            "priority": self.priority.value,
            "data": self.data,
            "version": "1.0"
        }


@dataclass
class WebhookEndpoint:
    """Webhook endpoint configuration"""
    url: str
    secret: Optional[str] = None
    event_types: List[EventType] = None
    headers: Dict[str, str] = None
    timeout: int = 30
    enabled: bool = True
    description: str = ""
    
    def __post_init__(self):
        if self.event_types is None:
            self.event_types = list(EventType)
        if self.headers is None:
            self.headers = {}


class WebhookNotificationSystem:
    """Manages webhook notifications for the creative automation pipeline"""
    
    def __init__(self, config_path: str = "webhook_config.json"):
        self.config_path = config_path
        self.endpoints: List[WebhookEndpoint] = []
        self.pending_events: List[WebhookEvent] = []
        self.sent_events: List[WebhookEvent] = []
        self.failed_events: List[WebhookEvent] = []
        
        self.logger = logging.getLogger(__name__)
        self.load_config()
    
    def add_endpoint(
        self,
        url: str,
        secret: Optional[str] = None,
        event_types: Optional[List[EventType]] = None,
        headers: Optional[Dict[str, str]] = None,
        description: str = ""
    ) -> str:
        """Add a new webhook endpoint"""
        endpoint = WebhookEndpoint(
            url=url,
            secret=secret,
            event_types=event_types or list(EventType),
            headers=headers or {},
            description=description
        )
        
        self.endpoints.append(endpoint)
        self.save_config()
        return url
    
    def remove_endpoint(self, url: str) -> bool:
        """Remove a webhook endpoint"""
        original_count = len(self.endpoints)
        self.endpoints = [ep for ep in self.endpoints if ep.url != url]
        
        if len(self.endpoints) < original_count:
            self.save_config()
            return True
        return False
    
    def update_endpoint(self, url: str, **kwargs) -> bool:
        """Update an existing webhook endpoint"""
        for endpoint in self.endpoints:
            if endpoint.url == url:
                for key, value in kwargs.items():
                    if hasattr(endpoint, key):
                        setattr(endpoint, key, value)
                self.save_config()
                return True
        return False
    
    def create_event(
        self,
        event_type: EventType,
        data: Dict[str, Any],
        priority: Priority = Priority.MEDIUM
    ) -> str:
        """Create a new webhook event"""
        event = WebhookEvent(
            event_id=str(uuid.uuid4()),
            event_type=event_type,
            timestamp=datetime.now().isoformat(),
            priority=priority,
            data=data
        )
        
        self.pending_events.append(event)
        return event.event_id
    
    async def send_event(self, event: WebhookEvent) -> Dict[str, Any]:
        """Send event to all relevant endpoints"""
        results = []
        
        for endpoint in self.endpoints:
            if not endpoint.enabled:
                continue
            
            if event.event_type not in endpoint.event_types:
                continue
            
            try:
                result = await self._send_to_endpoint(event, endpoint)
                results.append({
                    "endpoint": endpoint.url,
                    "status": "success" if result["success"] else "failed",
                    "response_code": result.get("status_code"),
                    "response_time": result.get("response_time")
                })
            except Exception as e:
                self.logger.error(f"Failed to send to {endpoint.url}: {e}")
                results.append({
                    "endpoint": endpoint.url,
                    "status": "error",
                    "error": str(e)
                })
        
        return {
            "event_id": event.event_id,
            "endpoints_contacted": len(results),
            "results": results
        }
    
    async def _send_to_endpoint(self, event: WebhookEvent, endpoint: WebhookEndpoint) -> Dict[str, Any]:
        """Send event to a specific endpoint"""
        payload = event.to_payload()
        headers = {
            "Content-Type": "application/json",
            "User-Agent": "Creative-Automation-Pipeline/1.0",
            **endpoint.headers
        }
        
        # Add signature if secret is configured
        if endpoint.secret:
            payload_json = json.dumps(payload)
            signature = self._generate_signature(payload_json, endpoint.secret)
            headers["X-Webhook-Signature"] = signature
        
        start_time = datetime.now()
        
        try:
            async with asyncio.timeout(endpoint.timeout):
                # Use aiohttp in production for better async support
                response = await asyncio.get_event_loop().run_in_executor(
                    None,
                    lambda: requests.post(
                        endpoint.url,
                        json=payload,
                        headers=headers,
                        timeout=endpoint.timeout
                    )
                )
            
            response_time = (datetime.now() - start_time).total_seconds()
            
            return {
                "success": response.status_code < 300,
                "status_code": response.status_code,
                "response_time": response_time,
                "response_text": response.text[:1000]  # Truncate long responses
            }
            
        except Exception as e:
            response_time = (datetime.now() - start_time).total_seconds()
            return {
                "success": False,
                "error": str(e),
                "response_time": response_time
            }
    
    def _generate_signature(self, payload: str, secret: str) -> str:
        """Generate HMAC signature for webhook payload"""
        signature = hmac.new(
            secret.encode('utf-8'),
            payload.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        return f"sha256={signature}"
    
    async def process_pending_events(self) -> Dict[str, Any]:
        """Process all pending webhook events"""
        if not self.pending_events:
            return {"processed": 0, "failed": 0}
        
        processed = 0
        failed = 0
        
        events_to_process = self.pending_events.copy()
        self.pending_events.clear()
        
        for event in events_to_process:
            try:
                result = await self.send_event(event)
                
                # Check if any endpoint succeeded
                success_count = sum(1 for r in result["results"] if r["status"] == "success")
                
                if success_count > 0:
                    self.sent_events.append(event)
                    processed += 1
                else:
                    # Retry logic
                    event.retry_count += 1
                    if event.retry_count < event.max_retries:
                        # Add back to pending with exponential backoff
                        await asyncio.sleep(2 ** event.retry_count)
                        self.pending_events.append(event)
                    else:
                        self.failed_events.append(event)
                        failed += 1
                
            except Exception as e:
                self.logger.error(f"Error processing event {event.event_id}: {e}")
                event.retry_count += 1
                if event.retry_count < event.max_retries:
                    self.pending_events.append(event)
                else:
                    self.failed_events.append(event)
                    failed += 1
        
        return {"processed": processed, "failed": failed}
    
    def get_stats(self) -> Dict[str, Any]:
        """Get webhook system statistics"""
        return {
            "endpoints": len(self.endpoints),
            "active_endpoints": len([ep for ep in self.endpoints if ep.enabled]),
            "pending_events": len(self.pending_events),
            "sent_events": len(self.sent_events),
            "failed_events": len(self.failed_events),
            "retry_queue": len([e for e in self.pending_events if e.retry_count > 0])
        }
    
    def save_config(self):
        """Save webhook configuration to file"""
        try:
            config = {
                "endpoints": [
                    {
                        "url": ep.url,
                        "secret": ep.secret,
                        "event_types": [et.value for et in ep.event_types],
                        "headers": ep.headers,
                        "timeout": ep.timeout,
                        "enabled": ep.enabled,
                        "description": ep.description
                    }
                    for ep in self.endpoints
                ]
            }
            
            with open(self.config_path, 'w') as f:
                json.dump(config, f, indent=2)
        except Exception as e:
            self.logger.error(f"Error saving webhook config: {e}")
    
    def load_config(self):
        """Load webhook configuration from file"""
        try:
            if not os.path.exists(self.config_path):
                return
            
            with open(self.config_path, 'r') as f:
                config = json.load(f)
            
            self.endpoints = []
            for ep_data in config.get("endpoints", []):
                endpoint = WebhookEndpoint(
                    url=ep_data["url"],
                    secret=ep_data.get("secret"),
                    event_types=[EventType(et) for et in ep_data.get("event_types", [])],
                    headers=ep_data.get("headers", {}),
                    timeout=ep_data.get("timeout", 30),
                    enabled=ep_data.get("enabled", True),
                    description=ep_data.get("description", "")
                )
                self.endpoints.append(endpoint)
        except Exception as e:
            self.logger.error(f"Error loading webhook config: {e}")


class NotificationTemplates:
    """Pre-built notification templates for common events"""
    
    @staticmethod
    def campaign_completed(campaign_id: str, assets_generated: int, duration: float, cost: float) -> Dict[str, Any]:
        """Template for campaign completion notification"""
        return {
            "title": "Campaign Completed Successfully",
            "campaign_id": campaign_id,
            "summary": f"Generated {assets_generated} assets in {duration:.1f}s for ${cost:.2f}",
            "metrics": {
                "assets_generated": assets_generated,
                "duration_seconds": duration,
                "cost_usd": cost,
                "assets_per_minute": (assets_generated / (duration / 60)) if duration > 0 else 0
            },
            "status": "success"
        }
    
    @staticmethod
    def campaign_failed(campaign_id: str, error: str, stage: str) -> Dict[str, Any]:
        """Template for campaign failure notification"""
        return {
            "title": "Campaign Generation Failed",
            "campaign_id": campaign_id,
            "error": error,
            "failed_stage": stage,
            "status": "failed",
            "requires_attention": True
        }
    
    @staticmethod
    def compliance_violation(campaign_id: str, violations: List[str], severity: str) -> Dict[str, Any]:
        """Template for compliance violation notification"""
        return {
            "title": f"Compliance {severity.title()} Detected",
            "campaign_id": campaign_id,
            "violations": violations,
            "severity": severity,
            "action_required": severity == "critical",
            "status": "warning" if severity == "warning" else "blocked"
        }
    
    @staticmethod
    def cost_threshold(current_cost: float, threshold: float, period: str) -> Dict[str, Any]:
        """Template for cost threshold notification"""
        return {
            "title": "Cost Threshold Exceeded",
            "current_cost": current_cost,
            "threshold": threshold,
            "period": period,
            "percentage_over": ((current_cost - threshold) / threshold * 100),
            "action_required": True,
            "status": "warning"
        }
    
    @staticmethod
    def ab_test_significant(test_id: str, test_name: str, winner: str, improvement: float) -> Dict[str, Any]:
        """Template for A/B test significance notification"""
        return {
            "title": "A/B Test Shows Significant Results",
            "test_id": test_id,
            "test_name": test_name,
            "winner": winner,
            "improvement_percentage": improvement,
            "action_recommended": "Consider implementing winning variant",
            "status": "significant"
        }
    
    @staticmethod
    def system_error(error_type: str, error_message: str, component: str) -> Dict[str, Any]:
        """Template for system error notification"""
        return {
            "title": f"System Error in {component}",
            "error_type": error_type,
            "error_message": error_message,
            "component": component,
            "timestamp": datetime.now().isoformat(),
            "severity": "high",
            "requires_attention": True
        }


# Integration with main pipeline
class PipelineNotifier:
    """Integration class for pipeline notifications"""
    
    def __init__(self, webhook_system: WebhookNotificationSystem):
        self.webhook_system = webhook_system
    
    async def notify_campaign_started(self, campaign_id: str, products: int):
        """Notify that a campaign has started"""
        data = {
            "title": "Campaign Generation Started",
            "campaign_id": campaign_id,
            "products_count": products,
            "status": "started"
        }
        
        self.webhook_system.create_event(
            EventType.CAMPAIGN_STARTED,
            data,
            Priority.LOW
        )
    
    async def notify_campaign_completed(self, campaign_id: str, assets_generated: int, duration: float, cost: float):
        """Notify that a campaign has completed successfully"""
        data = NotificationTemplates.campaign_completed(campaign_id, assets_generated, duration, cost)
        
        self.webhook_system.create_event(
            EventType.CAMPAIGN_COMPLETED,
            data,
            Priority.MEDIUM
        )
    
    async def notify_campaign_failed(self, campaign_id: str, error: str, stage: str):
        """Notify that a campaign has failed"""
        data = NotificationTemplates.campaign_failed(campaign_id, error, stage)
        
        self.webhook_system.create_event(
            EventType.CAMPAIGN_FAILED,
            data,
            Priority.HIGH
        )
    
    async def notify_compliance_issue(self, campaign_id: str, violations: List[str], severity: str):
        """Notify of compliance issues"""
        data = NotificationTemplates.compliance_violation(campaign_id, violations, severity)
        
        event_type = EventType.COMPLIANCE_VIOLATION if severity == "critical" else EventType.COMPLIANCE_WARNING
        priority = Priority.CRITICAL if severity == "critical" else Priority.MEDIUM
        
        self.webhook_system.create_event(event_type, data, priority)
    
    async def notify_cost_threshold(self, current_cost: float, threshold: float, period: str):
        """Notify when cost threshold is exceeded"""
        data = NotificationTemplates.cost_threshold(current_cost, threshold, period)
        
        self.webhook_system.create_event(
            EventType.COST_THRESHOLD,
            data,
            Priority.HIGH
        )
    
    async def notify_ab_test_significant(self, test_id: str, test_name: str, winner: str, improvement: float):
        """Notify when A/B test shows significant results"""
        data = NotificationTemplates.ab_test_significant(test_id, test_name, winner, improvement)
        
        self.webhook_system.create_event(
            EventType.AB_TEST_SIGNIFICANT,
            data,
            Priority.MEDIUM
        )


# Example webhook receiver for testing
def example_webhook_receiver():
    """Example Flask webhook receiver for testing"""
    try:
        from flask import Flask, request, jsonify
        
        app = Flask(__name__)
        
        @app.route('/webhook', methods=['POST'])
        def receive_webhook():
            data = request.get_json()
            
            print(f"Received webhook: {data['event_type']}")
            print(f"Event ID: {data['event_id']}")
            print(f"Priority: {data['priority']}")
            print(f"Data: {json.dumps(data['data'], indent=2)}")
            
            # Verify signature if present
            signature = request.headers.get('X-Webhook-Signature')
            if signature:
                # Implement signature verification
                print(f"Signature: {signature}")
            
            return jsonify({"status": "received"}), 200
        
        return app
    except ImportError:
        return None


# CLI integration will be added to main.py
import os