"""
Advanced Computer Vision & Brand Intelligence System
Sophisticated visual analysis for brand consistency, quality assessment, and asset optimization
"""

import cv2
import numpy as np
from PIL import Image, ImageEnhance, ImageFilter, ImageStat
import colorsys
from sklearn.cluster import KMeans
from sklearn.metrics.pairwise import cosine_similarity
import json
import os
from typing import Dict, List, Tuple, Any, Optional
from dataclasses import dataclass, asdict
from pathlib import Path
import logging
from datetime import datetime
import hashlib


@dataclass
class ColorPalette:
    """Brand color palette with analysis"""
    dominant_colors: List[Tuple[int, int, int]]
    color_percentages: List[float]
    hex_colors: List[str]
    color_harmony: str
    temperature: str  # warm, cool, neutral
    saturation_level: str  # high, medium, low
    brightness_level: str  # bright, medium, dark
    accessibility_score: float  # WCAG compliance for text overlay


@dataclass
class ImageQuality:
    """Comprehensive image quality assessment"""
    overall_score: float  # 0-100
    sharpness: float
    brightness: float
    contrast: float
    saturation: float
    noise_level: float
    compression_artifacts: float
    resolution_adequacy: float
    composition_score: float
    enhancement_recommendations: List[str]


@dataclass
class BrandConsistency:
    """Brand consistency analysis"""
    color_consistency: float  # 0-100
    style_consistency: float
    composition_consistency: float
    overall_brand_score: float
    violations: List[str]
    recommendations: List[str]


@dataclass
class VisualFeatures:
    """Extracted visual features for similarity analysis"""
    color_histogram: np.ndarray
    texture_features: np.ndarray
    edge_features: np.ndarray
    composition_features: Dict[str, float]
    feature_hash: str


