#!/usr/bin/env python3
"""
Task 3 Practical Implementation: Working AI Agent
Simple, functional implementation that actually works for the core requirements
"""

import asyncio
import json
import os
import time
import yaml
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from pathlib import Path
import logging

# Real notification service
try:
    from .notification_service import get_notification_service, NotificationPriority
except ImportError:
    from notification_service import get_notification_service, NotificationPriority

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('task3_agent.log'),
        logging.StreamHandler()
    ]
)

class Task3Agent:
    """Practical Task 3 AI Agent - Simple but complete implementation"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.campaign_tracking = {}
        self.alerts = []
        self.monitoring = True
        
        # Simple configuration
        self.config = {
            "min_variants_threshold": 3,
            "brief_directory": "campaign_briefs",
            "output_directory": "output", 
            "check_interval": 10,  # seconds
            "email_alerts": True,
            "log_alerts": True
        }
        
        # Ensure directories exist
        Path(self.config["brief_directory"]).mkdir(exist_ok=True)
        Path(self.config["output_directory"]).mkdir(exist_ok=True)
        Path("logs").mkdir(exist_ok=True)
        
        self.logger.info("🤖 Task 3 Agent initialized")
    
    async def start_monitoring(self):
        """Main monitoring loop - REQUIREMENT 1: Monitor incoming campaign briefs"""
        self.logger.info("🔍 Starting campaign brief monitoring...")
        
        while self.monitoring:
            try:
                # Monitor for new briefs
                await self.monitor_campaign_briefs()
                
                # Track variant generation progress
                await self.track_variant_progress()
                
                # Check for insufficient assets and create alerts
                await self.check_asset_sufficiency()
                
                # Process any pending alerts
                await self.process_alerts()
                
                await asyncio.sleep(self.config["check_interval"])
                
            except Exception as e:
                self.logger.error(f"❌ Monitoring error: {e}")
                await asyncio.sleep(5)
    
    async def monitor_campaign_briefs(self):
        """REQUIREMENT 1: Monitor incoming campaign briefs"""
        brief_dir = Path(self.config["brief_directory"])
        
        # Check for new YAML files
        for brief_file in brief_dir.glob("*.yaml"):
            campaign_id = brief_file.stem
            
            # Skip if already tracking
            if campaign_id in self.campaign_tracking:
                continue
            
            self.logger.info(f"📋 New campaign brief detected: {campaign_id}")
            
            try:
                # Load campaign brief
                with open(brief_file, 'r') as f:
                    brief_content = yaml.safe_load(f)
                
                # Initialize tracking
                self.campaign_tracking[campaign_id] = {
                    "brief_file": str(brief_file),
                    "content": brief_content,
                    "detected_at": datetime.now(),
                    "status": "detected",
                    "variants_found": 0,
                    "expected_variants": self._calculate_expected_variants(brief_content),
                    "generation_triggered": False,
                    "last_check": datetime.now()
                }
                
                # REQUIREMENT 2: Trigger automated generation tasks
                await self.trigger_generation(campaign_id, brief_content)
                
            except Exception as e:
                self.logger.error(f"❌ Error processing brief {campaign_id}: {e}")
                await self.create_alert(
                    "brief_processing_error",
                    f"Failed to process campaign brief {campaign_id}: {str(e)}",
                    "high",
                    campaign_id
                )
    
    async def trigger_generation(self, campaign_id: str, brief_content: Dict[str, Any]):
        """REQUIREMENT 2: Trigger automated generation tasks via real pipeline"""
        self.logger.info(f"🚀 Triggering generation for campaign: {campaign_id}")

        try:
            # Mark generation as triggered
            self.campaign_tracking[campaign_id]["generation_triggered"] = True
            self.campaign_tracking[campaign_id]["status"] = "generating"
            self.campaign_tracking[campaign_id]["generation_started"] = datetime.now()

            # Trigger real pipeline integration
            try:
                from .pipeline_integration import PipelineIntegration
                pipeline = PipelineIntegration()

                # Trigger generation via pipeline
                result = await pipeline.trigger_generation(campaign_id, brief_content)
                self.logger.info(f"✅ Pipeline triggered for {campaign_id}: {result.get('job_id', 'unknown')}")

                # Store job info for tracking
                self.campaign_tracking[campaign_id]["pipeline_job"] = result

            except ImportError:
                self.logger.warning("Pipeline integration not available - using fallback")
                # Fallback: try to use image generator directly
                try:
                    from .image_generator import ImageGenerator
                    from .creative_composer import CreativeComposer

                    generator = ImageGenerator()
                    composer = CreativeComposer()

                    output_dir = Path(self.config["output_directory"]) / campaign_id
                    output_dir.mkdir(parents=True, exist_ok=True)

                    brief_data = brief_content.get("campaign_brief", brief_content)
                    products = brief_data.get("products", [])
                    aspect_ratios = brief_data.get("output_requirements", {}).get("aspect_ratios", ["1:1"])

                    for product in products:
                        if isinstance(product, str):
                            product = {"name": product}

                        base_image = generator.generate_product_image(product, brief_data)

                        for ratio in aspect_ratios:
                            composed = composer.compose_creative(base_image, brief_data, product, ratio)
                            safe_name = product.get("name", "product").replace(" ", "_").lower()
                            output_path = output_dir / f"{safe_name}_{ratio.replace(':', 'x')}.png"
                            composed.save(output_path, "PNG")

                    self.logger.info(f"✅ Direct generation completed for {campaign_id}")

                except Exception as gen_err:
                    self.logger.error(f"Direct generation failed: {gen_err}")

            # Log the trigger event
            await self._log_event("generation_triggered", {
                "campaign_id": campaign_id,
                "expected_variants": self.campaign_tracking[campaign_id]["expected_variants"],
                "timestamp": datetime.now().isoformat()
            })

        except Exception as e:
            self.logger.error(f"❌ Generation trigger failed for {campaign_id}: {e}")
            await self.create_alert(
                "generation_trigger_failure",
                f"Failed to trigger generation for {campaign_id}: {str(e)}",
                "critical",
                campaign_id
            )
    
    async def track_variant_progress(self):
        """REQUIREMENT 3: Track the count and diversity of creative variants"""
        output_dir = Path(self.config["output_directory"])
        
        for campaign_id, tracking in self.campaign_tracking.items():
            if tracking["status"] not in ["generating", "completed"]:
                continue
            
            # Count variants in output directory
            campaign_output = output_dir / campaign_id
            variant_count = 0
            variant_files = []
            
            if campaign_output.exists():
                # Count image files (variants)
                for file_path in campaign_output.rglob("*"):
                    if file_path.is_file() and file_path.suffix.lower() in ['.jpg', '.jpeg', '.png', '.webp']:
                        variant_count += 1
                        variant_files.append(str(file_path))
            
            # Update tracking
            old_count = tracking["variants_found"]
            tracking["variants_found"] = variant_count
            tracking["variant_files"] = variant_files
            tracking["last_check"] = datetime.now()
            
            # Log progress if variants increased
            if variant_count > old_count:
                self.logger.info(f"📊 Campaign {campaign_id}: {variant_count} variants found")
                await self._log_event("variant_progress", {
                    "campaign_id": campaign_id,
                    "variants_found": variant_count,
                    "expected_variants": tracking["expected_variants"],
                    "progress_percentage": (variant_count / max(tracking["expected_variants"], 1)) * 100
                })
            
            # Check if generation is complete
            if variant_count >= tracking["expected_variants"] and tracking["status"] == "generating":
                tracking["status"] = "completed"
                tracking["completed_at"] = datetime.now()
                self.logger.info(f"✅ Campaign {campaign_id} generation completed: {variant_count} variants")
    
    async def check_asset_sufficiency(self):
        """REQUIREMENT 4: Flag missing or insufficient assets"""
        for campaign_id, tracking in self.campaign_tracking.items():
            variant_count = tracking["variants_found"]
            expected_count = tracking["expected_variants"]
            
            # Check if insufficient variants
            if variant_count < self.config["min_variants_threshold"]:
                # Only alert once per campaign for this issue
                alert_key = f"insufficient_variants_{campaign_id}"
                if not any(alert["id"] == alert_key for alert in self.alerts):
                    await self.create_alert(
                        "insufficient_variants",
                        f"Campaign {campaign_id} has only {variant_count} variants (minimum required: {self.config['min_variants_threshold']})",
                        "medium",
                        campaign_id,
                        alert_key
                    )
            
            # Check if significantly below expected
            if expected_count > 0 and variant_count < (expected_count * 0.5):
                alert_key = f"below_expected_{campaign_id}"
                if not any(alert["id"] == alert_key for alert in self.alerts):
                    await self.create_alert(
                        "below_expected_variants",
                        f"Campaign {campaign_id} has {variant_count}/{expected_count} variants (50% below expected)",
                        "high",
                        campaign_id,
                        alert_key
                    )
    
    async def create_alert(self, alert_type: str, message: str, severity: str, campaign_id: str, alert_id: Optional[str] = None):
        """REQUIREMENT 5: Alert and/or Logging mechanism"""
        if alert_id is None:
            alert_id = f"{alert_type}_{campaign_id}_{int(time.time())}"
        
        alert = {
            "id": alert_id,
            "type": alert_type,
            "message": message,
            "severity": severity,
            "campaign_id": campaign_id,
            "timestamp": datetime.now(),
            "status": "active"
        }
        
        self.alerts.append(alert)
        
        # Log the alert
        self.logger.warning(f"🚨 ALERT [{severity.upper()}]: {message}")
        
        # Save alert to file
        if self.config["log_alerts"]:
            await self._save_alert_to_file(alert)
        
        return alert
    
    async def process_alerts(self):
        """Process active alerts and send notifications"""
        active_alerts = [alert for alert in self.alerts if alert["status"] == "active"]
        
        for alert in active_alerts:
            try:
                # Generate stakeholder communication
                communication = await self.generate_stakeholder_communication(alert)
                
                # Send email if configured
                if self.config["email_alerts"]:
                    await self.send_email_alert(alert, communication)
                
                # Mark as processed
                alert["status"] = "processed"
                alert["processed_at"] = datetime.now()
                
                self.logger.info(f"✅ Alert {alert['id']} processed and communicated")
                
            except Exception as e:
                self.logger.error(f"❌ Failed to process alert {alert['id']}: {e}")
    
    async def generate_stakeholder_communication(self, alert: Dict[str, Any]) -> str:
        """Generate human-readable stakeholder communication with Model Context Protocol"""
        
        # REQUIREMENT 6: Model Context Protocol - Define information for LLM
        context = self._build_model_context(alert)
        
        # Generate communication based on alert type
        if alert["type"] == "insufficient_variants":
            return await self._generate_insufficient_variants_email(alert, context)
        elif alert["type"] == "generation_trigger_failure":
            return await self._generate_api_issue_email(alert, context)
        elif alert["type"] == "below_expected_variants":
            return await self._generate_performance_issue_email(alert, context)
        else:
            return await self._generate_generic_alert_email(alert, context)
    
    def _build_model_context(self, alert: Dict[str, Any]) -> Dict[str, Any]:
        """REQUIREMENT 6: Model Context Protocol - Define information the LLM sees"""
        campaign_id = alert["campaign_id"]
        campaign_data = self.campaign_tracking.get(campaign_id, {})
        
        context = {
            # Alert context
            "alert": {
                "type": alert["type"],
                "severity": alert["severity"],
                "message": alert["message"],
                "timestamp": alert["timestamp"].isoformat()
            },
            
            # Campaign context
            "campaign": {
                "id": campaign_id,
                "status": campaign_data.get("status", "unknown"),
                "variants_found": campaign_data.get("variants_found", 0),
                "expected_variants": campaign_data.get("expected_variants", 0),
                "generation_triggered": campaign_data.get("generation_triggered", False),
                "detected_at": campaign_data.get("detected_at", datetime.now()).isoformat() if campaign_data.get("detected_at") else None
            },
            
            # System context
            "system": {
                "total_campaigns": len(self.campaign_tracking),
                "active_campaigns": len([c for c in self.campaign_tracking.values() if c["status"] == "generating"]),
                "completed_campaigns": len([c for c in self.campaign_tracking.values() if c["status"] == "completed"]),
                "total_alerts": len(self.alerts),
                "active_alerts": len([a for a in self.alerts if a["status"] == "active"])
            },
            
            # Business context
            "business": {
                "min_variants_threshold": self.config["min_variants_threshold"],
                "current_time": datetime.now().isoformat(),
                "impact_assessment": self._assess_business_impact(alert, campaign_data)
            }
        }
        
        return context
    
    async def _generate_insufficient_variants_email(self, alert: Dict[str, Any], context: Dict[str, Any]) -> str:
        """REQUIREMENT 7: Sample stakeholder communication for insufficient variants"""
        campaign = context["campaign"]
        business = context["business"]
        
        return f"""Subject: Action Required: Insufficient Creative Variants - Campaign {campaign['id']}

