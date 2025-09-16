"""
AI Agent - Monitors pipeline operations and provides intelligent alerts.
"""

import asyncio
import logging
import json
import time
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)


@dataclass
class SystemMetrics:
    """System performance and status metrics."""
    timestamp: str
    queue_length: int
    api_costs_today: float
    success_rate_24h: float
    active_generations: int
    cache_hit_rate: float
    storage_usage_mb: float
    avg_generation_time: float


@dataclass
class Alert:
    """Alert structure for notifications."""
    id: str
    timestamp: str
    severity: str  # low, medium, high, critical
    alert_type: str
    title: str
    description: str
    context: Dict[str, Any]
    recommendations: List[str]
    stakeholders: List[str]


class CreativeAutomationAgent:
    """AI Agent for monitoring and managing creative automation pipeline."""
    
    def __init__(self, check_interval: int = 30):
        self.check_interval = check_interval
        self.running = False
        self.metrics_history = []
        self.alerts_sent = []
        
        # Monitoring thresholds
        self.thresholds = {
            'cost_daily_limit': 50.0,
            'success_rate_min': 85.0,
            'avg_generation_time_max': 60.0,
            'storage_limit_gb': 5.0,
            'queue_length_warning': 10
        }
        
        # Paths for monitoring
        self.output_dir = Path('output')
        self.cache_dir = Path('generated_cache')
        self.costs_file = Path('costs.json')
        self.logs_dir = Path('.')
        
        logger.info("AI Agent initialized for pipeline monitoring")
    
    async def start_monitoring(self):
        """Start the agent monitoring loop."""
        self.running = True
        logger.info("AI Agent started monitoring pipeline")
        
        try:
            while self.running:
                # Collect system metrics
                metrics = await self.collect_metrics()
                self.metrics_history.append(metrics)
                
                # Keep only last 24 hours of metrics
                cutoff_time = datetime.now() - timedelta(hours=24)
                self.metrics_history = [
                    m for m in self.metrics_history 
                    if datetime.fromisoformat(m.timestamp) > cutoff_time
                ]
                
                # Analyze for issues
                alerts = await self.analyze_metrics(metrics)
                
                # Process alerts
                for alert in alerts:
                    await self.handle_alert(alert)
                
                # Sleep until next check
                await asyncio.sleep(self.check_interval)
                
        except Exception as e:
            logger.error(f"Agent monitoring error: {e}")
        finally:
            logger.info("AI Agent stopped monitoring")
    
    def stop_monitoring(self):
        """Stop the agent monitoring loop."""
        self.running = False
    
    async def collect_metrics(self) -> SystemMetrics:
        """Collect current system metrics."""
        
        try:
            # Get current timestamp
            timestamp = datetime.now().isoformat()
            
            # Calculate API costs today
            api_costs_today = self._get_daily_api_costs()
            
            # Calculate cache hit rate
            cache_hit_rate = self._calculate_cache_hit_rate()
            
            # Calculate storage usage
            storage_usage_mb = self._calculate_storage_usage()
            
            # Calculate success rate (last 24h)
            success_rate_24h = self._calculate_success_rate()
            
            # Calculate average generation time
            avg_generation_time = self._calculate_avg_generation_time()
            
            # Count active generations (simplified)
            active_generations = 0  # Would integrate with actual pipeline status
            
            # Count queue length (simplified)
            queue_length = self._count_pending_campaigns()
            
            metrics = SystemMetrics(
                timestamp=timestamp,
                queue_length=queue_length,
                api_costs_today=api_costs_today,
                success_rate_24h=success_rate_24h,
                active_generations=active_generations,
                cache_hit_rate=cache_hit_rate,
                storage_usage_mb=storage_usage_mb,
                avg_generation_time=avg_generation_time
            )
            
            logger.debug(f"Collected metrics: {asdict(metrics)}")
            return metrics
            
        except Exception as e:
            logger.error(f"Error collecting metrics: {e}")
            # Return default metrics on error
            return SystemMetrics(
                timestamp=datetime.now().isoformat(),
                queue_length=0,
                api_costs_today=0.0,
                success_rate_24h=100.0,
                active_generations=0,
                cache_hit_rate=0.0,
                storage_usage_mb=0.0,
                avg_generation_time=0.0
            )
    
    async def analyze_metrics(self, metrics: SystemMetrics) -> List[Alert]:
        """Analyze metrics and generate alerts."""
        
        alerts = []
        
        # Check daily cost limit
        if metrics.api_costs_today > self.thresholds['cost_daily_limit']:
            alerts.append(self._create_alert(
                'critical',
                'cost_limit_exceeded',
                'Daily API Cost Limit Exceeded',
                f'Daily API costs (${metrics.api_costs_today:.2f}) exceeded limit (${self.thresholds["cost_daily_limit"]:.2f})',
                {'current_cost': metrics.api_costs_today, 'limit': self.thresholds['cost_daily_limit']},
                ['Pause non-urgent generation tasks', 'Review cost optimization', 'Consider increasing daily limit'],
                ['finance@company.com', 'operations@company.com']
            ))
        
        # Check success rate
        if metrics.success_rate_24h < self.thresholds['success_rate_min']:
            alerts.append(self._create_alert(
                'high',
                'low_success_rate',
                'Generation Success Rate Below Threshold',
                f'Success rate ({metrics.success_rate_24h:.1f}%) below minimum ({self.thresholds["success_rate_min"]:.1f}%)',
                {'current_rate': metrics.success_rate_24h, 'threshold': self.thresholds['success_rate_min']},
                ['Investigate API connectivity issues', 'Check error logs', 'Review prompt templates'],
                ['engineering@company.com', 'operations@company.com']
            ))
        
        # Check generation time
        if metrics.avg_generation_time > self.thresholds['avg_generation_time_max']:
            alerts.append(self._create_alert(
                'medium',
                'slow_generation',
                'Average Generation Time Increased',
                f'Average generation time ({metrics.avg_generation_time:.1f}s) exceeds normal range',
                {'current_time': metrics.avg_generation_time, 'threshold': self.thresholds['avg_generation_time_max']},
                ['Check API response times', 'Review system load', 'Consider scaling resources'],
                ['engineering@company.com']
            ))
        
        # Check queue length
        if metrics.queue_length > self.thresholds['queue_length_warning']:
            alerts.append(self._create_alert(
                'medium',
                'queue_backlog',
                'Campaign Queue Backlog Detected',
                f'Queue length ({metrics.queue_length}) indicates potential bottleneck',
                {'queue_length': metrics.queue_length, 'threshold': self.thresholds['queue_length_warning']},
                ['Scale up generation capacity', 'Prioritize urgent campaigns', 'Review resource allocation'],
                ['operations@company.com', 'creative-lead@company.com']
            ))
        
        # Check storage usage
        storage_gb = metrics.storage_usage_mb / 1024
        if storage_gb > self.thresholds['storage_limit_gb']:
            alerts.append(self._create_alert(
                'low',
                'storage_usage_high',
                'Storage Usage Approaching Limit',
                f'Storage usage ({storage_gb:.2f}GB) approaching limit ({self.thresholds["storage_limit_gb"]:.1f}GB)',
                {'current_usage_gb': storage_gb, 'limit_gb': self.thresholds['storage_limit_gb']},
                ['Clean up old cached assets', 'Archive completed campaigns', 'Consider storage expansion'],
                ['it@company.com']
            ))
        
        return alerts
    
    def _create_alert(
        self,
        severity: str,
        alert_type: str,
        title: str,
        description: str,
        context: Dict[str, Any],
        recommendations: List[str],
        stakeholders: List[str]
    ) -> Alert:
        """Create a structured alert."""
        
        alert_id = f"{alert_type}_{int(time.time())}"
        
        return Alert(
            id=alert_id,
            timestamp=datetime.now().isoformat(),
            severity=severity,
            alert_type=alert_type,
            title=title,
            description=description,
            context=context,
            recommendations=recommendations,
            stakeholders=stakeholders
        )
    
    async def handle_alert(self, alert: Alert):
        """Process and send alerts."""
        
        # Check if we've already sent this type of alert recently (prevent spam)
        recent_alerts = [
            a for a in self.alerts_sent 
            if a['alert_type'] == alert.alert_type and 
               datetime.fromisoformat(a['timestamp']) > datetime.now() - timedelta(hours=1)
        ]
        
        if recent_alerts:
            logger.debug(f"Skipping duplicate alert: {alert.alert_type}")
            return
        
        # Log the alert
        logger.warning(f"Alert generated: {alert.title} - {alert.description}")
        
        # Save alert to history
        self.alerts_sent.append(asdict(alert))
        
        # In a real implementation, this would:
        # 1. Send email notifications
        # 2. Post to Slack/Teams
        # 3. Update dashboard
        # 4. Create incident tickets
        
        # For now, save to file
        await self._save_alert_to_file(alert)
    
    async def _save_alert_to_file(self, alert: Alert):
        """Save alert to file for review."""
        
        alerts_dir = Path('alerts')
        alerts_dir.mkdir(exist_ok=True)
        
        alert_file = alerts_dir / f"alert_{alert.id}.json"
        
        try:
            with open(alert_file, 'w') as f:
                json.dump(asdict(alert), f, indent=2)
            
            logger.info(f"Alert saved to {alert_file}")
            
        except Exception as e:
            logger.error(f"Failed to save alert: {e}")
    
    def _get_daily_api_costs(self) -> float:
        """Get API costs for today."""
        
        if not self.costs_file.exists():
            return 0.0
        
        try:
            with open(self.costs_file, 'r') as f:
                costs = json.load(f)
            
            # In a real implementation, this would filter by date
            # For now, return total costs
            return costs.get('total_cost', 0.0)
            
        except Exception as e:
            logger.error(f"Error reading costs: {e}")
            return 0.0
    
    def _calculate_cache_hit_rate(self) -> float:
        """Calculate cache hit rate."""
        
        if not self.cache_dir.exists():
            return 0.0
        
        try:
            cached_files = list(self.cache_dir.glob('*.png'))
            if not cached_files:
                return 0.0
            
            # Simple calculation - in reality would track hits vs misses
            return 75.0  # Placeholder
            
        except Exception as e:
            logger.error(f"Error calculating cache hit rate: {e}")
            return 0.0
    
    def _calculate_storage_usage(self) -> float:
        """Calculate total storage usage in MB."""
        
        total_size = 0
        
        try:
            # Calculate output directory size
            if self.output_dir.exists():
                for file_path in self.output_dir.rglob('*'):
                    if file_path.is_file():
                        total_size += file_path.stat().st_size
            
            # Add cache directory size
            if self.cache_dir.exists():
                for file_path in self.cache_dir.rglob('*'):
                    if file_path.is_file():
                        total_size += file_path.stat().st_size
            
            return total_size / (1024 * 1024)  # Convert to MB
            
        except Exception as e:
            logger.error(f"Error calculating storage usage: {e}")
            return 0.0
    
    def _calculate_success_rate(self) -> float:
        """Calculate generation success rate."""
        
        # In a real implementation, this would analyze logs
        # For now, return a simulated rate
        return 92.5  # Placeholder
    
    def _calculate_avg_generation_time(self) -> float:
        """Calculate average generation time."""
        
        # In a real implementation, this would analyze timing logs
        # For now, return a simulated average
        return 25.3  # Placeholder in seconds
    
    def _count_pending_campaigns(self) -> int:
        """Count pending campaigns in queue."""
        
        # In a real implementation, this would check a queue system
        # For now, count YAML files that haven't been processed
        
        try:
            yaml_files = list(Path('.').glob('campaign_brief_*.yaml'))
            processed_campaigns = set()
            
            if self.output_dir.exists():
                for campaign_dir in self.output_dir.iterdir():
                    if campaign_dir.is_dir():
                        processed_campaigns.add(campaign_dir.name)
            
            # Simple heuristic - files without corresponding output
            pending = len(yaml_files) - len(processed_campaigns)
            return max(0, pending)
            
        except Exception as e:
            logger.error(f"Error counting pending campaigns: {e}")
            return 0
    
    def get_status_summary(self) -> Dict[str, Any]:
        """Get current agent status summary."""
        
        if not self.metrics_history:
            return {'status': 'no_data', 'message': 'No metrics collected yet'}
        
        latest_metrics = self.metrics_history[-1]
        recent_alerts = [
            a for a in self.alerts_sent 
            if datetime.fromisoformat(a['timestamp']) > datetime.now() - timedelta(hours=24)
        ]
        
        return {
            'status': 'running' if self.running else 'stopped',
            'last_check': latest_metrics.timestamp,
            'metrics': asdict(latest_metrics),
            'alerts_24h': len(recent_alerts),
            'critical_alerts': len([a for a in recent_alerts if a['severity'] == 'critical']),
            'monitoring_interval': self.check_interval
        }


# CLI interface for agent operations
async def run_agent_monitor(duration_minutes: int = 60):
    """Run the agent for a specified duration."""
    
    agent = CreativeAutomationAgent(check_interval=30)
    
    print(f"🤖 Starting AI Agent monitoring for {duration_minutes} minutes...")
    
    # Start monitoring
    monitor_task = asyncio.create_task(agent.start_monitoring())
    
    try:
        # Run for specified duration
        await asyncio.sleep(duration_minutes * 60)
        
    except KeyboardInterrupt:
        print("\n⏹️  Monitoring interrupted by user")
    
    finally:
        agent.stop_monitoring()
        monitor_task.cancel()
        
        try:
            await monitor_task
        except asyncio.CancelledError:
            pass
    
    # Print final status
    status = agent.get_status_summary()
    print(f"\n📊 Final Status:")
    print(f"   Metrics collected: {len(agent.metrics_history)}")
    print(f"   Alerts generated: {len(agent.alerts_sent)}")
    print(f"   Last API cost: ${status['metrics']['api_costs_today']:.2f}")
    print(f"   Success rate: {status['metrics']['success_rate_24h']:.1f}%")


if __name__ == "__main__":
    # Simple test run
    asyncio.run(run_agent_monitor(1))  # Run for 1 minute