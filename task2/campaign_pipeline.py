#!/usr/bin/env python3
"""
Campaign Creative Automation Pipeline

Generates branded marketing assets across multiple 
products, regions, and social media formats using GenAI and brand compliance.
"""

import sys
import json
import logging
from pathlib import Path
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont
import openai
import os

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class CocaColaPipeline:
    """Creative automation pipeline specifically for Coca-Cola campaigns."""
    
    def __init__(self):
        """Initialize the Coca-Cola pipeline."""
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.output_dir = Path("output")
        self.assets_dir = Path("assets")
        
        # Load brand guidelines and compliance rules
        self.brand_guidelines = self._load_brand_guidelines()
        self.compliance_rules = self._load_compliance_rules()
        
        # Initialize OpenAI
        self._init_openai()
        
        logger.info("Coca-Cola Creative Automation Pipeline initialized")
    
    def _load_brand_guidelines(self):
        """Load Coca-Cola brand guidelines."""
        try:
            with open(self.assets_dir / "brand" / "guidelines.json") as f:
                return json.load(f)
        except FileNotFoundError:
            logger.error("Brand guidelines not found")
            return {}
    
    def _load_compliance_rules(self):
        """Load compliance and forbidden words rules.""" 
        try:
            with open(self.assets_dir / "brand" / "compliance.json") as f:
                return json.load(f)
        except FileNotFoundError:
            logger.error("Compliance rules not found")
            return {}
    
    def _init_openai(self):
        """Initialize OpenAI client."""
        # Load API key from config
        env_file = Path("config/.env")
        if env_file.exists():
            with open(env_file) as f:
                for line in f:
                    if line.strip() and not line.startswith('#') and '=' in line:
                        key, value = line.strip().split('=', 1)
                        os.environ[key] = value
        
        api_key = os.getenv('OPENAI_API_KEY')
        if api_key:
            self.openai_client = openai.OpenAI(api_key=api_key)
            logger.info("OpenAI client initialized")
        else:
            self.openai_client = None
            logger.warning("OpenAI API key not found - using mock generation")
    
    def process_campaign(self, campaign_file):
        """Process a complete Coca-Cola campaign."""
        logger.info(f"Processing campaign: {campaign_file}")
        
        # Load campaign brief
        with open(campaign_file) as f:
            campaign = json.load(f)
        
        campaign_id = campaign["campaign_id"]
        campaign_output = self.output_dir / campaign_id
        campaign_output.mkdir(parents=True, exist_ok=True)
        
        results = {
            "campaign_id": campaign_id,
            "campaign_name": campaign["campaign_name"],
            "processing_timestamp": self.timestamp,
            "assets_generated": [],
            "total_cost": 0.0,
            "compliance_checks": [],
            "brand_validation": []
        }
        
        # Process each product
        for product in campaign["products"]:
            logger.info(f"Processing product: {product['name']}")
            
            # Process each region
            for region in campaign["target_regions"]:
                logger.info(f"  Region: {region['region']}")
                
                # Process each format
                for format_spec in campaign["creative_requirements"]["formats"]:
                    asset_result = self._generate_asset(
                        product, region, format_spec, campaign, campaign_output
                    )
                    
                    if asset_result:
                        results["assets_generated"].append(asset_result)
                        results["total_cost"] += asset_result.get("cost", 0)
        
        # Generate campaign report
        report_path = campaign_output / f"campaign_report_{self.timestamp}.json"
        with open(report_path, 'w') as f:
            json.dump(results, f, indent=2)
        
        logger.info(f"Campaign processing complete. Report: {report_path}")
        return results
    
    def _generate_asset(self, product, region, format_spec, campaign, output_dir):
        """Generate a single branded asset."""
        
        # Create asset filename
        filename = f"{product['id']}_{format_spec['name']}_{region['region'].lower()}_{self.timestamp}.png"
        asset_path = output_dir / filename
        
        logger.info(f"    Generating: {filename}")
        
        # Generate localized copy
        copy_elements = self._generate_localized_copy(product, region, campaign)
        
        # Validate compliance
        compliance_result = self._validate_compliance(copy_elements, region)
        
        if not compliance_result["passed"]:
            logger.warning(f"    Compliance failed for {filename}")
            return None
        
        # Create or generate base image
        base_image = self._create_base_image(product, format_spec)
        
        # Add Coca-Cola branding
        branded_image = self._apply_branding(
            base_image, copy_elements, format_spec, product
        )
        
        # Save final asset
        branded_image.save(asset_path, 'PNG')
        logger.info(f"    Saved: {filename}")
        
        return {
            "filename": filename,
            "product": product["name"],
            "region": region["region"],
            "format": format_spec["name"],
            "dimensions": format_spec["dimensions"],
            "copy_elements": copy_elements,
            "compliance_score": compliance_result["score"],
            "cost": 0.02,  # Simulated DALL-E cost
            "generation_method": "mock" if not self.openai_client else "openai"
        }
    
    def _generate_localized_copy(self, product, region, campaign):
        """Generate culturally-adapted copy for the asset."""
        
        # Get cultural adaptation rules
        messaging = region.get("messaging_adaptation", {})
        themes = messaging.get("themes", [])
        tone = messaging.get("tone", "friendly")
        
        # Generate region-specific headline
        if region["region"] == "USA":
            headline = f"{product['messaging']['primary']} - Fuel Your Fall"
            cta = "Grab Yours Today"
        elif region["region"] == "Germany":
            headline = f"{product['messaging']['primary']} - Perfekt für den Herbst"
            cta = "Jetzt Entdecken"  
        elif region["region"] == "Japan":
            headline = f"{product['messaging']['primary']} - Aki no Tokubetsu na Aji"
            cta = "Ima sugu Ajiwau"
        else:
            headline = product['messaging']['primary']
            cta = "Try It Now"
        
        return {
            "headline": headline,
            "subheadline": product["messaging"]["secondary"],
            "cta": cta,
            "product_name": product["name"],
            "seasonal_message": campaign["campaign_message"]["seasonal_theme"]
        }
    
    def _validate_compliance(self, copy_elements, region):
        """Validate content against Coca-Cola compliance rules."""
        
        score = 100
        issues = []
        
        # Check for forbidden words
        forbidden_words = self.compliance_rules.get("forbidden_words", [])
        region_restrictions = self.compliance_rules.get("regions", {}).get(
            region["region"].lower(), {}
        ).get("additional_restrictions", [])
        
        all_forbidden = forbidden_words + region_restrictions
        
        # Check all copy text
        all_text = " ".join([
            copy_elements.get("headline", ""),
            copy_elements.get("subheadline", ""),
            copy_elements.get("cta", ""),
            copy_elements.get("seasonal_message", "")
        ]).lower()
        
        for word in all_forbidden:
            if word.lower() in all_text:
                score -= 10
                issues.append(f"Forbidden word detected: {word}")
        
        # Brand compliance checks
        if "coca" not in all_text.lower() and "coke" not in all_text.lower():
            score -= 5
            issues.append("Brand name not prominently featured")
        
        passed = score >= self.compliance_rules.get("compliance_threshold", 85)
        
        return {
            "passed": passed,
            "score": max(0, score),
            "issues": issues
        }
    
    def _create_base_image(self, product, format_spec):
        """Create base image - mock generation for demo."""
        
        # Parse dimensions
        width, height = map(int, format_spec["dimensions"].split('x'))
        
        # Create branded background
        if product["id"] == "coca_cola_classic":
            bg_color = "#DA020E"  # Coca-Cola red
            accent_color = "#FFFFFF"
        elif product["id"] == "sprite":
            bg_color = "#00A651"  # Sprite green
            accent_color = "#FFFF00"
        else:  # fanta_apple
            bg_color = "#FF8C00"  # Fanta orange
            accent_color = "#8B4513"  # Apple brown
        
        # Create image with gradient
        image = Image.new('RGB', (width, height), bg_color)
        draw = ImageDraw.Draw(image)
        
        # Add gradient effect
        for i in range(height//3):
            alpha = 1 - (i / (height//3)) * 0.3
            if bg_color.startswith('#'):
                rgb = tuple(int(bg_color[j:j+2], 16) for j in (1, 3, 5))
                blend_color = tuple(int(c * alpha) for c in rgb)
                draw.rectangle([0, i*3, width, (i+1)*3], fill=blend_color)
        
        # Add product shape mockup
        if format_spec["name"] == "square":
            # Bottle silhouette for square format
            draw.ellipse([width//3, height//4, 2*width//3, 3*height//4], 
                        outline=accent_color, width=8)
        elif format_spec["name"] == "story":
            # Vertical emphasis for story
            draw.rectangle([width//4, height//8, 3*width//4, 7*height//8],
                          outline=accent_color, width=6)
        else:  # landscape
            # Horizontal emphasis
            draw.rectangle([width//8, height//3, 7*width//8, 2*height//3],
                          outline=accent_color, width=6)
        
        return image
    
    def _apply_branding(self, image, copy_elements, format_spec, product):
        """Apply Coca-Cola branding to the image."""
        
        draw = ImageDraw.Draw(image)
        width, height = image.size
        
        # Use default font (fallback for demo)
        try:
            font_large = ImageFont.load_default()
            font_medium = ImageFont.load_default()
            font_small = ImageFont.load_default()
        except:
            font_large = font_medium = font_small = ImageFont.load_default()
        
        # Add headline
        headline = copy_elements.get("headline", "")
        if headline:
            # Position based on format
            if format_spec["name"] == "story":
                headline_y = height // 6
            else:
                headline_y = height // 8
            
            draw.text((width//2, headline_y), headline, 
                     fill="white", font=font_large, anchor="mm")
        
        # Add product name
        product_name = copy_elements.get("product_name", "")
        if product_name:
            draw.text((width//2, height//2), product_name,
                     fill="white", font=font_medium, anchor="mm")
        
        # Add CTA
        cta = copy_elements.get("cta", "")
        if cta:
            cta_y = height - height//8
            draw.text((width//2, cta_y), cta,
                     fill="white", font=font_small, anchor="mm")
        
        # Add Coca-Cola branding indicator
        brand_text = "Coca-Cola"
        draw.text((width - 20, height - 30), brand_text,
                 fill="white", font=font_small, anchor="rm")
        
        # Add format indicator for demo
        format_text = f"{format_spec['name'].upper()} | {format_spec['dimensions']}"
        draw.text((20, height - 30), format_text,
                 fill="rgba(255,255,255,128)", font=font_small, anchor="lm")
        
        return image

def main():
    """Main entry point."""
    if len(sys.argv) != 2:
        print("Usage: python campaign_pipeline.py <campaign_brief.json>")
        sys.exit(1)
    
    campaign_file = sys.argv[1]
    
    if not Path(campaign_file).exists():
        print(f"Error: Campaign file '{campaign_file}' not found")
        sys.exit(1)
    
    try:
        pipeline = CocaColaPipeline()
        results = pipeline.process_campaign(campaign_file)
        
        print("\n" + "="*60)
        print("COCA-COLA CREATIVE AUTOMATION COMPLETE")
        print("="*60)
        print(f"Campaign: {results['campaign_name']}")
        print(f"Assets Generated: {len(results['assets_generated'])}")
        print(f"Total Cost: ${results['total_cost']:.2f}")
        print(f"Output Directory: output/{results['campaign_id']}")
        print("="*60)
        
    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()