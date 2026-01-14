"""
Creative Composer - Combines base images with text overlays and brand elements.
"""

import logging
from pathlib import Path
from typing import Dict, Any, Tuple, Optional
from PIL import Image, ImageDraw, ImageFont, ImageEnhance
import textwrap

try:
    from .utils import calculate_dimensions, sanitize_filename
except ImportError:
    from utils import calculate_dimensions, sanitize_filename

logger = logging.getLogger(__name__)


class CreativeComposer:
    """Composes final creative assets with text overlays and brand elements."""
    
    def __init__(self):
        self.font_cache = {}
        logger.info("Creative composer initialized")
    
    def compose_creative(
        self,
        base_image_path: Path,
        campaign_brief: Dict[str, Any],
        product: Dict[str, Any],
        aspect_ratio: str
    ) -> Image.Image:
        """Compose a final creative asset."""
        
        # Load and resize base image
        base_image = self._load_and_resize_image(base_image_path, aspect_ratio)
        
        # Create a copy to work with
        creative = base_image.copy()
        
        # Add campaign message overlay
        creative = self._add_text_overlay(creative, campaign_brief, product)
        
        # Add brand elements if specified
        if campaign_brief.get('brand_guidelines', {}).get('logo_required'):
            creative = self._add_logo_placeholder(creative)
        
        # Apply brand colors if specified
        creative = self._apply_brand_styling(creative, campaign_brief)
        
        logger.info(f"Composed creative for {product['name']} in {aspect_ratio}")
        return creative
    
    def _load_and_resize_image(self, image_path: Path, aspect_ratio: str) -> Image.Image:
        """Load and resize image to target aspect ratio."""
        
        try:
            # Load image
            image = Image.open(image_path)
            
            # Convert to RGB if necessary
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            # Calculate target dimensions
            target_width, target_height = calculate_dimensions(aspect_ratio)
            
            # Resize image while maintaining aspect ratio
            image = self._smart_resize(image, (target_width, target_height))
            
            return image
            
        except Exception as e:
            logger.error(f"Failed to load image {image_path}: {e}")
            
            # Create fallback image
            target_width, target_height = calculate_dimensions(aspect_ratio)
            fallback = Image.new('RGB', (target_width, target_height), color='#f0f0f0')
            return fallback
    
    def _smart_resize(self, image: Image.Image, target_size: Tuple[int, int]) -> Image.Image:
        """Resize image intelligently - crop to fit target aspect ratio."""
        
        target_width, target_height = target_size
        current_width, current_height = image.size
        
        # Calculate ratios
        target_ratio = target_width / target_height
        current_ratio = current_width / current_height
        
        if abs(target_ratio - current_ratio) < 0.01:
            # Aspect ratios are close enough, just resize
            return image.resize(target_size, Image.Resampling.LANCZOS)
        
        if current_ratio > target_ratio:
            # Image is wider than target, crop width
            new_width = int(current_height * target_ratio)
            left = (current_width - new_width) // 2
            image = image.crop((left, 0, left + new_width, current_height))
        else:
            # Image is taller than target, crop height
            new_height = int(current_width / target_ratio)
            top = (current_height - new_height) // 2
            image = image.crop((0, top, current_width, top + new_height))
        
        # Resize to exact target dimensions
        return image.resize(target_size, Image.Resampling.LANCZOS)
    
    def _add_text_overlay(
        self,
        image: Image.Image,
        campaign_brief: Dict[str, Any],
        product: Dict[str, Any]
    ) -> Image.Image:
        """Add campaign message and product name as text overlay."""
        
        draw = ImageDraw.Draw(image)
        width, height = image.size
        
        # Get text content
        campaign_message = campaign_brief.get('campaign_message', '')
        product_name = product.get('name', '')
        
        if not campaign_message and not product_name:
            return image
        
        # Define text areas
        message_area = {
            'x': int(width * 0.05),
            'y': int(height * 0.7),
            'width': int(width * 0.9),
            'height': int(height * 0.25)
        }
        
        # Add campaign message
        if campaign_message:
            self._draw_text_in_area(
                draw, campaign_message, message_area,
                font_size_ratio=0.06, font_weight='bold',
                text_color='white', outline_color='black'
            )
        
        # Add product name (smaller, above message)
        if product_name:
            product_area = {
                'x': message_area['x'],
                'y': message_area['y'] - int(height * 0.1),
                'width': message_area['width'],
                'height': int(height * 0.08)
            }
            
            self._draw_text_in_area(
                draw, product_name, product_area,
                font_size_ratio=0.04, font_weight='normal',
                text_color='white', outline_color='black'
            )
        
        return image
    
    def _draw_text_in_area(
        self,
        draw: ImageDraw.ImageDraw,
        text: str,
        area: Dict[str, int],
        font_size_ratio: float = 0.05,
        font_weight: str = 'normal',
        text_color: str = 'white',
        outline_color: str = 'black'
    ) -> None:
        """Draw text within a specified area with automatic wrapping and sizing."""
        
        # Calculate initial font size
        font_size = int(min(area['width'], area['height']) * font_size_ratio)
        font = self._get_font(font_size, font_weight)
        
        # Wrap text to fit area width
        wrapped_text = self._wrap_text(text, font, area['width'], draw)
        
        # Calculate total text height
        line_height = font_size * 1.2
        total_height = len(wrapped_text) * line_height
        
        # Adjust font size if text doesn't fit height
        if total_height > area['height']:
            scale_factor = area['height'] / total_height * 0.9
            font_size = int(font_size * scale_factor)
            font = self._get_font(font_size, font_weight)
            line_height = font_size * 1.2
            
            # Re-wrap with new font size
            wrapped_text = self._wrap_text(text, font, area['width'], draw)
        
        # Center text vertically in area
        total_text_height = len(wrapped_text) * line_height
        start_y = area['y'] + (area['height'] - total_text_height) // 2
        
        # Draw each line
        for i, line in enumerate(wrapped_text):
            # Center text horizontally
            bbox = draw.textbbox((0, 0), line, font=font)
            text_width = bbox[2] - bbox[0]
            x = area['x'] + (area['width'] - text_width) // 2
            y = start_y + i * line_height
            
            # Draw text with outline for better visibility
            outline_width = max(1, font_size // 20)
            
            # Draw outline
            for adj in range(-outline_width, outline_width + 1):
                for adj2 in range(-outline_width, outline_width + 1):
                    if adj != 0 or adj2 != 0:
                        draw.text((x + adj, y + adj2), line, font=font, fill=outline_color)
            
            # Draw main text
            draw.text((x, y), line, font=font, fill=text_color)
    
    def _wrap_text(self, text: str, font: ImageFont.ImageFont, max_width: int, draw: ImageDraw.ImageDraw) -> list:
        """Wrap text to fit within specified width."""
        
        words = text.split()
        lines = []
        current_line = []
        
        for word in words:
            # Test adding this word to current line
            test_line = ' '.join(current_line + [word])
            bbox = draw.textbbox((0, 0), test_line, font=font)
            test_width = bbox[2] - bbox[0]
            
            if test_width <= max_width:
                current_line.append(word)
            else:
                # Start new line
                if current_line:
                    lines.append(' '.join(current_line))
                current_line = [word]
        
        # Add final line
        if current_line:
            lines.append(' '.join(current_line))
        
        return lines
    
    def _get_font(self, size: int, weight: str = 'normal') -> ImageFont.ImageFont:
        """Get font with caching."""
        
        cache_key = f"{size}_{weight}"
        
        if cache_key in self.font_cache:
            return self.font_cache[cache_key]
        
        # Try to load system fonts
        font_paths = [
            "/System/Library/Fonts/Arial.ttf",
            "/System/Library/Fonts/Helvetica.ttc",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf"
        ]
        
        if weight == 'bold':
            font_paths.insert(0, "/System/Library/Fonts/Arial Bold.ttf")
            font_paths.insert(1, "/System/Library/Fonts/Helvetica-Bold.ttc")
        
        font = None
        for font_path in font_paths:
            try:
                font = ImageFont.truetype(font_path, size)
                break
            except (OSError, IOError):
                continue
        
        # Fallback to default font
        if font is None:
            try:
                font = ImageFont.load_default()
            except:
                font = ImageFont.load_default()
        
        self.font_cache[cache_key] = font
        return font
    
    def _add_logo_placeholder(self, image: Image.Image) -> Image.Image:
        """Add a placeholder logo area."""
        
        draw = ImageDraw.Draw(image)
        width, height = image.size
        
        # Logo placement (top-right corner)
        logo_size = min(width, height) // 8
        logo_x = width - logo_size - 20
        logo_y = 20
        
        # Draw logo placeholder
        logo_rect = [logo_x, logo_y, logo_x + logo_size, logo_y + logo_size]
        draw.rectangle(logo_rect, fill='white', outline='gray', width=2)
        
        # Add "LOGO" text
        font = self._get_font(logo_size // 4, 'bold')
        text = "LOGO"
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        
        text_x = logo_x + (logo_size - text_width) // 2
        text_y = logo_y + (logo_size - text_height) // 2
        
        draw.text((text_x, text_y), text, font=font, fill='gray')
        
        return image
    
    def _apply_brand_styling(self, image: Image.Image, campaign_brief: Dict[str, Any]) -> Image.Image:
        """Apply brand-specific styling adjustments."""
        
        brand_guidelines = campaign_brief.get('brand_guidelines', {})
        
        # Apply color adjustments if brand colors are specified
        primary_colors = brand_guidelines.get('primary_colors', [])
        
        if primary_colors:
            # Subtle color enhancement based on brand palette
            enhancer = ImageEnhance.Color(image)
            image = enhancer.enhance(1.1)  # Slight color boost
        
        return image