class BrandIntelligenceEngine:
    """Advanced computer vision engine for brand intelligence"""
    
    def __init__(self, brand_assets_dir: str = "brand_assets"):
        self.brand_assets_dir = Path(brand_assets_dir)
        self.brand_assets_dir.mkdir(exist_ok=True)
        self.logger = logging.getLogger(__name__)
        
        # Brand learning storage
        self.brand_profile_path = self.brand_assets_dir / "brand_profile.json"
        self.brand_profile = self._load_brand_profile()
        
        # Quality standards
        self.quality_standards = {
            "min_resolution": (800, 600),
            "min_sharpness": 30.0,
            "min_contrast": 20.0,
            "max_noise": 15.0,
            "min_overall_score": 70.0
        }
    
    def _load_brand_profile(self) -> Dict[str, Any]:
        """Load existing brand profile or create new one"""
        if self.brand_profile_path.exists():
            with open(self.brand_profile_path, 'r') as f:
                return json.load(f)
        
        return {
            "brand_colors": [],
            "style_signatures": [],
            "composition_preferences": {},
            "quality_baselines": {},
            "learned_patterns": {},
            "last_updated": datetime.now().isoformat()
        }
    
    def _save_brand_profile(self):
        """Save brand profile to disk"""
        self.brand_profile["last_updated"] = datetime.now().isoformat()
        with open(self.brand_profile_path, 'w') as f:
            json.dump(self.brand_profile, f, indent=2)
    
    def extract_color_palette(self, image_path: str, n_colors: int = 8) -> ColorPalette:
        """Extract dominant color palette with advanced analysis"""
        try:
            # Load image
            image = cv2.imread(image_path)
            if image is None:
                raise ValueError(f"Could not load image: {image_path}")
            
            # Convert to RGB
            image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            
            # Reshape for clustering
            pixels = image_rgb.reshape(-1, 3)
            
            # Remove very dark/light pixels for better color extraction
            mask = np.all(pixels > 20, axis=1) & np.all(pixels < 235, axis=1)
            filtered_pixels = pixels[mask]
            
            if len(filtered_pixels) < 100:
                filtered_pixels = pixels  # Fallback to all pixels
            
            # K-means clustering for dominant colors
            kmeans = KMeans(n_clusters=min(n_colors, len(filtered_pixels)), random_state=42, n_init=10)
            kmeans.fit(filtered_pixels)
            
            colors = kmeans.cluster_centers_.astype(int)
            
            # Calculate color percentages
            labels = kmeans.labels_
            total_pixels = len(labels)
            percentages = []
            
            for i in range(len(colors)):
                count = np.sum(labels == i)
                percentages.append(count / total_pixels * 100)
            
            # Sort by percentage
            sorted_indices = np.argsort(percentages)[::-1]
            colors = colors[sorted_indices]
            percentages = [percentages[i] for i in sorted_indices]
            
            # Convert to hex
            hex_colors = [f"#{r:02x}{g:02x}{b:02x}" for r, g, b in colors]
            
            # Analyze color harmony
            harmony = self._analyze_color_harmony(colors)
            
            # Analyze temperature
            temperature = self._analyze_color_temperature(colors, percentages)
            
            # Analyze saturation and brightness
            saturation_level = self._analyze_saturation(colors, percentages)
            brightness_level = self._analyze_brightness(colors, percentages)
            
            # Calculate accessibility score
            accessibility_score = self._calculate_accessibility_score(colors)
            
            return ColorPalette(
                dominant_colors=[tuple(color) for color in colors],
                color_percentages=percentages,
                hex_colors=hex_colors,
                color_harmony=harmony,
                temperature=temperature,
                saturation_level=saturation_level,
                brightness_level=brightness_level,
                accessibility_score=accessibility_score
            )
            
        except Exception as e:
            self.logger.error(f"Error extracting color palette: {e}")
            # Return default palette
            return ColorPalette(
                dominant_colors=[(128, 128, 128)],
                color_percentages=[100.0],
                hex_colors=["#808080"],
                color_harmony="unknown",
                temperature="neutral",
                saturation_level="medium",
                brightness_level="medium",
                accessibility_score=50.0
            )
    
    def _analyze_color_harmony(self, colors: np.ndarray) -> str:
        """Analyze color harmony relationships"""
        if len(colors) < 2:
            return "monochromatic"
        
        # Convert to HSV for harmony analysis
        hsv_colors = []
        for color in colors:
            r, g, b = color / 255.0
            h, s, v = colorsys.rgb_to_hsv(r, g, b)
            hsv_colors.append((h * 360, s, v))
        
        hues = [h for h, s, v in hsv_colors]
        
        # Check for complementary (opposite hues)
        for i in range(len(hues)):
            for j in range(i + 1, len(hues)):
                hue_diff = abs(hues[i] - hues[j])
                if 160 <= hue_diff <= 200:
                    return "complementary"
        
        # Check for triadic (120 degrees apart)
        if len(hues) >= 3:
            for i in range(len(hues)):
                for j in range(i + 1, len(hues)):
                    for k in range(j + 1, len(hues)):
                        diff1 = abs(hues[i] - hues[j])
                        diff2 = abs(hues[j] - hues[k])
                        diff3 = abs(hues[k] - hues[i])
                        if all(100 <= diff <= 140 for diff in [diff1, diff2, diff3]):
                            return "triadic"
        
        # Check for analogous (adjacent hues)
        for i in range(len(hues)):
            for j in range(i + 1, len(hues)):
                hue_diff = abs(hues[i] - hues[j])
                if 15 <= hue_diff <= 45:
                    return "analogous"
        
        # Check for monochromatic (same hue, different saturation/value)
        hue_range = max(hues) - min(hues)
        if hue_range < 30:
            return "monochromatic"
        
        return "complex"
    
    def _analyze_color_temperature(self, colors: np.ndarray, percentages: List[float]) -> str:
        """Analyze overall color temperature"""
        warm_weight = 0
        cool_weight = 0
        
        for color, percentage in zip(colors, percentages):
            r, g, b = color
            
            # Warm colors: reds, oranges, yellows
            if r > g and r > b:  # More red
                warm_weight += percentage
            elif r > b and g > b:  # Yellow/orange tones
                warm_weight += percentage
            
            # Cool colors: blues, greens, purples
            elif b > r and b > g:  # More blue
                cool_weight += percentage
            elif g > r and g > b:  # More green
                cool_weight += percentage
        
        if warm_weight > cool_weight + 20:
            return "warm"
        elif cool_weight > warm_weight + 20:
            return "cool"
        else:
            return "neutral"
    
    def _analyze_saturation(self, colors: np.ndarray, percentages: List[float]) -> str:
        """Analyze overall saturation level"""
        total_saturation = 0
        
        for color, percentage in zip(colors, percentages):
            r, g, b = color / 255.0
            _, s, _ = colorsys.rgb_to_hsv(r, g, b)
            total_saturation += s * percentage
        
        avg_saturation = total_saturation / 100
        
        if avg_saturation > 0.7:
            return "high"
        elif avg_saturation > 0.3:
            return "medium"
        else:
            return "low"
    
    def _analyze_brightness(self, colors: np.ndarray, percentages: List[float]) -> str:
        """Analyze overall brightness level"""
        total_brightness = 0
        
        for color, percentage in zip(colors, percentages):
            # Calculate perceived brightness
            r, g, b = color
            brightness = (0.299 * r + 0.587 * g + 0.114 * b) / 255
            total_brightness += brightness * percentage
        
        avg_brightness = total_brightness / 100
        
        if avg_brightness > 0.7:
            return "bright"
        elif avg_brightness > 0.3:
            return "medium"
        else:
            return "dark"
    
    def _calculate_accessibility_score(self, colors: np.ndarray) -> float:
        """Calculate WCAG accessibility score for text overlay"""
        scores = []
        
        for i in range(len(colors)):
            for j in range(i + 1, len(colors)):
                # Calculate contrast ratio
                l1 = self._get_relative_luminance(colors[i])
                l2 = self._get_relative_luminance(colors[j])
                
                contrast_ratio = (max(l1, l2) + 0.05) / (min(l1, l2) + 0.05)
                
                # WCAG AA requires 4.5:1 for normal text, 3:1 for large text
                if contrast_ratio >= 4.5:
                    scores.append(100)
                elif contrast_ratio >= 3.0:
                    scores.append(75)
                elif contrast_ratio >= 2.0:
                    scores.append(50)
                else:
                    scores.append(25)
        
        return np.mean(scores) if scores else 50.0
    
    def _get_relative_luminance(self, color: np.ndarray) -> float:
        """Calculate relative luminance for accessibility"""
        r, g, b = color / 255.0
        
        # Convert to linear RGB
        def linearize(c):
            return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
        
        r_lin = linearize(r)
        g_lin = linearize(g)
        b_lin = linearize(b)
        
        return 0.2126 * r_lin + 0.7152 * g_lin + 0.0722 * b_lin
    
    def assess_image_quality(self, image_path: str) -> ImageQuality:
        """Comprehensive image quality assessment"""
        try:
            # Load image
            image = cv2.imread(image_path)
            if image is None:
                raise ValueError(f"Could not load image: {image_path}")
            
            pil_image = Image.open(image_path)
            
            # Basic metrics
            height, width = image.shape[:2]
            
            # 1. Sharpness (using Laplacian variance)
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            sharpness = cv2.Laplacian(gray, cv2.CV_64F).var()
            
            # 2. Brightness
            brightness = np.mean(gray)
            
            # 3. Contrast (standard deviation)
            contrast = np.std(gray)
            
            # 4. Saturation
            hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
            saturation = np.mean(hsv[:, :, 1])
            
            # 5. Noise level (using high-frequency content)
            noise_level = self._estimate_noise(gray)
            
            # 6. Compression artifacts
            compression_artifacts = self._detect_compression_artifacts(gray)
            
            # 7. Resolution adequacy
            min_res = self.quality_standards["min_resolution"]
            resolution_adequacy = min(width / min_res[0], height / min_res[1]) * 100
            resolution_adequacy = min(resolution_adequacy, 100)
            
            # 8. Composition score
            composition_score = self._analyze_composition(image, gray)
            
            # Normalize scores to 0-100
            sharpness_score = min(sharpness / 100 * 100, 100)
            brightness_score = 100 - abs(brightness - 127) / 127 * 100
            contrast_score = min(contrast / 50 * 100, 100)
            saturation_score = min(saturation / 127 * 100, 100)
            noise_score = max(0, 100 - noise_level)
            artifacts_score = max(0, 100 - compression_artifacts)
            
            # Overall score (weighted average)
            weights = {
                'sharpness': 0.20,
                'brightness': 0.15,
                'contrast': 0.15,
                'saturation': 0.10,
                'noise': 0.15,
                'artifacts': 0.10,
                'resolution': 0.10,
                'composition': 0.05
            }
            
            overall_score = (
                sharpness_score * weights['sharpness'] +
                brightness_score * weights['brightness'] +
                contrast_score * weights['contrast'] +
                saturation_score * weights['saturation'] +
                noise_score * weights['noise'] +
                artifacts_score * weights['artifacts'] +
                resolution_adequacy * weights['resolution'] +
                composition_score * weights['composition']
            )
            
            # Generate enhancement recommendations
            recommendations = []
            if sharpness_score < 70:
                recommendations.append("Increase sharpness - image appears soft or blurry")
            if brightness_score < 70:
                if brightness < 100:
                    recommendations.append("Increase brightness - image appears too dark")
                else:
                    recommendations.append("Decrease brightness - image appears overexposed")
            if contrast_score < 70:
                recommendations.append("Increase contrast - image lacks definition")
            if saturation_score < 50:
                recommendations.append("Increase saturation - colors appear washed out")
            if noise_score < 70:
                recommendations.append("Apply noise reduction - image has visible noise")
            if resolution_adequacy < 80:
                recommendations.append("Use higher resolution - current resolution may be insufficient")
            
            return ImageQuality(
                overall_score=overall_score,
                sharpness=sharpness_score,
                brightness=brightness_score,
                contrast=contrast_score,
                saturation=saturation_score,
                noise_level=noise_score,
                compression_artifacts=artifacts_score,
                resolution_adequacy=resolution_adequacy,
                composition_score=composition_score,
                enhancement_recommendations=recommendations
            )
            
        except Exception as e:
            self.logger.error(f"Error assessing image quality: {e}")
            return ImageQuality(
                overall_score=50.0,
                sharpness=50.0,
                brightness=50.0,
                contrast=50.0,
                saturation=50.0,
                noise_level=50.0,
                compression_artifacts=50.0,
                resolution_adequacy=50.0,
                composition_score=50.0,
                enhancement_recommendations=["Unable to analyze image quality"]
            )
    
    def _estimate_noise(self, gray_image: np.ndarray) -> float:
        """Estimate noise level in image"""
        # Use high-pass filter to isolate noise
        kernel = np.array([[-1, -1, -1], [-1, 8, -1], [-1, -1, -1]])
        filtered = cv2.filter2D(gray_image, cv2.CV_64F, kernel)
        noise_level = np.std(filtered)
        return min(noise_level / 5, 100)  # Normalize to 0-100
    
    def _detect_compression_artifacts(self, gray_image: np.ndarray) -> float:
        """Detect JPEG compression artifacts"""
        # Detect block artifacts (8x8 patterns typical of JPEG)
        h, w = gray_image.shape
        artifact_score = 0
        
        # Check for blocking artifacts
        for i in range(8, h - 8, 8):
            for j in range(8, w - 8, 8):
                # Check discontinuity at block boundaries
                horizontal_diff = abs(int(gray_image[i, j]) - int(gray_image[i-1, j]))
                vertical_diff = abs(int(gray_image[i, j]) - int(gray_image[i, j-1]))
                artifact_score += horizontal_diff + vertical_diff
        
        # Normalize
        num_blocks = ((h // 8) - 1) * ((w // 8) - 1)
        if num_blocks > 0:
            artifact_score = artifact_score / num_blocks / 10
        
        return min(artifact_score, 100)
    
    def _analyze_composition(self, image: np.ndarray, gray: np.ndarray) -> float:
        """Analyze image composition quality"""
        h, w = gray.shape
        
        # Rule of thirds
        thirds_score = self._check_rule_of_thirds(gray)
        
        # Edge distribution
        edges = cv2.Canny(gray, 50, 150)
        edge_score = self._analyze_edge_distribution(edges)
        
        # Symmetry
        symmetry_score = self._check_symmetry(gray)
        
        # Focus distribution
        focus_score = self._analyze_focus_distribution(gray)
        
        # Combine scores
        composition_score = (thirds_score + edge_score + symmetry_score + focus_score) / 4
        return composition_score
    
    def _check_rule_of_thirds(self, gray: np.ndarray) -> float:
        """Check adherence to rule of thirds"""
        h, w = gray.shape
        
        # Define thirds lines
        h_lines = [h // 3, 2 * h // 3]
        v_lines = [w // 3, 2 * w // 3]
        
        # Find strong edges near thirds lines
        edges = cv2.Canny(gray, 50, 150)
        score = 0
        
        for line in h_lines:
            region = edges[max(0, line-10):min(h, line+10), :]
            score += np.sum(region) / (20 * w)
        
        for line in v_lines:
            region = edges[:, max(0, line-10):min(w, line+10)]
            score += np.sum(region) / (20 * h)
        
        return min(score / 4 * 100, 100)
    
    def _analyze_edge_distribution(self, edges: np.ndarray) -> float:
        """Analyze edge distribution for composition"""
        h, w = edges.shape
        
        # Divide into 9 regions (3x3 grid)
        regions = []
        for i in range(3):
            for j in range(3):
                region = edges[i*h//3:(i+1)*h//3, j*w//3:(j+1)*w//3]
                regions.append(np.sum(region))
        
        # Good composition has balanced edge distribution
        edge_variance = np.var(regions)
        max_variance = np.var([np.sum(edges), 0, 0, 0, 0, 0, 0, 0, 0])
        
        # Lower variance = better distribution
        distribution_score = max(0, 100 - (edge_variance / max_variance * 100))
        return distribution_score
    
    def _check_symmetry(self, gray: np.ndarray) -> float:
        """Check for symmetry in composition"""
        h, w = gray.shape
        
        # Horizontal symmetry
        top_half = gray[:h//2, :]
        bottom_half = np.flipud(gray[h//2:, :])
        
        # Ensure same dimensions
        min_h = min(top_half.shape[0], bottom_half.shape[0])
        top_half = top_half[:min_h, :]
        bottom_half = bottom_half[:min_h, :]
        
        h_symmetry = 100 - np.mean(np.abs(top_half.astype(float) - bottom_half.astype(float)))
        
        # Vertical symmetry
        left_half = gray[:, :w//2]
        right_half = np.fliplr(gray[:, w//2:])
        
        # Ensure same dimensions
        min_w = min(left_half.shape[1], right_half.shape[1])
        left_half = left_half[:, :min_w]
        right_half = right_half[:, :min_w]
        
        v_symmetry = 100 - np.mean(np.abs(left_half.astype(float) - right_half.astype(float)))
        
        return max(h_symmetry, v_symmetry)
    
    def _analyze_focus_distribution(self, gray: np.ndarray) -> float:
        """Analyze focus distribution (depth of field)"""
        # Use gradient magnitude to estimate focus
        grad_x = cv2.Sobel(gray, cv2.CV_64F, 1, 0, ksize=3)
        grad_y = cv2.Sobel(gray, cv2.CV_64F, 0, 1, ksize=3)
        gradient_magnitude = np.sqrt(grad_x**2 + grad_y**2)
        
        # Good focus has high gradients in important areas
        h, w = gray.shape
        center_region = gradient_magnitude[h//4:3*h//4, w//4:3*w//4]
        center_focus = np.mean(center_region)
        
        edge_regions = [
            gradient_magnitude[:h//4, :],  # top
            gradient_magnitude[3*h//4:, :],  # bottom
            gradient_magnitude[:, :w//4],  # left
            gradient_magnitude[:, 3*w//4:]  # right
        ]
        edge_focus = np.mean([np.mean(region) for region in edge_regions if region.size > 0])
        
        # Good composition has higher focus in center than edges
        if edge_focus > 0:
            focus_ratio = center_focus / edge_focus
            focus_score = min(focus_ratio * 25, 100)
        else:
            focus_score = 50
        
        return focus_score
    
    def extract_visual_features(self, image_path: str) -> VisualFeatures:
        """Extract comprehensive visual features for similarity analysis"""
        try:
            image = cv2.imread(image_path)
            if image is None:
                raise ValueError(f"Could not load image: {image_path}")
            
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            
            # 1. Color histogram features
            hist_b = cv2.calcHist([image], [0], None, [32], [0, 256])
            hist_g = cv2.calcHist([image], [1], None, [32], [0, 256])
            hist_r = cv2.calcHist([image], [2], None, [32], [0, 256])
            color_histogram = np.concatenate([hist_b.flatten(), hist_g.flatten(), hist_r.flatten()])
            color_histogram = color_histogram / np.sum(color_histogram)  # Normalize
            
            # 2. Texture features (using Local Binary Patterns)
            texture_features = self._extract_lbp_features(gray)
            
            # 3. Edge features
            edges = cv2.Canny(gray, 50, 150)
            edge_features = self._extract_edge_features(edges)
            
            # 4. Composition features
            composition_features = {
                'aspect_ratio': image.shape[1] / image.shape[0],
                'center_brightness': np.mean(gray[gray.shape[0]//4:3*gray.shape[0]//4, 
                                                  gray.shape[1]//4:3*gray.shape[1]//4]),
                'edge_density': np.sum(edges) / edges.size,
                'brightness_variance': np.var(gray),
                'dominant_orientation': self._get_dominant_orientation(edges)
            }
            
            # Create feature hash for quick comparison
            all_features = np.concatenate([
                color_histogram, 
                texture_features, 
                edge_features,
                list(composition_features.values())
            ])
            feature_hash = hashlib.md5(all_features.tobytes()).hexdigest()
            
            return VisualFeatures(
                color_histogram=color_histogram,
                texture_features=texture_features,
                edge_features=edge_features,
                composition_features=composition_features,
                feature_hash=feature_hash
            )
            
        except Exception as e:
            self.logger.error(f"Error extracting visual features: {e}")
            # Return default features
            return VisualFeatures(
                color_histogram=np.zeros(96),
                texture_features=np.zeros(256),
                edge_features=np.zeros(10),
                composition_features={},
                feature_hash="error"
            )
    
    def _extract_lbp_features(self, gray: np.ndarray) -> np.ndarray:
        """Extract Local Binary Pattern features for texture analysis"""
        # Simple LBP implementation
        h, w = gray.shape
        lbp = np.zeros_like(gray)
        
        for i in range(1, h-1):
            for j in range(1, w-1):
                center = gray[i, j]
                binary_string = ''
                
                # 8 neighbors
                neighbors = [
                    gray[i-1, j-1], gray[i-1, j], gray[i-1, j+1],
                    gray[i, j+1], gray[i+1, j+1], gray[i+1, j],
                    gray[i+1, j-1], gray[i, j-1]
                ]
                
                for neighbor in neighbors:
                    binary_string += '1' if neighbor >= center else '0'
                
                lbp[i, j] = int(binary_string, 2)
        
        # Create histogram of LBP patterns
        hist, _ = np.histogram(lbp.flatten(), bins=256, range=(0, 256))
        return hist / np.sum(hist)  # Normalize
    
    def _extract_edge_features(self, edges: np.ndarray) -> np.ndarray:
        """Extract edge-based features"""
        features = []
        
        # Edge density
        features.append(np.sum(edges) / edges.size)
        
        # Edge distribution in quadrants
        h, w = edges.shape
        quadrants = [
            edges[:h//2, :w//2],
            edges[:h//2, w//2:],
            edges[h//2:, :w//2],
            edges[h//2:, w//2:]
        ]
        
        for quad in quadrants:
            features.append(np.sum(quad) / quad.size)
        
        # Horizontal vs vertical edge ratio
        sobel_x = cv2.Sobel(edges, cv2.CV_64F, 1, 0)
        sobel_y = cv2.Sobel(edges, cv2.CV_64F, 0, 1)
        
        h_edges = np.sum(np.abs(sobel_x) > np.abs(sobel_y))
        v_edges = np.sum(np.abs(sobel_y) > np.abs(sobel_x))
        
        if v_edges > 0:
            features.append(h_edges / v_edges)
        else:
            features.append(1.0)
        
        # Edge strength distribution
        edge_strengths = np.sqrt(sobel_x**2 + sobel_y**2)
        features.extend([
            np.mean(edge_strengths),
            np.std(edge_strengths),
            np.max(edge_strengths)
        ])
        
        return np.array(features)
    
    def _get_dominant_orientation(self, edges: np.ndarray) -> float:
        """Get dominant edge orientation"""
        # Use Hough transform to find dominant lines
        lines = cv2.HoughLines(edges, 1, np.pi/180, threshold=100)
        
        if lines is not None:
            angles = lines[:, 0, 1]  # Extract angles
            # Convert to degrees
            angles_deg = angles * 180 / np.pi
            # Dominant angle
            hist, bins = np.histogram(angles_deg, bins=36, range=(0, 180))
            dominant_bin = np.argmax(hist)
            return bins[dominant_bin]
        
        return 0.0
    
    def calculate_visual_similarity(self, features1: VisualFeatures, features2: VisualFeatures) -> float:
        """Calculate visual similarity between two sets of features"""
        try:
            # Color similarity (histogram correlation)
            color_sim = cv2.compareHist(features1.color_histogram.astype(np.float32),
                                      features2.color_histogram.astype(np.float32),
                                      cv2.HISTCMP_CORREL)
            
            # Texture similarity (cosine similarity)
            texture_sim = cosine_similarity([features1.texture_features], [features2.texture_features])[0][0]
            
            # Edge similarity
            edge_sim = cosine_similarity([features1.edge_features], [features2.edge_features])[0][0]
            
            # Composition similarity
            comp_sim = self._compare_composition(features1.composition_features, features2.composition_features)
            
            # Weighted average
            weights = [0.3, 0.3, 0.2, 0.2]  # color, texture, edge, composition
            similarities = [color_sim, texture_sim, edge_sim, comp_sim]
            
            # Handle NaN values
            valid_similarities = []
            valid_weights = []
            for sim, weight in zip(similarities, weights):
                if not np.isnan(sim):
                    valid_similarities.append(sim)
                    valid_weights.append(weight)
            
            if valid_similarities:
                # Normalize weights
                total_weight = sum(valid_weights)
                valid_weights = [w / total_weight for w in valid_weights]
                overall_similarity = sum(s * w for s, w in zip(valid_similarities, valid_weights))
            else:
                overall_similarity = 0.0
            
            return max(0.0, min(1.0, overall_similarity))
            
        except Exception as e:
            self.logger.error(f"Error calculating visual similarity: {e}")
            return 0.0
    
    def _compare_composition(self, comp1: Dict[str, float], comp2: Dict[str, float]) -> float:
        """Compare composition features"""
        if not comp1 or not comp2:
            return 0.0
        
        common_keys = set(comp1.keys()) & set(comp2.keys())
        if not common_keys:
            return 0.0
        
        similarities = []
        for key in common_keys:
            val1, val2 = comp1[key], comp2[key]
            if key == 'aspect_ratio':
                # Aspect ratio similarity
                sim = 1 - abs(val1 - val2) / max(val1, val2, 1.0)
            else:
                # Normalized difference
                max_val = max(abs(val1), abs(val2), 1.0)
                sim = 1 - abs(val1 - val2) / max_val
            
            similarities.append(max(0.0, sim))
        
        return np.mean(similarities)
    
    def validate_brand_consistency(self, image_path: str, brand_reference_images: List[str] = None) -> BrandConsistency:
        """Validate brand consistency against reference images"""
        try:
            if not brand_reference_images:
                brand_reference_images = self._get_brand_reference_images()
            
            if not brand_reference_images:
                return BrandConsistency(
                    color_consistency=50.0,
                    style_consistency=50.0,
                    composition_consistency=50.0,
                    overall_brand_score=50.0,
                    violations=[],
                    recommendations=["No brand reference images available for comparison"]
                )
            
            # Extract features for target image
            target_features = self.extract_visual_features(image_path)
            target_palette = self.extract_color_palette(image_path)
            
            # Compare with reference images
            color_similarities = []
            style_similarities = []
            composition_similarities = []
            
            for ref_path in brand_reference_images:
                if os.path.exists(ref_path):
                    ref_features = self.extract_visual_features(ref_path)
                    ref_palette = self.extract_color_palette(ref_path)
                    
                    # Color consistency
                    color_sim = self._compare_color_palettes(target_palette, ref_palette)
                    color_similarities.append(color_sim)
                    
                    # Style consistency (visual features)
                    style_sim = self.calculate_visual_similarity(target_features, ref_features)
                    style_similarities.append(style_sim)
                    
                    # Composition consistency
                    comp_sim = self._compare_composition(target_features.composition_features,
                                                       ref_features.composition_features)
                    composition_similarities.append(comp_sim)
            
            # Calculate averages
            color_consistency = np.mean(color_similarities) * 100 if color_similarities else 50.0
            style_consistency = np.mean(style_similarities) * 100 if style_similarities else 50.0
            composition_consistency = np.mean(composition_similarities) * 100 if composition_similarities else 50.0
            
            # Overall brand score
            overall_brand_score = (color_consistency + style_consistency + composition_consistency) / 3
            
            # Generate violations and recommendations
            violations = []
            recommendations = []
            
            if color_consistency < 70:
                violations.append("Color palette significantly differs from brand standards")
                recommendations.append("Adjust color palette to match brand guidelines")
            
            if style_consistency < 70:
                violations.append("Visual style inconsistent with brand identity")
                recommendations.append("Review and adjust visual elements to align with brand style")
            
            if composition_consistency < 70:
                violations.append("Composition patterns differ from brand templates")
                recommendations.append("Consider using brand-approved composition layouts")
            
            return BrandConsistency(
                color_consistency=color_consistency,
                style_consistency=style_consistency,
                composition_consistency=composition_consistency,
                overall_brand_score=overall_brand_score,
                violations=violations,
                recommendations=recommendations
            )
            
        except Exception as e:
            self.logger.error(f"Error validating brand consistency: {e}")
            return BrandConsistency(
                color_consistency=0.0,
                style_consistency=0.0,
                composition_consistency=0.0,
                overall_brand_score=0.0,
                violations=["Error during brand consistency analysis"],
                recommendations=["Unable to perform brand consistency check"]
            )
    
    def _compare_color_palettes(self, palette1: ColorPalette, palette2: ColorPalette) -> float:
        """Compare two color palettes for similarity"""
        # Convert colors to LAB color space for perceptual comparison
        def rgb_to_lab(rgb):
            r, g, b = [x / 255.0 for x in rgb]
            # Convert to XYZ first (simplified)
            x = 0.412453 * r + 0.357580 * g + 0.180423 * b
            y = 0.212671 * r + 0.715160 * g + 0.072169 * b
            z = 0.019334 * r + 0.119193 * g + 0.950227 * b
            
            # Convert XYZ to LAB (simplified)
            def f(t):
                return t**(1/3) if t > 0.008856 else 7.787 * t + 16/116
            
            fx, fy, fz = f(x/0.95047), f(y/1.00000), f(z/1.08883)
            l = 116 * fy - 16
            a = 500 * (fx - fy)
            b = 200 * (fy - fz)
            return l, a, b
        
        # Convert dominant colors to LAB
        lab1 = [rgb_to_lab(color) for color in palette1.dominant_colors[:5]]
        lab2 = [rgb_to_lab(color) for color in palette2.dominant_colors[:5]]
        
        # Find best matches between palettes
        similarities = []
        for color1 in lab1:
            best_sim = 0
            for color2 in lab2:
                # Calculate Delta E (color difference)
                delta_e = np.sqrt(sum((c1 - c2)**2 for c1, c2 in zip(color1, color2)))
                # Convert to similarity (0-1)
                sim = max(0, 1 - delta_e / 100)
                best_sim = max(best_sim, sim)
            similarities.append(best_sim)
        
        return np.mean(similarities)
    
    def _get_brand_reference_images(self) -> List[str]:
        """Get list of brand reference images"""
        reference_patterns = ["brand_*.jpg", "brand_*.png", "logo_*.jpg", "logo_*.png", "reference_*.jpg", "reference_*.png"]
        reference_images = []
        
        for pattern in reference_patterns:
            import glob
            matches = glob.glob(str(self.brand_assets_dir / pattern))
            reference_images.extend(matches)
        
        return reference_images
    
    def learn_from_approved_asset(self, image_path: str, asset_metadata: Dict[str, Any] = None):
        """Learn brand patterns from approved assets"""
        try:
            # Extract features
            features = self.extract_visual_features(image_path)
            palette = self.extract_color_palette(image_path)
            quality = self.assess_image_quality(image_path)
            
            # Update brand profile
            self.brand_profile["brand_colors"].extend(palette.hex_colors[:3])  # Top 3 colors
            
            # Keep only recent colors (last 50)
            self.brand_profile["brand_colors"] = self.brand_profile["brand_colors"][-50:]
            
            # Store style signature
            style_signature = {
                "feature_hash": features.feature_hash,
                "composition": features.composition_features,
                "color_harmony": palette.color_harmony,
                "color_temperature": palette.temperature,
                "quality_score": quality.overall_score,
                "learned_date": datetime.now().isoformat(),
                "metadata": asset_metadata or {}
            }
            
            self.brand_profile["style_signatures"].append(style_signature)
            
            # Keep only recent signatures (last 20)
            self.brand_profile["style_signatures"] = self.brand_profile["style_signatures"][-20:]
            
            # Update quality baselines
            if "quality_baseline" not in self.brand_profile:
                self.brand_profile["quality_baseline"] = {}
            
            baseline = self.brand_profile["quality_baseline"]
            baseline["min_quality"] = max(baseline.get("min_quality", 0), quality.overall_score - 10)
            baseline["target_sharpness"] = max(baseline.get("target_sharpness", 0), quality.sharpness)
            baseline["target_contrast"] = max(baseline.get("target_contrast", 0), quality.contrast)
            
            # Save updated profile
            self._save_brand_profile()
            
            self.logger.info(f"Learned brand patterns from: {image_path}")
            
        except Exception as e:
            self.logger.error(f"Error learning from approved asset: {e}")
    
    def enhance_image(self, image_path: str, output_path: str = None, enhancement_level: str = "moderate") -> str:
        """Enhance image quality based on assessment"""
        try:
            # Load image
            pil_image = Image.open(image_path)
            
            # Assess current quality
            quality = self.assess_image_quality(image_path)
            
            # Apply enhancements based on assessment
            enhanced_image = pil_image.copy()
            
            enhancement_multipliers = {
                "subtle": 0.3,
                "moderate": 0.6,
                "aggressive": 1.0
            }
            
            multiplier = enhancement_multipliers.get(enhancement_level, 0.6)
            
            # Sharpness enhancement
            if quality.sharpness < 70:
                enhancer = ImageEnhance.Sharpness(enhanced_image)
                factor = 1 + (0.5 * multiplier)
                enhanced_image = enhancer.enhance(factor)
            
            # Contrast enhancement
            if quality.contrast < 70:
                enhancer = ImageEnhance.Contrast(enhanced_image)
                factor = 1 + (0.3 * multiplier)
                enhanced_image = enhancer.enhance(factor)
            
            # Brightness adjustment
            if quality.brightness < 70:
                enhancer = ImageEnhance.Brightness(enhanced_image)
                if quality.brightness < 50:  # Too dark
                    factor = 1 + (0.2 * multiplier)
                else:  # Too bright
                    factor = 1 - (0.2 * multiplier)
                enhanced_image = enhancer.enhance(factor)
            
            # Color enhancement
            if quality.saturation < 60:
                enhancer = ImageEnhance.Color(enhanced_image)
                factor = 1 + (0.2 * multiplier)
                enhanced_image = enhancer.enhance(factor)
            
            # Noise reduction (simple blur for high noise)
            if quality.noise_level < 60:
                enhanced_image = enhanced_image.filter(ImageFilter.GaussianBlur(radius=0.5 * multiplier))
            
            # Save enhanced image
            if output_path is None:
                base, ext = os.path.splitext(image_path)
                output_path = f"{base}_enhanced{ext}"
            
            enhanced_image.save(output_path, quality=95, optimize=True)
            
            self.logger.info(f"Enhanced image saved to: {output_path}")
            return output_path
            
        except Exception as e:
            self.logger.error(f"Error enhancing image: {e}")
            return image_path
    
    def generate_brand_report(self, image_paths: List[str]) -> Dict[str, Any]:
        """Generate comprehensive brand intelligence report"""
        try:
            report = {
                "analysis_date": datetime.now().isoformat(),
                "total_images": len(image_paths),
                "images_analyzed": [],
                "brand_consistency": {
                    "overall_score": 0.0,
                    "color_consistency": 0.0,
                    "style_consistency": 0.0,
                    "quality_consistency": 0.0
                },
                "quality_summary": {
                    "average_quality": 0.0,
                    "quality_distribution": {},
                    "enhancement_recommendations": []
                },
                "color_analysis": {
                    "dominant_colors": [],
                    "color_harmony_distribution": {},
                    "temperature_distribution": {},
                    "accessibility_scores": []
                },
                "recommendations": [],
                "brand_learning_summary": {}
            }
            
            # Analyze each image
            all_qualities = []
            all_palettes = []
            all_consistency_scores = []
            
            for image_path in image_paths:
                if os.path.exists(image_path):
                    try:
                        # Quality assessment
                        quality = self.assess_image_quality(image_path)
                        all_qualities.append(quality)
                        
                        # Color analysis
                        palette = self.extract_color_palette(image_path)
                        all_palettes.append(palette)
                        
                        # Brand consistency
                        consistency = self.validate_brand_consistency(image_path)
                        all_consistency_scores.append(consistency)
                        
                        # Add to report
                        report["images_analyzed"].append({
                            "path": image_path,
                            "quality_score": quality.overall_score,
                            "brand_score": consistency.overall_brand_score,
                            "dominant_colors": palette.hex_colors[:3],
                            "color_harmony": palette.color_harmony,
                            "enhancement_needed": len(quality.enhancement_recommendations) > 0
                        })
                        
                    except Exception as e:
                        self.logger.error(f"Error analyzing {image_path}: {e}")
            
            # Calculate summaries
            if all_qualities:
                report["quality_summary"]["average_quality"] = np.mean([q.overall_score for q in all_qualities])
                
                # Quality distribution
                quality_bins = {"excellent": 0, "good": 0, "fair": 0, "poor": 0}
                for quality in all_qualities:
                    if quality.overall_score >= 90:
                        quality_bins["excellent"] += 1
                    elif quality.overall_score >= 75:
                        quality_bins["good"] += 1
                    elif quality.overall_score >= 60:
                        quality_bins["fair"] += 1
                    else:
                        quality_bins["poor"] += 1
                
                report["quality_summary"]["quality_distribution"] = quality_bins
                
                # Collect all enhancement recommendations
                all_recommendations = []
                for quality in all_qualities:
                    all_recommendations.extend(quality.enhancement_recommendations)
                
                # Count most common recommendations
                from collections import Counter
                rec_counts = Counter(all_recommendations)
                report["quality_summary"]["enhancement_recommendations"] = [
                    {"recommendation": rec, "frequency": count}
                    for rec, count in rec_counts.most_common(5)
                ]
            
            # Brand consistency summary
            if all_consistency_scores:
                report["brand_consistency"]["overall_score"] = np.mean([c.overall_brand_score for c in all_consistency_scores])
                report["brand_consistency"]["color_consistency"] = np.mean([c.color_consistency for c in all_consistency_scores])
                report["brand_consistency"]["style_consistency"] = np.mean([c.style_consistency for c in all_consistency_scores])
            
            # Color analysis summary
            if all_palettes:
                # Collect all dominant colors
                all_colors = []
                harmony_counts = {}
                temp_counts = {}
                
                for palette in all_palettes:
                    all_colors.extend(palette.hex_colors[:3])
                    harmony_counts[palette.color_harmony] = harmony_counts.get(palette.color_harmony, 0) + 1
                    temp_counts[palette.temperature] = temp_counts.get(palette.temperature, 0) + 1
                
                # Most common colors
                from collections import Counter
                color_counts = Counter(all_colors)
                report["color_analysis"]["dominant_colors"] = [
                    {"color": color, "frequency": count}
                    for color, count in color_counts.most_common(10)
                ]
                
                report["color_analysis"]["color_harmony_distribution"] = harmony_counts
                report["color_analysis"]["temperature_distribution"] = temp_counts
                report["color_analysis"]["accessibility_scores"] = [p.accessibility_score for p in all_palettes]
            
            # Generate recommendations
            recommendations = []
            
            if report["quality_summary"]["average_quality"] < 75:
                recommendations.append("Overall image quality needs improvement. Consider implementing automated enhancement.")
            
            if report["brand_consistency"]["overall_score"] < 70:
                recommendations.append("Brand consistency is below target. Review brand guidelines and ensure consistent application.")
            
            if len(quality_bins.get("poor", 0)) > len(image_paths) * 0.2:
                recommendations.append("More than 20% of images have poor quality. Implement quality gates in the pipeline.")
            
            # Color accessibility
            low_accessibility = [score for score in report["color_analysis"]["accessibility_scores"] if score < 50]
            if len(low_accessibility) > len(image_paths) * 0.3:
                recommendations.append("30% of images have poor color accessibility. Review color choices for text overlay compatibility.")
            
            report["recommendations"] = recommendations
            
            # Brand learning summary
            report["brand_learning_summary"] = {
                "learned_colors": len(set(self.brand_profile.get("brand_colors", []))),
                "style_signatures": len(self.brand_profile.get("style_signatures", [])),
                "last_learning_date": self.brand_profile.get("last_updated", "Never")
            }
            
            return report
            
        except Exception as e:
            self.logger.error(f"Error generating brand report: {e}")
            return {
                "error": str(e),
                "analysis_date": datetime.now().isoformat(),
                "total_images": len(image_paths)
            }