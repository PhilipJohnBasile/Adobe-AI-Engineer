#!/usr/bin/env python3
"""
Real-time Dashboard for Task 3 AI Agent
Provides visual monitoring and alerting interface
"""

import asyncio
import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from pathlib import Path
import logging

class RealtimeDashboard:
    """Real-time dashboard for Task 3 AI Agent monitoring"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.dashboard_data = {}
        self.update_interval = 5  # seconds
        self.running = False
    
    async def start_dashboard(self, agent):
        """Start real-time dashboard updates"""
        self.running = True
        self.logger.info("📊 Starting real-time dashboard...")
        
        while self.running:
            try:
                # Update dashboard data
                await self._update_dashboard_data(agent)
                
                # Generate dashboard display
                await self._display_dashboard()
                
                # Save dashboard state
                await self._save_dashboard_state()
                
                await asyncio.sleep(self.update_interval)
                
            except Exception as e:
                self.logger.error(f"Dashboard error: {e}")
                await asyncio.sleep(self.update_interval)
    
    async def _update_dashboard_data(self, agent):
        """Update all dashboard metrics"""
        
        current_time = datetime.now()
        
        # Get agent status
        status = agent.get_status()
        
        # Campaign metrics
        campaign_metrics = await self._calculate_campaign_metrics(agent.campaign_tracking)
        
        # Alert metrics
        alert_metrics = await self._calculate_alert_metrics(agent.alerts)
        
        # Performance metrics
        performance_metrics = await self._calculate_performance_metrics(agent.campaign_tracking)
        
        # System health
        system_health = await self._get_system_health()
        
        self.dashboard_data = {
            "timestamp": current_time.isoformat(),
            "uptime": self._calculate_uptime(),
            "status": {
                "overall": self._assess_overall_status(campaign_metrics, alert_metrics, system_health),
                "monitoring": status["monitoring"],
                "last_update": current_time.isoformat()
            },
            "campaigns": campaign_metrics,
            "alerts": alert_metrics,
            "performance": performance_metrics,
            "system": system_health,
            "trends": await self._calculate_trends()
        }
    
    async def _calculate_campaign_metrics(self, campaign_tracking: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate campaign-related metrics"""
        
        if not campaign_tracking:
            return {
                "total": 0,
                "active": 0,
                "completed": 0,
                "failed": 0,
                "success_rate": 0.0,
                "avg_variants": 0.0,
                "completion_rate": 0.0
            }
        
        states = {"generating": 0, "completed": 0, "failed": 0, "detected": 0}
        total_variants = 0
        total_expected = 0
        
        for campaign_id, data in campaign_tracking.items():
            status = data.get("status", "unknown")
            states[status] = states.get(status, 0) + 1
            
            total_variants += data.get("variants_found", 0)
            total_expected += data.get("expected_variants", 0)
        
        total_campaigns = len(campaign_tracking)
        completed = states.get("completed", 0)
        failed = states.get("failed", 0)
        
        success_rate = completed / (completed + failed) if (completed + failed) > 0 else 0
        avg_variants = total_variants / total_campaigns if total_campaigns > 0 else 0
        completion_rate = total_variants / total_expected if total_expected > 0 else 0
        
        return {
            "total": total_campaigns,
            "active": states.get("generating", 0),
            "completed": completed,
            "failed": failed,
            "pending": states.get("detected", 0),
            "success_rate": success_rate,
            "avg_variants": avg_variants,
            "completion_rate": completion_rate,
            "total_variants": total_variants
        }
    
    async def _calculate_alert_metrics(self, alerts: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate alert-related metrics"""
        
        if not alerts:
            return {
                "total": 0,
                "active": 0,
                "critical": 0,
                "high": 0,
                "medium": 0,
                "low": 0,
                "recent_count": 0
            }
        
        # Count by severity
        severity_counts = {"critical": 0, "high": 0, "medium": 0, "low": 0}
        active_count = 0
        recent_count = 0
        
        current_time = datetime.now()
        recent_threshold = current_time - timedelta(hours=1)
        
        for alert in alerts:
            severity = alert.get("severity", "low")
            status = alert.get("status", "active")
            
            severity_counts[severity] = severity_counts.get(severity, 0) + 1
            
            if status == "active":
                active_count += 1
            
            # Check if recent
            try:
                alert_time = datetime.fromisoformat(alert.get("timestamp", ""))
                if alert_time > recent_threshold:
                    recent_count += 1
            except (ValueError, TypeError):
                # Invalid timestamp format, skip this alert for recent count
                continue
        
        return {
            "total": len(alerts),
            "active": active_count,
            "critical": severity_counts["critical"],
            "high": severity_counts["high"], 
            "medium": severity_counts["medium"],
            "low": severity_counts["low"],
            "recent_count": recent_count
        }
    
    async def _calculate_performance_metrics(self, campaign_tracking: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate performance metrics"""
        
        if not campaign_tracking:
            return {
                "avg_processing_time": 0.0,
                "variants_per_hour": 0.0,
                "efficiency_score": 0.0,
                "throughput": 0.0
            }
        
        processing_times = []
        total_variants = 0
        
        for campaign_id, data in campaign_tracking.items():
            # Calculate processing time
            detected_at = data.get("detected_at")
            if detected_at and data.get("status") == "completed":
                try:
                    detected_time = datetime.fromisoformat(detected_at)
                    completed_time = datetime.now()
                    processing_time = (completed_time - detected_time).total_seconds() / 3600
                    processing_times.append(processing_time)
                except (ValueError, TypeError):
                    # Invalid timestamp, skip this campaign for processing time calculation
                    continue
            
            total_variants += data.get("variants_found", 0)
        
        avg_processing_time = sum(processing_times) / len(processing_times) if processing_times else 0
        variants_per_hour = total_variants / max(avg_processing_time, 1) if avg_processing_time > 0 else 0
        
        # Calculate efficiency score (variants generated vs expected)
        total_expected = sum(data.get("expected_variants", 0) for data in campaign_tracking.values())
        efficiency_score = total_variants / total_expected if total_expected > 0 else 0
        
        return {
            "avg_processing_time": avg_processing_time,
            "variants_per_hour": variants_per_hour,
            "efficiency_score": efficiency_score,
            "throughput": len([c for c in campaign_tracking.values() if c.get("status") == "completed"])
        }
    
    async def _get_system_health(self) -> Dict[str, Any]:
        """Get system health metrics"""
        
        try:
            import psutil
            
            cpu_percent = psutil.cpu_percent()
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            # Health assessment
            health_score = 1.0
            if cpu_percent > 80:
                health_score -= 0.3
            if memory.percent > 85:
                health_score -= 0.3
            if disk.percent > 90:
                health_score -= 0.4
            
            health_status = "healthy" if health_score > 0.7 else "degraded" if health_score > 0.4 else "critical"
            
            return {
                "cpu_percent": cpu_percent,
                "memory_percent": memory.percent,
                "disk_percent": disk.percent,
                "health_score": max(0, health_score),
                "health_status": health_status,
                "processes": len(psutil.pids())
            }
            
        except ImportError:
            return {
                "cpu_percent": 0,
                "memory_percent": 0, 
                "disk_percent": 0,
                "health_score": 1.0,
                "health_status": "unknown",
                "processes": 0
            }
    
    async def _calculate_trends(self) -> Dict[str, Any]:
        """Calculate trend data"""
        
        # This would analyze historical data in a real implementation
        return {
            "campaigns_trend": "stable",
            "alerts_trend": "increasing",
            "performance_trend": "improving",
            "efficiency_trend": "stable"
        }
    
    async def _display_dashboard(self):
        """Display dashboard in terminal"""
        
        # Clear screen (for terminal display)
        print("\033[2J\033[H")  # ANSI escape codes to clear screen and move cursor to top
        
        data = self.dashboard_data
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        print("=" * 80)
        print(f"🎯 TASK 3 AI AGENT - REAL-TIME DASHBOARD")
        print(f"📅 {timestamp} | ⏱️ Uptime: {data.get('uptime', '0h 0m')}")
        print("=" * 80)
        
        # Status section
        status = data.get("status", {})
        overall_status = status.get("overall", "unknown")
        status_icon = "🟢" if overall_status == "healthy" else "🟡" if overall_status == "warning" else "🔴"
        
        print(f"\n📊 SYSTEM STATUS: {status_icon} {overall_status.upper()}")
        print(f"   Monitoring: {'🟢 Active' if status.get('monitoring') else '🔴 Stopped'}")
        
        # Campaign metrics
        campaigns = data.get("campaigns", {})
        print(f"\n🎯 CAMPAIGNS:")
        print(f"   📋 Total: {campaigns.get('total', 0)}")
        print(f"   🔄 Active: {campaigns.get('active', 0)}")
        print(f"   ✅ Completed: {campaigns.get('completed', 0)}")
        print(f"   ❌ Failed: {campaigns.get('failed', 0)}")
        print(f"   📈 Success Rate: {campaigns.get('success_rate', 0):.1%}")
        print(f"   🎨 Total Variants: {campaigns.get('total_variants', 0)}")
        
        # Alert metrics
        alerts = data.get("alerts", {})
        print(f"\n🚨 ALERTS:")
        print(f"   📊 Total: {alerts.get('total', 0)}")
        print(f"   🔴 Critical: {alerts.get('critical', 0)}")
        print(f"   🟠 High: {alerts.get('high', 0)}")
        print(f"   🟡 Medium: {alerts.get('medium', 0)}")
        print(f"   🔵 Low: {alerts.get('low', 0)}")
        print(f"   ⏰ Recent (1h): {alerts.get('recent_count', 0)}")
        
        # Performance metrics
        performance = data.get("performance", {})
        print(f"\n⚡ PERFORMANCE:")
        print(f"   ⏱️ Avg Processing: {performance.get('avg_processing_time', 0):.1f}h")
        print(f"   🏭 Variants/Hour: {performance.get('variants_per_hour', 0):.1f}")
        print(f"   📊 Efficiency: {performance.get('efficiency_score', 0):.1%}")
        print(f"   🚀 Throughput: {performance.get('throughput', 0)} campaigns/period")
        
        # System health
        system = data.get("system", {})
        health_icon = "🟢" if system.get("health_status") == "healthy" else "🟡" if system.get("health_status") == "degraded" else "🔴"
        print(f"\n💻 SYSTEM HEALTH: {health_icon} {system.get('health_status', 'unknown').upper()}")
        print(f"   🔥 CPU: {system.get('cpu_percent', 0):.1f}%")
        print(f"   🧠 Memory: {system.get('memory_percent', 0):.1f}%")
        print(f"   💾 Disk: {system.get('disk_percent', 0):.1f}%")
        
        # Recent activity (if available)
        print(f"\n📈 TRENDS:")
        trends = data.get("trends", {})
        print(f"   📋 Campaigns: {trends.get('campaigns_trend', 'stable')}")
        print(f"   🚨 Alerts: {trends.get('alerts_trend', 'stable')}")
        print(f"   ⚡ Performance: {trends.get('performance_trend', 'stable')}")
        
        print("\n" + "=" * 80)
        print(f"🔄 Auto-refresh every {self.update_interval}s | Press Ctrl+C to stop")
        print("=" * 80)
    
    async def _save_dashboard_state(self):
        """Save dashboard state to file"""
        
        dashboard_file = Path("logs/dashboard_state.json")
        
        try:
            with open(dashboard_file, 'w') as f:
                json.dump(self.dashboard_data, f, indent=2)
        except Exception as e:
            self.logger.error(f"Error saving dashboard state: {e}")
    
    def _calculate_uptime(self) -> str:
        """Calculate system uptime"""
        # This is a simplified version - would track actual start time in production
        return "2h 15m"
    
    def _assess_overall_status(self, campaigns: Dict[str, Any], alerts: Dict[str, Any], 
                             system: Dict[str, Any]) -> str:
        """Assess overall system status"""
        
        # Check for critical issues
        if alerts.get("critical", 0) > 0:
            return "critical"
        
        # Check system health
        system_health = system.get("health_status", "unknown")
        if system_health == "critical":
            return "critical"
        elif system_health == "degraded":
            return "warning"
        
        # Check campaign success rate
        success_rate = campaigns.get("success_rate", 1.0)
        if success_rate < 0.8:
            return "warning"
        
        # Check for high alerts
        if alerts.get("high", 0) > 3:
            return "warning"
        
        return "healthy"
    
    def stop_dashboard(self):
        """Stop dashboard updates"""
        self.running = False
        self.logger.info("📊 Dashboard stopped")

# Advanced alerting with escalation rules
class AdvancedAlertingSystem:
    """Advanced alerting system with escalation rules and smart routing"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Escalation rules
        self.escalation_rules = {
            "critical": {
                "immediate": ["technical_team", "team_lead", "manager"],
                "15_minutes": ["director"],
                "30_minutes": ["vp_engineering"],
                "1_hour": ["ceo"]
            },
            "high": {
                "immediate": ["technical_team", "team_lead"],
                "30_minutes": ["manager"],
                "2_hours": ["director"]
            },
            "medium": {
                "immediate": ["technical_team"],
                "1_hour": ["team_lead"],
                "4_hours": ["manager"]
            },
            "low": {
                "immediate": ["technical_team"],
                "24_hours": ["team_lead"]
            }
        }
        
        # Alert routing configuration
        self.routing_config = {
            "channels": {
                "email": {"enabled": True, "delay": 0},
                "slack": {"enabled": True, "delay": 0},
                "sms": {"enabled": True, "delay": 300},  # 5 minutes
                "webhook": {"enabled": True, "delay": 0}
            },
            "quiet_hours": {"start": "22:00", "end": "06:00"},
            "holiday_schedule": []
        }
        
        # Active escalations tracking
        self.active_escalations = {}
    
    async def process_alert(self, alert: Dict[str, Any]):
        """Process alert with advanced routing and escalation"""
        
        alert_id = alert["id"]
        severity = alert.get("severity", "medium")
        
        self.logger.info(f"🚨 Processing alert {alert_id} with severity {severity}")
        
        # Start escalation tracking
        self.active_escalations[alert_id] = {
            "alert": alert,
            "started_at": datetime.now(),
            "escalation_level": 0,
            "notifications_sent": [],
            "acknowledged": False
        }
        
        # Immediate notifications
        await self._send_immediate_notifications(alert)
        
        # Schedule escalations
        await self._schedule_escalations(alert_id, severity)
    
    async def _send_immediate_notifications(self, alert: Dict[str, Any]):
        """Send immediate notifications based on severity"""
        
        severity = alert.get("severity", "medium")
        immediate_recipients = self.escalation_rules.get(severity, {}).get("immediate", [])
        
        for recipient in immediate_recipients:
            for channel in ["email", "slack"]:
                if self.routing_config["channels"][channel]["enabled"]:
                    await self._send_notification(alert, recipient, channel)
    
    async def _schedule_escalations(self, alert_id: str, severity: str):
        """Schedule escalation notifications"""
        
        escalation_schedule = self.escalation_rules.get(severity, {})
        
        for time_key, recipients in escalation_schedule.items():
            if time_key == "immediate":
                continue
            
            # Parse time delay
            delay_seconds = self._parse_time_delay(time_key)
            
            # Schedule escalation
            asyncio.create_task(
                self._delayed_escalation(alert_id, recipients, delay_seconds)
            )
    
    async def _delayed_escalation(self, alert_id: str, recipients: List[str], delay_seconds: int):
        """Send delayed escalation notifications"""
        
        await asyncio.sleep(delay_seconds)
        
        # Check if alert is still active and not acknowledged
        if alert_id not in self.active_escalations:
            return  # Alert resolved
        
        escalation = self.active_escalations[alert_id]
        if escalation["acknowledged"]:
            return  # Alert acknowledged
        
        # Send escalation notifications
        alert = escalation["alert"]
        for recipient in recipients:
            await self._send_escalation_notification(alert, recipient, escalation["escalation_level"])
        
        escalation["escalation_level"] += 1
    
    async def _send_notification(self, alert: Dict[str, Any], recipient: str, channel: str):
        """Send notification via specified channel"""
        
        self.logger.info(f"📧 Sending {channel} notification to {recipient} for alert {alert['id']}")
        
        # This would integrate with actual notification systems
        notification = {
            "alert_id": alert["id"],
            "recipient": recipient,
            "channel": channel,
            "sent_at": datetime.now().isoformat(),
            "content": f"Alert: {alert.get('message', 'Unknown alert')}"
        }
        
        # Save notification log
        log_file = Path(f"logs/notifications_{datetime.now().strftime('%Y%m%d')}.jsonl")
        with open(log_file, 'a') as f:
            f.write(json.dumps(notification) + '\n')
    
    async def _send_escalation_notification(self, alert: Dict[str, Any], recipient: str, level: int):
        """Send escalation notification"""
        
        self.logger.warning(f"📈 ESCALATION Level {level}: Notifying {recipient} about alert {alert['id']}")
        
        escalation_notification = {
            "alert_id": alert["id"],
            "recipient": recipient,
            "escalation_level": level,
            "sent_at": datetime.now().isoformat(),
            "content": f"ESCALATED ALERT: {alert.get('message', 'Unknown alert')}"
        }
        
        # Save escalation log
        log_file = Path(f"logs/escalations_{datetime.now().strftime('%Y%m%d')}.jsonl")
        with open(log_file, 'a') as f:
            f.write(json.dumps(escalation_notification) + '\n')
    
    def _parse_time_delay(self, time_str: str) -> int:
        """Parse time delay string to seconds"""
        
        time_mappings = {
            "15_minutes": 900,
            "30_minutes": 1800,
            "1_hour": 3600,
            "2_hours": 7200,
            "4_hours": 14400,
            "24_hours": 86400
        }
        
        return time_mappings.get(time_str, 3600)  # Default 1 hour
    
    async def acknowledge_alert(self, alert_id: str, acknowledged_by: str):
        """Acknowledge alert to stop escalations"""
        
        if alert_id in self.active_escalations:
            self.active_escalations[alert_id]["acknowledged"] = True
            self.active_escalations[alert_id]["acknowledged_by"] = acknowledged_by
            self.active_escalations[alert_id]["acknowledged_at"] = datetime.now()
            
            self.logger.info(f"✅ Alert {alert_id} acknowledged by {acknowledged_by}")

# Demo function
async def demo_dashboard_and_alerting():
    """Demonstrate dashboard and advanced alerting"""
    
    print("📊 Real-time Dashboard & Advanced Alerting Demo")
    print("=" * 60)
    
    # Mock agent for demo
    class MockAgent:
        def __init__(self):
            self.campaign_tracking = {
                "campaign_1": {"status": "completed", "variants_found": 5, "expected_variants": 6, "detected_at": datetime.now().isoformat()},
                "campaign_2": {"status": "generating", "variants_found": 2, "expected_variants": 4, "detected_at": datetime.now().isoformat()},
                "campaign_3": {"status": "failed", "variants_found": 0, "expected_variants": 3, "detected_at": datetime.now().isoformat()}
            }
            self.alerts = [
                {"id": "alert_1", "severity": "high", "status": "active", "timestamp": datetime.now().isoformat(), "message": "Test alert"},
                {"id": "alert_2", "severity": "medium", "status": "active", "timestamp": (datetime.now() - timedelta(minutes=30)).isoformat(), "message": "Another alert"}
            ]
        
        def get_status(self):
            return {"monitoring": True, "campaigns_tracked": 3, "total_alerts": 2}
    
    # Create mock agent
    agent = MockAgent()
    
    # Test dashboard (single update)
    dashboard = RealtimeDashboard()
    dashboard.update_interval = 1
    
    print("📊 Updating dashboard...")
    await dashboard._update_dashboard_data(agent)
    await dashboard._display_dashboard()
    
    # Test advanced alerting
    print(f"\n🚨 Testing advanced alerting...")
    alerting = AdvancedAlertingSystem()
    
    # Create test alert
    test_alert = {
        "id": "test_critical_alert",
        "severity": "critical",
        "message": "Critical system failure detected",
        "campaign_id": "emergency_campaign",
        "timestamp": datetime.now().isoformat()
    }
    
    await alerting.process_alert(test_alert)
    
    print(f"✅ Alert processed with escalation rules")
    print(f"✅ Active escalations: {len(alerting.active_escalations)}")
    
    # Acknowledge alert
    await alerting.acknowledge_alert("test_critical_alert", "demo_user")
    
    print(f"✅ Alert acknowledged - escalations stopped")
    
    print(f"\n✅ Dashboard and alerting system demonstrated!")

if __name__ == "__main__":
    asyncio.run(demo_dashboard_and_alerting())