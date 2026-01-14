"""
A/B Testing Framework for Creative Variants
Enables performance testing of different creative approaches
"""

import json
import logging
import os
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
import random
import math
from enum import Enum

logger = logging.getLogger(__name__)


class TestStatus(Enum):
    DRAFT = "draft"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    STOPPED = "stopped"


class Variant:
    """Represents a single creative variant in an A/B test"""
    
    def __init__(self, variant_id: str, name: str, description: str, config: Dict[str, Any]):
        self.variant_id = variant_id
        self.name = name
        self.description = description
        self.config = config
        self.impressions = 0
        self.clicks = 0
        self.conversions = 0
        self.cost = 0.0
        self.created_at = datetime.now().isoformat()
    
    @property
    def ctr(self) -> float:
        """Click-through rate"""
        return (self.clicks / self.impressions) if self.impressions > 0 else 0.0
    
    @property
    def cvr(self) -> float:
        """Conversion rate"""
        return (self.conversions / self.clicks) if self.clicks > 0 else 0.0
    
    @property
    def cpc(self) -> float:
        """Cost per click"""
        return (self.cost / self.clicks) if self.clicks > 0 else 0.0
    
    @property
    def cpa(self) -> float:
        """Cost per acquisition"""
        return (self.cost / self.conversions) if self.conversions > 0 else 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "variant_id": self.variant_id,
            "name": self.name,
            "description": self.description,
            "config": self.config,
            "metrics": {
                "impressions": self.impressions,
                "clicks": self.clicks,
                "conversions": self.conversions,
                "cost": self.cost,
                "ctr": self.ctr,
                "cvr": self.cvr,
                "cpc": self.cpc,
                "cpa": self.cpa
            },
            "created_at": self.created_at
        }


