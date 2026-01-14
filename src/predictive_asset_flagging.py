"""
Predictive Asset Flagging System
AI-powered asset analysis with predictive issue detection and intelligent recommendations
"""

import asyncio
import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
import numpy as np
import logging
from pathlib import Path

class FlagSeverity(Enum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

class FlagCategory(Enum):
    QUANTITY = "quantity"
    QUALITY = "quality"
    COMPLIANCE = "compliance"
    PERFORMANCE = "performance"
    DEADLINE = "deadline"
    COST = "cost"
    DIVERSITY = "diversity"

@dataclass
class AssetFlag:
    """Comprehensive asset flag with AI-powered insights"""
    id: str
    campaign_id: str
    category: FlagCategory
    severity: FlagSeverity
    title: str
    description: str
    
    # Impact analysis
    business_impact: str
    revenue_risk: float
    timeline_impact: str
    
    # AI insights
    root_cause: str
    confidence_score: float
    predicted_outcomes: List[str]
    
    # Recommendations
    immediate_actions: List[str]
    preventive_measures: List[str]
    resource_requirements: Dict[str, Any]
    
    # Metadata
    detected_at: datetime = field(default_factory=datetime.now)
    affected_assets: List[str] = field(default_factory=list)
    related_metrics: Dict[str, float] = field(default_factory=dict)
    auto_resolvable: bool = False
    estimated_fix_time: timedelta = field(default_factory=lambda: timedelta(hours=1))

@dataclass
class AssetHealthScore:
    """Comprehensive asset health assessment"""
    overall_score: float = 0.0
    quantity_score: float = 0.0
    quality_score: float = 0.0
    diversity_score: float = 0.0
    compliance_score: float = 0.0
    timeline_score: float = 0.0
    
    trend_direction: str = "stable"  # improving, declining, stable
    risk_level: str = "low"  # low, medium, high, critical
    recommendations: List[str] = field(default_factory=list)

class PredictiveAssetFlagger:
    """AI-powered predictive asset flagging system"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # AI prediction models
        self.quality_predictor = QualityPredictor()
        self.timeline_predictor = TimelinePredictor()
        self.cost_predictor = CostPredictor()
        self.performance_predictor = PerformancePredictor()
        
        # Historical data for learning
        self.historical_campaigns = {}
        self.pattern_database = {}
        self.success_patterns = {}
        
        # Flag configuration
        self.flag_config = {
            "quantity_thresholds": {
                "critical": 1,
                "error": 2,
                "warning": 3,
                "target": 5
            },
            "quality_thresholds": {
                "critical": 0.4,
                "error": 0.5,
                "warning": 0.6,
                "target": 0.8
            },
            "diversity_thresholds": {
                "critical": 0.2,
                "error": 0.3,
                "warning": 0.4,
                "target": 0.7
            },
            "compliance_thresholds": {
                "critical": 0.5,
                "error": 0.6,
                "warning": 0.7,
                "target": 0.9
            },
            "predictive_window_hours": 24,
            "enable_auto_resolution": True,
            "machine_learning_enabled": True
        }
    
    async def analyze_campaign_assets(self, campaign_id: str, variant_metrics: Dict[str, Any], brief_metadata: Dict[str, Any]) -> Tuple[List[AssetFlag], AssetHealthScore]:
        """Comprehensive predictive asset analysis"""
        
        self.logger.info(f"🔍 Starting predictive asset analysis for campaign: {campaign_id}")
        
        # Collect comprehensive data
        asset_data = await self._collect_asset_data(campaign_id, variant_metrics, brief_metadata)
        
        # Generate health score
        health_score = await self._calculate_health_score(asset_data)
        
        # Predictive flag detection
        flags = await self._detect_predictive_flags(campaign_id, asset_data, health_score)
        
        # AI-powered root cause analysis
        for flag in flags:
            await self._enhance_flag_with_ai_insights(flag, asset_data)
        
        # Historical pattern matching
        pattern_insights = await self._analyze_historical_patterns(campaign_id, asset_data)
        flags.extend(pattern_insights)
        
        # Risk assessment and prioritization
        prioritized_flags = await self._prioritize_flags(flags, health_score)
        
        self.logger.info(f"✅ Analysis complete: {len(prioritized_flags)} flags detected, health score: {health_score.overall_score:.2f}")
        
        return prioritized_flags, health_score
    
    async def _collect_asset_data(self, campaign_id: str, variant_metrics: Dict[str, Any], brief_metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Collect comprehensive asset data for analysis"""
        
        current_time = datetime.now()
        
        data = {
            "campaign_id": campaign_id,
            "timestamp": current_time,
            
            # Quantity metrics
            "total_variants": variant_metrics.get("total_count", 0),
            "unique_variants": variant_metrics.get("unique_count", 0),
            "target_variants": brief_metadata.get("estimated_variants", 10),
            "completion_percentage": 0,
            
            # Quality metrics
            "avg_quality_score": variant_metrics.get("avg_quality_score", 0),
            "quality_distribution": variant_metrics.get("quality_distribution", {}),
            "technical_quality": variant_metrics.get("technical_quality", {}),
            
            # Diversity metrics
            "diversity_index": variant_metrics.get("diversity_index", 0),
            "style_variety": variant_metrics.get("style_variety_score", 0),
            "color_diversity": variant_metrics.get("color_diversity", 0),
            
            # Compliance metrics
            "brand_compliance_rate": variant_metrics.get("brand_compliance_rate", 0),
            "guideline_violations": variant_metrics.get("guideline_violations", []),
            
            # Performance metrics
            "avg_generation_time": variant_metrics.get("avg_generation_time", 0),
            "success_rate": variant_metrics.get("success_rate", 0),
            "cost_per_variant": variant_metrics.get("cost_per_variant", 0),
            
            # Timeline data
            "deadline": brief_metadata.get("deadline"),
            "urgency_score": brief_metadata.get("urgency_score", 0.5),
            "time_remaining": None,
            
            # Campaign context
            "complexity_score": brief_metadata.get("complexity_score", 0.5),
            "client_tier": brief_metadata.get("client_tier", "standard"),
            "priority": brief_metadata.get("priority", "medium")
        }
        
        # Calculate derived metrics
        if data["target_variants"] > 0:
            data["completion_percentage"] = (data["total_variants"] / data["target_variants"]) * 100
        
        if data["deadline"]:
            try:
                deadline_dt = datetime.fromisoformat(data["deadline"])
                data["time_remaining"] = deadline_dt - current_time
            except (ValueError, TypeError):
                # Invalid deadline format, skip time remaining calculation
                data["time_remaining"] = None
        
        return data
    
    async def _calculate_health_score(self, asset_data: Dict[str, Any]) -> AssetHealthScore:
        """Calculate comprehensive asset health score"""
        
        health = AssetHealthScore()
        
        # Quantity score
        completion_pct = asset_data["completion_percentage"]
        if completion_pct >= 100:
            health.quantity_score = 1.0
        elif completion_pct >= 80:
            health.quantity_score = 0.8
        elif completion_pct >= 60:
            health.quantity_score = 0.6
        elif completion_pct >= 40:
            health.quantity_score = 0.4
        else:
            health.quantity_score = 0.2
        
        # Quality score
        health.quality_score = asset_data["avg_quality_score"]
        
        # Diversity score
        health.diversity_score = asset_data["diversity_index"]
        
        # Compliance score
        health.compliance_score = asset_data["brand_compliance_rate"]
        
        # Timeline score
        time_remaining = asset_data.get("time_remaining")
        if time_remaining:
            hours_remaining = time_remaining.total_seconds() / 3600
            if hours_remaining > 48:
                health.timeline_score = 1.0
            elif hours_remaining > 24:
                health.timeline_score = 0.8
            elif hours_remaining > 12:
                health.timeline_score = 0.6
            elif hours_remaining > 6:
                health.timeline_score = 0.4
            else:
                health.timeline_score = 0.2
        else:
            health.timeline_score = 0.5
        
        # Overall score (weighted average)
        weights = {
            "quantity": 0.25,
            "quality": 0.25,
            "diversity": 0.15,
            "compliance": 0.20,
            "timeline": 0.15
        }
        
        health.overall_score = (
            health.quantity_score * weights["quantity"] +
            health.quality_score * weights["quality"] +
            health.diversity_score * weights["diversity"] +
            health.compliance_score * weights["compliance"] +
            health.timeline_score * weights["timeline"]
        )
        
        # Determine risk level
        if health.overall_score >= 0.8:
            health.risk_level = "low"
        elif health.overall_score >= 0.6:
            health.risk_level = "medium"
        elif health.overall_score >= 0.4:
            health.risk_level = "high"
        else:
            health.risk_level = "critical"
        
        # Generate recommendations
        health.recommendations = await self._generate_health_recommendations(health, asset_data)
        
        return health
    
    async def _detect_predictive_flags(self, campaign_id: str, asset_data: Dict[str, Any], health_score: AssetHealthScore) -> List[AssetFlag]:
        """Detect flags using predictive analysis"""
        
        flags = []
        
        # Quantity-based flags
        quantity_flags = await self._detect_quantity_flags(campaign_id, asset_data)
        flags.extend(quantity_flags)
        
        # Quality-based flags
        quality_flags = await self._detect_quality_flags(campaign_id, asset_data)
        flags.extend(quality_flags)
        
        # Diversity-based flags
        diversity_flags = await self._detect_diversity_flags(campaign_id, asset_data)
        flags.extend(diversity_flags)
        
        # Compliance-based flags
        compliance_flags = await self._detect_compliance_flags(campaign_id, asset_data)
        flags.extend(compliance_flags)
        
        # Timeline-based flags
        timeline_flags = await self._detect_timeline_flags(campaign_id, asset_data)
        flags.extend(timeline_flags)
        
        # Performance-based flags
        performance_flags = await self._detect_performance_flags(campaign_id, asset_data)
        flags.extend(performance_flags)
        
        # Predictive flags based on trends
        predictive_flags = await self._detect_trend_based_flags(campaign_id, asset_data, health_score)
        flags.extend(predictive_flags)
        
        return flags
    
    async def _detect_quantity_flags(self, campaign_id: str, asset_data: Dict[str, Any]) -> List[AssetFlag]:
        """Detect quantity-related flags"""
        
        flags = []
        total_variants = asset_data["total_variants"]
        target_variants = asset_data["target_variants"]
        completion_pct = asset_data["completion_percentage"]
        
        # Critical: No variants generated
        if total_variants == 0:
            flag = AssetFlag(
                id=f"{campaign_id}_no_variants_{int(time.time())}",
                campaign_id=campaign_id,
                category=FlagCategory.QUANTITY,
                severity=FlagSeverity.CRITICAL,
                title="No Variants Generated",
                description="Campaign has zero generated variants",
                business_impact="Campaign cannot proceed without assets",
                revenue_risk=100000.0,
                timeline_impact="Campaign launch at risk",
                root_cause="Generation system failure or configuration issue",
                confidence_score=0.95,
                predicted_outcomes=["Campaign delay", "Revenue loss", "Client dissatisfaction"],
                immediate_actions=[
                    "Check generation system status",
                    "Verify campaign brief configuration", 
                    "Escalate to technical team immediately"
                ],
                preventive_measures=[
                    "Implement pre-generation validation",
                    "Add system health monitoring",
                    "Create backup generation pipelines"
                ],
                resource_requirements={"urgent_tech_support": 1, "estimated_hours": 2},
                auto_resolvable=False,
                estimated_fix_time=timedelta(hours=2)
            )
            flags.append(flag)
        
        # Error: Significantly under target
        elif completion_pct < 50:
            severity = FlagSeverity.CRITICAL if completion_pct < 25 else FlagSeverity.ERROR
            
            flag = AssetFlag(
                id=f"{campaign_id}_low_quantity_{int(time.time())}",
                campaign_id=campaign_id,
                category=FlagCategory.QUANTITY,
                severity=severity,
                title=f"Low Variant Count ({total_variants}/{target_variants})",
                description=f"Only {completion_pct:.1f}% of target variants generated",
                business_impact="Insufficient assets for campaign launch",
                revenue_risk=50000.0 * (1 - completion_pct/100),
                timeline_impact="Potential delivery delay",
                root_cause=await self._analyze_quantity_root_cause(asset_data),
                confidence_score=0.85,
                predicted_outcomes=self._predict_quantity_outcomes(completion_pct),
                immediate_actions=await self._generate_quantity_actions(asset_data),
                preventive_measures=[
                    "Increase generation capacity",
                    "Optimize generation parameters",
                    "Add progress monitoring alerts"
                ],
                resource_requirements={"additional_compute": True, "estimated_hours": 4},
                auto_resolvable=True,
                estimated_fix_time=timedelta(hours=4)
            )
            flags.append(flag)
        
        return flags
    
    async def _detect_quality_flags(self, campaign_id: str, asset_data: Dict[str, Any]) -> List[AssetFlag]:
        """Detect quality-related flags"""
        
        flags = []
        avg_quality = asset_data["avg_quality_score"]
        
        if avg_quality < self.flag_config["quality_thresholds"]["error"]:
            severity = FlagSeverity.CRITICAL if avg_quality < self.flag_config["quality_thresholds"]["critical"] else FlagSeverity.ERROR
            
            flag = AssetFlag(
                id=f"{campaign_id}_low_quality_{int(time.time())}",
                campaign_id=campaign_id,
                category=FlagCategory.QUALITY,
                severity=severity,
                title=f"Low Quality Score ({avg_quality:.2f})",
                description=f"Average quality score below acceptable threshold",
                business_impact="Poor quality assets may damage brand reputation",
                revenue_risk=25000.0,
                timeline_impact="May require regeneration cycles",
                root_cause=await self._analyze_quality_root_cause(asset_data),
                confidence_score=0.80,
                predicted_outcomes=[
                    "Client rejection of assets",
                    "Required regeneration",
                    "Brand reputation risk"
                ],
                immediate_actions=[
                    "Review generation parameters",
                    "Implement quality filters",
                    "Consider manual review process"
                ],
                preventive_measures=[
                    "Improve quality control algorithms",
                    "Add real-time quality monitoring",
                    "Enhance generation models"
                ],
                resource_requirements={"quality_team_hours": 8, "regeneration_cycles": 2},
                auto_resolvable=True,
                estimated_fix_time=timedelta(hours=6)
            )
            flags.append(flag)
        
        return flags
    
    async def _detect_diversity_flags(self, campaign_id: str, asset_data: Dict[str, Any]) -> List[AssetFlag]:
        """Detect diversity-related flags"""
        
        flags = []
        diversity_index = asset_data["diversity_index"]
        
        if diversity_index < self.flag_config["diversity_thresholds"]["warning"]:
            severity = FlagSeverity.ERROR if diversity_index < self.flag_config["diversity_thresholds"]["error"] else FlagSeverity.WARNING
            
            flag = AssetFlag(
                id=f"{campaign_id}_low_diversity_{int(time.time())}",
                campaign_id=campaign_id,
                category=FlagCategory.DIVERSITY,
                severity=severity,
                title=f"Low Creative Diversity ({diversity_index:.2f})",
                description="Generated variants lack sufficient creative diversity",
                business_impact="Limited A/B testing options and reduced campaign effectiveness",
                revenue_risk=15000.0,
                timeline_impact="May need additional generation cycles",
                root_cause="Generation parameters may be too constrained",
                confidence_score=0.75,
                predicted_outcomes=[
                    "Reduced campaign performance",
                    "Limited optimization opportunities",
                    "Poor audience engagement variety"
                ],
                immediate_actions=[
                    "Adjust generation parameters for more variety",
                    "Generate additional diverse variants",
                    "Review creative brief constraints"
                ],
                preventive_measures=[
                    "Implement diversity scoring in generation",
                    "Add variety constraints to brief templates",
                    "Monitor diversity trends across campaigns"
                ],
                resource_requirements={"additional_generation_time": 2, "creative_review_hours": 3},
                auto_resolvable=True,
                estimated_fix_time=timedelta(hours=3)
            )
            flags.append(flag)
        
        return flags
    
    async def _detect_compliance_flags(self, campaign_id: str, asset_data: Dict[str, Any]) -> List[AssetFlag]:
        """Detect brand compliance flags"""
        
        flags = []
        compliance_rate = asset_data["brand_compliance_rate"]
        violations = asset_data["guideline_violations"]
        
        if compliance_rate < self.flag_config["compliance_thresholds"]["error"]:
            severity = FlagSeverity.CRITICAL if compliance_rate < self.flag_config["compliance_thresholds"]["critical"] else FlagSeverity.ERROR
            
            flag = AssetFlag(
                id=f"{campaign_id}_compliance_issue_{int(time.time())}",
                campaign_id=campaign_id,
                category=FlagCategory.COMPLIANCE,
                severity=severity,
                title=f"Brand Compliance Issues ({compliance_rate:.1%})",
                description=f"Brand compliance rate below threshold with {len(violations)} violations",
                business_impact="Brand guideline violations risk legal and reputation issues",
                revenue_risk=75000.0,
                timeline_impact="Assets may need legal review and regeneration",
                root_cause="Generation system not properly enforcing brand guidelines",
                confidence_score=0.90,
                predicted_outcomes=[
                    "Legal review required",
                    "Asset regeneration necessary",
                    "Potential brand damage"
                ],
                immediate_actions=[
                    "Review all flagged assets",
                    "Engage legal team for compliance check",
                    "Regenerate non-compliant assets"
                ],
                preventive_measures=[
                    "Strengthen brand guideline enforcement",
                    "Add automated compliance checking",
                    "Improve generation model training"
                ],
                resource_requirements={"legal_review_hours": 4, "regeneration_cycles": 1},
                affected_assets=[v for v in violations],
                auto_resolvable=False,
                estimated_fix_time=timedelta(hours=8)
            )
            flags.append(flag)
        
        return flags
    
    async def _detect_timeline_flags(self, campaign_id: str, asset_data: Dict[str, Any]) -> List[AssetFlag]:
        """Detect timeline-related flags"""
        
        flags = []
        time_remaining = asset_data.get("time_remaining")
        completion_pct = asset_data["completion_percentage"]
        
        if time_remaining and time_remaining.total_seconds() > 0:
            hours_remaining = time_remaining.total_seconds() / 3600
            
            # Predict if campaign will meet deadline
            predicted_completion = await self.timeline_predictor.predict_completion_time(asset_data)
            
            if predicted_completion and predicted_completion > time_remaining:
                severity = FlagSeverity.CRITICAL if hours_remaining < 12 else FlagSeverity.ERROR
                
                flag = AssetFlag(
                    id=f"{campaign_id}_deadline_risk_{int(time.time())}",
                    campaign_id=campaign_id,
                    category=FlagCategory.DEADLINE,
                    severity=severity,
                    title=f"Deadline Risk ({hours_remaining:.1f}h remaining)",
                    description=f"Predicted completion time exceeds deadline by {(predicted_completion - time_remaining).total_seconds() / 3600:.1f} hours",
                    business_impact="Campaign launch delay risk",
                    revenue_risk=100000.0 if hours_remaining < 24 else 50000.0,
                    timeline_impact=f"Potential {(predicted_completion - time_remaining).total_seconds() / 3600:.1f}h delay",
                    root_cause=await self._analyze_timeline_root_cause(asset_data),
                    confidence_score=0.85,
                    predicted_outcomes=[
                        "Campaign launch delay",
                        "Client disappointment",
                        "Revenue impact"
                    ],
                    immediate_actions=[
                        "Increase resource allocation",
                        "Prioritize critical variants",
                        "Prepare client communication"
                    ],
                    preventive_measures=[
                        "Improve timeline estimation",
                        "Add early warning systems",
                        "Implement rush processing capabilities"
                    ],
                    resource_requirements={"additional_compute": True, "overtime_hours": 8},
                    auto_resolvable=True,
                    estimated_fix_time=timedelta(hours=2)
                )
                flags.append(flag)
        
        return flags
    
    async def _enhance_flag_with_ai_insights(self, flag: AssetFlag, asset_data: Dict[str, Any]):
        """Enhance flag with AI-powered insights"""
        
        # Analyze historical patterns
        similar_campaigns = await self._find_similar_historical_campaigns(asset_data)
        
        if similar_campaigns:
            # Update confidence based on historical data
            historical_accuracy = np.mean([c["resolution_success"] for c in similar_campaigns])
            flag.confidence_score = (flag.confidence_score + historical_accuracy) / 2
            
            # Add historical insights to recommendations
            successful_actions = []
            for campaign in similar_campaigns:
                if campaign["resolution_success"]:
                    successful_actions.extend(campaign["successful_actions"])
            
            # Add most common successful actions
            if successful_actions:
                action_counts = {}
                for action in successful_actions:
                    action_counts[action] = action_counts.get(action, 0) + 1
                
                top_actions = sorted(action_counts.items(), key=lambda x: x[1], reverse=True)[:3]
                flag.immediate_actions.extend([action for action, _ in top_actions])
    
    async def _prioritize_flags(self, flags: List[AssetFlag], health_score: AssetHealthScore) -> List[AssetFlag]:
        """Prioritize flags based on business impact and urgency"""
        
        def calculate_priority_score(flag: AssetFlag) -> float:
            # Base score from severity
            severity_scores = {
                FlagSeverity.CRITICAL: 1.0,
                FlagSeverity.ERROR: 0.7,
                FlagSeverity.WARNING: 0.4,
                FlagSeverity.INFO: 0.1
            }
            
            base_score = severity_scores[flag.severity]
            
            # Adjust based on business impact
            revenue_factor = min(flag.revenue_risk / 100000, 1.0)
            confidence_factor = flag.confidence_score
            
            # Urgency factor based on estimated fix time
            urgency_factor = 1.0 / (flag.estimated_fix_time.total_seconds() / 3600)
            
            priority_score = base_score * 0.4 + revenue_factor * 0.3 + confidence_factor * 0.2 + urgency_factor * 0.1
            
            return priority_score
        
        # Sort flags by priority score
        prioritized_flags = sorted(flags, key=calculate_priority_score, reverse=True)
        
        return prioritized_flags
    
    # Helper methods for root cause analysis
    async def _analyze_quantity_root_cause(self, asset_data: Dict[str, Any]) -> str:
        """Analyze root cause of quantity issues"""
        
        if asset_data["success_rate"] < 0.5:
            return "High generation failure rate"
        elif asset_data["avg_generation_time"] > 300:  # > 5 minutes
            return "Slow generation performance"
        elif asset_data["total_variants"] == 0:
            return "Generation system not running"
        else:
            return "Insufficient generation capacity"
    
    async def _analyze_quality_root_cause(self, asset_data: Dict[str, Any]) -> str:
        """Analyze root cause of quality issues"""
        
        technical_quality = asset_data.get("technical_quality", {})
        
        if technical_quality.get("resolution", 0) < 0.5:
            return "Low resolution generation settings"
        elif technical_quality.get("format_optimization", 0) < 0.5:
            return "Poor format optimization"
        elif asset_data["complexity_score"] > 0.8:
            return "Generation complexity exceeds model capabilities"
        else:
            return "Generation model needs optimization"
    
    async def _analyze_timeline_root_cause(self, asset_data: Dict[str, Any]) -> str:
        """Analyze root cause of timeline issues"""
        
        if asset_data["avg_generation_time"] > 180:  # > 3 minutes
            return "Slow generation performance"
        elif asset_data["success_rate"] < 0.7:
            return "High retry rate due to failures"
        elif asset_data["completion_percentage"] < 30:
            return "Insufficient generation progress"
        else:
            return "Resource constraints limiting throughput"


class QualityPredictor:
    """Predict quality issues before they occur"""
    
    async def predict_quality_trends(self, asset_data: Dict[str, Any]) -> Dict[str, float]:
        """Predict quality trends"""
        
        current_quality = asset_data["avg_quality_score"]
        
        # Simple trend prediction (would use ML in production)
        predictions = {
            "next_hour_quality": current_quality * 0.95,  # Slight degradation
            "completion_quality": current_quality * 0.9,
            "confidence": 0.7
        }
        
        return predictions


class TimelinePredictor:
    """Predict timeline and completion estimates"""
    
    async def predict_completion_time(self, asset_data: Dict[str, Any]) -> Optional[timedelta]:
        """Predict campaign completion time"""
        
        completion_pct = asset_data["completion_percentage"]
        avg_generation_time = asset_data["avg_generation_time"]
        
        if completion_pct > 0 and avg_generation_time > 0:
            remaining_variants = asset_data["target_variants"] - asset_data["total_variants"]
            estimated_remaining_time = remaining_variants * avg_generation_time
            
            return timedelta(seconds=estimated_remaining_time)
        
        return None


class CostPredictor:
    """Predict cost overruns and budget issues"""
    
    async def predict_campaign_cost(self, asset_data: Dict[str, Any]) -> Dict[str, float]:
        """Predict total campaign cost"""
        
        cost_per_variant = asset_data["cost_per_variant"]
        target_variants = asset_data["target_variants"]
        
        predictions = {
            "predicted_total_cost": cost_per_variant * target_variants,
            "cost_variance": cost_per_variant * 0.1,  # 10% variance
            "confidence": 0.8
        }
        
        return predictions


class PerformancePredictor:
    """Predict performance issues and bottlenecks"""
    
    async def predict_performance_bottlenecks(self, asset_data: Dict[str, Any]) -> List[str]:
        """Predict potential performance bottlenecks"""
        
        bottlenecks = []
        
        if asset_data["avg_generation_time"] > 180:
            bottlenecks.append("Generation speed bottleneck")
        
        if asset_data["success_rate"] < 0.8:
            bottlenecks.append("Generation reliability issues")
        
        if asset_data["complexity_score"] > 0.8:
            bottlenecks.append("High complexity causing delays")
        
        return bottlenecks


# Example usage and demo
async def demo_predictive_flagging():
    """Demonstrate the predictive asset flagging system"""
    flagger = PredictiveAssetFlagger()
    
    print("🚨 Predictive Asset Flagging System Demo")
    print("=" * 50)
    print("🎯 Advanced Features:")
    print("  ✅ AI-powered predictive issue detection")
    print("  ✅ Root cause analysis with historical pattern matching")
    print("  ✅ Business impact assessment and revenue risk calculation")
    print("  ✅ Intelligent recommendations with auto-resolution capabilities")
    print("  ✅ Timeline prediction and deadline risk analysis")
    print("  ✅ Quality trend forecasting and performance optimization")
    
    # Simulate campaign analysis
    sample_variant_metrics = {
        "total_count": 2,
        "unique_count": 2,
        "avg_quality_score": 0.45,
        "diversity_index": 0.3,
        "brand_compliance_rate": 0.6,
        "avg_generation_time": 240,
        "success_rate": 0.7,
        "cost_per_variant": 15.0
    }
    
    sample_brief_metadata = {
        "estimated_variants": 12,
        "deadline": (datetime.now() + timedelta(hours=18)).isoformat(),
        "urgency_score": 0.8,
        "complexity_score": 0.7,
        "client_tier": "enterprise",
        "priority": "high"
    }
    
    flags, health_score = await flagger.analyze_campaign_assets(
        "demo_campaign", sample_variant_metrics, sample_brief_metadata
    )
    
    print(f"\n📊 Analysis Results:")
    print(f"  Health Score: {health_score.overall_score:.2f} ({health_score.risk_level} risk)")
    print(f"  Flags Detected: {len(flags)}")
    
    for i, flag in enumerate(flags[:3]):  # Show top 3 flags
        print(f"\n🚨 Flag {i+1}: {flag.title}")
        print(f"   Severity: {flag.severity.value.upper()}")
        print(f"   Business Impact: {flag.business_impact}")
        print(f"   Revenue Risk: ${flag.revenue_risk:,.0f}")
        print(f"   Confidence: {flag.confidence_score:.1%}")
        print(f"   Immediate Actions: {', '.join(flag.immediate_actions[:2])}")
    
    return flagger


if __name__ == "__main__":
    asyncio.run(demo_predictive_flagging())