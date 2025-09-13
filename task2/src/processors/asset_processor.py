"""
Asset Processing Module

Handles image processing, text overlay, brand element integration,
and format conversion for generated creative assets.
"""

import logging
from typing import Dict, List, Any, Optional, Tuple
from PIL import Image, ImageDraw, ImageFont, ImageEnhance, ImageFilter
import numpy as np
from pathlib import Path
import colorsys
import os

import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from generators.text_generator import TextGenerator

logger = logging.getLogger(__name__)


class AssetProcessor:
    """Processes and enhances assets with text, branding, and format conversion."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize the asset processor with configuration."""
        self.config = config
        self.brand_config = config.get("brand", {})
        self.text_generator = TextGenerator(config)
        
        # Load brand assets
        self._load_brand_assets()
        
        logger.info("AssetProcessor initialized")
    
    def _load_brand_assets(self):
        """Load brand assets like logos and fonts."""
        
        # Load logo if available
        logo_path = os.getenv("BRAND_LOGO_PATH", "assets/brand/logo.png")
        if os.path.exists(logo_path):
            try:
                self.brand_logo = Image.open(logo_path).convert("RGBA")
                logger.info(f"Brand logo loaded: {logo_path}")
            except Exception as e:
                logger.warning(f"Failed to load brand logo: {e}")
                self.brand_logo = None
        else:
            self.brand_logo = None
            logger.info("No brand logo found, will create text-based logo")
        
        # Setup font paths (fallback to system fonts)
        self.font_paths = self._get_font_paths()
    
    def _get_font_paths(self) -> Dict[str, str]:
        """Get available font paths for text rendering."""
        
        font_paths = {}
        
        # Try to find system fonts
        system_font_dirs = [
            "C:/Windows/Fonts/",  # Windows
            "/System/Library/Fonts/",  # macOS
            "/usr/share/fonts/",  # Linux
        ]
        
        for font_dir in system_font_dirs:
            if os.path.exists(font_dir):
                # Look for common fonts
                fonts_to_find = {
                    "arial": ["arial.ttf", "Arial.ttf"],
                    "helvetica": ["helvetica.ttf", "Helvetica.ttf"],
                    "montserrat": ["montserrat.ttf", "Montserrat-Regular.ttf"]
                }
                
                for font_name, font_files in fonts_to_find.items():
                    for font_file in font_files:
                        font_path = os.path.join(font_dir, font_file)
                        if os.path.exists(font_path):
                            font_paths[font_name] = font_path
                            break
        
        logger.info(f"Available fonts: {list(font_paths.keys())}")
        return font_paths
    
    def process_existing_asset(self,
                             asset_path: str,
                             format_config: Dict[str, Any],
                             product: Dict[str, Any],
                             campaign_brief: Dict[str, Any],
                             region: Dict[str, Any]) -> Optional[Image.Image]:
        """Process an existing asset for the campaign."""
        
        logger.info(f"Processing existing asset: {asset_path}")
        
        try:
            # Load existing asset
            image = Image.open(asset_path).convert("RGB")
            
            # Resize to target format
            target_size = (format_config["width"], format_config["height"])
            image = self._smart_resize(image, target_size)
            
            # Enhance image quality
            image = self._enhance_image(image)
            
            # Add campaign-specific overlays
            processed_image = self._add_campaign_overlays(
                image, format_config, product, campaign_brief, region
            )
            
            logger.info("Existing asset processed successfully")
            return processed_image
            
        except Exception as e:
            logger.error(f"Failed to process existing asset: {e}")
            return None
    
    def process_generated_asset(self,
                              generated_image: Image.Image,
                              format_config: Dict[str, Any], 
                              product: Dict[str, Any],
                              campaign_brief: Dict[str, Any],
                              region: Dict[str, Any]) -> Optional[Image.Image]:
        """Process a newly generated asset."""
        
        logger.info("Processing generated asset")
        
        try:
            # Ensure correct format and size
            image = generated_image.convert("RGB")
            target_size = (format_config["width"], format_config["height"])
            
            if image.size != target_size:
                image = self._smart_resize(image, target_size)
            
            # Apply brand-consistent enhancements
            image = self._apply_brand_enhancements(image)
            
            # Add campaign overlays
            processed_image = self._add_campaign_overlays(
                image, format_config, product, campaign_brief, region
            )
            
            logger.info("Generated asset processed successfully")
            return processed_image
            
        except Exception as e:
            logger.error(f"Failed to process generated asset: {e}")
            return None
    
    def _smart_resize(self, image: Image.Image, target_size: Tuple[int, int]) -> Image.Image:
        """Intelligently resize image maintaining quality and aspect ratio."""
        
        current_size = image.size
        target_width, target_height = target_size
        
        # Calculate scaling to fit target while maintaining aspect ratio
        scale_w = target_width / current_size[0]
        scale_h = target_height / current_size[1]
        scale = max(scale_w, scale_h)  # Scale to fill
        
        # Calculate new size
        new_width = int(current_size[0] * scale)
        new_height = int(current_size[1] * scale)
        
        # Resize with high-quality resampling
        resized = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
        
        # Center crop to exact target size
        left = (new_width - target_width) // 2
        top = (new_height - target_height) // 2
        right = left + target_width
        bottom = top + target_height
        
        cropped = resized.crop((left, top, right, bottom))
        
        logger.debug(f"Resized from {current_size} to {target_size}")
        return cropped
    
    def _enhance_image(self, image: Image.Image) -> Image.Image:
        """Apply image enhancements for better visual quality."""
        
        try:
            # Slight sharpening
            enhancer = ImageEnhance.Sharpness(image)
            image = enhancer.enhance(1.1)
            
            # Color enhancement
            enhancer = ImageEnhance.Color(image)
            image = enhancer.enhance(1.05)
            
            # Contrast adjustment
            enhancer = ImageEnhance.Contrast(image)
            image = enhancer.enhance(1.02)
            
            logger.debug("Image enhancements applied")
            return image
            
        except Exception as e:
            logger.warning(f"Image enhancement failed: {e}")
            return image
    
    def _apply_brand_enhancements(self, image: Image.Image) -> Image.Image:
        """Apply brand-specific image enhancements."""
        
        # Apply subtle brand color grading
        brand_colors = self.brand_config.get("primary_colors", [])
        if brand_colors:
            image = self._apply_color_grading(image, brand_colors[0])
        
        return image
    
    def _apply_color_grading(self, image: Image.Image, brand_color: str) -> Image.Image:
        """Apply subtle color grading toward brand colors."""
        
        try:
            # Convert brand color to RGB
            brand_rgb = self._hex_to_rgb(brand_color)
            
            # Apply very subtle color overlay (5% opacity)
            overlay = Image.new("RGB", image.size, brand_rgb)
            graded = Image.blend(image, overlay, 0.05)
            
            return graded
            
        except Exception as e:
            logger.warning(f"Color grading failed: {e}")
            return image
    
    def _add_campaign_overlays(self,
                             image: Image.Image,
                             format_config: Dict[str, Any],
                             product: Dict[str, Any],
                             campaign_brief: Dict[str, Any], 
                             region: Dict[str, Any]) -> Image.Image:
        """Add campaign-specific overlays like text and branding."""
        
        # Create overlay canvas
        overlay = Image.new("RGBA", image.size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay)
        
        # Generate localized copy
        copy_elements = self.text_generator.generate_localized_copy(
            product, campaign_brief, region, format_config
        )
        
        # Add text overlays
        self._add_text_overlays(overlay, draw, copy_elements, format_config)
        
        # Add brand logo
        self._add_brand_logo(overlay, format_config)
        
        # Add benefit callouts
        if copy_elements.get("benefit_callout"):
            self._add_benefit_callout(overlay, draw, copy_elements["benefit_callout"], format_config)
        
        # Add disclaimer if required
        if copy_elements.get("disclaimer"):
            self._add_disclaimer(overlay, draw, copy_elements["disclaimer"], format_config)
        
        # Composite overlay onto image
        final_image = Image.alpha_composite(image.convert("RGBA"), overlay)
        
        return final_image.convert("RGB")
    
    def _add_text_overlays(self,
                          overlay: Image.Image,
                          draw: ImageDraw.Draw,
                          copy_elements: Dict[str, str],
                          format_config: Dict[str, Any]):
        """Add text overlays to the image."""
        
        width, height = overlay.size
        brand_colors = self.brand_config.get("primary_colors", ["#000000"])
        
        # Define text areas based on format
        if "story" in format_config.get("name", "").lower():
            # Vertical format - text at bottom
            headline_area = (width * 0.1, height * 0.7, width * 0.9, height * 0.85)
            body_area = (width * 0.1, height * 0.85, width * 0.9, height * 0.95)
            cta_area = (width * 0.1, height * 0.95, width * 0.9, height * 1.0)
        elif "landscape" in format_config.get("name", "").lower():
            # Horizontal format - text on right side
            headline_area = (width * 0.55, height * 0.2, width * 0.95, height * 0.4)
            body_area = (width * 0.55, height * 0.4, width * 0.95, height * 0.7)
            cta_area = (width * 0.55, height * 0.75, width * 0.95, height * 0.9)
        else:
            # Square format - text at bottom
            headline_area = (width * 0.1, height * 0.65, width * 0.9, height * 0.8)
            body_area = (width * 0.1, height * 0.8, width * 0.9, height * 0.9)
            cta_area = (width * 0.1, height * 0.9, width * 0.9, height * 1.0)
        
        # Add headline
        if copy_elements.get("headline"):
            self._draw_text_with_background(
                draw, copy_elements["headline"], headline_area,
                font_size=self._get_font_size("headline", format_config),
                color=brand_colors[0], weight="bold"
            )
        
        # Add body text
        if copy_elements.get("body_text"):
            self._draw_text_with_background(
                draw, copy_elements["body_text"], body_area,
                font_size=self._get_font_size("body", format_config),
                color="#333333", weight="regular"
            )
        
        # Add CTA button
        if copy_elements.get("cta"):
            self._draw_cta_button(draw, copy_elements["cta"], cta_area, format_config)
    
    def _get_font_size(self, text_type: str, format_config: Dict[str, Any]) -> int:
        """Calculate appropriate font size based on format and text type."""
        
        base_size = min(format_config["width"], format_config["height"]) // 25
        
        size_multipliers = {
            "headline": 1.8,
            "body": 1.0,
            "cta": 1.2,
            "disclaimer": 0.6
        }
        
        return int(base_size * size_multipliers.get(text_type, 1.0))
    
    def _draw_text_with_background(self,
                                 draw: ImageDraw.Draw,
                                 text: str,
                                 area: Tuple[int, int, int, int],
                                 font_size: int,
                                 color: str,
                                 weight: str = "regular"):
        """Draw text with semi-transparent background for readability."""
        
        x1, y1, x2, y2 = area
        
        try:
            # Load font
            font = self._get_font(font_size, weight)
            
            # Calculate text size and position
            bbox = draw.textbbox((0, 0), text, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
            
            # Center text in area
            text_x = x1 + (x2 - x1 - text_width) // 2
            text_y = y1 + (y2 - y1 - text_height) // 2
            
            # Draw semi-transparent background
            padding = 20
            bg_rect = [
                text_x - padding, text_y - padding,
                text_x + text_width + padding, text_y + text_height + padding
            ]
            draw.rounded_rectangle(bg_rect, radius=10, fill=(0, 0, 0, 128))
            
            # Draw text
            rgb_color = self._hex_to_rgb(color)
            draw.text((text_x, text_y), text, font=font, fill=rgb_color)
            
        except Exception as e:
            logger.warning(f"Text drawing failed: {e}")
    
    def _draw_cta_button(self,
                        draw: ImageDraw.Draw,
                        cta_text: str,
                        area: Tuple[int, int, int, int],
                        format_config: Dict[str, Any]):
        """Draw CTA as a branded button."""
        
        x1, y1, x2, y2 = area
        
        try:
            font = self._get_font(self._get_font_size("cta", format_config), "bold")
            
            # Calculate button size
            bbox = draw.textbbox((0, 0), cta_text, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
            
            button_width = text_width + 40
            button_height = text_height + 20
            
            # Center button in area
            button_x = x1 + (x2 - x1 - button_width) // 2
            button_y = y1 + (y2 - y1 - button_height) // 2
            
            # Draw button background
            brand_color = self.brand_config.get("primary_colors", ["#FF6B35"])[0]
            button_rect = [
                button_x, button_y,
                button_x + button_width, button_y + button_height
            ]
            draw.rounded_rectangle(button_rect, radius=15, fill=self._hex_to_rgb(brand_color))
            
            # Draw button text
            text_x = button_x + (button_width - text_width) // 2
            text_y = button_y + (button_height - text_height) // 2
            draw.text((text_x, text_y), cta_text, font=font, fill=(255, 255, 255))
            
        except Exception as e:
            logger.warning(f"CTA button drawing failed: {e}")
    
    def _add_brand_logo(self, overlay: Image.Image, format_config: Dict[str, Any]):
        """Add brand logo to the image."""
        
        if not self.brand_logo:
            return
        
        try:
            # Calculate logo size (8% of image area minimum)
            width, height = overlay.size
            min_area = (width * height) * 0.08
            logo_size = int((min_area ** 0.5))
            
            # Resize logo
            logo_aspect = self.brand_logo.size[0] / self.brand_logo.size[1]
            if logo_aspect > 1:  # Wider logo
                logo_width = logo_size
                logo_height = int(logo_size / logo_aspect)
            else:  # Taller logo
                logo_height = logo_size
                logo_width = int(logo_size * logo_aspect)
            
            resized_logo = self.brand_logo.resize((logo_width, logo_height), Image.Resampling.LANCZOS)
            
            # Position logo (bottom-right with margin)
            margin = self.brand_config.get("spacing", {}).get("margin", 60)
            logo_x = width - logo_width - margin
            logo_y = height - logo_height - margin
            
            # Paste logo with alpha blending
            overlay.paste(resized_logo, (logo_x, logo_y), resized_logo)
            
        except Exception as e:
            logger.warning(f"Logo placement failed: {e}")
    
    def _add_benefit_callout(self,
                           overlay: Image.Image,
                           draw: ImageDraw.Draw,
                           benefit_text: str,
                           format_config: Dict[str, Any]):
        """Add benefit callout badge."""
        
        width, height = overlay.size
        
        try:
            font = self._get_font(self._get_font_size("body", format_config), "regular")
            
            # Position in top-left area
            callout_x = width * 0.05
            callout_y = height * 0.05
            
            # Draw callout with brand accent color
            accent_color = self.brand_config.get("secondary_colors", ["#F7931E"])[0]
            
            bbox = draw.textbbox((0, 0), benefit_text, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
            
            # Draw background badge
            badge_rect = [
                callout_x, callout_y,
                callout_x + text_width + 20, callout_y + text_height + 10
            ]
            draw.rounded_rectangle(badge_rect, radius=8, fill=self._hex_to_rgb(accent_color))
            
            # Draw text
            draw.text((callout_x + 10, callout_y + 5), benefit_text, font=font, fill=(255, 255, 255))
            
        except Exception as e:
            logger.warning(f"Benefit callout failed: {e}")
    
    def _add_disclaimer(self,
                       overlay: Image.Image,
                       draw: ImageDraw.Draw,
                       disclaimer_text: str,
                       format_config: Dict[str, Any]):
        """Add legal disclaimer text."""
        
        width, height = overlay.size
        
        try:
            font = self._get_font(self._get_font_size("disclaimer", format_config), "regular")
            
            # Position at bottom center
            bbox = draw.textbbox((0, 0), disclaimer_text, font=font)
            text_width = bbox[2] - bbox[0]
            
            disclaimer_x = (width - text_width) // 2
            disclaimer_y = height - 30
            
            # Draw with semi-transparent background
            draw.text((disclaimer_x, disclaimer_y), disclaimer_text, font=font, fill=(100, 100, 100))
            
        except Exception as e:
            logger.warning(f"Disclaimer text failed: {e}")
    
    def _get_font(self, size: int, weight: str = "regular") -> ImageFont.FreeTypeFont:
        """Get font object with specified size and weight."""
        
        try:
            # Try to get preferred brand font
            brand_font = self.brand_config.get("fonts", {}).get("primary", "arial")
            font_path = self.font_paths.get(brand_font.lower())
            
            if font_path:
                return ImageFont.truetype(font_path, size)
            
            # Fallback to default font
            return ImageFont.load_default()
            
        except Exception as e:
            logger.warning(f"Font loading failed: {e}")
            return ImageFont.load_default()
    
    def _hex_to_rgb(self, hex_color: str) -> Tuple[int, int, int]:
        """Convert hex color to RGB tuple."""
        
        try:
            hex_color = hex_color.lstrip('#')
            return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
        except Exception:
            return (0, 0, 0)  # Default to black