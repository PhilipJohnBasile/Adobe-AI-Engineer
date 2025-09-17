"""
Image Generator - Uses OpenAI DALL-E to generate product images when assets are missing.
"""

import logging
import os
from pathlib import Path
from typing import Dict, Any, Optional
import requests
from PIL import Image
import openai

from .utils import update_cost_tracking, sanitize_filename

logger = logging.getLogger(__name__)


class ImageGenerator:
    """Generates product images using OpenAI DALL-E API."""
    
    def __init__(self):
        self.client = openai.OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        self.cache_dir = Path('generated_cache')
        self.cache_dir.mkdir(exist_ok=True)
        
        # DALL-E pricing (as of 2024)
        self.pricing = {
            'dall-e-3': {'1024x1024': 0.040, '1024x1792': 0.080, '1792x1024': 0.080},
            'dall-e-2': {'1024x1024': 0.020, '512x512': 0.018, '256x256': 0.016}
        }
        
        logger.info("Image generator initialized with OpenAI DALL-E")
    
    def generate_product_image(
        self, 
        product: Dict[str, Any], 
        campaign_brief: Dict[str, Any],
        model: str = "dall-e-3",
        size: str = "1024x1024"
    ) -> Path:
        """Generate a product image using DALL-E."""
        
        product_name = product['name']
        sanitized_name = sanitize_filename(product_name)
        
        # Check cache first
        cache_filename = f"{sanitized_name}_{model}_{size}.png"
        cache_path = self.cache_dir / cache_filename
        
        if cache_path.exists():
            logger.info(f"Using cached image for {product_name}")
            return cache_path
        
        # Build prompt
        prompt = self._build_image_prompt(product, campaign_brief)
        
        logger.info(f"Generating image for {product_name} with prompt: {prompt[:100]}...")
        
        try:
            # Generate image
            response = self.client.images.generate(
                model=model,
                prompt=prompt,
                size=size,
                quality="standard",
                n=1
            )
            
            # Download and save image
            image_url = response.data[0].url
            image_response = requests.get(image_url)
            image_response.raise_for_status()
            
            # Save to cache
            with open(cache_path, 'wb') as f:
                f.write(image_response.content)
            
            # Track costs
            cost = self.pricing.get(model, {}).get(size, 0.040)
            update_cost_tracking('dalle', cost)
            
            logger.info(f"Generated and cached image: {cache_path}")
            return cache_path
            
        except Exception as e:
            logger.error(f"Failed to generate image for {product_name}: {e}")
            
            # Return placeholder image
            placeholder_path = self._create_placeholder_image(product_name, size)
            return placeholder_path
    
    def _build_image_prompt(self, product: Dict[str, Any], campaign_brief: Dict[str, Any]) -> str:
        """Build a detailed prompt for image generation."""
        
        product_name = product['name']
        product_description = product.get('description', '')
        product_keywords = product.get('target_keywords', [])
        
        # Base product prompt
        prompt_parts = [
            f"A high-quality product photography image of {product_name}.",
            f"Product description: {product_description}."
        ]
        
        # Add localized campaign message for context
        campaign_message = campaign_brief.get('campaign_message', '')
        if campaign_message:
            prompt_parts.append(f"Campaign context: {campaign_message}.")
        
        # Add target audience context
        if 'target_audience' in campaign_brief:
            audience = campaign_brief['target_audience']
            if isinstance(audience, str):
                prompt_parts.append(f"Target audience: {audience}.")
            elif isinstance(audience, dict):
                demographics = audience.get('demographics', '')
                if demographics:
                    prompt_parts.append(f"Target audience: {demographics}.")
        
        # Add brand guidelines if available
        if 'brand_guidelines' in campaign_brief:
            brand = campaign_brief['brand_guidelines']
            colors = brand.get('primary_colors', [])
            if colors:
                prompt_parts.append(f"Use brand colors: {', '.join(colors)}.")
        
        # Add keywords
        if product_keywords:
            prompt_parts.append(f"Keywords: {', '.join(product_keywords)}.")
        
        # Style specifications
        style_specs = [
            "Professional product photography",
            "Clean white background or minimal context",
            "Good lighting",
            "High resolution",
            "Commercial advertising style",
            "Photorealistic",
            "No text or typography in the image"
        ]
        
        prompt_parts.extend(style_specs)
        
        # Join all parts
        prompt = " ".join(prompt_parts)
        
        # Ensure prompt is not too long (DALL-E has limits)
        if len(prompt) > 1000:
            prompt = prompt[:997] + "..."
        
        return prompt
    
    def _create_placeholder_image(self, product_name: str, size: str) -> Path:
        """Create a placeholder image when generation fails."""
        
        try:
            # Parse size
            width, height = map(int, size.split('x'))
            
            # Create simple placeholder
            placeholder = Image.new('RGB', (width, height), color='#f0f0f0')
            
            # Add text if PIL supports it
            try:
                from PIL import ImageDraw, ImageFont
                
                draw = ImageDraw.Draw(placeholder)
                
                # Try to use a font, fall back to default
                try:
                    font_size = min(width, height) // 20
                    font = ImageFont.truetype("/System/Library/Fonts/Arial.ttf", font_size)
                except:
                    font = ImageFont.load_default()
                
                text = f"PLACEHOLDER\n{product_name}"
                
                # Get text bounding box
                bbox = draw.textbbox((0, 0), text, font=font)
                text_width = bbox[2] - bbox[0]
                text_height = bbox[3] - bbox[1]
                
                # Center text
                x = (width - text_width) // 2
                y = (height - text_height) // 2
                
                draw.text((x, y), text, fill='#666666', font=font)
                
            except ImportError:
                # ImageDraw not available, skip text
                pass
            
            # Save placeholder
            sanitized_name = sanitize_filename(product_name)
            placeholder_path = self.cache_dir / f"{sanitized_name}_placeholder.png"
            placeholder.save(placeholder_path)
            
            logger.warning(f"Created placeholder image: {placeholder_path}")
            return placeholder_path
            
        except Exception as e:
            logger.error(f"Failed to create placeholder: {e}")
            raise
    
    def clear_cache(self) -> None:
        """Clear the generated image cache."""
        
        try:
            import shutil
            shutil.rmtree(self.cache_dir)
            self.cache_dir.mkdir(exist_ok=True)
            logger.info("Image cache cleared")
            
        except Exception as e:
            logger.error(f"Failed to clear cache: {e}")
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get statistics about the image cache."""
        
        stats = {
            'cached_images': 0,
            'total_size_mb': 0.0,
            'images': []
        }
        
        if not self.cache_dir.exists():
            return stats
        
        total_size = 0
        for image_path in self.cache_dir.glob('*.png'):
            size = image_path.stat().st_size
            total_size += size
            
            stats['images'].append({
                'name': image_path.name,
                'size_mb': size / (1024 * 1024)
            })
        
        stats['cached_images'] = len(stats['images'])
        stats['total_size_mb'] = total_size / (1024 * 1024)
        
        return stats