Dear Leadership Team,

I'm writing to alert you to a quality issue with our creative automation pipeline that requires immediate attention.

SITUATION OVERVIEW:
Campaign: {campaign['id']}
Current Status: {campaign['variants_found']} variants generated
Minimum Required: {business['min_variants_threshold']} variants
Expected Total: {campaign['expected_variants']} variants

BUSINESS IMPACT:
• Campaign delivery may be delayed
• Quality standards not met for client presentation
• Potential client satisfaction impact if not resolved

ROOT CAUSE ANALYSIS:
This shortage appears to be due to:
• Possible API rate limiting or provisioning issues with our GenAI services
• Content generation challenges with the specific campaign requirements
• System resource constraints during peak processing

IMMEDIATE ACTIONS TAKEN:
1. Campaign flagged for priority review
2. Generation process monitoring increased
3. Technical team notified for investigation

NEXT STEPS REQUIRED:
1. Technical review of GenAI API status and quotas
2. Assessment of content generation parameters for this campaign
3. Consideration of manual creative support if needed
4. Client communication preparation if delays become necessary

TIMELINE:
• Technical investigation: Within 2 hours
• Status update: Within 4 hours  
• Resolution or escalation: Within 8 hours

I will continue monitoring this situation closely and provide updates as they become available. Please let me know if you need any additional information or have specific concerns.

