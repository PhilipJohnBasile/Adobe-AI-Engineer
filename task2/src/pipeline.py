#!/usr/bin/env python3
"""
Creative Automation Pipeline - Main Entry Point

This module orchestrates the entire creative generation pipeline from campaign brief
to final branded assets across multiple formats and regions.
"""

import sys
import json
import yaml
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime
import argparse

# Internal modules
from generators.image_generator import ImageGenerator
from generators.text_generator import TextGenerator
from processors.asset_processor import AssetProcessor
from validators.brand_validator import BrandValidator
from validators.compliance_validator import ComplianceValidator

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('pipeline.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)


class CreativeAutomationPipeline:
    """Main pipeline orchestrator for creative automation."""
    
    def __init__(self, config_path: str = "config/config.yaml"):
        """Initialize the pipeline with configuration."""
        self.config = self._load_config(config_path)
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Initialize components
        self.image_generator = ImageGenerator(self.config)
        self.text_generator = TextGenerator(self.config)
        self.asset_processor = AssetProcessor(self.config)
        self.brand_validator = BrandValidator(self.config)
        self.compliance_validator = ComplianceValidator(self.config)
        
        # Create output directory
        self.output_base = Path("output")
        self.output_base.mkdir(exist_ok=True)
        
        logger.info("Creative Automation Pipeline initialized")
    
    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """Load configuration from YAML file."""
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
                logger.info(f"Configuration loaded from {config_path}")
                return config
        except FileNotFoundError:
            logger.error(f"Configuration file {config_path} not found")
            raise
        except yaml.YAMLError as e:
            logger.error(f"Error parsing configuration: {e}")
            raise
    
    def process_campaign(self, brief_path: str) -> Dict[str, Any]:
        """Process a complete campaign from brief to final assets."""
        logger.info(f"Starting campaign processing for: {brief_path}")
        
        # Load campaign brief
        campaign_brief = self._load_campaign_brief(brief_path)
        
        # Initialize results tracking
        results = {
            "campaign_id": campaign_brief.get("campaign_id"),
            "processing_timestamp": self.timestamp,
            "products_processed": [],
            "total_assets_generated": 0,
            "validation_results": {},
            "errors": []
        }
        
        try:
            # Process each product in the campaign
            for product in campaign_brief.get("products", []):
                logger.info(f"Processing product: {product['name']}")
                
                product_results = self._process_product(
                    product, 
                    campaign_brief,
                    results
                )
                results["products_processed"].append(product_results)
            
            # Generate campaign summary report
            self._generate_campaign_report(campaign_brief, results)
            
            logger.info("Campaign processing completed successfully")
            return results
            
        except Exception as e:
            error_msg = f"Campaign processing failed: {str(e)}"
            logger.error(error_msg)
            results["errors"].append(error_msg)
            return results
    
    def _load_campaign_brief(self, brief_path: str) -> Dict[str, Any]:
        """Load and validate campaign brief."""
        try:
            with open(brief_path, 'r', encoding='utf-8') as f:
                if brief_path.endswith('.json'):
                    brief = json.load(f)
                elif brief_path.endswith('.yaml') or brief_path.endswith('.yml'):
                    brief = yaml.safe_load(f)
                else:
                    raise ValueError("Brief must be JSON or YAML format")
                
                logger.info(f"Campaign brief loaded: {brief.get('campaign_name', 'Unknown')}")
                return brief
                
        except Exception as e:
            logger.error(f"Failed to load campaign brief: {e}")
            raise
    
    def _process_product(self, product: Dict[str, Any], campaign_brief: Dict[str, Any], results: Dict[str, Any]) -> Dict[str, Any]:
        """Process a single product across all formats and regions."""
        
        product_results = {
            "product_id": product["id"],
            "product_name": product["name"],
            "assets_generated": [],
            "validation_passed": True,
            "errors": []
        }
        
        # Create product output directory
        product_dir = self.output_base / product["id"]
        product_dir.mkdir(exist_ok=True)
        
        # Get aspect ratios to generate
        aspect_ratios = self.config["aspect_ratios"]
        
        # Process each target region
        for region in campaign_brief.get("target_regions", []):
            logger.info(f"Processing region: {region['region']}")
            
            # Process each aspect ratio
            for format_name, format_config in aspect_ratios.items():
                try:
                    asset_result = self._generate_single_asset(
                        product,
                        campaign_brief,
                        region,
                        format_name,
                        format_config,
                        product_dir
                    )
                    
                    if asset_result:
                        product_results["assets_generated"].append(asset_result)
                        results["total_assets_generated"] += 1
                        
                except Exception as e:
                    error_msg = f"Failed to generate {format_name} for {region['region']}: {str(e)}"
                    logger.error(error_msg)
                    product_results["errors"].append(error_msg)
                    product_results["validation_passed"] = False
        
        return product_results
    
    def _generate_single_asset(self, 
                             product: Dict[str, Any], 
                             campaign_brief: Dict[str, Any],
                             region: Dict[str, Any],
                             format_name: str,
                             format_config: Dict[str, Any],
                             product_dir: Path) -> Optional[Dict[str, Any]]:
        """Generate a single creative asset."""
        
        logger.info(f"Generating {format_name} asset for {region['region']}")
        
        # Check for existing assets first
        existing_asset = self._check_existing_assets(product, format_name, region)
        if existing_asset:
            logger.info(f"Using existing asset: {existing_asset}")
            # Process existing asset (resize, add text overlay, etc.)
            processed_asset = self.asset_processor.process_existing_asset(
                existing_asset, format_config, product, campaign_brief, region
            )
        else:
            # Generate new asset using GenAI
            logger.info("No existing asset found, generating new image")
            generated_image = self.image_generator.generate_product_image(
                product, campaign_brief, region, format_config
            )
            
            # Process generated image (add text, branding, etc.)
            processed_asset = self.asset_processor.process_generated_asset(
                generated_image, format_config, product, campaign_brief, region
            )
        
        if not processed_asset:
            logger.error("Failed to process asset")
            return None
        
        # Validate brand compliance
        brand_validation = self.brand_validator.validate_asset(
            processed_asset, campaign_brief.get("brand_guidelines", {})
        )
        
        # Validate content compliance
        compliance_validation = self.compliance_validator.validate_content(
            processed_asset, campaign_brief.get("compliance_requirements", {})
        )
        
        # Save final asset if validation passes
        if brand_validation["passed"] and compliance_validation["passed"]:
            final_path = self._save_final_asset(
                processed_asset, product, region, format_name, product_dir
            )
            
            return {
                "asset_path": str(final_path),
                "format": format_name,
                "region": region["region"],
                "dimensions": f"{format_config['width']}x{format_config['height']}",
                "brand_validation": brand_validation,
                "compliance_validation": compliance_validation,
                "generation_method": "existing" if existing_asset else "generated"
            }
        else:
            logger.warning(f"Asset failed validation for {format_name} in {region['region']}")
            return None
    
    def _check_existing_assets(self, product: Dict[str, Any], format_name: str, region: Dict[str, Any]) -> Optional[str]:
        """Check if suitable existing assets are available."""
        
        asset_dir = Path("assets") / product["id"]
        if not asset_dir.exists():
            return None
        
        # Look for existing assets that might be suitable
        for asset_file in product.get("existing_assets", []):
            asset_path = asset_dir / asset_file
            if asset_path.exists():
                logger.info(f"Found existing asset: {asset_path}")
                return str(asset_path)
        
        return None
    
    def _save_final_asset(self, 
                         asset: Any,
                         product: Dict[str, Any], 
                         region: Dict[str, Any],
                         format_name: str,
                         product_dir: Path) -> Path:
        """Save the final processed asset."""
        
        filename = f"{product['id']}_{format_name}_{region['region']}_{self.timestamp}.png"
        final_path = product_dir / filename
        
        # Save the image
        if hasattr(asset, 'save'):
            asset.save(final_path, 'PNG')
        else:
            # Handle other asset types
            with open(final_path, 'wb') as f:
                f.write(asset)
        
        logger.info(f"Asset saved: {final_path}")
        return final_path
    
    def _generate_campaign_report(self, campaign_brief: Dict[str, Any], results: Dict[str, Any]):
        """Generate a comprehensive campaign report."""
        
        report = {
            "campaign_summary": {
                "campaign_id": campaign_brief.get("campaign_id"),
                "campaign_name": campaign_brief.get("campaign_name"),
                "processing_date": self.timestamp,
                "total_products": len(campaign_brief.get("products", [])),
                "total_regions": len(campaign_brief.get("target_regions", [])),
                "total_assets_generated": results["total_assets_generated"]
            },
            "generation_results": results["products_processed"],
            "validation_summary": results["validation_results"],
            "errors": results["errors"]
        }
        
        # Save report
        report_path = self.output_base / f"campaign_report_{self.timestamp}.json"
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Campaign report saved: {report_path}")


def main():
    """Main entry point for the pipeline."""
    parser = argparse.ArgumentParser(description='Creative Automation Pipeline')
    parser.add_argument('brief_path', help='Path to campaign brief file (JSON or YAML)')
    parser.add_argument('--config', default='config/config.yaml', help='Path to configuration file')
    parser.add_argument('--debug', action='store_true', help='Enable debug logging')
    
    args = parser.parse_args()
    
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
    
    try:
        # Initialize pipeline
        pipeline = CreativeAutomationPipeline(args.config)
        
        # Process campaign
        results = pipeline.process_campaign(args.brief_path)
        
        # Print summary
        print(f"\n{'='*60}")
        print("CAMPAIGN PROCESSING COMPLETE")
        print(f"{'='*60}")
        print(f"Campaign ID: {results.get('campaign_id', 'Unknown')}")
        print(f"Total Assets Generated: {results['total_assets_generated']}")
        print(f"Products Processed: {len(results['products_processed'])}")
        
        if results['errors']:
            print(f"Errors Encountered: {len(results['errors'])}")
            for error in results['errors']:
                print(f"  - {error}")
        
        print(f"\nOutput saved to: {Path('output').absolute()}")
        print(f"{'='*60}\n")
        
    except Exception as e:
        logger.error(f"Pipeline execution failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()