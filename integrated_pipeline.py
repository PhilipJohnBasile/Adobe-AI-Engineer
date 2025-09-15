#!/usr/bin/env python3
"""
Integrated Campaign Pipeline for React App + Python AI Generation
Works with campaigns created in the React Router app
"""

import sys
import json
import logging
from pathlib import Path
from datetime import datetime
import os

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class IntegratedPipeline:
    """Pipeline that integrates with React campaign manager."""
    
    def __init__(self):
        """Initialize the integrated pipeline."""
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.output_dir = Path("output")
        self.campaigns_dir = Path("campaigns")  # React app saves here
        self.assets_dir = Path("campaign-manager/public/assets")
        
        # Create output directory if needed
        self.output_dir.mkdir(exist_ok=True)
        
        logger.info("Integrated Campaign Pipeline initialized")
    
    def process_campaign_from_react(self, campaign_id):
        """Process a campaign created by the React app."""
        campaign_file = self.campaigns_dir / f"{campaign_id}.json"
        
        if not campaign_file.exists():
            logger.error(f"Campaign file not found: {campaign_file}")
            return None
        
        logger.info(f"Processing campaign from React app: {campaign_id}")
        
        with open(campaign_file) as f:
            campaign = json.load(f)
        
        # Generate assets for the campaign
        assets = self._generate_campaign_assets(campaign)
        
        return {
            "campaign_id": campaign_id,
            "assets": assets,
            "timestamp": self.timestamp
        }
    
    def _generate_campaign_assets(self, campaign):
        """Generate AI assets for a campaign."""
        assets = []
        
        # Process each product in the campaign
        for product in campaign.get('products', []):
            # Use 'id' field, fallback to 'product_id' or 'UNKNOWN'
            product_id = product.get('id') or product.get('product_id', 'UNKNOWN')
            
            # Generate assets for each region
            for region_data in campaign.get('target_regions', [{'region': 'Global'}]):
                # Extract region name from object or use as string
                if isinstance(region_data, dict):
                    region = region_data.get('region', 'Global')
                else:
                    region = str(region_data)
                
                # Generate different format assets
                for format_type in ['square', 'story', 'landscape']:
                    asset = self._create_asset(
                        campaign, 
                        product, 
                        region, 
                        format_type
                    )
                    assets.append(asset)
        
        logger.info(f"Generated {len(assets)} assets for campaign")
        return assets
    
    def _create_asset(self, campaign, product, region, format_type):
        """Create a single asset (mock for now, would call AI here)."""
        
        # Get product ID from either 'id' or 'product_id' field
        product_id = product.get('id') or product.get('product_id', 'UNKNOWN')
        
        # Asset filename
        filename = f"{product_id}_{format_type}_{region}_{self.timestamp}.json"
        filepath = self.output_dir / filename
        
        # Asset metadata (in production, this would include AI-generated content)
        asset_data = {
            "campaign_id": campaign.get('campaign_id'),
            "campaign_name": campaign.get('campaign_name'),
            "product": product,
            "region": region,
            "format": format_type,
            "dimensions": self._get_dimensions(format_type),
            "generated_at": self.timestamp,
            "content": {
                "headline": campaign.get('campaign_message', {}).get('primary_headline'),
                "subheadline": campaign.get('campaign_message', {}).get('secondary_headline'),
                "call_to_action": "Shop Now",
                "brand_voice": campaign.get('campaign_message', {}).get('brand_voice')
            },
            "status": "generated",
            "ai_provider": "mock_generator"
        }
        
        # Save asset metadata
        with open(filepath, 'w') as f:
            json.dump(asset_data, f, indent=2)
        
        logger.info(f"Created asset: {filename}")
        
        return {
            "filename": filename,
            "path": str(filepath),
            "type": format_type,
            "region": region,
            "product_id": product_id
        }
    
    def _get_dimensions(self, format_type):
        """Get dimensions for different format types."""
        dimensions = {
            "square": {"width": 1080, "height": 1080},
            "story": {"width": 1080, "height": 1920},
            "landscape": {"width": 1920, "height": 1080}
        }
        return dimensions.get(format_type, {"width": 1080, "height": 1080})

def main():
    """Main entry point for the integrated pipeline."""
    if len(sys.argv) < 2:
        print("Usage: python integrated_pipeline.py <campaign_file_or_id>")
        sys.exit(1)
    
    campaign_input = sys.argv[1]
    
    # Initialize pipeline
    pipeline = IntegratedPipeline()
    
    # Check if input is a file path or just an ID
    if campaign_input.endswith('.json'):
        # Full file path provided
        campaign_path = Path(campaign_input)
        campaign_id = campaign_path.stem
    else:
        # Just the campaign ID provided
        campaign_id = campaign_input
    
    # Process the campaign
    result = pipeline.process_campaign_from_react(campaign_id)
    
    if result:
        print(json.dumps(result, indent=2))
        logger.info(f"Successfully processed campaign: {campaign_id}")
    else:
        logger.error(f"Failed to process campaign: {campaign_id}")
        sys.exit(1)

if __name__ == "__main__":
    main()