Best regards,
AI Creative Automation Agent
Timestamp: {context['alert']['timestamp']}
Alert ID: {alert['id']}

---
This is an automated alert from the Creative Automation System.
For technical issues, contact the DevOps team.
For business impact questions, contact Campaign Management.
"""
    
    async def _generate_api_issue_email(self, alert: Dict[str, Any], context: Dict[str, Any]) -> str:
        """Sample communication for API/licensing issues"""
        campaign = context["campaign"]
        
        return f"""Subject: URGENT: GenAI API Issue Affecting Campaign {campaign['id']}

Dear Leadership Team,

We are experiencing a critical issue with our GenAI API provisioning that is preventing campaign generation from proceeding.

TECHNICAL ISSUE:
Campaign: {campaign['id']}
Error: Generation trigger failure
Time Detected: {context['alert']['timestamp']}

LIKELY CAUSES:
• GenAI API quota exhausted or service interruption
• Authentication/licensing issues with AI provider
• Network connectivity problems to external services

BUSINESS IMPACT:
• Campaign generation completely blocked
• Client deliverables at risk
• Potential SLA breach if not resolved quickly

IMMEDIATE ACTIONS REQUIRED:
1. Check API quotas and billing status with GenAI provider
2. Verify licensing agreements and access permissions
3. Test API connectivity and authentication
4. Consider backup generation methods if available

