"""
AI Agent System for Creative Automation Pipeline
Implements autonomous monitoring, task triggering, and stakeholder communication
"""

import asyncio
import json
import os
import time
import yaml
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from pathlib import Path

import openai
from .pipeline_orchestrator import PipelineOrchestrator


class CreativeAutomationAgent:
    """AI-driven agent for monitoring and managing creative automation pipeline"""
    
    def __init__(self):
        self.orchestrator = PipelineOrchestrator()
        self.monitoring = True
        self.check_interval = 30  # seconds
        self.alert_history = []
        self.campaign_tracking = {}
        
        # Enhanced Configuration with adaptive thresholds
        self.config = {
            "min_variants_threshold": 3,
            "cost_alert_threshold": 50.0,  # dollars
            "success_rate_threshold": 0.8,  # 80%
            "max_queue_length": 10,
            "adaptive_thresholds": True,
            "performance_history_window": 24,  # hours
            "circuit_breaker_threshold": 5,  # consecutive failures
            "recovery_timeout": 300  # seconds
        }
        
        # Circuit breaker state
        self.circuit_breaker = {
            "consecutive_failures": 0,
            "last_failure_time": None,
            "state": "closed"  # closed, open, half-open
        }
        
        # Initialize OpenAI with enhanced error handling
        self.openai_client = None
        if os.getenv("OPENAI_API_KEY"):
            try:
                from openai import OpenAI
                self.openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
            except Exception as e:
                print(f"⚠️ OpenAI initialization failed: {e}. Using fallback communication.")
    
    async def start_monitoring(self):
        """Start the main monitoring loop"""
        print("🤖 AI Agent: Starting creative automation monitoring...")
        
        while self.monitoring:
            try:
                # Monitor campaign briefs
                await self.monitor_campaign_briefs()
                
                # Check system health
                await self.monitor_system_health()
                
                # Track creative variants
                await self.track_creative_variants()
                
                # Process any alerts
                await self.process_alerts()
                
                # Enhanced error recovery and adaptive management
                await self._enhanced_error_recovery()
                
                # Reset circuit breaker on successful cycle
                if self.circuit_breaker["state"] in ["half-open", "closed"]:
                    self._reset_circuit_breaker()
                
                await asyncio.sleep(self.check_interval)
                
            except Exception as e:
                print(f"❌ Agent monitoring error: {str(e)}")
                await self._handle_circuit_breaker_failure()
                await asyncio.sleep(5)  # Short delay on error
    
    async def monitor_campaign_briefs(self):
        """Monitor incoming campaign briefs and trigger generation"""
        brief_dir = Path("campaign_briefs")
        if not brief_dir.exists():
            brief_dir.mkdir(exist_ok=True)
            return
        
        # Look for new campaign briefs
        for brief_file in brief_dir.glob("*.yaml"):
            campaign_id = brief_file.stem
            
            if campaign_id not in self.campaign_tracking:
                print(f"🔍 Agent: New campaign brief detected: {campaign_id}")
                
                # Load and validate brief
                try:
                    with open(brief_file, 'r') as f:
                        campaign_brief = yaml.safe_load(f)
                    
                    # Initialize tracking
                    self.campaign_tracking[campaign_id] = {
                        "brief_file": str(brief_file),
                        "detected_at": datetime.now().isoformat(),
                        "status": "detected",
                        "variants_generated": 0,
                        "target_variants": 0,
                        "last_check": datetime.now().isoformat()
                    }
                    
                    # Trigger automated generation
                    await self.trigger_generation(campaign_id, campaign_brief)
                    
                except Exception as e:
                    await self._handle_circuit_breaker_failure()
                    await self.create_alert(
                        "generation_failure",
                        f"Failed to process campaign brief {campaign_id}: {str(e)}",
                        "high"
                    )
    
    async def trigger_generation(self, campaign_id: str, campaign_brief: Dict[str, Any]):
        """Trigger automated generation tasks"""
        print(f"🚀 Agent: Triggering generation for campaign {campaign_id}")
        
        try:
            # Calculate expected variants
            brief_data = campaign_brief.get("campaign_brief", {})
            products = brief_data.get("products", [])
            aspect_ratios = brief_data.get("output_requirements", {}).get("aspect_ratios", ["1:1", "9:16", "16:9"])
            expected_variants = len(products) * len(aspect_ratios)
            
            # Update tracking
            self.campaign_tracking[campaign_id].update({
                "status": "generating",
                "target_variants": expected_variants,
                "generation_started": datetime.now().isoformat()
            })
            
            # Trigger generation using sync method wrapped in async
            import asyncio
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                self.orchestrator.process_campaign_sync,
                campaign_brief,
                "assets",
                "output",
                False,  # force_generate
                False,  # skip_compliance
                None    # localize_for
            )
            
            # Update tracking with results
            self.campaign_tracking[campaign_id].update({
                "status": "completed",
                "variants_generated": result.get("assets_generated", 0),
                "generation_completed": datetime.now().isoformat(),
                "output_path": result.get("output_path", ""),
                "api_cost": result.get("total_cost", 0)
            })
            
            print(f"✅ Agent: Campaign {campaign_id} generation completed")
            
            # Check if variants are sufficient
            if result.get("assets_generated", 0) < self.config["min_variants_threshold"]:
                await self.create_alert(
                    "insufficient_variants",
                    f"Campaign {campaign_id} generated only {result.get('assets_generated', 0)} variants (minimum: {self.config['min_variants_threshold']})",
                    "medium"
                )
            
        except Exception as e:
            self.campaign_tracking[campaign_id]["status"] = "failed"
            await self.create_alert(
                "generation_failure",
                f"Generation failed for campaign {campaign_id}: {str(e)}",
                "high"
            )
    
    async def track_creative_variants(self):
        """Track count and diversity of creative variants"""
        output_dir = Path("output")
        if not output_dir.exists():
            return
        
        for campaign_id, tracking in self.campaign_tracking.items():
            if tracking["status"] == "completed":
                continue
                
            # Check output directory for this campaign
            campaign_output = output_dir / campaign_id
            if campaign_output.exists():
                variant_count = 0
                aspect_ratios = set()
                products = set()
                
                # Count variants
                for product_dir in campaign_output.iterdir():
                    if product_dir.is_dir():
                        products.add(product_dir.name)
                        for variant_file in product_dir.glob("*.jpg"):
                            variant_count += 1
                            # Extract aspect ratio from filename (e.g., "1x1.jpg")
                            aspect_ratios.add(variant_file.stem)
                
                # Update tracking
                tracking.update({
                    "variants_generated": variant_count,
                    "products_processed": len(products),
                    "aspect_ratios_covered": list(aspect_ratios),
                    "diversity_score": len(aspect_ratios) * len(products),
                    "last_check": datetime.now().isoformat()
                })
                
                # Check for insufficient variants
                if variant_count < self.config["min_variants_threshold"]:
                    await self.create_alert(
                        "insufficient_variants",
                        f"Campaign {campaign_id} has only {variant_count} variants (minimum: {self.config['min_variants_threshold']})",
                        "medium"
                    )
    
    async def monitor_system_health(self):
        """Monitor overall system health and performance"""
        try:
            # Check costs
            costs_file = Path("costs.json")
            if costs_file.exists():
                with open(costs_file, 'r') as f:
                    costs = json.load(f)
                    total_cost = costs.get("total_cost", 0)
                    
                    if total_cost > self.config["cost_alert_threshold"]:
                        await self.create_alert(
                            "cost_spike",
                            f"Daily API costs ({total_cost:.2f}) exceeded threshold ({self.config['cost_alert_threshold']})",
                            "high"
                        )
            
            # Check queue length
            active_campaigns = len([c for c in self.campaign_tracking.values() if c["status"] == "generating"])
            if active_campaigns > self.config["max_queue_length"]:
                await self.create_alert(
                    "queue_overload",
                    f"Generation queue overloaded: {active_campaigns} active campaigns",
                    "medium"
                )
            
            # Calculate success rate
            completed = len([c for c in self.campaign_tracking.values() if c["status"] == "completed"])
            failed = len([c for c in self.campaign_tracking.values() if c["status"] == "failed"])
            total = completed + failed
            
            if total > 0:
                success_rate = completed / total
                if success_rate < self.config["success_rate_threshold"]:
                    await self.create_alert(
                        "low_success_rate",
                        f"Generation success rate ({success_rate:.1%}) below threshold ({self.config['success_rate_threshold']:.1%})",
                        "high"
                    )
            
        except Exception as e:
            print(f"⚠️ Agent: Health monitoring error: {str(e)}")
    
    async def create_alert(self, alert_type: str, message: str, severity: str):
        """Create and queue an alert for processing"""
        alert = {
            "id": f"alert_{int(time.time())}_{len(self.alert_history)}",
            "type": alert_type,
            "message": message,
            "severity": severity,
            "timestamp": datetime.now().isoformat(),
            "status": "pending"
        }
        
        self.alert_history.append(alert)
        print(f"🚨 Agent Alert [{severity.upper()}]: {message}")
        
        # Save alert to file
        alerts_dir = Path("alerts")
        alerts_dir.mkdir(exist_ok=True)
        
        with open(alerts_dir / f"{alert['id']}.json", 'w') as f:
            json.dump(alert, f, indent=2)
    
    async def process_alerts(self):
        """Process pending alerts and generate communications"""
        pending_alerts = [a for a in self.alert_history if a["status"] == "pending"]
        
        for alert in pending_alerts:
            try:
                # Generate human-readable communication
                communication = await self.generate_stakeholder_communication(alert)
                
                # Log communication
                await self.log_communication(alert, communication)
                
                # Mark as processed
                alert["status"] = "processed"
                alert["processed_at"] = datetime.now().isoformat()
                
            except Exception as e:
                print(f"❌ Agent: Failed to process alert {alert['id']}: {str(e)}")
    
    async def generate_stakeholder_communication(self, alert: Dict[str, Any]) -> str:
        """Generate human-readable alert using LLM with rich business context"""
        if not os.getenv("OPENAI_API_KEY"):
            return self._generate_fallback_communication(alert)
        
        try:
            # Prepare comprehensive context for LLM (Model Context Protocol)
            context = await self._build_comprehensive_context(alert)
            
            prompt = f"""
You are an AI agent managing creative automation pipelines for a global consumer goods company.
Generate a professional alert communication for stakeholders based on comprehensive business context.

ALERT DETAILS:
- Type: {context['alert_details']['type']}
- Severity: {context['alert_details']['severity']} 
- Message: {context['alert_details']['message']}
- Business Impact: {context['alert_details']['business_impact']['estimated_delay_hours']}h delay, ${context['alert_details']['business_impact']['revenue_at_risk']} revenue at risk
- Urgency: {context['stakeholder_context']['urgency_level']}

SYSTEM PERFORMANCE:
- Success Rate: {context['system_status']['performance_metrics']['success_rate']:.1%} (threshold: {context['system_status']['performance_metrics']['success_rate_threshold']:.1%})
- Queue: {context['system_status']['queue_metrics']['active_campaigns']}/{context['system_status']['queue_metrics']['processing_capacity']} campaigns
- Cost: ${context['system_status']['cost_metrics']['total_cost_today']:.2f} ({context['system_status']['cost_metrics']['budget_utilization']:.1f}% of budget)
- Variants: {context['system_status']['performance_metrics']['total_variants_generated']} total, avg {context['system_status']['performance_metrics']['avg_variants_per_campaign']:.1f} per campaign

ALERT CONTEXT:
- Alerts Today: {context['alert_context']['total_alerts_today']} ({context['alert_context']['critical_alerts_today']} critical, {context['alert_context']['high_alerts_today']} high)
- Repeated Issue: {context['alert_context']['repeated_alert_type']}
- Escalation Required: {context['stakeholder_context']['escalation_required']}

RECOMMENDED ACTIONS:
{chr(10).join(f"• {action}" for action in context['recommended_actions'][:5])}

Generate a professional, executive-level communication that:
1. Clearly explains the business situation and immediate impact
2. Provides specific financial and operational context
3. Includes urgency assessment and escalation requirements
4. Lists concrete, actionable next steps with timeframes
5. Maintains professional tone appropriate for leadership

Format as email content with clear sections and business language.
"""
            
            # Use enhanced OpenAI client with error handling
            if not self.openai_client:
                print("⚠️ OpenAI client not available, using fallback communication")
                return self._generate_fallback_communication(alert)
            
            response = self.openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a professional AI agent generating stakeholder communications for creative automation systems."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=500,
                temperature=0.3
            )
            
            self._reset_circuit_breaker()  # Successful OpenAI call
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            print(f"⚠️ Agent: LLM communication failed: {str(e)}")
            await self._handle_circuit_breaker_failure()
            return self._generate_fallback_communication(alert)
    
    def _generate_fallback_communication(self, alert: Dict[str, Any]) -> str:
        """Generate fallback communication without LLM"""
        severity_map = {
            "low": "INFORMATIONAL",
            "medium": "WARNING", 
            "high": "URGENT",
            "critical": "CRITICAL"
        }
        
        return f"""
CREATIVE AUTOMATION ALERT - {severity_map.get(alert['severity'], 'UNKNOWN')}

Alert Type: {alert['type']}
Timestamp: {alert['timestamp']}
Severity: {alert['severity'].upper()}

Description:
{alert['message']}

System Status:
- Active Campaigns: {len([c for c in self.campaign_tracking.values() if c['status'] == 'generating'])}
- Completed Today: {len([c for c in self.campaign_tracking.values() if c['status'] == 'completed'])}
- Failed Today: {len([c for c in self.campaign_tracking.values() if c['status'] == 'failed'])}

Recommended Actions:
- Review campaign status and resource allocation
- Check system logs for detailed error information
- Contact automation team if issue persists

Next Update: {(datetime.now() + timedelta(hours=1)).isoformat()}
        """
    
    async def log_communication(self, alert: Dict[str, Any], communication: str):
        """Log the generated communication"""
        logs_dir = Path("logs")
        logs_dir.mkdir(exist_ok=True)
        
        log_entry = {
            "alert_id": alert["id"],
            "timestamp": datetime.now().isoformat(),
            "severity": alert["severity"],
            "communication": communication
        }
        
        # Save to individual log file
        with open(logs_dir / f"alert_{alert['id']}_communication.json", 'w') as f:
            json.dump(log_entry, f, indent=2)
        
        # Also save human-readable version
        with open(logs_dir / f"alert_{alert['id']}_email.txt", 'w') as f:
            f.write(f"Subject: Creative Automation Alert - {alert['type'].replace('_', ' ').title()}\n\n")
            f.write(communication)
        
        print(f"📧 Agent: Communication logged for alert {alert['id']}")
    
    async def _build_comprehensive_context(self, alert: Dict[str, Any]) -> Dict[str, Any]:
        """Build comprehensive business context for LLM (Model Context Protocol)"""
        import os
        
        # Calculate comprehensive metrics
        active_campaigns = [c for c in self.campaign_tracking.values() if c["status"] == "generating"]
        completed_campaigns = [c for c in self.campaign_tracking.values() if c["status"] == "completed"]
        failed_campaigns = [c for c in self.campaign_tracking.values() if c["status"] == "failed"]
        
        # Cost analysis
        total_cost = 0
        try:
            if os.path.exists("costs.json"):
                with open("costs.json", 'r') as f:
                    costs = json.load(f)
                    total_cost = costs.get("total_cost", 0)
        except:
            total_cost = 0
        
        # Performance metrics
        total_campaigns = len(completed_campaigns) + len(failed_campaigns)
        success_rate = (len(completed_campaigns) / total_campaigns) if total_campaigns > 0 else 0
        
        # Variant analysis
        total_variants = sum(c.get("variants_generated", 0) for c in self.campaign_tracking.values())
        avg_variants_per_campaign = total_variants / len(self.campaign_tracking) if self.campaign_tracking else 0
        
        # Alert analysis
        today = datetime.now().isoformat()[:10]
        todays_alerts = [a for a in self.alert_history if a["timestamp"][:10] == today]
        critical_alerts = [a for a in todays_alerts if a["severity"] == "critical"]
        high_alerts = [a for a in todays_alerts if a["severity"] == "high"]
        
        # Business impact assessment
        estimated_delay_hours = 0
        revenue_at_risk = 0
        
        if alert["type"] == "generation_failure":
            estimated_delay_hours = 2
            revenue_at_risk = 25000
        elif alert["type"] == "cost_spike":
            estimated_delay_hours = 0
            revenue_at_risk = total_cost * 10  # Cost overrun impact
        elif alert["type"] == "insufficient_variants":
            estimated_delay_hours = 1
            revenue_at_risk = 15000
        
        return {
            "alert_details": {
                "id": alert["id"],
                "type": alert["type"],
                "severity": alert["severity"],
                "message": alert["message"],
                "timestamp": alert["timestamp"],
                "business_impact": {
                    "estimated_delay_hours": estimated_delay_hours,
                    "revenue_at_risk": revenue_at_risk,
                    "affected_campaigns": len(active_campaigns) + len(failed_campaigns)
                }
            },
            "system_status": {
                "current_time": datetime.now().isoformat(),
                "queue_metrics": {
                    "active_campaigns": len(active_campaigns),
                    "completed_campaigns": len(completed_campaigns),
                    "failed_campaigns": len(failed_campaigns),
                    "queue_length": len(active_campaigns),
                    "processing_capacity": self.config["max_queue_length"]
                },
                "performance_metrics": {
                    "success_rate": success_rate,
                    "success_rate_threshold": self.config["success_rate_threshold"],
                    "total_variants_generated": total_variants,
                    "avg_variants_per_campaign": avg_variants_per_campaign,
                    "min_variants_threshold": self.config["min_variants_threshold"]
                },
                "cost_metrics": {
                    "total_cost_today": total_cost,
                    "cost_threshold": self.config["cost_alert_threshold"],
                    "avg_cost_per_campaign": total_cost / max(len(completed_campaigns), 1),
                    "budget_utilization": (total_cost / self.config["cost_alert_threshold"]) * 100
                }
            },
            "alert_context": {
                "total_alerts_today": len(todays_alerts),
                "critical_alerts_today": len(critical_alerts),
                "high_alerts_today": len(high_alerts),
                "alert_frequency": len(todays_alerts) / 24,  # alerts per hour
                "repeated_alert_type": alert["type"] in [a["type"] for a in todays_alerts[:-1]]
            },
            "campaign_portfolio": {
                "total_campaigns_tracked": len(self.campaign_tracking),
                "campaign_details": [
                    {
                        "id": cid,
                        "status": data["status"],
                        "variants_generated": data.get("variants_generated", 0),
                        "target_variants": data.get("target_variants", 0),
                        "completion_rate": (data.get("variants_generated", 0) / max(data.get("target_variants", 1), 1)) * 100
                    }
                    for cid, data in list(self.campaign_tracking.items())[:5]  # Last 5 campaigns
                ]
            },
            "recommended_actions": self._generate_recommended_actions(alert, success_rate, total_cost),
            "stakeholder_context": {
                "urgency_level": self._calculate_urgency_level(alert, len(critical_alerts), len(failed_campaigns)),
                "escalation_required": len(critical_alerts) > 2 or len(failed_campaigns) > 3,
                "next_review_time": (datetime.now() + timedelta(hours=1)).isoformat()
            }
        }
    
    def _generate_recommended_actions(self, alert: Dict[str, Any], success_rate: float, total_cost: float) -> List[str]:
        """Generate context-aware recommended actions"""
        actions = []
        
        if alert["type"] == "generation_failure":
            actions.extend([
                "Immediately review system logs for root cause analysis",
                "Check API connectivity and authentication status", 
                "Verify campaign brief format and required fields",
                "Consider engaging backup generation providers",
                "Notify creative team of potential manual asset requirements"
            ])
        elif alert["type"] == "cost_spike":
            actions.extend([
                "Review API usage patterns and optimize batch processing",
                "Implement cost controls and rate limiting",
                "Evaluate alternative AI providers for cost optimization",
                "Update budget forecasts and alert stakeholders"
            ])
        elif alert["type"] == "insufficient_variants":
            actions.extend([
                "Review generation parameters and quality thresholds",
                "Check asset requirements and aspect ratio specifications",
                "Consider lowering quality gates temporarily to meet deadlines",
                "Engage creative team for manual variant creation"
            ])
        elif alert["type"] == "low_success_rate":
            actions.extend([
                "Conduct comprehensive system health check",
                "Review recent changes to generation pipeline",
                "Implement additional error handling and retry logic",
                "Schedule emergency team meeting for issue resolution"
            ])
        
        # Add general actions based on system state
        if success_rate < 0.5:
            actions.append("URGENT: Success rate critically low - consider system maintenance")
        if total_cost > self.config["cost_alert_threshold"] * 0.9:
            actions.append("Budget nearing limit - implement cost controls immediately")
            
        return actions
    
    def _calculate_urgency_level(self, alert: Dict[str, Any], critical_alerts: int, failed_campaigns: int) -> str:
        """Calculate business urgency level"""
        severity_score = {"low": 1, "medium": 2, "high": 3, "critical": 4}.get(alert["severity"], 2)
        
        # Factor in system state
        if critical_alerts > 2:
            severity_score += 1
        if failed_campaigns > 3:
            severity_score += 1
        if alert["type"] in ["generation_failure", "cost_spike"]:
            severity_score += 1
            
        if severity_score >= 5:
            return "CRITICAL - Immediate C-suite notification required"
        elif severity_score >= 4:
            return "HIGH - Leadership review required within 2 hours"
        elif severity_score >= 3:
            return "MEDIUM - Team lead review required within 4 hours"
        else:
            return "LOW - Standard monitoring and review"
    
    def stop_monitoring(self):
        """Stop the monitoring loop"""
        self.monitoring = False
        print("🛑 AI Agent: Monitoring stopped")
    
    def get_status(self) -> Dict[str, Any]:
        """Get current agent status"""
        return {
            "monitoring": self.monitoring,
            "campaigns_tracked": len(self.campaign_tracking),
            "alerts_generated": len(self.alert_history),
            "pending_alerts": len([a for a in self.alert_history if a["status"] == "pending"]),
            "last_check": datetime.now().isoformat(),
            "configuration": self.config,
            "campaign_summary": {
                "active": len([c for c in self.campaign_tracking.values() if c["status"] == "generating"]),
                "completed": len([c for c in self.campaign_tracking.values() if c["status"] == "completed"]),
                "failed": len([c for c in self.campaign_tracking.values() if c["status"] == "failed"])
            }
        }
    
    def get_campaign_tracking(self) -> Dict[str, Any]:
        """Get detailed campaign tracking information"""
        return self.campaign_tracking
    
    def get_alert_history(self) -> List[Dict[str, Any]]:
        """Get alert history"""
        return self.alert_history
    
    async def _handle_circuit_breaker_failure(self):
        """Handle circuit breaker logic for system failures"""
        self.circuit_breaker["consecutive_failures"] += 1
        self.circuit_breaker["last_failure_time"] = datetime.now()
        
        if self.circuit_breaker["consecutive_failures"] >= self.config["circuit_breaker_threshold"]:
            self.circuit_breaker["state"] = "open"
            print(f"⚠️ Circuit breaker OPEN - {self.circuit_breaker['consecutive_failures']} consecutive failures")
            
            # Create critical alert about system instability
            await self.create_alert(
                "system_instability",
                f"System experiencing {self.circuit_breaker['consecutive_failures']} consecutive failures. Circuit breaker activated.",
                "critical"
            )
    
    async def _check_circuit_breaker_recovery(self):
        """Check if circuit breaker can transition to half-open state"""
        if self.circuit_breaker["state"] == "open":
            last_failure = self.circuit_breaker["last_failure_time"]
            if last_failure and (datetime.now() - last_failure).seconds >= self.config["recovery_timeout"]:
                self.circuit_breaker["state"] = "half-open"
                print("🔄 Circuit breaker HALF-OPEN - Testing recovery")
    
    def _reset_circuit_breaker(self):
        """Reset circuit breaker after successful operation"""
        if self.circuit_breaker["consecutive_failures"] > 0:
            print(f"✅ Circuit breaker RESET - System recovery confirmed")
        
        self.circuit_breaker["consecutive_failures"] = 0
        self.circuit_breaker["state"] = "closed"
        self.circuit_breaker["last_failure_time"] = None
    
    async def _adapt_thresholds_based_on_performance(self):
        """Dynamically adapt monitoring thresholds based on historical performance"""
        if not self.config["adaptive_thresholds"]:
            return
        
        # Analyze performance over the last 24 hours
        now = datetime.now()
        window_start = now - timedelta(hours=self.config["performance_history_window"])
        
        recent_campaigns = [
            c for c in self.campaign_tracking.values() 
            if datetime.fromisoformat(c.get("detected_at", "1970-01-01T00:00:00")) >= window_start
        ]
        
        if len(recent_campaigns) < 3:
            return  # Need more data
        
        # Calculate adaptive success rate threshold
        completed = len([c for c in recent_campaigns if c["status"] == "completed"])
        total = len([c for c in recent_campaigns if c["status"] in ["completed", "failed"]])
        
        if total > 0:
            current_success_rate = completed / total
            
            # Adjust threshold based on recent performance
            if current_success_rate < 0.5:  # Poor performance
                self.config["success_rate_threshold"] = max(0.6, current_success_rate + 0.1)
                print(f"📉 Adapted success rate threshold to {self.config['success_rate_threshold']:.1%} due to poor performance")
            elif current_success_rate > 0.9:  # Excellent performance
                self.config["success_rate_threshold"] = min(0.95, current_success_rate - 0.05)
                print(f"📈 Adapted success rate threshold to {self.config['success_rate_threshold']:.1%} for higher standards")
        
        # Adapt cost thresholds based on actual usage patterns
        recent_costs = []
        try:
            if os.path.exists("costs.json"):
                with open("costs.json", 'r') as f:
                    costs = json.load(f)
                    # Simulate daily cost tracking (would be implemented in real system)
                    daily_cost = costs.get("total_cost", 0) / max(len(recent_campaigns), 1)
                    if daily_cost > 0:
                        recent_costs.append(daily_cost)
        except:
            pass
        
        if recent_costs:
            avg_daily_cost = sum(recent_costs) / len(recent_costs)
            # Set threshold at 150% of average to catch real spikes
            adaptive_cost_threshold = avg_daily_cost * 1.5
            
            if abs(adaptive_cost_threshold - self.config["cost_alert_threshold"]) > 10:
                self.config["cost_alert_threshold"] = adaptive_cost_threshold
                print(f"💰 Adapted cost threshold to ${adaptive_cost_threshold:.2f} based on usage patterns")
    
    async def _enhanced_error_recovery(self):
        """Enhanced error recovery with multiple strategies"""
        try:
            # Check circuit breaker state
            await self._check_circuit_breaker_recovery()
            
            # Adapt thresholds based on performance
            await self._adapt_thresholds_based_on_performance()
            
            # If in half-open state, test with minimal operations
            if self.circuit_breaker["state"] == "half-open":
                print("🧪 Testing system recovery...")
                # Try a simple operation
                test_campaigns = len(self.campaign_tracking)
                if test_campaigns >= 0:  # Simple test that should always pass
                    self._reset_circuit_breaker()
                    print("✅ System recovery confirmed")
            
            # Clear old alert history to prevent memory buildup
            if len(self.alert_history) > 100:
                cutoff = datetime.now() - timedelta(days=7)
                self.alert_history = [
                    alert for alert in self.alert_history
                    if datetime.fromisoformat(alert["timestamp"]) > cutoff
                ]
                print(f"🧹 Cleaned old alerts - {len(self.alert_history)} alerts retained")
            
        except Exception as e:
            print(f"⚠️ Error recovery failed: {e}")