class ABTest:
    """A/B test experiment for creative variants"""
    
    def __init__(
        self,
        test_name: str,
        campaign_id: str,
        description: str = "",
        traffic_split: Optional[Dict[str, float]] = None,
        min_sample_size: int = 1000,
        confidence_level: float = 0.95,
        min_runtime_hours: int = 24
    ):
        self.test_id = str(uuid.uuid4())
        self.test_name = test_name
        self.campaign_id = campaign_id
        self.description = description
        self.variants: Dict[str, Variant] = {}
        self.traffic_split = traffic_split or {}
        self.min_sample_size = min_sample_size
        self.confidence_level = confidence_level
        self.min_runtime_hours = min_runtime_hours
        
        self.status = TestStatus.DRAFT
        self.created_at = datetime.now()
        self.started_at: Optional[datetime] = None
        self.ended_at: Optional[datetime] = None
        
        self.hypothesis = ""
        self.success_metric = "ctr"  # ctr, cvr, cpa, cpc
        self.notes: List[str] = []
    
    def add_variant(self, name: str, description: str, config: Dict[str, Any]) -> str:
        """Add a new variant to the test"""
        variant_id = f"variant_{len(self.variants) + 1}"
        variant = Variant(variant_id, name, description, config)
        self.variants[variant_id] = variant
        
        # Auto-adjust traffic split for equal distribution
        if not self.traffic_split:
            split_percentage = 1.0 / len(self.variants)
            self.traffic_split = {vid: split_percentage for vid in self.variants.keys()}
        
        return variant_id
    
    def start_test(self) -> bool:
        """Start the A/B test"""
        if len(self.variants) < 2:
            raise ValueError("At least 2 variants required to start test")
        
        if sum(self.traffic_split.values()) != 1.0:
            raise ValueError("Traffic split must sum to 1.0")
        
        self.status = TestStatus.RUNNING
        self.started_at = datetime.now()
        self.notes.append(f"Test started at {self.started_at.isoformat()}")
        return True
    
    def pause_test(self) -> bool:
        """Pause the running test"""
        if self.status != TestStatus.RUNNING:
            return False
        
        self.status = TestStatus.PAUSED
        self.notes.append(f"Test paused at {datetime.now().isoformat()}")
        return True
    
    def resume_test(self) -> bool:
        """Resume a paused test"""
        if self.status != TestStatus.PAUSED:
            return False
        
        self.status = TestStatus.RUNNING
        self.notes.append(f"Test resumed at {datetime.now().isoformat()}")
        return True
    
    def stop_test(self, reason: str = "") -> bool:
        """Stop the test manually"""
        if self.status not in [TestStatus.RUNNING, TestStatus.PAUSED]:
            return False
        
        self.status = TestStatus.STOPPED
        self.ended_at = datetime.now()
        self.notes.append(f"Test stopped at {self.ended_at.isoformat()}: {reason}")
        return True
    
    def record_impression(self, variant_id: str, count: int = 1) -> bool:
        """Record impressions for a variant"""
        if variant_id not in self.variants:
            return False
        
        self.variants[variant_id].impressions += count
        return True
    
    def record_click(self, variant_id: str, count: int = 1) -> bool:
        """Record clicks for a variant"""
        if variant_id not in self.variants:
            return False
        
        self.variants[variant_id].clicks += count
        return True
    
    def record_conversion(self, variant_id: str, count: int = 1) -> bool:
        """Record conversions for a variant"""
        if variant_id not in self.variants:
            return False
        
        self.variants[variant_id].conversions += count
        return True
    
    def record_cost(self, variant_id: str, cost: float) -> bool:
        """Record cost for a variant"""
        if variant_id not in self.variants:
            return False
        
        self.variants[variant_id].cost += cost
        return True
    
    def get_variant_assignment(self, user_id: str) -> str:
        """Consistently assign users to variants based on traffic split"""
        # Use hash for consistent assignment
        hash_value = hash(f"{self.test_id}_{user_id}") % 1000000
        percentage = hash_value / 1000000
        
        cumulative_split = 0.0
        for variant_id, split in self.traffic_split.items():
            cumulative_split += split
            if percentage <= cumulative_split:
                return variant_id
        
        # Fallback to first variant
        return list(self.variants.keys())[0]
    
    def calculate_statistical_significance(self) -> Dict[str, Any]:
        """Calculate statistical significance between variants"""
        if len(self.variants) != 2:
            return {"error": "Statistical significance calculation only supports 2 variants"}
        
        variants = list(self.variants.values())
        v1, v2 = variants[0], variants[1]
        
        # Calculate significance for CTR
        if v1.impressions > 0 and v2.impressions > 0:
            p1 = v1.ctr
            p2 = v2.ctr
            n1 = v1.impressions
            n2 = v2.impressions
            
            # Pooled standard error
            p_pooled = (v1.clicks + v2.clicks) / (n1 + n2)
            se = math.sqrt(p_pooled * (1 - p_pooled) * (1/n1 + 1/n2))
            
            if se > 0:
                z_score = abs(p1 - p2) / se
                # Approximate p-value for two-tailed test
                p_value = 2 * (1 - self._normal_cdf(abs(z_score)))
                
                return {
                    "variant_1": {"name": v1.name, "ctr": p1, "sample_size": n1},
                    "variant_2": {"name": v2.name, "ctr": p2, "sample_size": n2},
                    "z_score": z_score,
                    "p_value": p_value,
                    "significant": p_value < (1 - self.confidence_level),
                    "confidence_level": self.confidence_level,
                    "winner": v1.name if p1 > p2 else v2.name if p2 > p1 else "tie"
                }
        
        return {"error": "Insufficient data for significance calculation"}
    
    def _normal_cdf(self, x: float) -> float:
        """Cumulative distribution function for standard normal distribution"""
        return (1.0 + math.erf(x / math.sqrt(2.0))) / 2.0
    
    def check_completion_criteria(self) -> Dict[str, Any]:
        """Check if test meets completion criteria"""
        if self.status != TestStatus.RUNNING:
            return {"ready_to_complete": False, "reason": "Test not running"}
        
        # Check minimum runtime
        if self.started_at:
            runtime_hours = (datetime.now() - self.started_at).total_seconds() / 3600
            if runtime_hours < self.min_runtime_hours:
                return {
                    "ready_to_complete": False,
                    "reason": f"Minimum runtime not met. {runtime_hours:.1f}/{self.min_runtime_hours} hours"
                }
        
        # Check minimum sample size
        total_impressions = sum(v.impressions for v in self.variants.values())
        if total_impressions < self.min_sample_size:
            return {
                "ready_to_complete": False,
                "reason": f"Minimum sample size not met. {total_impressions}/{self.min_sample_size} impressions"
            }
        
        # Check statistical significance
        significance = self.calculate_statistical_significance()
        if "error" not in significance and significance.get("significant"):
            return {
                "ready_to_complete": True,
                "reason": "Statistical significance achieved",
                "significance": significance
            }
        
        return {
            "ready_to_complete": False,
            "reason": "Statistical significance not yet achieved",
            "current_significance": significance
        }
    
    def generate_report(self) -> Dict[str, Any]:
        """Generate comprehensive test report"""
        report = {
            "test_info": {
                "test_id": self.test_id,
                "test_name": self.test_name,
                "campaign_id": self.campaign_id,
                "description": self.description,
                "hypothesis": self.hypothesis,
                "success_metric": self.success_metric,
                "status": self.status.value,
                "created_at": self.created_at.isoformat(),
                "started_at": self.started_at.isoformat() if self.started_at else None,
                "ended_at": self.ended_at.isoformat() if self.ended_at else None
            },
            "variants": [v.to_dict() for v in self.variants.values()],
            "traffic_split": self.traffic_split,
            "statistical_analysis": self.calculate_statistical_significance(),
            "completion_criteria": self.check_completion_criteria(),
            "summary": self._generate_summary(),
            "recommendations": self._generate_recommendations(),
            "notes": self.notes
        }
        
        return report
    
    def _generate_summary(self) -> Dict[str, Any]:
        """Generate test summary statistics"""
        total_impressions = sum(v.impressions for v in self.variants.values())
        total_clicks = sum(v.clicks for v in self.variants.values())
        total_conversions = sum(v.conversions for v in self.variants.values())
        total_cost = sum(v.cost for v in self.variants.values())
        
        # Find best performing variant by success metric
        best_variant = None
        best_value = 0
        
        for variant in self.variants.values():
            if self.success_metric == "ctr":
                value = variant.ctr
            elif self.success_metric == "cvr":
                value = variant.cvr
            elif self.success_metric == "cpa":
                value = -variant.cpa if variant.cpa > 0 else 0  # Lower is better
            elif self.success_metric == "cpc":
                value = -variant.cpc if variant.cpc > 0 else 0  # Lower is better
            else:
                value = variant.ctr
            
            if value > best_value:
                best_value = value
                best_variant = variant
        
        return {
            "total_impressions": total_impressions,
            "total_clicks": total_clicks,
            "total_conversions": total_conversions,
            "total_cost": total_cost,
            "overall_ctr": total_clicks / total_impressions if total_impressions > 0 else 0,
            "overall_cvr": total_conversions / total_clicks if total_clicks > 0 else 0,
            "best_variant": best_variant.name if best_variant else None,
            "improvement": self._calculate_improvement(),
            "duration_hours": (datetime.now() - self.started_at).total_seconds() / 3600 if self.started_at else 0
        }
    
    def _calculate_improvement(self) -> Optional[float]:
        """Calculate percentage improvement of best variant over baseline"""
        if len(self.variants) < 2:
            return None
        
        variants = list(self.variants.values())
        baseline = variants[0]  # Assume first variant is baseline
        best_variant = max(variants, key=lambda v: getattr(v, self.success_metric))
        
        if best_variant == baseline:
            return 0.0
        
        baseline_value = getattr(baseline, self.success_metric)
        best_value = getattr(best_variant, self.success_metric)
        
        if baseline_value > 0:
            return ((best_value - baseline_value) / baseline_value) * 100
        
        return None
    
    def _generate_recommendations(self) -> List[str]:
        """Generate actionable recommendations based on test results"""
        recommendations = []
        
        completion_check = self.check_completion_criteria()
        
        if completion_check["ready_to_complete"]:
            significance = completion_check.get("significance", {})
            if significance.get("significant"):
                winner = significance.get("winner")
                recommendations.append(f"✅ Test is ready to conclude. Winner: {winner}")
                recommendations.append(f"🚀 Implement {winner} for improved performance")
        else:
            recommendations.append(f"⏳ Continue test: {completion_check['reason']}")
        
        # Performance recommendations
        variants = list(self.variants.values())
        if len(variants) >= 2:
            best_ctr = max(v.ctr for v in variants)
            worst_ctr = min(v.ctr for v in variants)
            
            if best_ctr > worst_ctr * 1.2:  # 20% difference
                recommendations.append("📈 Significant performance difference detected between variants")
        
        # Sample size recommendations
        total_impressions = sum(v.impressions for v in variants)
        if total_impressions < self.min_sample_size:
            recommendations.append(f"📊 Increase traffic to reach minimum sample size ({total_impressions}/{self.min_sample_size})")
        
        return recommendations


