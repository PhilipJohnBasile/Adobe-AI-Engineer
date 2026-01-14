#!/usr/bin/env python3
"""
Enhanced Diversity Tracker for Task 3
Addresses the missing "diversity" aspect of variant tracking requirement
"""

import asyncio
import json
import hashlib
from datetime import datetime
from typing import Dict, List, Any, Tuple
from pathlib import Path
from dataclasses import dataclass, field
import logging
from PIL import Image
import numpy as np

@dataclass
class DiversityMetrics:
    """Comprehensive diversity analysis results"""
    total_variants: int = 0
    unique_variants: int = 0
    duplicate_variants: int = 0
    
    # Visual diversity
    color_diversity_score: float = 0.0
    composition_diversity_score: float = 0.0
    content_diversity_score: float = 0.0
    
    # Format diversity
    format_distribution: Dict[str, int] = field(default_factory=dict)
    resolution_distribution: Dict[str, int] = field(default_factory=dict)
    aspect_ratio_distribution: Dict[str, int] = field(default_factory=dict)
    
    # Quality diversity
    quality_distribution: Dict[str, int] = field(default_factory=dict)  # high, medium, low
    
    # Overall diversity index (0-1, higher = more diverse)
    overall_diversity_index: float = 0.0
    
    # Diversity recommendations
    diversity_gaps: List[str] = field(default_factory=list)
    improvement_suggestions: List[str] = field(default_factory=list)

