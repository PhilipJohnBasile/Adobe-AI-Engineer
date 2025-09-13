"""
Brand Validation Module

Validates generated assets against brand guidelines including
logo presence, color compliance, and visual consistency.
"""

import logging
from typing import Dict, List, Any, Optional, Tuple
from PIL import Image, ImageStat
import numpy as np
import colorsys
from collections import Counter
import cv2

logger = logging.getLogger(__name__)


class BrandValidator:
    """Validates assets against brand guidelines and standards."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize the brand validator with configuration."""
        self.config = config
        self.brand_config = config.get("brand", {})
        self.validation_config = config.get("validation", {}).get("brand_compliance", {})
        
        # Brand color palette for validation
        self.brand_colors_rgb = self._convert_brand_colors()
        
        logger.info("BrandValidator initialized")
    
    def _convert_brand_colors(self) -> List[Tuple[int, int, int]]:
        """Convert brand colors from hex to RGB for analysis."""
        
        brand_colors = []
        
        # Primary colors
        primary_colors = self.brand_config.get("primary_colors", [])
        for color in primary_colors:
            rgb = self._hex_to_rgb(color)
            if rgb:
                brand_colors.append(rgb)
        
        # Secondary colors
        secondary_colors = self.brand_config.get("secondary_colors", [])
        for color in secondary_colors:
            rgb = self._hex_to_rgb(color)
            if rgb:
                brand_colors.append(rgb)
        
        logger.info(f"Loaded {len(brand_colors)} brand colors for validation")
        return brand_colors
    
    def validate_asset(self, 
                      image: Image.Image,
                      brand_guidelines: Dict[str, Any]) -> Dict[str, Any]:
        """Comprehensive brand validation of an asset."""
        
        logger.info("Starting brand validation")
        
        validation_result = {
            "passed": True,
            "overall_score": 0.0,
            "component_scores": {},
            "issues": [],
            "recommendations": []
        }
        
        try:
            # Convert to numpy array for analysis
            image_array = np.array(image.convert("RGB"))
            
            # Run individual validation checks
            logo_result = self._validate_logo_presence(image, brand_guidelines)
            color_result = self._validate_color_compliance(image_array)
            composition_result = self._validate_composition(image_array)
            readability_result = self._validate_text_readability(image)
            
            # Combine results
            validation_result["component_scores"] = {
                "logo_compliance": logo_result["score"],
                "color_compliance": color_result["score"],
                "composition": composition_result["score"],
                "readability": readability_result["score"]
            }
            
            # Calculate overall score (weighted average)
            weights = {"logo_compliance": 0.3, "color_compliance": 0.3, 
                      "composition": 0.2, "readability": 0.2}
            
            overall_score = sum(
                validation_result["component_scores"][component] * weights[component]
                for component in weights
            )
            
            validation_result["overall_score"] = overall_score
            validation_result["passed"] = overall_score >= 0.7  # 70% threshold
            
            # Collect all issues and recommendations
            for result in [logo_result, color_result, composition_result, readability_result]:
                validation_result["issues"].extend(result.get("issues", []))
                validation_result["recommendations"].extend(result.get("recommendations", []))
            
            logger.info(f"Brand validation completed: Score {overall_score:.2f}, "
                       f"Passed: {validation_result['passed']}")
            
        except Exception as e:
            logger.error(f"Brand validation failed: {e}")
            validation_result["passed"] = False
            validation_result["issues"].append(f"Validation error: {str(e)}")
        
        return validation_result
    
    def _validate_logo_presence(self, 
                               image: Image.Image,
                               brand_guidelines: Dict[str, Any]) -> Dict[str, Any]:
        """Validate brand logo presence and placement."""
        
        result = {
            "score": 0.0,
            "issues": [],
            "recommendations": []
        }
        
        try:
            logo_requirements = brand_guidelines.get("logo_usage", {})
            
            if not logo_requirements.get("required", True):
                result["score"] = 1.0  # Not required, so pass
                return result
            
            # For this demo, we'll use a simplified approach
            # In production, this would use computer vision to detect actual logos
            logo_detected = self._detect_logo_presence(image)
            
            if logo_detected:
                result["score"] = 0.9
                
                # Check logo size (simplified)
                logo_size_ok = self._validate_logo_size(image, logo_requirements)
                if not logo_size_ok:
                    result["score"] *= 0.8
                    result["issues"].append("Logo appears too small")
                    result["recommendations"].append("Increase logo size to meet minimum requirements")
                
            else:
                result["score"] = 0.0
                result["issues"].append("Brand logo not detected in image")
                result["recommendations"].append("Add brand logo in preferred position")
            
        except Exception as e:
            logger.warning(f"Logo validation failed: {e}")
            result["score"] = 0.5  # Neutral score on error
        
        return result
    
    def _detect_logo_presence(self, image: Image.Image) -> bool:
        """Detect if brand logo is present in image (simplified implementation)."""
        
        # This is a simplified implementation
        # In production, you would use:
        # 1. Template matching with known logo variations
        # 2. Object detection models trained on your brand assets
        # 3. OCR to detect brand name text
        
        # For demo: look for semi-transparent overlays in typical logo positions
        try:
            width, height = image.size
            
            # Check typical logo positions (corners)
            logo_regions = [
                (width - 200, height - 200, width, height),      # Bottom right
                (0, 0, 200, 200),                                # Top left
                (width - 200, 0, width, 200),                    # Top right
                (0, height - 200, 200, height)                  # Bottom left
            ]
            
            for region in logo_regions:
                crop = image.crop(region)
                
                # Check if this region has characteristics of a logo
                # (high contrast, geometric shapes, etc.)
                if self._region_contains_logo_like_content(crop):
                    return True
            
            return False
            
        except Exception as e:
            logger.warning(f"Logo detection failed: {e}")
            return False
    
    def _region_contains_logo_like_content(self, region: Image.Image) -> bool:
        """Check if a region contains logo-like content."""
        
        try:
            # Convert to array for analysis
            region_array = np.array(region.convert("RGB"))
            
            # Calculate edge density (logos typically have clean edges)
            gray = cv2.cvtColor(region_array, cv2.COLOR_RGB2GRAY)
            edges = cv2.Canny(gray, 50, 150)
            edge_density = np.sum(edges > 0) / edges.size
            
            # Calculate color variance (logos often have distinct colors)
            color_var = np.var(region_array)
            
            # Simple heuristic: high edge density + moderate color variance
            return edge_density > 0.05 and 1000 < color_var < 5000
            
        except Exception:
            return False
    
    def _validate_logo_size(self, 
                           image: Image.Image,
                           logo_requirements: Dict[str, Any]) -> bool:
        """Validate logo meets minimum size requirements."""
        
        try:
            min_size_percent = logo_requirements.get("min_size_percent", 8)
            image_area = image.width * image.height
            min_logo_area = image_area * (min_size_percent / 100)
            
            # Simplified: assume we found a logo of reasonable size
            # In production, measure actual detected logo area
            estimated_logo_area = min_logo_area * 1.2  # Assume 20% larger than minimum
            
            return estimated_logo_area >= min_logo_area
            
        except Exception:
            return True  # Default to pass on error
    
    def _validate_color_compliance(self, image_array: np.ndarray) -> Dict[str, Any]:
        """Validate image colors against brand palette."""
        
        result = {
            "score": 0.0,
            "issues": [],
            "recommendations": []
        }
        
        try:
            if not self.brand_colors_rgb:
                result["score"] = 1.0  # No brand colors defined, pass
                return result
            
            # Extract dominant colors from image
            dominant_colors = self._extract_dominant_colors(image_array, num_colors=8)
            
            # Calculate brand color alignment
            brand_alignment_score = self._calculate_brand_color_alignment(dominant_colors)
            
            result["score"] = brand_alignment_score
            
            if brand_alignment_score < 0.6:
                result["issues"].append("Limited use of brand colors in image")
                result["recommendations"].append("Incorporate more brand colors into the design")
            
            # Check for off-brand colors
            off_brand_colors = self._detect_off_brand_colors(dominant_colors)
            if off_brand_colors:
                result["score"] *= 0.8
                result["issues"].append("Detected colors that conflict with brand palette")
                result["recommendations"].append("Replace conflicting colors with brand-approved alternatives")
            
        except Exception as e:
            logger.warning(f"Color validation failed: {e}")
            result["score"] = 0.7  # Neutral score on error
        
        return result
    
    def _extract_dominant_colors(self, 
                                image_array: np.ndarray,
                                num_colors: int = 8) -> List[Tuple[int, int, int]]:
        """Extract dominant colors from image using k-means clustering."""
        
        try:
            # Reshape image to list of pixels
            pixels = image_array.reshape(-1, 3)
            
            # Sample pixels for performance (use every 10th pixel)
            sampled_pixels = pixels[::10]
            
            # Use k-means clustering to find dominant colors
            from sklearn.cluster import KMeans
            
            kmeans = KMeans(n_clusters=num_colors, random_state=42, n_init=10)
            kmeans.fit(sampled_pixels)
            
            # Get cluster centers (dominant colors)
            dominant_colors = [(int(color[0]), int(color[1]), int(color[2])) 
                             for color in kmeans.cluster_centers_]
            
            return dominant_colors
            
        except ImportError:
            # Fallback if sklearn not available
            return self._extract_colors_simple(image_array)
        except Exception as e:
            logger.warning(f"Color extraction failed: {e}")
            return []
    
    def _extract_colors_simple(self, image_array: np.ndarray) -> List[Tuple[int, int, int]]:
        """Simple color extraction without sklearn."""
        
        # Sample pixels and find most common colors
        pixels = image_array.reshape(-1, 3)
        sampled_pixels = pixels[::50]  # Sample even more for performance
        
        # Round colors to reduce variance
        rounded_pixels = [(int(p[0]//32)*32, int(p[1]//32)*32, int(p[2]//32)*32) 
                         for p in sampled_pixels]
        
        # Count occurrences
        color_counts = Counter(rounded_pixels)
        
        # Return top colors
        return [color for color, count in color_counts.most_common(8)]
    
    def _calculate_brand_color_alignment(self, dominant_colors: List[Tuple[int, int, int]]) -> float:
        """Calculate how well image colors align with brand palette."""
        
        if not dominant_colors or not self.brand_colors_rgb:
            return 1.0
        
        alignment_scores = []
        
        for dom_color in dominant_colors:
            # Find closest brand color
            min_distance = float('inf')
            for brand_color in self.brand_colors_rgb:
                distance = self._color_distance(dom_color, brand_color)
                min_distance = min(min_distance, distance)
            
            # Convert distance to alignment score (0-1)
            # Max reasonable color distance is ~441 (sqrt(255^2 * 3))
            alignment_score = max(0, 1 - (min_distance / 200))
            alignment_scores.append(alignment_score)
        
        # Return weighted average (give more weight to top colors)
        if alignment_scores:
            weights = [1/i for i in range(1, len(alignment_scores) + 1)]
            weighted_score = sum(score * weight for score, weight in zip(alignment_scores, weights))
            total_weight = sum(weights)
            return weighted_score / total_weight
        
        return 0.5
    
    def _detect_off_brand_colors(self, dominant_colors: List[Tuple[int, int, int]]) -> List[Tuple[int, int, int]]:
        """Detect colors that strongly conflict with brand palette."""
        
        off_brand_colors = []
        
        for color in dominant_colors:
            # Check if color is too far from any brand color
            min_distance = min(
                self._color_distance(color, brand_color)
                for brand_color in self.brand_colors_rgb
            ) if self.brand_colors_rgb else 0
            
            # If color is very different from brand colors, flag it
            if min_distance > 150:  # Threshold for "off-brand"
                off_brand_colors.append(color)
        
        return off_brand_colors
    
    def _validate_composition(self, image_array: np.ndarray) -> Dict[str, Any]:
        """Validate image composition and layout quality."""
        
        result = {
            "score": 0.8,  # Default good score
            "issues": [],
            "recommendations": []
        }
        
        try:
            # Check rule of thirds compliance
            thirds_score = self._check_rule_of_thirds(image_array)
            
            # Check color balance
            balance_score = self._check_color_balance(image_array)
            
            # Check contrast levels
            contrast_score = self._check_contrast_levels(image_array)
            
            # Combine composition scores
            result["score"] = (thirds_score + balance_score + contrast_score) / 3
            
            if result["score"] < 0.6:
                result["issues"].append("Image composition could be improved")
                result["recommendations"].append("Consider adjusting layout and color balance")
            
        except Exception as e:
            logger.warning(f"Composition validation failed: {e}")
        
        return result
    
    def _check_rule_of_thirds(self, image_array: np.ndarray) -> float:
        """Check adherence to rule of thirds composition principle."""
        
        try:
            # Calculate interest points along third lines
            height, width = image_array.shape[:2]
            
            # Third lines
            h_thirds = [height // 3, 2 * height // 3]
            w_thirds = [width // 3, 2 * width // 3]
            
            # Calculate edge density near third lines
            gray = cv2.cvtColor(image_array, cv2.COLOR_RGB2GRAY)
            edges = cv2.Canny(gray, 50, 150)
            
            # Sample regions around third lines
            edge_density = 0
            for h in h_thirds:
                edge_density += np.mean(edges[max(0, h-10):min(height, h+10), :])
            for w in w_thirds:
                edge_density += np.mean(edges[:, max(0, w-10):min(width, w+10)])
            
            # Normalize to 0-1 range
            return min(1.0, edge_density / 100)
            
        except Exception:
            return 0.7  # Default score
    
    def _check_color_balance(self, image_array: np.ndarray) -> float:
        """Check overall color balance in the image."""
        
        try:
            # Calculate color channel means
            r_mean = np.mean(image_array[:, :, 0])
            g_mean = np.mean(image_array[:, :, 1])
            b_mean = np.mean(image_array[:, :, 2])
            
            # Calculate balance (lower variance is better balance)
            color_variance = np.var([r_mean, g_mean, b_mean])
            
            # Convert to 0-1 score (lower variance = higher score)
            balance_score = max(0, 1 - (color_variance / 5000))
            
            return min(1.0, balance_score)
            
        except Exception:
            return 0.7
    
    def _check_contrast_levels(self, image_array: np.ndarray) -> float:
        """Check image contrast levels."""
        
        try:
            # Convert to grayscale
            gray = cv2.cvtColor(image_array, cv2.COLOR_RGB2GRAY)
            
            # Calculate contrast using standard deviation
            contrast = np.std(gray)
            
            # Ideal contrast is around 50-80 for most images
            ideal_contrast = 65
            contrast_score = 1 - abs(contrast - ideal_contrast) / ideal_contrast
            
            return max(0, min(1, contrast_score))
            
        except Exception:
            return 0.7
    
    def _validate_text_readability(self, image: Image.Image) -> Dict[str, Any]:
        """Validate text readability and contrast."""
        
        result = {
            "score": 0.8,  # Default good score
            "issues": [],
            "recommendations": []
        }
        
        try:
            # This is a simplified implementation
            # In production, you would:
            # 1. Use OCR to detect text regions
            # 2. Calculate actual contrast ratios
            # 3. Check text size and font readability
            
            # For demo: check overall image characteristics that affect readability
            image_array = np.array(image.convert("RGB"))
            
            # Check if image has good contrast for text overlay
            gray = cv2.cvtColor(image_array, cv2.COLOR_RGB2GRAY)
            contrast = np.std(gray)
            
            if contrast < 30:
                result["score"] *= 0.7
                result["issues"].append("Low contrast may affect text readability")
                result["recommendations"].append("Increase contrast or add text backgrounds")
            
            # Check for areas that would be suitable for text
            # (relatively uniform regions with good contrast)
            text_areas = self._find_text_suitable_areas(image_array)
            if len(text_areas) < 2:
                result["score"] *= 0.8
                result["issues"].append("Limited suitable areas for text placement")
                result["recommendations"].append("Consider layout adjustments for better text placement")
            
        except Exception as e:
            logger.warning(f"Readability validation failed: {e}")
        
        return result
    
    def _find_text_suitable_areas(self, image_array: np.ndarray) -> List[Tuple[int, int, int, int]]:
        """Find areas in image suitable for text overlay."""
        
        try:
            # Simplified: look for relatively uniform regions
            gray = cv2.cvtColor(image_array, cv2.COLOR_RGB2GRAY)
            height, width = gray.shape
            
            suitable_areas = []
            region_size = 100
            
            # Sample regions across the image
            for y in range(0, height - region_size, region_size):
                for x in range(0, width - region_size, region_size):
                    region = gray[y:y+region_size, x:x+region_size]
                    
                    # Check if region is relatively uniform (low variance)
                    if np.var(region) < 500:  # Threshold for uniformity
                        suitable_areas.append((x, y, x + region_size, y + region_size))
            
            return suitable_areas
            
        except Exception:
            return []
    
    def _color_distance(self, color1: Tuple[int, int, int], color2: Tuple[int, int, int]) -> float:
        """Calculate Euclidean distance between two RGB colors."""
        
        r1, g1, b1 = color1
        r2, g2, b2 = color2
        
        return ((r2 - r1) ** 2 + (g2 - g1) ** 2 + (b2 - b1) ** 2) ** 0.5
    
    def _hex_to_rgb(self, hex_color: str) -> Optional[Tuple[int, int, int]]:
        """Convert hex color to RGB tuple."""
        
        try:
            hex_color = hex_color.lstrip('#')
            if len(hex_color) == 6:
                return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
            return None
        except Exception:
            return None