"""
Pipeline Orchestrator for API Integration
Coordinates the complete creative automation workflow
"""

import asyncio
from typing import Dict, Any, Optional
import json
import yaml
import tempfile
import os
from datetime import datetime

from .asset_manager import AssetManager
from .image_generator import ImageGenerator
from .creative_composer import CreativeComposer
from .compliance_checker import ComplianceChecker
from .localization import LocalizationManager


class PipelineOrchestrator:
    """Orchestrates the complete creative automation pipeline"""
    
    def __init__(self):
        self.asset_manager = AssetManager()
        self.image_generator = ImageGenerator()
        self.creative_composer = CreativeComposer()
        self.compliance_checker = ComplianceChecker()
        self.localizer = LocalizationManager()
    
    def validate_campaign_brief(self, campaign_brief: Dict[str, Any]) -> Dict[str, Any]:
        """Validate campaign brief structure and content"""
        errors = []
        warnings = []
        suggestions = []
        
        try:
            # Check required top-level structure
            if "campaign_brief" not in campaign_brief:
                errors.append("Missing 'campaign_brief' root key")
                return {"valid": False, "errors": errors}
            
            brief = campaign_brief["campaign_brief"]
            
            # Required fields validation
            required_fields = ["campaign_id", "products", "target_region"]
            for field in required_fields:
                if field not in brief:
                    errors.append(f"Missing required field: {field}")
            
            # Products validation
            if "products" in brief:
                if not isinstance(brief["products"], list) or len(brief["products"]) == 0:
                    errors.append("Products must be a non-empty list")
                else:
                    for i, product in enumerate(brief["products"]):
                        if not isinstance(product, dict):
                            errors.append(f"Product {i+1} must be an object")
                            continue
                        
                        if "name" not in product:
                            errors.append(f"Product {i+1} missing 'name' field")
                        if "description" not in product:
                            warnings.append(f"Product {i+1} missing 'description' field")
            
            # Output requirements validation
            if "output_requirements" in brief:
                output_req = brief["output_requirements"]
                if "aspect_ratios" in output_req:
                    valid_ratios = ["1:1", "9:16", "16:9"]
                    for ratio in output_req["aspect_ratios"]:
                        if ratio not in valid_ratios:
                            warnings.append(f"Unusual aspect ratio: {ratio}")
            
            # Brand guidelines validation
            if "brand_guidelines" in brief:
                brand = brief["brand_guidelines"]
                if "primary_colors" in brand:
                    if not isinstance(brand["primary_colors"], list):
                        warnings.append("Primary colors should be a list")
            
            # Suggestions for optimization
            if "target_audience" not in brief:
                suggestions.append("Add target_audience for better AI generation")
            if "campaign_message" not in brief:
                suggestions.append("Add campaign_message for text overlay")
            
            return {
                "valid": len(errors) == 0,
                "errors": errors,
                "warnings": warnings,
                "suggestions": suggestions
            }
            
        except Exception as e:
            return {
                "valid": False,
                "errors": [f"Validation error: {str(e)}"]
            }
    
    async def process_campaign_async(
        self,
        campaign_brief: Dict[str, Any],
        assets_dir: str = "assets",
        output_dir: str = "output",
        force_generate: bool = False,
        skip_compliance: bool = False,
        localize_for: Optional[str] = None
    ) -> Dict[str, Any]:
        """Asynchronously process a complete campaign"""
        
        # Save campaign brief to temporary file for processing
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(campaign_brief, f)
            brief_path = f.name
        
        try:
            # Import main processing function
            from main import process_campaign_brief
            
            # Process the campaign
            result = await asyncio.get_event_loop().run_in_executor(
                None,
                process_campaign_brief,
                brief_path,
                assets_dir,
                output_dir,
                force_generate,
                skip_compliance,
                localize_for,
                False  # verbose
            )
            
            # Add metadata
            result.update({
                "processed_at": datetime.now().isoformat(),
                "processing_mode": "api",
                "output_path": os.path.join(output_dir, campaign_brief["campaign_brief"]["campaign_id"])
            })
            
            return result
            
        finally:
            # Cleanup temporary file
            if os.path.exists(brief_path):
                os.unlink(brief_path)
    
    def process_campaign_sync(
        self,
        campaign_brief: Dict[str, Any],
        assets_dir: str = "assets",
        output_dir: str = "output",
        force_generate: bool = False,
        skip_compliance: bool = False,
        localize_for: Optional[str] = None
    ) -> Dict[str, Any]:
        """Synchronously process a complete campaign"""
        
        brief = campaign_brief["campaign_brief"]
        campaign_id = brief["campaign_id"]
        
        result = {
            "campaign_id": campaign_id,
            "status": "processing",
            "assets_generated": 0,
            "errors": [],
            "warnings": []
        }
        
        try:
            # 1. Localization (if requested)
            if localize_for:
                brief = self.localizer.localize_campaign(brief, localize_for)
                result["localized_for"] = localize_for
            
            # 2. Compliance checking (unless skipped)
            if not skip_compliance:
                compliance_result = self.compliance_checker.check_campaign_brief({"campaign_brief": brief})
                if compliance_result["critical"]:
                    result["status"] = "failed"
                    result["errors"] = compliance_result["critical"]
                    return result
                result["compliance_warnings"] = compliance_result["warnings"]
            
            # 3. Asset discovery and generation
            products = brief["products"]
            aspect_ratios = brief.get("output_requirements", {}).get("aspect_ratios", ["1:1", "9:16", "16:9"])
            
            campaign_output_dir = os.path.join(output_dir, campaign_id)
            os.makedirs(campaign_output_dir, exist_ok=True)
            
            for product in products:
                product_name = product["name"]
                
                # Check for existing assets
                existing_asset = self.asset_manager.find_existing_asset(product_name, assets_dir)
                
                if existing_asset and not force_generate:
                    base_image_path = existing_asset
                else:
                    # Generate new asset
                    base_image_path = self.image_generator.generate_product_image(
                        product_name,
                        product["description"],
                        product.get("target_keywords", [])
                    )
                
                # Generate creatives for each aspect ratio
                product_output_dir = os.path.join(campaign_output_dir, product_name.replace(" ", "_"))
                os.makedirs(product_output_dir, exist_ok=True)
                
                for ratio in aspect_ratios:
                    output_path = os.path.join(product_output_dir, f"{ratio.replace(':', 'x')}.jpg")
                    
                    self.creative_composer.create_creative(
                        base_image_path,
                        output_path,
                        ratio,
                        brief.get("campaign_message", ""),
                        brief.get("brand_guidelines", {})
                    )
                    
                    result["assets_generated"] += 1
            
            # 4. Generate report
            generation_report = {
                "campaign_id": campaign_id,
                "generated_at": datetime.now().isoformat(),
                "total_assets": result["assets_generated"],
                "products_processed": len(products),
                "aspect_ratios": aspect_ratios,
                "localized_for": localize_for,
                "compliance_checked": not skip_compliance
            }
            
            report_path = os.path.join(campaign_output_dir, "generation_report.json")
            with open(report_path, 'w') as f:
                json.dump(generation_report, f, indent=2)
            
            result["status"] = "completed"
            result["output_path"] = campaign_output_dir
            result["report_path"] = report_path
            
            return result
            
        except Exception as e:
            result["status"] = "failed"
            result["errors"].append(str(e))
            return result