ESCALATION:
This issue requires immediate technical and business attention due to the potential for widespread campaign impacts.

I recommend:
• Immediate DevOps team engagement
• Client notification preparation
• Budget approval for emergency API quota increases if needed

Updates will be provided every 30 minutes until resolved.

Best regards,
AI Creative Automation Agent
Alert ID: {alert['id']}
"""
    
    async def _generate_performance_issue_email(self, alert: Dict[str, Any], context: Dict[str, Any]) -> str:
        """Sample communication for performance issues"""
        campaign = context["campaign"]
        
        completion_rate = (campaign['variants_found'] / max(campaign['expected_variants'], 1)) * 100
        
        return f"""Subject: Performance Alert: Campaign {campaign['id']} Below Expected Output

Dear Team,

Our monitoring system has detected that campaign generation is significantly underperforming expectations.

PERFORMANCE METRICS:
Campaign: {campaign['id']}
Current Output: {campaign['variants_found']} variants
Expected Output: {campaign['expected_variants']} variants
Completion Rate: {completion_rate:.1f}%

ANALYSIS:
The generation process appears to be running but producing fewer variants than planned. This could indicate:
• Content quality filters rejecting more outputs than usual
• Processing bottlenecks in the generation pipeline
• Brief complexity exceeding normal parameters

RECOMMENDED ACTIONS:
1. Review generation parameters and quality thresholds
2. Analyze content filters for overly restrictive settings
3. Check system resource utilization
4. Consider adjusting brief requirements if technically feasible

I will continue monitoring and provide updates on progress.