# Agent Management Functions
async def start_agent():
    """Start the AI agent in background"""
    agent = CreativeAutomationAgent()
    await agent.start_monitoring()

async def run_agent_monitor(agent: CreativeAutomationAgent, duration_minutes: int):
    """Run agent monitoring for a specified duration"""
    duration_seconds = duration_minutes * 60
    start_time = time.time()
    
    # Override monitoring duration
    original_monitoring = agent.monitoring
    agent.monitoring = True
    
    try:
        while agent.monitoring and (time.time() - start_time) < duration_seconds:
            # Monitor campaign briefs
            await agent.monitor_campaign_briefs()
            
            # Check system health
            await agent.monitor_system_health()
            
            # Track creative variants
            await agent.track_creative_variants()
            
            # Process any alerts
            await agent.process_alerts()
            
            # Show periodic status
            elapsed = time.time() - start_time
            remaining = duration_seconds - elapsed
            if int(elapsed) % 30 == 0:  # Every 30 seconds
                print(f"🕐 Agent monitoring: {remaining/60:.1f} minutes remaining")
            
            await asyncio.sleep(agent.check_interval)
    
    finally:
        agent.monitoring = original_monitoring
        print("🏁 Agent monitoring session completed")

def create_test_alert():
    """Create a test alert for demonstration"""
    agent = CreativeAutomationAgent()
    
    # Simulate creating an alert
    asyncio.run(agent.create_alert(
        "test_alert",
        "This is a test alert to demonstrate the AI agent system",
        "medium"
    ))
    
    return agent.get_status()


if __name__ == "__main__":
    # Demo the agent system
    agent = CreativeAutomationAgent()
    print("🤖 AI Agent Demo Starting...")
    
    # Create a test alert
    asyncio.run(agent.create_alert(
        "demo_alert",
        "Demo: System initialization complete",
        "low"
    ))
    
    print("Agent Status:")
    print(json.dumps(agent.get_status(), indent=2))