class ABTestManager:
    """Manages multiple A/B tests for the creative automation pipeline"""
    
    def __init__(self, storage_path: str = "ab_tests.json"):
        self.storage_path = storage_path
        self.tests: Dict[str, ABTest] = {}
        self.load_tests()
    
    def create_test(
        self,
        test_name: str,
        campaign_id: str,
        description: str = "",
        min_sample_size: int = 1000,
        confidence_level: float = 0.95
    ) -> str:
        """Create a new A/B test"""
        test = ABTest(
            test_name=test_name,
            campaign_id=campaign_id,
            description=description,
            min_sample_size=min_sample_size,
            confidence_level=confidence_level
        )
        
        self.tests[test.test_id] = test
        self.save_tests()
        return test.test_id
    
    def get_test(self, test_id: str) -> Optional[ABTest]:
        """Get test by ID"""
        return self.tests.get(test_id)
    
    def list_tests(self, campaign_id: Optional[str] = None, status: Optional[TestStatus] = None) -> List[Dict[str, Any]]:
        """List tests with optional filters"""
        tests = []
        for test in self.tests.values():
            if campaign_id and test.campaign_id != campaign_id:
                continue
            if status and test.status != status:
                continue
            
            tests.append({
                "test_id": test.test_id,
                "test_name": test.test_name,
                "campaign_id": test.campaign_id,
                "status": test.status.value,
                "variant_count": len(test.variants),
                "created_at": test.created_at.isoformat()
            })
        
        return sorted(tests, key=lambda x: x["created_at"], reverse=True)
    
    def save_tests(self):
        """Save tests to storage"""
        try:
            # Convert tests to serializable format
            serializable_tests = {}
            for test_id, test in self.tests.items():
                test_data = {
                    "test_id": test.test_id,
                    "test_name": test.test_name,
                    "campaign_id": test.campaign_id,
                    "description": test.description,
                    "status": test.status.value,
                    "created_at": test.created_at.isoformat(),
                    "started_at": test.started_at.isoformat() if test.started_at else None,
                    "ended_at": test.ended_at.isoformat() if test.ended_at else None,
                    "variants": [v.to_dict() for v in test.variants.values()],
                    "traffic_split": test.traffic_split,
                    "min_sample_size": test.min_sample_size,
                    "confidence_level": test.confidence_level,
                    "hypothesis": test.hypothesis,
                    "success_metric": test.success_metric,
                    "notes": test.notes
                }
                serializable_tests[test_id] = test_data
            
            with open(self.storage_path, 'w') as f:
                json.dump(serializable_tests, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving tests: {e}")
    
    def load_tests(self):
        """Load tests from storage"""
        try:
            if os.path.exists(self.storage_path):
                with open(self.storage_path, 'r') as f:
                    data = json.load(f)
                
                for test_id, test_data in data.items():
                    # Reconstruct ABTest object
                    test = ABTest(
                        test_name=test_data["test_name"],
                        campaign_id=test_data["campaign_id"],
                        description=test_data["description"],
                        min_sample_size=test_data["min_sample_size"],
                        confidence_level=test_data["confidence_level"]
                    )
                    
                    test.test_id = test_data["test_id"]
                    test.status = TestStatus(test_data["status"])
                    test.created_at = datetime.fromisoformat(test_data["created_at"])
                    test.started_at = datetime.fromisoformat(test_data["started_at"]) if test_data["started_at"] else None
                    test.ended_at = datetime.fromisoformat(test_data["ended_at"]) if test_data["ended_at"] else None
                    test.traffic_split = test_data["traffic_split"]
                    test.hypothesis = test_data["hypothesis"]
                    test.success_metric = test_data["success_metric"]
                    test.notes = test_data["notes"]
                    
                    # Reconstruct variants
                    for variant_data in test_data["variants"]:
                        variant = Variant(
                            variant_data["variant_id"],
                            variant_data["name"],
                            variant_data["description"],
                            variant_data["config"]
                        )
                        metrics = variant_data["metrics"]
                        variant.impressions = metrics["impressions"]
                        variant.clicks = metrics["clicks"]
                        variant.conversions = metrics["conversions"]
                        variant.cost = metrics["cost"]
                        variant.created_at = variant_data["created_at"]
                        
                        test.variants[variant.variant_id] = variant
                    
                    self.tests[test_id] = test
        except Exception as e:
            logger.error(f"Error loading tests: {e}")
    
    def simulate_test_data(self, test_id: str, days: int = 7) -> bool:
        """Simulate test data for demonstration purposes"""
        test = self.get_test(test_id)
        if not test or len(test.variants) < 2:
            return False
        
        variants = list(test.variants.values())
        
        # Simulate different performance levels
        base_ctr = 0.02  # 2% base CTR
        base_cvr = 0.05  # 5% base CVR
        
        for i, variant in enumerate(variants):
            # Variant 1 (baseline): normal performance
            # Variant 2+: varying performance levels
            performance_multiplier = 1.0 + (i * 0.2)  # 0%, 20%, 40% better
            
            daily_impressions = random.randint(800, 1200)
            ctr = base_ctr * performance_multiplier * random.uniform(0.8, 1.2)
            cvr = base_cvr * performance_multiplier * random.uniform(0.8, 1.2)
            
            for day in range(days):
                impressions = random.randint(int(daily_impressions * 0.7), int(daily_impressions * 1.3))
                clicks = int(impressions * ctr * random.uniform(0.8, 1.2))
                conversions = int(clicks * cvr * random.uniform(0.8, 1.2))
                cost = clicks * 0.5  # $0.50 per click
                
                variant.impressions += impressions
                variant.clicks += clicks
                variant.conversions += conversions
                variant.cost += cost
        
        self.save_tests()
        return True