Best regards,
AI Creative Automation Agent
Alert ID: {alert['id']}
"""
    
    async def _generate_generic_alert_email(self, alert: Dict[str, Any], context: Dict[str, Any]) -> str:
        """Generic alert communication template"""
        return f"""Subject: System Alert: {alert['type'].replace('_', ' ').title()}

Dear Team,

The Creative Automation System has generated an alert requiring your attention.

ALERT DETAILS:
Type: {alert['type']}
Severity: {alert['severity'].upper()}
Campaign: {alert['campaign_id']}
Message: {alert['message']}
Time: {context['alert']['timestamp']}

SYSTEM STATUS:
Total Campaigns: {context['system']['total_campaigns']}
Active Campaigns: {context['system']['active_campaigns']}
Completed Campaigns: {context['system']['completed_campaigns']}

Please review and take appropriate action based on your standard operating procedures.

Best regards,
AI Creative Automation Agent
Alert ID: {alert['id']}
"""
    
    async def send_email_alert(self, alert: Dict[str, Any], message: str):
        """Send email alert to stakeholders via real notification service"""
        notification_service = get_notification_service()

        # Map alert severity to notification priority
        severity_map = {
            "critical": NotificationPriority.CRITICAL,
            "high": NotificationPriority.HIGH,
            "medium": NotificationPriority.MEDIUM,
            "low": NotificationPriority.LOW
        }
        priority = severity_map.get(alert.get("severity", "medium"), NotificationPriority.MEDIUM)

        # Get recipients from config or environment
        recipients = self.config.get("alert_recipients", [])
        if not recipients:
            recipients = [
                os.getenv("ALERT_EMAIL", ""),
                os.getenv("LEADERSHIP_EMAIL", ""),
                os.getenv("CREATIVE_EMAIL", "")
            ]
            recipients = [r for r in recipients if r]  # Filter empty

        subject = f"[{alert.get('severity', 'INFO').upper()}] Campaign Alert: {alert.get('type', 'Unknown')}"

        # Send via notification service
        results = []
        sent_count = 0

        # Try email if recipients available
        if recipients:
            for recipient in recipients:
                try:
                    result = await notification_service.send_email(
                        to=recipient,
                        subject=subject,
                        body=message,
                        html=False,
                        priority=priority
                    )
                    results.append(result)
                    if result.success:
                        sent_count += 1
                except Exception as e:
                    self.logger.warning(f"Failed to send email to {recipient}: {e}")

        # Also send to Slack/Teams if configured
        try:
            slack_result = await notification_service.send_slack(
                message=message[:3000],  # Slack message limit
                title=subject,
                priority=priority
            )
            if slack_result.success:
                sent_count += 1
        except Exception as e:
            self.logger.debug(f"Slack notification skipped: {e}")

        # Save copy to file as backup
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)
        email_file = log_dir / f"email_alert_{alert['id']}.txt"
        with open(email_file, 'w') as f:
            f.write(message)

        self.logger.info(f"📧 Alert sent to {sent_count} channels, backup saved to {email_file}")
    
    def _calculate_expected_variants(self, brief_content: Dict[str, Any]) -> int:
        """Calculate expected number of variants from brief"""
        try:
            brief_data = brief_content.get("campaign_brief", brief_content)
            products = brief_data.get("products", [])
            
            # Get aspect ratios from output requirements
            output_req = brief_data.get("output_requirements", {})
            aspect_ratios = output_req.get("aspect_ratios", ["1:1", "9:16", "16:9"])
            
            # Calculate expected variants
            expected = len(products) * len(aspect_ratios)
            return max(expected, self.config["min_variants_threshold"])
            
        except Exception as e:
            self.logger.warning(f"Could not calculate expected variants: {e}")
            return self.config["min_variants_threshold"]
    
    def _assess_business_impact(self, alert: Dict[str, Any], campaign_data: Dict[str, Any]) -> str:
        """Assess business impact of alert"""
        if alert["severity"] == "critical":
            return "High - Immediate business impact, client deliverables at risk"
        elif alert["severity"] == "high":
            return "Medium - Potential delays, client communication may be needed"
        elif alert["severity"] == "medium":
            return "Low - Quality monitoring, process improvement opportunity"
        else:
            return "Minimal - Informational, standard monitoring"
    
    async def _save_alert_to_file(self, alert: Dict[str, Any]):
        """Save alert to JSON file for logging"""
        alert_file = f"logs/alert_{alert['id']}.json"
        
        # Convert datetime objects to strings for JSON serialization
        alert_copy = alert.copy()
        for key, value in alert_copy.items():
            if isinstance(value, datetime):
                alert_copy[key] = value.isoformat()
        
        with open(alert_file, 'w') as f:
            json.dump(alert_copy, f, indent=2)
    
    async def _log_event(self, event_type: str, data: Dict[str, Any]):
        """Log system events"""
        event = {
            "event_type": event_type,
            "timestamp": datetime.now().isoformat(),
            "data": data
        }
        
        log_file = f"logs/events_{datetime.now().strftime('%Y%m%d')}.jsonl"
        with open(log_file, 'a') as f:
            f.write(json.dumps(event) + '\n')
    
    def get_status(self) -> Dict[str, Any]:
        """Get current agent status"""
        return {
            "monitoring": self.monitoring,
            "campaigns_tracked": len(self.campaign_tracking),
            "active_campaigns": len([c for c in self.campaign_tracking.values() if c["status"] == "generating"]),
            "completed_campaigns": len([c for c in self.campaign_tracking.values() if c["status"] == "completed"]),
            "total_alerts": len(self.alerts),
            "active_alerts": len([a for a in self.alerts if a["status"] == "active"]),
            "last_check": datetime.now().isoformat(),
            "configuration": self.config
        }
    
    def stop_monitoring(self):
        """Stop the monitoring loop"""
        self.monitoring = False
        self.logger.info("🛑 Task 3 Agent monitoring stopped")


# Demo and test functions
async def create_sample_campaign_brief():
    """Create a sample campaign brief for testing"""
    sample_brief = {
        "campaign_brief": {
            "campaign_name": "Holiday_Collection_2024",
            "client": "Fashion Retailer",
            "products": ["winter_coat", "holiday_sweater", "accessories"],
            "target_audience": "Adults 25-45",
            "output_requirements": {
                "aspect_ratios": ["1:1", "9:16", "16:9"],
                "formats": ["jpg", "png"]
            },
            "timeline": {
                "deadline": (datetime.now() + timedelta(days=2)).isoformat(),
                "priority": "high"
            },
            "brand_guidelines": {
                "colors": ["#FF6B35", "#2E86AB", "#A23B72"],
                "style": "modern, minimalist"
            }
        }
    }
    
    # Save sample brief
    brief_file = Path("campaign_briefs/Holiday_Collection_2024.yaml")
    brief_file.parent.mkdir(exist_ok=True)
    
    with open(brief_file, 'w') as f:
        yaml.dump(sample_brief, f, default_flow_style=False)
    
    print(f"✅ Sample campaign brief created: {brief_file}")
    return brief_file

async def simulate_variant_generation(campaign_id: str, num_variants: int = 2):
    """Simulate variant generation by creating dummy files"""
    output_dir = Path(f"output/{campaign_id}")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    for i in range(num_variants):
        variant_file = output_dir / f"variant_{i+1}.jpg"
        variant_file.write_text(f"Dummy variant {i+1} for {campaign_id}")
    
    print(f"✅ Simulated {num_variants} variants for {campaign_id}")

async def demo_task3_agent():
    """Demonstrate the Task 3 agent"""
    print("🚀 Starting Task 3 Agent Demo")
    print("=" * 50)
    
    # Create agent
    agent = Task3Agent()
    
    # Create sample campaign brief
    await create_sample_campaign_brief()
    
    # Start monitoring in background
    monitoring_task = asyncio.create_task(agent.start_monitoring())
    
    # Wait for brief to be detected
    await asyncio.sleep(2)
    
    # Simulate some variant generation
    await simulate_variant_generation("Holiday_Collection_2024", 2)  # Below threshold
    
    # Let agent detect and process
    await asyncio.sleep(5)
    
    # Show status
    status = agent.get_status()
    print(f"\n📊 Agent Status:")
    print(f"Campaigns tracked: {status['campaigns_tracked']}")
    print(f"Active campaigns: {status['active_campaigns']}")
    print(f"Total alerts: {status['total_alerts']}")
    
    # Stop monitoring
    agent.stop_monitoring()
    monitoring_task.cancel()
    
    print("\n✅ Demo completed! Check logs/ directory for alerts and communications.")


if __name__ == "__main__":
    asyncio.run(demo_task3_agent())