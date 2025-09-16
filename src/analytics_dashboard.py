"""
Analytics Dashboard - Provides performance insights and campaign analytics.
"""

import logging
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
import json
import statistics
from collections import defaultdict, Counter

logger = logging.getLogger(__name__)


class AnalyticsDashboard:
    """Generates performance analytics and insights for the creative automation pipeline."""
    
    def __init__(self, data_retention_days: int = 30):
        self.data_retention_days = data_retention_days
        self.output_dir = Path('output')
        self.batch_dir = Path('batch_output')
        self.costs_file = Path('costs.json')
        self.cache_dir = Path('generated_cache')
        
        logger.info("Analytics dashboard initialized")
    
    def generate_performance_report(self) -> Dict[str, Any]:
        """Generate comprehensive performance analytics report."""
        
        # Collect data from various sources
        campaign_data = self._collect_campaign_data()
        cost_data = self._collect_cost_data()
        performance_metrics = self._calculate_performance_metrics(campaign_data)
        trends = self._analyze_trends(campaign_data)
        
        return {
            'report_generated': datetime.now().isoformat(),
            'summary': self._generate_summary(campaign_data, cost_data),
            'performance_metrics': performance_metrics,
            'cost_analysis': cost_data,
            'campaign_insights': self._generate_campaign_insights(campaign_data),
            'trends': trends,
            'recommendations': self._generate_recommendations(performance_metrics, cost_data)
        }
    
    def _collect_campaign_data(self) -> List[Dict[str, Any]]:
        """Collect data from all completed campaigns."""
        
        campaigns = []
        
        # Single campaigns
        if self.output_dir.exists():
            for campaign_dir in self.output_dir.iterdir():
                if campaign_dir.is_dir():
                    campaign_data = self._extract_campaign_data(campaign_dir)
                    if campaign_data:
                        campaigns.append(campaign_data)
        
        # Batch campaigns
        if self.batch_dir.exists():
            for campaign_dir in self.batch_dir.rglob('*/'):
                if campaign_dir.is_dir() and (campaign_dir / 'generation_report.json').exists():
                    campaign_data = self._extract_campaign_data(campaign_dir)
                    if campaign_data:
                        campaigns.append(campaign_data)
        
        # Filter by retention period
        cutoff_date = datetime.now() - timedelta(days=self.data_retention_days)
        campaigns = [
            c for c in campaigns 
            if datetime.fromisoformat(c['generated_at']) > cutoff_date
        ]
        
        logger.info(f"Collected data for {len(campaigns)} campaigns")
        return campaigns
    
    def _extract_campaign_data(self, campaign_dir: Path) -> Optional[Dict[str, Any]]:
        """Extract data from a single campaign directory."""
        
        try:
            # Load generation report
            report_file = campaign_dir / 'generation_report.json'
            if not report_file.exists():
                return None
            
            with open(report_file, 'r') as f:
                report_data = json.load(f)
            
            # Extract basic metrics
            campaign_data = {
                'campaign_id': report_data.get('campaign_id', 'unknown'),
                'generated_at': report_data.get('generated_at'),
                'products': report_data.get('products', 0),
                'aspect_ratios': report_data.get('aspect_ratios', []),
                'generated_files': report_data.get('generated_files', []),
                'api_calls_made': report_data.get('api_calls_made', 0),
                'localized_for': report_data.get('localized_for'),
                'compliance_score': report_data.get('compliance_score'),
                'campaign_dir': str(campaign_dir)
            }
            
            # Calculate additional metrics
            campaign_data['total_assets'] = len(campaign_data['generated_files'])
            campaign_data['unique_aspect_ratios'] = len(set(campaign_data['aspect_ratios']))
            
            # Check for compliance and localization reports
            campaign_data['has_compliance_report'] = (campaign_dir / 'compliance_report.txt').exists()
            campaign_data['has_localization_report'] = (campaign_dir / 'localization_report.txt').exists()
            
            # Extract file sizes
            total_size = 0
            for file_path in campaign_dir.rglob('*.jpg'):
                if file_path.exists():
                    total_size += file_path.stat().st_size
            
            campaign_data['total_size_mb'] = total_size / (1024 * 1024)
            
            return campaign_data
            
        except Exception as e:
            logger.error(f"Error extracting campaign data from {campaign_dir}: {e}")
            return None
    
    def _collect_cost_data(self) -> Dict[str, Any]:
        """Collect and analyze cost data."""
        
        if not self.costs_file.exists():
            return {
                'total_cost': 0.0,
                'api_calls': 0,
                'cost_per_call': 0.0,
                'services': {}
            }
        
        try:
            with open(self.costs_file, 'r') as f:
                cost_data = json.load(f)
            
            # Calculate additional metrics
            total_cost = cost_data.get('total_cost', 0.0)
            total_calls = cost_data.get('api_calls', 0)
            
            cost_analysis = {
                'total_cost': total_cost,
                'api_calls': total_calls,
                'cost_per_call': total_cost / total_calls if total_calls > 0 else 0.0,
                'services': {}
            }
            
            # Analyze by service
            for service, service_data in cost_data.items():
                if isinstance(service_data, dict) and 'cost' in service_data:
                    cost_analysis['services'][service] = {
                        'cost': service_data['cost'],
                        'calls': service_data.get('calls', 0),
                        'cost_per_call': service_data['cost'] / service_data.get('calls', 1),
                        'percentage_of_total': (service_data['cost'] / total_cost * 100) if total_cost > 0 else 0
                    }
            
            return cost_analysis
            
        except Exception as e:
            logger.error(f"Error collecting cost data: {e}")
            return {
                'total_cost': 0.0,
                'api_calls': 0,
                'cost_per_call': 0.0,
                'services': {}
            }
    
    def _calculate_performance_metrics(self, campaigns: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate performance metrics from campaign data."""
        
        if not campaigns:
            return {
                'total_campaigns': 0,
                'total_assets': 0,
                'avg_assets_per_campaign': 0,
                'avg_products_per_campaign': 0,
                'avg_compliance_score': 0,
                'localization_rate': 0,
                'api_efficiency': 0
            }
        
        # Basic statistics
        total_campaigns = len(campaigns)
        total_assets = sum(c.get('total_assets', 0) for c in campaigns)
        total_products = sum(c.get('products', 0) for c in campaigns)
        total_api_calls = sum(c.get('api_calls_made', 0) for c in campaigns)
        
        # Compliance scores
        compliance_scores = [c.get('compliance_score') for c in campaigns if c.get('compliance_score')]
        avg_compliance = statistics.mean(compliance_scores) if compliance_scores else 0
        
        # Localization analysis
        localized_campaigns = len([c for c in campaigns if c.get('localized_for')])
        localization_rate = (localized_campaigns / total_campaigns * 100) if total_campaigns > 0 else 0
        
        # API efficiency (assets per API call)
        api_efficiency = total_assets / total_api_calls if total_api_calls > 0 else 0
        
        return {
            'total_campaigns': total_campaigns,
            'total_assets': total_assets,
            'avg_assets_per_campaign': total_assets / total_campaigns if total_campaigns > 0 else 0,
            'avg_products_per_campaign': total_products / total_campaigns if total_campaigns > 0 else 0,
            'avg_compliance_score': avg_compliance,
            'localization_rate': localization_rate,
            'api_efficiency': api_efficiency,
            'total_api_calls': total_api_calls,
            'compliance_score_distribution': self._calculate_distribution(compliance_scores)
        }
    
    def _analyze_trends(self, campaigns: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze trends in campaign data over time."""
        
        if len(campaigns) < 2:
            return {'insufficient_data': True}
        
        # Group campaigns by date
        campaigns_by_date = defaultdict(list)
        
        for campaign in campaigns:
            try:
                date = datetime.fromisoformat(campaign['generated_at']).date()
                campaigns_by_date[date].append(campaign)
            except (ValueError, TypeError):
                continue
        
        # Calculate daily metrics
        daily_metrics = []
        for date, day_campaigns in sorted(campaigns_by_date.items()):
            daily_assets = sum(c.get('total_assets', 0) for c in day_campaigns)
            daily_api_calls = sum(c.get('api_calls_made', 0) for c in day_campaigns)
            daily_compliance = [c.get('compliance_score') for c in day_campaigns if c.get('compliance_score')]
            
            daily_metrics.append({
                'date': date.isoformat(),
                'campaigns': len(day_campaigns),
                'assets': daily_assets,
                'api_calls': daily_api_calls,
                'avg_compliance': statistics.mean(daily_compliance) if daily_compliance else None
            })
        
        # Calculate trends
        if len(daily_metrics) >= 2:
            recent_campaigns = daily_metrics[-7:]  # Last 7 days
            previous_campaigns = daily_metrics[-14:-7] if len(daily_metrics) >= 14 else daily_metrics[:-7]
            
            recent_avg = statistics.mean([d['campaigns'] for d in recent_campaigns])
            previous_avg = statistics.mean([d['campaigns'] for d in previous_campaigns]) if previous_campaigns else recent_avg
            
            campaign_trend = ((recent_avg - previous_avg) / previous_avg * 100) if previous_avg > 0 else 0
        else:
            campaign_trend = 0
        
        return {
            'daily_metrics': daily_metrics,
            'campaign_volume_trend': campaign_trend,
            'peak_day': max(daily_metrics, key=lambda x: x['campaigns']) if daily_metrics else None,
            'trend_period_days': len(daily_metrics)
        }
    
    def _generate_campaign_insights(self, campaigns: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate insights about campaign patterns and optimization opportunities."""
        
        if not campaigns:
            return {}
        
        # Analyze aspect ratio usage
        aspect_ratio_usage = Counter()
        for campaign in campaigns:
            for ratio in campaign.get('aspect_ratios', []):
                aspect_ratio_usage[ratio] += 1
        
        # Analyze localization patterns
        localization_usage = Counter()
        for campaign in campaigns:
            market = campaign.get('localized_for')
            if market:
                localization_usage[market] += 1
        
        # Analyze product count distribution
        product_counts = [c.get('products', 0) for c in campaigns]
        
        # File size analysis
        file_sizes = [c.get('total_size_mb', 0) for c in campaigns if c.get('total_size_mb', 0) > 0]
        
        insights = {
            'aspect_ratio_preferences': dict(aspect_ratio_usage.most_common()),
            'popular_markets': dict(localization_usage.most_common()),
            'product_distribution': {
                'avg_products': statistics.mean(product_counts) if product_counts else 0,
                'max_products': max(product_counts) if product_counts else 0,
                'min_products': min(product_counts) if product_counts else 0
            },
            'file_size_analysis': {
                'avg_size_mb': statistics.mean(file_sizes) if file_sizes else 0,
                'total_storage_mb': sum(file_sizes),
                'largest_campaign_mb': max(file_sizes) if file_sizes else 0
            }
        }
        
        return insights
    
    def _generate_recommendations(self, performance: Dict[str, Any], costs: Dict[str, Any]) -> List[str]:
        """Generate actionable recommendations based on analytics."""
        
        recommendations = []
        
        # Cost optimization
        if costs['cost_per_call'] > 0.05:
            recommendations.append(
                f"Consider optimizing API usage - current cost per call (${costs['cost_per_call']:.3f}) "
                "is above optimal range. Implement better caching strategies."
            )
        
        # Compliance optimization
        if performance.get('avg_compliance_score', 100) < 90:
            recommendations.append(
                f"Compliance score ({performance.get('avg_compliance_score', 0):.1f}%) could be improved. "
                "Review campaign brief templates and content guidelines."
            )
        
        # API efficiency
        if performance.get('api_efficiency', 0) < 2:
            recommendations.append(
                f"API efficiency ({performance.get('api_efficiency', 0):.1f} assets per call) is low. "
                "Increase asset reuse and improve caching strategies."
            )
        
        # Localization opportunities
        if performance.get('localization_rate', 0) < 30:
            recommendations.append(
                f"Localization rate ({performance.get('localization_rate', 0):.1f}%) suggests missed "
                "opportunities for global market expansion. Consider promoting localization features."
            )
        
        # Volume recommendations
        if performance.get('total_campaigns', 0) < 10:
            recommendations.append(
                "Campaign volume is low. Consider batch processing to improve efficiency and "
                "demonstrate scalability capabilities."
            )
        
        return recommendations
    
    def _calculate_distribution(self, values: List[float]) -> Dict[str, float]:
        """Calculate distribution statistics for a list of values."""
        
        if not values:
            return {}
        
        sorted_values = sorted(values)
        
        return {
            'min': min(values),
            'max': max(values),
            'mean': statistics.mean(values),
            'median': statistics.median(values),
            'std_dev': statistics.stdev(values) if len(values) > 1 else 0,
            'percentile_25': sorted_values[len(sorted_values) // 4],
            'percentile_75': sorted_values[3 * len(sorted_values) // 4]
        }
    
    def _generate_summary(self, campaigns: List[Dict[str, Any]], costs: Dict[str, Any]) -> Dict[str, Any]:
        """Generate executive summary of performance."""
        
        total_campaigns = len(campaigns)
        total_assets = sum(c.get('total_assets', 0) for c in campaigns)
        total_cost = costs.get('total_cost', 0)
        
        # Calculate ROI metrics
        cost_per_campaign = total_cost / total_campaigns if total_campaigns > 0 else 0
        cost_per_asset = total_cost / total_assets if total_assets > 0 else 0
        
        # Efficiency metrics
        avg_assets_per_campaign = total_assets / total_campaigns if total_campaigns > 0 else 0
        
        return {
            'total_campaigns_processed': total_campaigns,
            'total_assets_generated': total_assets,
            'total_cost_spent': total_cost,
            'cost_per_campaign': cost_per_campaign,
            'cost_per_asset': cost_per_asset,
            'avg_assets_per_campaign': avg_assets_per_campaign,
            'operational_efficiency': {
                'campaigns_per_dollar': total_campaigns / total_cost if total_cost > 0 else 0,
                'assets_per_dollar': total_assets / total_cost if total_cost > 0 else 0
            }
        }
    
    def export_dashboard_html(self, report_data: Dict[str, Any], output_path: str = "analytics_dashboard.html") -> str:
        """Export analytics dashboard as HTML file."""
        
        html_content = self._generate_dashboard_html(report_data)
        
        with open(output_path, 'w') as f:
            f.write(html_content)
        
        logger.info(f"Analytics dashboard exported to {output_path}")
        return output_path
    
    def _generate_dashboard_html(self, report_data: Dict[str, Any]) -> str:
        """Generate HTML dashboard content."""
        
        summary = report_data.get('summary', {})
        performance = report_data.get('performance_metrics', {})
        costs = report_data.get('cost_analysis', {})
        insights = report_data.get('campaign_insights', {})
        
        return f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Creative Automation Pipeline - Analytics Dashboard</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; background-color: #f5f5f5; }}
        .container {{ max-width: 1200px; margin: 0 auto; }}
        .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; border-radius: 10px; margin-bottom: 20px; }}
        .card {{ background: white; padding: 20px; border-radius: 10px; margin-bottom: 20px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
        .metric {{ display: inline-block; margin: 10px; padding: 15px; background: #f8f9fa; border-radius: 5px; text-align: center; }}
        .metric-value {{ font-size: 24px; font-weight: bold; color: #333; }}
        .metric-label {{ font-size: 14px; color: #666; }}
        .grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; }}
        .recommendation {{ background: #e3f2fd; border-left: 4px solid #2196f3; padding: 10px; margin: 10px 0; }}
        .insight {{ background: #f3e5f5; border-left: 4px solid #9c27b0; padding: 10px; margin: 10px 0; }}
        .success {{ color: #4caf50; }}
        .warning {{ color: #ff9800; }}
        .error {{ color: #f44336; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🎨 Creative Automation Pipeline</h1>
            <h2>Analytics Dashboard</h2>
            <p>Generated: {report_data.get('report_generated', 'Unknown')}</p>
        </div>
        
        <div class="card">
            <h2>📊 Executive Summary</h2>
            <div class="grid">
                <div class="metric">
                    <div class="metric-value">{summary.get('total_campaigns_processed', 0)}</div>
                    <div class="metric-label">Total Campaigns</div>
                </div>
                <div class="metric">
                    <div class="metric-value">{summary.get('total_assets_generated', 0)}</div>
                    <div class="metric-label">Assets Generated</div>
                </div>
                <div class="metric">
                    <div class="metric-value">${summary.get('total_cost_spent', 0):.2f}</div>
                    <div class="metric-label">Total Cost</div>
                </div>
                <div class="metric">
                    <div class="metric-value">${summary.get('cost_per_campaign', 0):.3f}</div>
                    <div class="metric-label">Cost per Campaign</div>
                </div>
            </div>
        </div>
        
        <div class="grid">
            <div class="card">
                <h3>🎯 Performance Metrics</h3>
                <p><strong>API Efficiency:</strong> {performance.get('api_efficiency', 0):.2f} assets per call</p>
                <p><strong>Avg Compliance Score:</strong> {performance.get('avg_compliance_score', 0):.1f}%</p>
                <p><strong>Localization Rate:</strong> {performance.get('localization_rate', 0):.1f}%</p>
                <p><strong>Avg Assets per Campaign:</strong> {performance.get('avg_assets_per_campaign', 0):.1f}</p>
            </div>
            
            <div class="card">
                <h3>💰 Cost Analysis</h3>
                <p><strong>Total API Calls:</strong> {costs.get('api_calls', 0)}</p>
                <p><strong>Cost per API Call:</strong> ${costs.get('cost_per_call', 0):.3f}</p>
                <p><strong>Primary Service:</strong> DALL-E ({costs.get('services', {}).get('dalle', {}).get('percentage_of_total', 0):.1f}%)</p>
            </div>
        </div>
        
        <div class="card">
            <h3>💡 Key Insights</h3>
            <div class="insight">
                <strong>Popular Aspect Ratios:</strong> {', '.join(list(insights.get('aspect_ratio_preferences', {}).keys())[:3])}
            </div>
            <div class="insight">
                <strong>Average File Size:</strong> {insights.get('file_size_analysis', {}).get('avg_size_mb', 0):.2f} MB per campaign
            </div>
            <div class="insight">
                <strong>Most Popular Markets:</strong> {', '.join(list(insights.get('popular_markets', {}).keys())[:3])}
            </div>
        </div>
        
        <div class="card">
            <h3>🚀 Recommendations</h3>
            {"".join([f'<div class="recommendation">{rec}</div>' for rec in report_data.get('recommendations', [])])}
        </div>
    </div>
</body>
</html>
        """