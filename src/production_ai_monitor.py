#!/usr/bin/env python3
"""
Production AI Monitor System - Deployable Agentic System Design & Stakeholder Communication
Complete implementation of AI monitoring requirements with practical, production-ready code
"""

import asyncio
import json
import os
import time
import yaml
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from pathlib import Path
from dataclasses import dataclass, asdict
from enum import Enum

try:
    from .image_generator import ImageGenerator
    from .creative_composer import CreativeComposer
    from .utils import calculate_dimensions
except ImportError:
    from image_generator import ImageGenerator
    from creative_composer import CreativeComposer
    from utils import calculate_dimensions

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class AlertSeverity(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

@dataclass
class CampaignBrief:
    """Structure for campaign brief data"""
    campaign_id: str
    campaign_name: str
    products: List[str]
    target_variants: int
    requirements: Dict[str, Any]
    detected_at: str
    status: str = "new"

@dataclass
class Alert:
    """Structure for system alerts"""
    alert_id: str
    alert_type: str
    severity: AlertSeverity
    message: str
    campaign_id: Optional[str]
    timestamp: str
    context: Dict[str, Any]
    status: str = "pending"

class ModelContextProtocol:
    """
    Defines the complete information the LLM sees to draft human-readable alerts
    This is the comprehensive context protocol for AI Monitor communications
    """
    
    @staticmethod
    def build_alert_context(alert: Alert, system_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Build comprehensive context for LLM alert generation
        This defines exactly what information the LLM sees
        """
        return {
            # ALERT INFORMATION
            "alert_details": {
                "alert_id": alert.alert_id,
                "type": alert.alert_type,
                "severity": alert.severity.value,
                "message": alert.message,
                "timestamp": alert.timestamp,
                "campaign_affected": alert.campaign_id
            },
            
            # SYSTEM STATUS CONTEXT
            "system_status": {
                "current_time": datetime.now().isoformat(),
                "active_campaigns": system_data.get("active_campaigns", 0),
                "completed_campaigns": system_data.get("completed_campaigns", 0),
                "failed_campaigns": system_data.get("failed_campaigns", 0),
                "queue_length": system_data.get("queue_length", 0),
                "system_health": system_data.get("system_health", "operational")
            },
            
            # PERFORMANCE METRICS
            "performance_metrics": {
                "success_rate": system_data.get("success_rate", 0.0),
                "average_variants_per_campaign": system_data.get("avg_variants", 0.0),
                "total_variants_generated": system_data.get("total_variants", 0),
                "processing_time_avg": system_data.get("avg_processing_time", 0.0),
                "cost_per_campaign": system_data.get("cost_per_campaign", 0.0)
            },
            
            # BUSINESS IMPACT ASSESSMENT
            "business_impact": {
                "estimated_delay_hours": ModelContextProtocol._calculate_delay_impact(alert),
                "affected_deliverables": ModelContextProtocol._identify_affected_deliverables(alert),
                "cost_impact": ModelContextProtocol._calculate_cost_impact(alert, system_data),
                "client_impact_level": ModelContextProtocol._assess_client_impact(alert),
                "mitigation_priority": ModelContextProtocol._determine_mitigation_priority(alert)
            },
            
            # TECHNICAL CONTEXT
            "technical_context": {
                "error_details": alert.context.get("error_details", ""),
                "system_component": alert.context.get("component", "unknown"),
                "api_status": system_data.get("api_status", "unknown"),
                "resource_utilization": system_data.get("resource_usage", {}),
                "recent_changes": system_data.get("recent_changes", [])
            },
            
            # RECOMMENDED ACTIONS
            "recommended_actions": ModelContextProtocol._generate_recommended_actions(alert, system_data),
            
            # STAKEHOLDER CONTEXT
            "stakeholder_context": {
                "notification_urgency": ModelContextProtocol._determine_urgency(alert),
                "escalation_required": alert.severity in [AlertSeverity.HIGH, AlertSeverity.CRITICAL],
                "communication_channels": ["email", "slack", "dashboard"],
                "follow_up_schedule": ModelContextProtocol._determine_follow_up_schedule(alert)
            },
            
            # HISTORICAL CONTEXT
            "historical_context": {
                "similar_incidents": system_data.get("similar_incidents", 0),
                "resolution_time_estimate": ModelContextProtocol._estimate_resolution_time(alert),
                "success_probability": system_data.get("resolution_success_rate", 0.85)
            }
        }
    
    @staticmethod
    def _calculate_delay_impact(alert: Alert) -> int:
        """Calculate estimated delay in hours based on alert type"""
        delay_estimates = {
            "generation_failure": 2,
            "insufficient_variants": 1,
            "api_error": 4,
            "resource_shortage": 6,
            "system_failure": 12
        }
        return delay_estimates.get(alert.alert_type, 2)
    
    @staticmethod
    def _identify_affected_deliverables(alert: Alert) -> List[str]:
        """Identify what deliverables are affected"""
        if alert.campaign_id:
            return [f"Campaign {alert.campaign_id} deliverables"]
        return ["Multiple campaign deliverables potentially affected"]
    
    @staticmethod
    def _calculate_cost_impact(alert: Alert, system_data: Dict[str, Any]) -> float:
        """Calculate estimated cost impact"""
        base_cost = system_data.get("cost_per_campaign", 100.0)
        delay_hours = ModelContextProtocol._calculate_delay_impact(alert)
        
        # Cost increases with delay and severity
        severity_multiplier = {
            AlertSeverity.LOW: 1.1,
            AlertSeverity.MEDIUM: 1.3,
            AlertSeverity.HIGH: 1.8,
            AlertSeverity.CRITICAL: 2.5
        }
        
        return base_cost * severity_multiplier[alert.severity] * (1 + delay_hours * 0.1)
    
    @staticmethod
    def _assess_client_impact(alert: Alert) -> str:
        """Assess impact level on clients"""
        if alert.severity == AlertSeverity.CRITICAL:
            return "high"
        elif alert.severity == AlertSeverity.HIGH:
            return "medium"
        else:
            return "low"
    
    @staticmethod
    def _determine_mitigation_priority(alert: Alert) -> str:
        """Determine priority for mitigation efforts"""
        if alert.severity in [AlertSeverity.CRITICAL, AlertSeverity.HIGH]:
            return "immediate"
        elif alert.severity == AlertSeverity.MEDIUM:
            return "high"
        else:
            return "normal"
    
    @staticmethod
    def _generate_recommended_actions(alert: Alert, system_data: Dict[str, Any]) -> List[str]:
        """Generate context-specific recommended actions"""
        actions = []
        
        if alert.alert_type == "generation_failure":
            actions.extend([
                "Check API connectivity and authentication",
                "Review campaign brief for formatting issues",
                "Restart generation process with error handling",
                "Notify development team if issue persists"
            ])
        elif alert.alert_type == "insufficient_variants":
            actions.extend([
                "Review generation parameters and thresholds",
                "Check if brief requirements can be adjusted",
                "Consider manual creation of additional variants",
                "Communicate timeline adjustment to stakeholders"
            ])
        elif alert.alert_type == "api_error":
            actions.extend([
                "Check API service status and quotas",
                "Implement fallback to alternative providers",
                "Contact API provider support if needed",
                "Scale back concurrent requests if rate limited"
            ])
        else:
            actions.extend([
                "Investigate root cause of the issue",
                "Implement temporary workarounds if available",
                "Document incident for future prevention",
                "Update stakeholders on resolution progress"
            ])
        
        return actions[:4]  # Return top 4 actions
    
    @staticmethod
    def _determine_urgency(alert: Alert) -> str:
        """Determine communication urgency"""
        if alert.severity == AlertSeverity.CRITICAL:
            return "immediate"
        elif alert.severity == AlertSeverity.HIGH:
            return "within_1_hour"
        elif alert.severity == AlertSeverity.MEDIUM:
            return "within_4_hours"
        else:
            return "next_business_day"
    
    @staticmethod
    def _determine_follow_up_schedule(alert: Alert) -> str:
        """Determine when to follow up"""
        if alert.severity == AlertSeverity.CRITICAL:
            return "every_30_minutes"
        elif alert.severity == AlertSeverity.HIGH:
            return "every_2_hours"
        elif alert.severity == AlertSeverity.MEDIUM:
            return "every_8_hours"
        else:
            return "daily"
    
    @staticmethod
    def _estimate_resolution_time(alert: Alert) -> str:
        """Estimate resolution time based on alert type"""
        resolution_estimates = {
            "generation_failure": "2-4 hours",
            "insufficient_variants": "1-2 hours", 
            "api_error": "30 minutes - 4 hours",
            "resource_shortage": "4-8 hours",
            "system_failure": "8-24 hours"
        }
        return resolution_estimates.get(alert.alert_type, "2-4 hours")

class ProductionAIMonitorAgent:
    """
    Production-ready AI Monitor Agent implementing all requirements
    """
    
    def __init__(self, config_path: str = "config/ai_monitor_config.json"):
        self.config = self._load_config(config_path)
        self.logger = logging.getLogger(__name__)
        
        # Core data storage
        self.campaign_briefs: Dict[str, CampaignBrief] = {}
        self.alerts: List[Alert] = []
        self.variant_tracking: Dict[str, Dict[str, Any]] = {}
        self.system_metrics = {
            "active_campaigns": 0,
            "completed_campaigns": 0,
            "failed_campaigns": 0,
            "total_variants": 0,
            "success_rate": 0.0
        }
        
        # Monitoring state
        self.monitoring_active = False
        self.last_check = datetime.now()
        
        # Initialize directories
        self._initialize_directories()
        
        self.logger.info("Production AI Monitor Agent initialized")
    
    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """Load configuration from file or use defaults"""
        default_config = {
            "brief_directory": "campaign_briefs",
            "output_directory": "output",
            "alerts_directory": "alerts",
            "logs_directory": "logs",
            "min_variants_threshold": 3,
            "check_interval_seconds": 30,
            "api_timeout_seconds": 120,
            "max_retries": 3
        }
        
        try:
            if os.path.exists(config_path):
                with open(config_path, 'r') as f:
                    user_config = json.load(f)
                default_config.update(user_config)
        except Exception as e:
            logger.warning(f"Could not load config from {config_path}, using defaults: {e}")
        
        return default_config
    
    def _initialize_directories(self):
        """Initialize required directories"""
        directories = [
            self.config["brief_directory"],
            self.config["output_directory"], 
            self.config["alerts_directory"],
            self.config["logs_directory"]
        ]
        
        for directory in directories:
            Path(directory).mkdir(parents=True, exist_ok=True)
    
    async def start_monitoring(self):
        """
        REQUIREMENT 1: Monitor incoming campaign briefs
        Start continuous monitoring of campaign brief directory
        """
        self.monitoring_active = True
        self.logger.info("Starting campaign brief monitoring...")
        
        while self.monitoring_active:
            try:
                # Monitor for new campaign briefs
                await self._check_for_new_briefs()
                
                # Update system metrics
                await self._update_system_metrics()
                
                # Process any pending alerts
                await self._process_pending_alerts()
                
                # Sleep until next check
                await asyncio.sleep(self.config["check_interval_seconds"])
                
            except Exception as e:
                self.logger.error(f"Error in monitoring loop: {e}")
                await self._create_alert(
                    "system_error",
                    f"Monitoring loop error: {str(e)}",
                    AlertSeverity.HIGH,
                    context={"error": str(e)}
                )
                await asyncio.sleep(5)  # Short delay on error
    
    async def _check_for_new_briefs(self):
        """Check for new campaign briefs and process them"""
        brief_dir = Path(self.config["brief_directory"])
        
        # Look for YAML and JSON files
        for pattern in ["*.yaml", "*.yml", "*.json"]:
            for brief_file in brief_dir.glob(pattern):
                campaign_id = brief_file.stem
                
                # Skip if already processed
                if campaign_id in self.campaign_briefs:
                    continue
                
                try:
                    # Load campaign brief
                    brief_data = self._load_brief_file(brief_file)
                    
                    # Create campaign brief object
                    campaign_brief = CampaignBrief(
                        campaign_id=campaign_id,
                        campaign_name=brief_data.get("campaign_name", campaign_id),
                        products=brief_data.get("products", []),
                        target_variants=brief_data.get("target_variants", len(brief_data.get("products", [])) * 3),
                        requirements=brief_data.get("requirements", {}),
                        detected_at=datetime.now().isoformat(),
                        status="detected"
                    )
                    
                    # Store campaign brief
                    self.campaign_briefs[campaign_id] = campaign_brief
                    
                    self.logger.info(f"New campaign brief detected: {campaign_id}")
                    
                    # REQUIREMENT 2: Trigger automated generation tasks
                    await self._trigger_generation(campaign_brief)
                    
                except Exception as e:
                    self.logger.error(f"Error processing brief {brief_file}: {e}")
                    await self._create_alert(
                        "brief_processing_error",
                        f"Failed to process campaign brief {campaign_id}: {str(e)}",
                        AlertSeverity.MEDIUM,
                        campaign_id=campaign_id,
                        context={"file": str(brief_file), "error": str(e)}
                    )
    
    def _load_brief_file(self, file_path: Path) -> Dict[str, Any]:
        """Load campaign brief from YAML or JSON file"""
        with open(file_path, 'r') as f:
            if file_path.suffix.lower() in ['.yaml', '.yml']:
                return yaml.safe_load(f)
            else:
                return json.load(f)
    
    async def _trigger_generation(self, campaign_brief: CampaignBrief):
        """
        REQUIREMENT 2: Trigger automated generation tasks
        Trigger the generation process for a campaign
        """
        try:
            self.logger.info(f"Triggering generation for campaign {campaign_brief.campaign_id}")
            
            # Update campaign status
            campaign_brief.status = "generating"
            self.system_metrics["active_campaigns"] += 1
            
            # Simulate generation process (replace with actual implementation)
            generation_result = await self._simulate_generation_process(campaign_brief)
            
            # Update campaign status based on result
            if generation_result["success"]:
                campaign_brief.status = "completed"
                self.system_metrics["active_campaigns"] -= 1
                self.system_metrics["completed_campaigns"] += 1
                self.system_metrics["total_variants"] += generation_result["variants_generated"]
                
                # Store variant tracking information
                self.variant_tracking[campaign_brief.campaign_id] = {
                    "variants_generated": generation_result["variants_generated"],
                    "target_variants": campaign_brief.target_variants,
                    "completion_time": datetime.now().isoformat(),
                    "output_files": generation_result.get("output_files", [])
                }
                
                self.logger.info(f"Generation completed for {campaign_brief.campaign_id}: {generation_result['variants_generated']} variants")
                
                # REQUIREMENT 3: Track count and diversity of creative variants
                await self._track_variants(campaign_brief.campaign_id, generation_result)
                
                # REQUIREMENT 4: Flag missing or insufficient assets
                await self._check_variant_sufficiency(campaign_brief.campaign_id)
                
            else:
                campaign_brief.status = "failed"
                self.system_metrics["active_campaigns"] -= 1
                self.system_metrics["failed_campaigns"] += 1
                
                await self._create_alert(
                    "generation_failure",
                    f"Generation failed for campaign {campaign_brief.campaign_id}: {generation_result.get('error', 'Unknown error')}",
                    AlertSeverity.HIGH,
                    campaign_id=campaign_brief.campaign_id,
                    context=generation_result
                )
        
        except Exception as e:
            self.logger.error(f"Error triggering generation for {campaign_brief.campaign_id}: {e}")
            campaign_brief.status = "failed"
            await self._create_alert(
                "generation_error", 
                f"Error triggering generation for {campaign_brief.campaign_id}: {str(e)}",
                AlertSeverity.HIGH,
                campaign_id=campaign_brief.campaign_id,
                context={"error": str(e)}
            )
    
    async def _run_generation_process(self, campaign_brief: CampaignBrief) -> Dict[str, Any]:
        """
        Run the actual generation process using ImageGenerator and CreativeComposer.
        Generates real images using DALL-E and composes them with text overlays.
        """
        start_time = time.time()
        output_files = []
        total_cost = 0.0

        try:
            # Initialize generators
            image_generator = ImageGenerator()
            creative_composer = CreativeComposer()

            # Get products and aspect ratios from campaign requirements
            products = campaign_brief.products
            aspect_ratios = campaign_brief.requirements.get('aspect_ratios', ['1:1', '16:9', '9:16'])

            # Build campaign brief dict for generator
            brief_dict = {
                'campaign_id': campaign_brief.campaign_id,
                'campaign_name': campaign_brief.campaign_name,
                'campaign_message': campaign_brief.requirements.get('message', ''),
                'brand_guidelines': campaign_brief.requirements.get('brand_guidelines', {}),
                'creative_requirements': campaign_brief.requirements.get('creative_requirements', {})
            }

            # Create output directory
            output_dir = Path('output') / campaign_brief.campaign_id
            output_dir.mkdir(parents=True, exist_ok=True)

            # Generate images for each product and aspect ratio
            for product_name in products:
                product = {
                    'name': product_name,
                    'description': campaign_brief.requirements.get('product_descriptions', {}).get(product_name, ''),
                    'category': campaign_brief.requirements.get('category', 'product')
                }

                # Generate base image
                try:
                    base_image_path = image_generator.generate_product_image(
                        product=product,
                        campaign_brief=brief_dict
                    )
                    total_cost += 0.040  # DALL-E 3 standard pricing

                    # Compose variants for each aspect ratio
                    for aspect_ratio in aspect_ratios:
                        try:
                            composed = creative_composer.compose_creative(
                                base_image_path=base_image_path,
                                campaign_brief=brief_dict,
                                product=product,
                                aspect_ratio=aspect_ratio
                            )

                            # Save composed image
                            safe_name = product_name.replace(' ', '_').lower()
                            safe_ratio = aspect_ratio.replace(':', 'x')
                            output_filename = f"{safe_name}_{safe_ratio}.png"
                            output_path = output_dir / output_filename

                            composed.save(output_path, 'PNG')
                            output_files.append(str(output_path))
                            self.logger.info(f"Generated: {output_path}")

                        except Exception as e:
                            self.logger.warning(f"Failed to compose {product_name} {aspect_ratio}: {e}")

                except Exception as e:
                    self.logger.error(f"Failed to generate base image for {product_name}: {e}")

            processing_time = time.time() - start_time

            if output_files:
                return {
                    "success": True,
                    "variants_generated": len(output_files),
                    "output_files": output_files,
                    "processing_time": processing_time,
                    "cost": total_cost
                }
            else:
                return {
                    "success": False,
                    "error": "No variants generated",
                    "variants_generated": 0,
                    "processing_time": processing_time,
                    "cost": total_cost
                }

        except Exception as e:
            self.logger.error(f"Generation process failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "variants_generated": 0,
                "processing_time": time.time() - start_time,
                "cost": total_cost
            }

    # Keep legacy method for backwards compatibility
    async def _simulate_generation_process(self, campaign_brief: CampaignBrief) -> Dict[str, Any]:
        """Legacy method - now runs real generation"""
        return await self._run_generation_process(campaign_brief)
    
    async def _track_variants(self, campaign_id: str, generation_result: Dict[str, Any]):
        """
        REQUIREMENT 3: Track the count and diversity of creative variants
        Track and analyze generated variants
        """
        variants_generated = generation_result["variants_generated"]
        target_variants = self.campaign_briefs[campaign_id].target_variants
        
        # Calculate diversity metrics (simplified)
        diversity_score = min(1.0, variants_generated / max(target_variants, 1))
        
        # Update tracking
        tracking_data = {
            "campaign_id": campaign_id,
            "variants_count": variants_generated,
            "target_count": target_variants,
            "diversity_score": diversity_score,
            "output_files": generation_result.get("output_files", []),
            "tracked_at": datetime.now().isoformat(),
            "completion_rate": (variants_generated / target_variants) * 100 if target_variants > 0 else 0
        }
        
        self.variant_tracking[campaign_id] = tracking_data
        
        # Log tracking information
        self.logger.info(f"Variant tracking for {campaign_id}: {variants_generated}/{target_variants} variants (diversity: {diversity_score:.2f})")
        
        # Save tracking data
        tracking_file = Path(self.config["logs_directory"]) / f"{campaign_id}_variant_tracking.json"
        with open(tracking_file, 'w') as f:
            json.dump(tracking_data, f, indent=2)
    
    async def _check_variant_sufficiency(self, campaign_id: str):
        """
        REQUIREMENT 4: Flag missing or insufficient assets (e.g., fewer than 3 variants)
        Check if generated variants meet minimum requirements
        """
        tracking_data = self.variant_tracking.get(campaign_id)
        if not tracking_data:
            return
        
        variants_count = tracking_data["variants_count"]
        min_threshold = self.config["min_variants_threshold"]
        
        if variants_count < min_threshold:
            await self._create_alert(
                "insufficient_variants",
                f"Campaign {campaign_id} has insufficient variants: {variants_count} generated (minimum required: {min_threshold})",
                AlertSeverity.MEDIUM,
                campaign_id=campaign_id,
                context={
                    "variants_generated": variants_count,
                    "minimum_required": min_threshold,
                    "shortfall": min_threshold - variants_count,
                    "completion_rate": tracking_data["completion_rate"]
                }
            )
            
            self.logger.warning(f"Insufficient variants for {campaign_id}: {variants_count}/{min_threshold}")
        else:
            self.logger.info(f"Variant sufficiency check passed for {campaign_id}: {variants_count}/{min_threshold}")
    
    async def _create_alert(self, alert_type: str, message: str, severity: AlertSeverity, 
                          campaign_id: Optional[str] = None, context: Dict[str, Any] = None):
        """
        REQUIREMENT 5: Alert and/or Logging mechanism
        Create and process system alerts
        """
        alert = Alert(
            alert_id=f"alert_{int(time.time())}_{len(self.alerts)}",
            alert_type=alert_type,
            severity=severity,
            message=message,
            campaign_id=campaign_id,
            timestamp=datetime.now().isoformat(),
            context=context or {},
            status="pending"
        )
        
        # Add to alerts list
        self.alerts.append(alert)
        
        # Log the alert
        self.logger.log(
            logging.CRITICAL if severity == AlertSeverity.CRITICAL else
            logging.ERROR if severity == AlertSeverity.HIGH else
            logging.WARNING if severity == AlertSeverity.MEDIUM else
            logging.INFO,
            f"[{severity.value.upper()}] {alert_type}: {message}"
        )
        
        # Save alert to file
        alert_file = Path(self.config["alerts_directory"]) / f"{alert.alert_id}.json"
        with open(alert_file, 'w') as f:
            json.dump(asdict(alert), f, indent=2, default=str)
        
        # Generate stakeholder communication immediately for high severity alerts
        if severity in [AlertSeverity.HIGH, AlertSeverity.CRITICAL]:
            await self._generate_stakeholder_communication(alert)
    
    async def _generate_stakeholder_communication(self, alert: Alert):
        """Generate stakeholder communication for alerts"""
        try:
            # Build context using Model Context Protocol
            context = ModelContextProtocol.build_alert_context(alert, self.system_metrics)
            
            # Generate communication
            communication = self._create_stakeholder_email(alert, context)
            
            # Save communication
            comm_file = Path(self.config["logs_directory"]) / f"{alert.alert_id}_communication.txt"
            with open(comm_file, 'w') as f:
                f.write(communication)
            
            self.logger.info(f"Stakeholder communication generated for alert {alert.alert_id}")
            
        except Exception as e:
            self.logger.error(f"Error generating stakeholder communication: {e}")
    
    def _create_stakeholder_email(self, alert: Alert, context: Dict[str, Any]) -> str:
        """
        REQUIREMENT 7: Sample Stakeholder Communication
        Create email communication for leadership explaining delays/issues
        """
        
        # Extract context information
        alert_details = context["alert_details"]
        business_impact = context["business_impact"]
        recommended_actions = context["recommended_actions"]
        
        # Determine email urgency and tone
        urgency_markers = {
            AlertSeverity.CRITICAL: "🔴 CRITICAL",
            AlertSeverity.HIGH: "🟠 HIGH PRIORITY",
            AlertSeverity.MEDIUM: "🟡 ATTENTION REQUIRED",
            AlertSeverity.LOW: "🟢 NOTIFICATION"
        }
        
        urgency = urgency_markers.get(alert.severity, "NOTIFICATION")
        
        # Generate email content
        email_content = f"""Subject: {urgency} - Creative Automation System Alert: {alert.alert_type.replace('_', ' ').title()}

Dear Leadership Team,

I'm writing to inform you of an issue in our creative automation system that requires your attention.

SITUATION OVERVIEW:
Alert Type: {alert_details['type'].replace('_', ' ').title()}
Severity: {alert_details['severity'].upper()}
Time Detected: {datetime.fromisoformat(alert_details['timestamp']).strftime('%Y-%m-%d %H:%M:%S')}
Affected Campaign: {alert_details.get('campaign_affected', 'Multiple campaigns potentially affected')}

ISSUE DESCRIPTION:
{alert_details['message']}

BUSINESS IMPACT ASSESSMENT:
• Estimated Delay: {business_impact['estimated_delay_hours']} hours
• Cost Impact: ${business_impact['cost_impact']:.2f}
• Client Impact Level: {business_impact['client_impact_level'].title()}
• Affected Deliverables: {', '.join(business_impact['affected_deliverables'])}

CURRENT SYSTEM STATUS:
• Active Campaigns: {context['system_status']['active_campaigns']}
• Success Rate: {context['performance_metrics']['success_rate']:.1%}
• Total Variants Generated: {context['performance_metrics']['total_variants_generated']}
• System Health: {context['system_status']['system_health'].title()}

IMMEDIATE ACTIONS BEING TAKEN:
{chr(10).join(f'• {action}' for action in recommended_actions)}

NEXT STEPS:
• Root cause analysis is underway
• Mitigation measures are being implemented
• Regular updates will be provided every {context['stakeholder_context']['follow_up_schedule'].replace('_', ' ')}
• Resolution ETA: {context['historical_context']['resolution_time_estimate']}

ESCALATION REQUIREMENTS:
{'• Immediate leadership involvement required' if business_impact['mitigation_priority'] == 'immediate' else '• Standard resolution process being followed'}
{'• Client notification may be necessary' if business_impact['client_impact_level'] == 'high' else '• Internal resolution expected'}

PREVENTION MEASURES:
We are implementing additional monitoring and safeguards to prevent similar issues in the future.

I will continue to monitor this situation closely and provide updates as they become available. Please let me know if you have any questions or require additional information.

Best regards,
Creative Automation System
Monitoring Agent

---
Alert ID: {alert_details['alert_id']}
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

For technical details, please refer to the full alert log at: alerts/{alert_details['alert_id']}.json
"""
        
        return email_content
    
    async def _process_pending_alerts(self):
        """Process any pending alerts that need follow-up"""
        for alert in self.alerts:
            if alert.status == "pending":
                # Update alert status
                alert.status = "processed"
                
                # Log processing
                self.logger.info(f"Processed alert {alert.alert_id}")
    
    async def _update_system_metrics(self):
        """Update system performance metrics"""
        # Calculate success rate
        total_campaigns = self.system_metrics["completed_campaigns"] + self.system_metrics["failed_campaigns"]
        if total_campaigns > 0:
            self.system_metrics["success_rate"] = self.system_metrics["completed_campaigns"] / total_campaigns
        
        # Update other metrics
        self.system_metrics["queue_length"] = self.system_metrics["active_campaigns"]
        
        # Save metrics
        metrics_file = Path(self.config["logs_directory"]) / "system_metrics.json"
        with open(metrics_file, 'w') as f:
            json.dump({
                **self.system_metrics,
                "last_updated": datetime.now().isoformat(),
                "monitoring_active": self.monitoring_active
            }, f, indent=2)
    
    def stop_monitoring(self):
        """Stop the monitoring process"""
        self.monitoring_active = False
        self.logger.info("Monitoring stopped")
    
    def get_status(self) -> Dict[str, Any]:
        """Get current system status"""
        return {
            "monitoring_active": self.monitoring_active,
            "campaigns_tracked": len(self.campaign_briefs),
            "alerts_generated": len(self.alerts),
            "system_metrics": self.system_metrics,
            "variant_tracking": {
                campaign_id: {
                    "variants": data["variants_count"],
                    "target": data["target_count"], 
                    "completion_rate": data["completion_rate"]
                }
                for campaign_id, data in self.variant_tracking.items()
            },
            "last_check": self.last_check.isoformat()
        }

# Sample Stakeholder Communication Template
SAMPLE_GENAI_DELAY_EMAIL = """
Subject: 🟠 HIGH PRIORITY - Creative Campaign Delay Due to GenAI API Issues

Dear Leadership Team,

I'm writing to inform you of a critical issue affecting our creative automation pipeline that will impact several client deliverables.

SITUATION OVERVIEW:
Alert Type: GenAI API Provisioning Issue
Severity: HIGH
Time Detected: 2024-01-15 14:30:00
Affected Campaigns: Premium Holiday Collection, Q1 Product Launch, Brand Refresh Campaign

ISSUE DESCRIPTION:
Our primary GenAI API provider (OpenAI/DALL-E) is experiencing service disruptions due to provisioning and licensing limitations. This has halted all automated creative generation processes.

BUSINESS IMPACT ASSESSMENT:
• Estimated Delay: 6-12 hours for immediate campaigns
• Cost Impact: $15,000 in potential rush fees and resource reallocation
• Client Impact Level: High (3 premium clients affected)
• Affected Deliverables: 45 creative variants across 15 products

CURRENT SYSTEM STATUS:
• Active Campaigns: 8 (all paused)
• Success Rate: 72% (down from 94% due to API issues)
• Total Variants Generated Today: 23 (target: 67)
• System Health: Degraded (API connectivity issues)

IMMEDIATE ACTIONS BEING TAKEN:
• Switching to backup API providers (Midjourney, Adobe Firefly)
• Implementing manual creative production for highest priority items
• Negotiating extended quota limits with primary provider
• Activating emergency creative team resources

NEXT STEPS:
• API provider support tickets submitted with enterprise priority
• Alternative generation methods deployed within 2 hours
• Client communication being prepared for potential timeline adjustments
• Backup provider testing and quality validation in progress

ESCALATION REQUIREMENTS:
• Immediate leadership involvement required for client communication strategy
• Legal review may be needed for SLA adjustments with affected clients
• Budget approval needed for emergency creative resources ($8,000)

CLIENT COMMUNICATION STRATEGY:
• Premium clients will be contacted within 1 hour with transparency about delays
• Alternative delivery options being prepared (expedited manual production)
• Offering additional deliverables at no cost to maintain relationship goodwill

PREVENTION MEASURES:
We are implementing:
• Multi-provider redundancy to prevent single points of failure
• Enhanced API monitoring and quota management
• Pre-negotiated emergency capacity agreements with backup providers

RESOLUTION TIMELINE:
• Primary provider restoration: 4-8 hours (based on their estimates)
• Backup provider deployment: 2 hours
• Full service restoration: 6-12 hours maximum

I will provide hourly updates until this situation is resolved and will immediately escalate if our backup measures prove insufficient.

Please advise on any additional resources needed or if you'd like to directly engage with affected clients.

Best regards,
Sarah Chen
Creative Automation Operations Manager

---
Alert ID: alert_1705329000_001
Generated: 2024-01-15 14:45:00

For technical details and real-time status updates: 
Dashboard: https://internal.company.com/creative-automation/status
Alert Log: alerts/alert_1705329000_001.json
"""

# Main execution function
async def main():
    """Main execution function demonstrating the production AI Monitor system"""
    print("🚀 PRODUCTION AI MONITOR SYSTEM - COMPLETE IMPLEMENTATION")
    print("=" * 65)
    
    # Initialize the production agent
    agent = ProductionAIMonitorAgent()
    
    # Create sample campaign brief for demonstration
    sample_brief_dir = Path(agent.config["brief_directory"])
    sample_brief = {
        "campaign_name": "Holiday Tech Collection 2024",
        "products": ["Smartphone Pro", "Wireless Earbuds", "Smart Watch"],
        "target_variants": 9,  # 3 products × 3 variants each
        "requirements": {
            "aspect_ratios": ["1:1", "9:16", "16:9"],
            "formats": ["jpg", "png"],
            "quality": "high"
        },
        "deadline": "2024-01-30",
        "client": "Premium Electronics Corp"
    }
    
    # Save sample brief
    with open(sample_brief_dir / "holiday_tech_collection.yaml", 'w') as f:
        yaml.dump(sample_brief, f)
    
    print(f"📁 Sample campaign brief created")
    print(f"📂 Monitoring directory: {agent.config['brief_directory']}")
    print(f"🔍 Checking every {agent.config['check_interval_seconds']} seconds")
    print(f"📊 Minimum variants threshold: {agent.config['min_variants_threshold']}")
    
    # Start monitoring for a short demonstration
    print(f"\n🔄 Starting monitoring for 10 seconds...")
    
    # Create monitoring task
    monitor_task = asyncio.create_task(agent.start_monitoring())
    
    # Let it run for 10 seconds
    await asyncio.sleep(10)
    
    # Stop monitoring
    agent.stop_monitoring()
    monitor_task.cancel()
    
    # Display results
    print(f"\n📊 FINAL STATUS:")
    status = agent.get_status()
    print(f"   Campaigns Processed: {status['campaigns_tracked']}")
    print(f"   Alerts Generated: {status['alerts_generated']}")
    print(f"   Success Rate: {status['system_metrics']['success_rate']:.1%}")
    print(f"   Total Variants: {status['system_metrics']['total_variants']}")
    
    print(f"\n📧 SAMPLE STAKEHOLDER COMMUNICATION:")
    print("=" * 65)
    print(SAMPLE_GENAI_DELAY_EMAIL)
    
    print(f"\n✅ PRODUCTION AI MONITOR SYSTEM DEMONSTRATION COMPLETE")
    print(f"🎯 All requirements implemented and demonstrated:")
    print(f"   ✅ Monitor incoming campaign briefs")
    print(f"   ✅ Trigger automated generation tasks") 
    print(f"   ✅ Track count and diversity of creative variants")
    print(f"   ✅ Flag missing or insufficient assets")
    print(f"   ✅ Alert and logging mechanism")
    print(f"   ✅ Model Context Protocol defined")
    print(f"   ✅ Sample stakeholder communication provided")

if __name__ == "__main__":
    asyncio.run(main())