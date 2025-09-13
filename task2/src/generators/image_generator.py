"""
Image Generation Module

Handles AI-powered image generation using various GenAI services like DALL-E 3,
with fallback strategies and intelligent prompt engineering for brand-consistent results.
"""

import os
import logging
import requests
import base64
from typing import Dict, List, Any, Optional, Tuple
from PIL import Image
import openai
from io import BytesIO
import time
from datetime import datetime, timedelta
import threading

# Import cost tracking utilities
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))
from utils.cost_tracker import CostTracker, CacheManager

logger = logging.getLogger(__name__)


class ImageGenerator:
    """Manages AI image generation with multiple service providers and rate limiting."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize the image generator with configuration."""
        self.config = config
        self.genai_config = config.get("genai", {})
        self.primary_service = self.genai_config.get("primary_service", "openai")
        
        # Initialize API clients
        self._init_api_clients()
        
        # Rate limiting tracking
        self._rate_limits = {}
        self._rate_lock = threading.Lock()
        
        # Cost tracking and caching for demo efficiency
        self.cost_tracker = CostTracker(config)
        self.cache_manager = CacheManager(config)
        
        # Prompt templates
        self.prompt_templates = self._load_prompt_templates()
        
        logger.info(f"ImageGenerator initialized with primary service: {self.primary_service}")
    
    def _check_rate_limit(self, service: str) -> bool:
        """Check if service is within rate limits."""
        with self._rate_lock:
            now = datetime.now()
            service_config = self.genai_config.get("services", {}).get(service, {})
            rate_limit = service_config.get("rate_limit_per_minute", 10)
            
            # Initialize or clean old requests
            if service not in self._rate_limits:
                self._rate_limits[service] = []
            
            # Remove requests older than 1 minute
            self._rate_limits[service] = [
                req_time for req_time in self._rate_limits[service]
                if now - req_time < timedelta(minutes=1)
            ]
            
            # Check if under rate limit
            if len(self._rate_limits[service]) < rate_limit:
                self._rate_limits[service].append(now)
                return True
            
            return False
    
    def _wait_for_rate_limit(self, service: str) -> float:
        """Calculate wait time for rate limit reset."""
        with self._rate_lock:
            if service not in self._rate_limits or not self._rate_limits[service]:
                return 0.0
            
            oldest_request = min(self._rate_limits[service])
            wait_time = 60 - (datetime.now() - oldest_request).total_seconds()
            return max(0, wait_time)
    
    def _init_api_clients(self):
        """Initialize API clients."""
        # Load environment variables from .env file
        from pathlib import Path
        import os
        env_path = Path(__file__).parent.parent.parent / "config" / ".env"
        if env_path.exists():
            with open(env_path) as f:
                for line in f:
                    if line.strip() and not line.startswith('#') and '=' in line:
                        key, value = line.strip().split('=', 1)
                        os.environ[key] = value
        
        # OpenAI API configuration (no organization for project-scoped keys)
        self.openai_api_key = os.getenv('OPENAI_API_KEY')
        if self.openai_api_key:
            self.openai_client = openai.OpenAI(
                api_key=self.openai_api_key
                # Don't include organization for project-scoped keys
            )
            logger.info("OpenAI API configured successfully")
        else:
            logger.warning("OpenAI API not configured - missing API key")
            self.openai_client = None
    
    def _load_prompt_templates(self) -> Dict[str, str]:
        """Load prompt engineering templates for different scenarios."""
        return {
            "product_hero": """Create a high-quality, professional product image featuring {product_name}.
            
Product Details:
- Category: {category}
- Key Benefits: {benefits}
- Target Audience: {audience}
- Regional Context: {region}

Style Requirements:
- {style_preferences}
- Bright, vibrant, lifestyle-focused
- Professional product photography quality
- Clean background with subtle texture
- Excellent lighting that highlights product features

Brand Guidelines:
- Primary colors: {brand_colors}
- Mood: {brand_voice}
- Avoid: {avoid_elements}

The image should be suitable for {format_description} and convey {key_message}.""",
            
            "lifestyle_scene": """Create an engaging lifestyle scene showcasing {product_name} in a real-world context.

Scene Context:
- Setting: {lifestyle_context}
- Target demographic: {audience}
- Regional cultural context: {region}
- Activity/scenario: {usage_scenario}

Visual Requirements:
- Authentic, relatable scenario
- Natural lighting and composition
- Product integrated naturally into scene
- High-quality, professional photography style
- Colors that complement brand palette: {brand_colors}

Mood and Tone:
- {brand_voice}
- {tone}
- Aspirational yet achievable

Format: {format_description}
Key Message: {key_message}""",
            
            "abstract_brand": """Create an abstract, branded background design suitable for {product_name} marketing.

Design Elements:
- Brand colors: {brand_colors}
- Style: {style_preferences}
- Mood: {brand_voice}
- Format: {format_description}

Requirements:
- Professional, clean design
- Suitable as background for text overlay
- Represents brand values: {brand_values}
- Appeals to {audience}
- Regional preference: {region}

Avoid:
- {avoid_elements}
- Overly busy patterns that compete with text
- Colors outside brand palette"""
        }
    
    def generate_product_image(self, 
                             product: Dict[str, Any],
                             campaign_brief: Dict[str, Any], 
                             region: Dict[str, Any],
                             format_config: Dict[str, Any]) -> Optional[Image.Image]:
        """Generate a product image using AI based on campaign requirements."""
        
        logger.info(f"Generating image for product: {product['name']}")
        
        # Determine the best generation strategy
        generation_strategy = self._determine_generation_strategy(product, campaign_brief)
        
        # Build prompt based on strategy
        prompt = self._build_generation_prompt(
            product, campaign_brief, region, format_config, generation_strategy
        )
        
        # Check cache first for demo efficiency
        cached_result = self.cache_manager.get_cached_result(prompt, "image")
        if cached_result:
            logger.info("Using cached image result")
            return cached_result
        
        # Check budget before proceeding
        budget_check = self.cost_tracker.should_proceed_with_generation("openai", "dall-e-2", 1)
        if not budget_check["proceed"]:
            logger.error(f"Cannot generate image: {budget_check['reason']}")
            return None
        
        # Generate image with retry logic
        image = self._generate_with_retry(prompt, format_config)
        
        if image:
            logger.info("Image generation successful")
            # Cache the result for future use
            self.cache_manager.cache_result(prompt, image, "image")
            return image
        else:
            logger.error("Image generation failed after all retries")
            return None
    
    def _determine_generation_strategy(self, product: Dict[str, Any], campaign_brief: Dict[str, Any]) -> str:
        """Determine the best generation strategy based on product and campaign context."""
        
        # Check if product has existing assets
        if product.get("existing_assets"):
            return "enhancement"  # Enhance existing assets
        
        # Check campaign creative requirements
        creative_reqs = campaign_brief.get("creative_requirements", {})
        must_include = creative_reqs.get("must_include", [])
        
        if "Product hero shot" in must_include:
            return "product_hero"
        elif "Lifestyle context" in must_include:
            return "lifestyle_scene" 
        else:
            return "abstract_brand"
    
    def _build_generation_prompt(self,
                               product: Dict[str, Any],
                               campaign_brief: Dict[str, Any],
                               region: Dict[str, Any], 
                               format_config: Dict[str, Any],
                               strategy: str) -> str:
        """Build a detailed generation prompt based on strategy and requirements."""
        
        # Extract relevant information
        brand_guidelines = campaign_brief.get("brand_guidelines", {})
        creative_reqs = campaign_brief.get("creative_requirements", {})
        message = campaign_brief.get("campaign_message", {})
        audience = campaign_brief.get("target_audience", {}).get("primary", {})
        
        # Prepare template variables
        template_vars = {
            "product_name": product["name"],
            "category": product["category"],
            "benefits": ", ".join(product.get("key_benefits", [])),
            "audience": audience.get("demographics", "health-conscious consumers"),
            "region": region["region"],
            "brand_colors": ", ".join(brand_guidelines.get("color_palette", {}).get("primary", [])),
            "brand_voice": message.get("brand_voice", "confident and approachable"),
            "style_preferences": creative_reqs.get("style_preferences", "bright and vibrant"),
            "avoid_elements": ", ".join(creative_reqs.get("avoid", [])),
            "format_description": format_config["description"],
            "key_message": message.get("primary_headline", ""),
            "tone": message.get("tone", "energetic and inspiring"),
            "lifestyle_context": self._get_lifestyle_context(region, audience),
            "usage_scenario": self._get_usage_scenario(product, audience),
            "brand_values": self._extract_brand_values(campaign_brief)
        }
        
        # Select and format template
        template = self.prompt_templates.get(strategy, self.prompt_templates["product_hero"])
        full_prompt = template.format(**template_vars)
        
        # For DALL-E 2, truncate to stay under 1000 character limit
        if len(full_prompt) > 900:  # Leave some buffer
            # Create a shorter prompt for DALL-E 2
            short_prompt = f"Professional product photography of {template_vars['product_name']}, {template_vars['category']}. {template_vars['style_preferences']}. Bright lighting, clean background, {template_vars['brand_voice']} mood. Marketing quality, space for text overlay."
            final_prompt = short_prompt
            logger.info(f"Shortened prompt for DALL-E 2: {len(final_prompt)} characters")
        else:
            final_prompt = full_prompt
        
        logger.debug(f"Generated prompt for {strategy}: {final_prompt[:200]}...")
        return final_prompt
    
    def _get_lifestyle_context(self, region: Dict[str, Any], audience: Dict[str, Any]) -> str:
        """Generate appropriate lifestyle context based on region and audience."""
        
        regional_contexts = {
            "North America": "Modern urban environment, coffee shop, gym, outdoor park",
            "Europe": "Sophisticated urban setting, café culture, cycling, outdoor markets",
            "Asia Pacific": "Dynamic city environment, technology integration, wellness focus",
            "Latin America": "Vibrant community setting, family gatherings, outdoor activities"
        }
        
        return regional_contexts.get(region["region"], "Contemporary lifestyle setting")
    
    def _get_usage_scenario(self, product: Dict[str, Any], audience: Dict[str, Any]) -> str:
        """Generate product usage scenario based on product type and audience."""
        
        category_scenarios = {
            "Beverages": "Refreshing moment during workout, office break, outdoor activity",
            "Snacks": "Pre-workout fuel, office snack, on-the-go energy boost",
            "Health & Wellness": "Morning routine, post-workout recovery, daily wellness ritual"
        }
        
        return category_scenarios.get(product["category"], "Daily lifestyle integration")
    
    def _extract_brand_values(self, campaign_brief: Dict[str, Any]) -> str:
        """Extract brand values from campaign brief."""
        
        message = campaign_brief.get("campaign_message", {})
        key_messages = message.get("key_messages", [])
        
        if key_messages:
            return ", ".join(key_messages)
        else:
            return "Quality, authenticity, customer-focused"
    
    def _generate_with_retry(self, prompt: str, format_config: Dict[str, Any]) -> Optional[Image.Image]:
        """Generate image with rate limiting and fallback handling."""
        
        # Simplified for OpenAI-only demo
        if self.openai_client:
            # Check rate limits
            if not self._check_rate_limit("openai"):
                wait_time = self._wait_for_rate_limit("openai")
                if wait_time > 0:
                    logger.warning(f"Rate limit hit, waiting {wait_time:.1f}s")
                    if wait_time < 30:  # Only wait if reasonable
                        time.sleep(wait_time)
                    else:
                        logger.info("Skipping due to long wait time")
                        return None
            
            return self._generate_with_openai(prompt, format_config)
        
        logger.error("All generation services failed or unavailable")
        return None
    
    
    
    
    def _generate_with_openai(self, prompt: str, format_config: Dict[str, Any]) -> Optional[Image.Image]:
        """Generate image using OpenAI DALL-E."""
        
        max_retries = self.genai_config.get("services", {}).get("openai", {}).get("max_retries", 3)
        
        for attempt in range(max_retries):
            try:
                logger.info(f"OpenAI DALL-E attempt {attempt + 1}/{max_retries}")
                
                # Use cheaper DALL-E 2 model for demo
                response = self.openai_client.images.generate(
                    model="dall-e-2",
                    prompt=prompt,
                    size=self._get_dall_e_size(format_config),
                    n=1
                )
                
                # Download and convert to PIL Image
                image_url = response.data[0].url
                image_response = requests.get(image_url, timeout=30)
                image_response.raise_for_status()
                
                image = Image.open(BytesIO(image_response.content))
                
                # Resize to exact format requirements if needed
                target_size = (format_config["width"], format_config["height"])
                if image.size != target_size:
                    image = image.resize(target_size, Image.Resampling.LANCZOS)
                
                # Track cost for budget monitoring
                self.cost_tracker.track_openai_image("dall-e-2", self._get_dall_e_size(format_config), True)
                
                logger.info(f"OpenAI image generated successfully: {image.size}")
                return image
                
            except Exception as e:
                logger.warning(f"OpenAI attempt {attempt + 1} failed: {str(e)}")
                
                if attempt < max_retries - 1:
                    wait_time = 2 ** attempt
                    time.sleep(wait_time)
        
        return None
    
    def _get_dall_e_size(self, format_config: Dict[str, Any]) -> str:
        """Convert format config to DALL-E supported size string."""
        
        width = format_config["width"]
        height = format_config["height"]
        
        # Map to closest DALL-E supported sizes
        if width == height:  # Square
            return "1024x1024"
        elif width > height:  # Landscape
            return "1792x1024"
        else:  # Portrait
            return "1024x1792"
    
    def enhance_existing_image(self, image_path: str, enhancement_prompt: str) -> Optional[Image.Image]:
        """Enhance an existing image using AI (placeholder for future implementation)."""
        
        logger.info(f"Enhancing existing image: {image_path}")
        
        # For now, just load and return the existing image
        # In a full implementation, this would use image-to-image generation
        try:
            image = Image.open(image_path)
            logger.info(f"Loaded existing image: {image.size}")
            return image
        except Exception as e:
            logger.error(f"Failed to load existing image: {e}")
            return None
    
    def validate_generated_image(self, image: Image.Image, requirements: Dict[str, Any]) -> Dict[str, Any]:
        """Validate generated image against requirements."""
        
        validation_result = {
            "passed": True,
            "issues": [],
            "scores": {}
        }
        
        # Basic technical validation
        if image.size[0] < 512 or image.size[1] < 512:
            validation_result["passed"] = False
            validation_result["issues"].append("Image resolution too low")
        
        # Color analysis (placeholder)
        validation_result["scores"]["color_vibrancy"] = 0.8
        validation_result["scores"]["composition"] = 0.9
        
        logger.info(f"Image validation result: {validation_result}")
        return validation_result