class EnhancedDiversityTracker:
    """Enhanced diversity tracker that actually analyzes variant diversity"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
    async def analyze_campaign_diversity(self, campaign_id: str, output_dir: Path) -> DiversityMetrics:
        """Analyze actual diversity of creative variants for a campaign"""
        
        self.logger.info(f"🎨 Analyzing diversity for campaign: {campaign_id}")
        
        # Find all variant files
        campaign_path = output_dir / campaign_id
        if not campaign_path.exists():
            return DiversityMetrics()
        
        variant_files = list(campaign_path.rglob("*"))
        variant_files = [f for f in variant_files if f.is_file() and f.suffix.lower() in ['.jpg', '.jpeg', '.png', '.webp']]
        
        if not variant_files:
            return DiversityMetrics()
        
        metrics = DiversityMetrics()
        metrics.total_variants = len(variant_files)
        
        # 1. Analyze file-level diversity
        await self._analyze_file_diversity(variant_files, metrics)
        
        # 2. Analyze visual diversity (if images can be processed)
        await self._analyze_visual_diversity(variant_files, metrics)
        
        # 3. Calculate overall diversity index
        metrics.overall_diversity_index = self._calculate_diversity_index(metrics)
        
        # 4. Generate recommendations
        await self._generate_diversity_recommendations(metrics)
        
        self.logger.info(f"✅ Diversity analysis complete: {metrics.overall_diversity_index:.2f} diversity index")
        
        return metrics
    
    async def _analyze_file_diversity(self, variant_files: List[Path], metrics: DiversityMetrics):
        """Analyze file-level diversity (formats, sizes, duplicates)"""
        
        file_hashes = set()
        
        for file_path in variant_files:
            try:
                # Check for duplicates using file hash
                file_hash = self._calculate_file_hash(file_path)
                file_hashes.add(file_hash)
                
                # Format distribution
                format_key = file_path.suffix.lower().replace('.', '')
                metrics.format_distribution[format_key] = metrics.format_distribution.get(format_key, 0) + 1
                
                # Try to get image properties
                try:
                    with Image.open(file_path) as img:
                        # Resolution distribution
                        resolution = f"{img.size[0]}x{img.size[1]}"
                        metrics.resolution_distribution[resolution] = metrics.resolution_distribution.get(resolution, 0) + 1
                        
                        # Aspect ratio distribution
                        width, height = img.size
                        aspect_ratio = self._classify_aspect_ratio(width, height)
                        metrics.aspect_ratio_distribution[aspect_ratio] = metrics.aspect_ratio_distribution.get(aspect_ratio, 0) + 1
                        
                except Exception as e:
                    self.logger.warning(f"Could not analyze image {file_path}: {e}")
                
            except Exception as e:
                self.logger.warning(f"Error analyzing file {file_path}: {e}")
        
        metrics.unique_variants = len(file_hashes)
        metrics.duplicate_variants = metrics.total_variants - metrics.unique_variants
    
    async def _analyze_visual_diversity(self, variant_files: List[Path], metrics: DiversityMetrics):
        """Analyze visual diversity of variants"""
        
        color_features = []
        
        for file_path in variant_files:
            try:
                with Image.open(file_path) as img:
                    # Convert to RGB if needed
                    if img.mode != 'RGB':
                        img = img.convert('RGB')
                    
                    # Simple color analysis - get dominant colors
                    img_array = np.array(img.resize((50, 50)))  # Resize for performance
                    
                    # Calculate average color
                    avg_color = np.mean(img_array.reshape(-1, 3), axis=0)
                    color_features.append(avg_color)
                    
            except Exception as e:
                self.logger.warning(f"Could not analyze visual features of {file_path}: {e}")
        
        if color_features:
            # Calculate color diversity using variance
            color_matrix = np.array(color_features)
            color_variance = np.var(color_matrix, axis=0)
            metrics.color_diversity_score = np.mean(color_variance) / 255.0  # Normalize to 0-1
            
            # Simple composition diversity (based on variance in color distribution)
            metrics.composition_diversity_score = min(1.0, np.std(color_matrix.flatten()) / 100.0)
            
            # Content diversity approximation
            metrics.content_diversity_score = min(1.0, len(color_features) / 10.0)  # More variants = more potential content diversity
    
    def _calculate_diversity_index(self, metrics: DiversityMetrics) -> float:
        """Calculate overall diversity index (0-1)"""
        
        components = []
        
        # Format diversity (0-1)
        format_count = len(metrics.format_distribution)
        format_diversity = min(1.0, format_count / 3.0)  # Assume 3 formats is maximum diversity
        components.append(format_diversity * 0.15)
        
        # Resolution diversity (0-1) 
        resolution_count = len(metrics.resolution_distribution)
        resolution_diversity = min(1.0, resolution_count / 5.0)  # 5 different resolutions is good diversity
        components.append(resolution_diversity * 0.15)
        
        # Aspect ratio diversity (0-1)
        aspect_count = len(metrics.aspect_ratio_distribution)
        aspect_diversity = min(1.0, aspect_count / 3.0)  # 3 aspect ratios (square, portrait, landscape)
        components.append(aspect_diversity * 0.20)
        
        # Duplicate penalty
        if metrics.total_variants > 0:
            uniqueness = metrics.unique_variants / metrics.total_variants
        else:
            uniqueness = 0.0
        components.append(uniqueness * 0.25)
        
        # Visual diversity
        components.append(metrics.color_diversity_score * 0.15)
        components.append(metrics.composition_diversity_score * 0.10)
        
        return sum(components)
    
    async def _generate_diversity_recommendations(self, metrics: DiversityMetrics):
        """Generate recommendations to improve diversity"""
        
        # Check for diversity gaps
        if metrics.duplicate_variants > 0:
            metrics.diversity_gaps.append(f"{metrics.duplicate_variants} duplicate variants detected")
            metrics.improvement_suggestions.append("Remove duplicate variants to improve uniqueness")
        
        if len(metrics.format_distribution) < 2:
            metrics.diversity_gaps.append("Limited format diversity")
            metrics.improvement_suggestions.append("Generate variants in multiple formats (JPG, PNG, WebP)")
        
        if len(metrics.aspect_ratio_distribution) < 2:
            metrics.diversity_gaps.append("Limited aspect ratio diversity")
            metrics.improvement_suggestions.append("Include square (1:1), portrait (9:16), and landscape (16:9) variants")
        
        if metrics.color_diversity_score < 0.3:
            metrics.diversity_gaps.append("Low color diversity")
            metrics.improvement_suggestions.append("Generate variants with more varied color schemes and themes")
        
        if metrics.overall_diversity_index < 0.5:
            metrics.diversity_gaps.append("Overall low diversity score")
            metrics.improvement_suggestions.append("Review generation parameters to increase variant diversity")
    
    def _calculate_file_hash(self, file_path: Path) -> str:
        """Calculate file hash for duplicate detection"""
        hasher = hashlib.md5()
        try:
            with open(file_path, 'rb') as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hasher.update(chunk)
            return hasher.hexdigest()
        except (OSError, IOError):
            return f"error_{file_path.name}_{datetime.now().timestamp()}"
    
    def _classify_aspect_ratio(self, width: int, height: int) -> str:
        """Classify aspect ratio into standard categories"""
        ratio = width / height
        
        if 0.9 <= ratio <= 1.1:
            return "square"
        elif ratio < 0.9:
            return "portrait"
        else:
            return "landscape"

# Integration with Task3Agent
class DiversityEnhancedAgent:
    """Enhanced Task 3 Agent with proper diversity tracking"""
    
    def __init__(self):
        self.diversity_tracker = EnhancedDiversityTracker()
        self.logger = logging.getLogger(__name__)
    
    async def track_creative_variants_with_diversity(self, campaign_id: str, output_dir: Path) -> Dict[str, Any]:
        """ENHANCED REQUIREMENT 3: Track count AND diversity of creative variants"""
        
        # Get basic count
        variant_files = list((output_dir / campaign_id).rglob("*"))
        variant_files = [f for f in variant_files if f.is_file() and f.suffix.lower() in ['.jpg', '.jpeg', '.png', '.webp']]
        
        basic_metrics = {
            "variant_count": len(variant_files),
            "last_updated": datetime.now().isoformat()
        }
        
        # Get diversity analysis
        diversity_metrics = await self.diversity_tracker.analyze_campaign_diversity(campaign_id, output_dir)
        
        # Combine metrics
        enhanced_metrics = {
            **basic_metrics,
            "diversity": {
                "overall_diversity_index": diversity_metrics.overall_diversity_index,
                "unique_variants": diversity_metrics.unique_variants,
                "duplicate_variants": diversity_metrics.duplicate_variants,
                "format_distribution": diversity_metrics.format_distribution,
                "aspect_ratio_distribution": diversity_metrics.aspect_ratio_distribution,
                "color_diversity_score": diversity_metrics.color_diversity_score,
                "diversity_gaps": diversity_metrics.diversity_gaps,
                "improvement_suggestions": diversity_metrics.improvement_suggestions
            }
        }
        
        # Flag diversity issues
        await self._flag_diversity_issues(campaign_id, diversity_metrics)
        
        return enhanced_metrics
    
    async def _flag_diversity_issues(self, campaign_id: str, metrics: DiversityMetrics):
        """Flag diversity-related issues"""
        
        if metrics.overall_diversity_index < 0.4:
            await self._create_diversity_alert(
                campaign_id,
                "low_diversity",
                f"Campaign {campaign_id} has low diversity (index: {metrics.overall_diversity_index:.2f})",
                "medium",
                metrics.diversity_gaps,
                metrics.improvement_suggestions
            )
        
        if metrics.duplicate_variants > metrics.total_variants * 0.3:  # More than 30% duplicates
            await self._create_diversity_alert(
                campaign_id,
                "high_duplicates",
                f"Campaign {campaign_id} has {metrics.duplicate_variants} duplicate variants",
                "high",
                ["High duplicate content reduces effective variant count"],
                ["Remove duplicate variants", "Review generation parameters for uniqueness"]
            )
    
    async def _create_diversity_alert(self, campaign_id: str, alert_type: str, message: str, 
                                    severity: str, gaps: List[str], suggestions: List[str]):
        """Create diversity-specific alert"""
        
        alert = {
            "id": f"{alert_type}_{campaign_id}_{int(time.time())}",
            "type": alert_type,
            "message": message,
            "severity": severity,
            "campaign_id": campaign_id,
            "timestamp": datetime.now().isoformat(),
            "diversity_gaps": gaps,
            "improvement_suggestions": suggestions
        }
        
        self.logger.warning(f"🎨 DIVERSITY ALERT [{severity.upper()}]: {message}")
        
        # Save alert
        alert_file = Path(f"logs/diversity_alert_{alert['id']}.json")
        with open(alert_file, 'w') as f:
            json.dump(alert, f, indent=2)

# Demo function
async def demo_enhanced_diversity_tracking():
    """Demonstrate enhanced diversity tracking"""
    
    print("🎨 Enhanced Diversity Tracking Demo")
    print("=" * 50)
    
    # Create sample variants with different characteristics
    output_dir = Path("output")
    campaign_id = "diversity_test_campaign"
    campaign_output = output_dir / campaign_id
    campaign_output.mkdir(parents=True, exist_ok=True)
    
    # Create sample variant files with different properties
    from PIL import Image
    
    # Different colors and aspect ratios
    variants = [
        {"name": "red_square.jpg", "color": (255, 0, 0), "size": (500, 500)},
        {"name": "blue_landscape.jpg", "color": (0, 0, 255), "size": (800, 450)},
        {"name": "green_portrait.png", "color": (0, 255, 0), "size": (450, 800)},
        {"name": "yellow_square.jpg", "color": (255, 255, 0), "size": (500, 500)},
        {"name": "duplicate_red.jpg", "color": (255, 0, 0), "size": (500, 500)},  # Duplicate
    ]
    
    for variant in variants:
        img = Image.new('RGB', variant["size"], variant["color"])
        img.save(campaign_output / variant["name"])
    
    print(f"✅ Created {len(variants)} test variants")
    
    # Analyze diversity
    tracker = EnhancedDiversityTracker()
    metrics = await tracker.analyze_campaign_diversity(campaign_id, output_dir)
    
    print(f"\n📊 Diversity Analysis Results:")
    print(f"Total Variants: {metrics.total_variants}")
    print(f"Unique Variants: {metrics.unique_variants}")
    print(f"Duplicate Variants: {metrics.duplicate_variants}")
    print(f"Overall Diversity Index: {metrics.overall_diversity_index:.2f}")
    print(f"Color Diversity Score: {metrics.color_diversity_score:.2f}")
    print(f"Format Distribution: {metrics.format_distribution}")
    print(f"Aspect Ratio Distribution: {metrics.aspect_ratio_distribution}")
    
    if metrics.diversity_gaps:
        print(f"\n🚨 Diversity Gaps Identified:")
        for gap in metrics.diversity_gaps:
            print(f"  • {gap}")
    
    if metrics.improvement_suggestions:
        print(f"\n💡 Improvement Suggestions:")
        for suggestion in metrics.improvement_suggestions:
            print(f"  • {suggestion}")
    
    # Clean up
    import shutil
    shutil.rmtree(campaign_output)
    
    print(f"\n✅ Enhanced diversity tracking demonstrated!")

if __name__ == "__main__":
    asyncio.run(demo_enhanced_diversity_tracking())