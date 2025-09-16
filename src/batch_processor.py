"""
Batch Processor - Handles multiple campaign processing with optimization and scheduling.
"""

import asyncio
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
import json
import yaml
from concurrent.futures import ThreadPoolExecutor, as_completed

from .asset_manager import AssetManager
from .image_generator import ImageGenerator
from .creative_composer import CreativeComposer
from .compliance_checker import ComplianceChecker
from .localization import LocalizationManager
from .utils import validate_campaign_brief, update_cost_tracking

logger = logging.getLogger(__name__)


class BatchProcessor:
    """Processes multiple campaigns efficiently with optimization and scheduling."""
    
    def __init__(self, max_concurrent: int = 3, max_api_calls_per_minute: int = 10):
        self.max_concurrent = max_concurrent
        self.max_api_calls_per_minute = max_api_calls_per_minute
        self.api_call_timestamps = []
        
        # Initialize components
        self.asset_manager = AssetManager()
        self.image_generator = ImageGenerator()
        self.creative_composer = CreativeComposer()
        self.compliance_checker = ComplianceChecker()
        self.localization_manager = LocalizationManager()
        
        logger.info(f"Batch processor initialized (max_concurrent: {max_concurrent})")
    
    async def process_campaign_batch(
        self,
        campaign_files: List[str],
        output_dir: str = "batch_output",
        localization_map: Optional[Dict[str, str]] = None,
        skip_compliance: bool = False
    ) -> Dict[str, Any]:
        """Process multiple campaigns in batch with optimization."""
        
        batch_start = datetime.now()
        
        # Validate all campaigns first
        valid_campaigns = []
        validation_errors = []
        
        for campaign_file in campaign_files:
            try:
                campaign_brief = self._load_campaign_brief(campaign_file)
                if validate_campaign_brief(campaign_brief):
                    valid_campaigns.append({
                        'file': campaign_file,
                        'brief': campaign_brief,
                        'localize_to': localization_map.get(campaign_file) if localization_map else None
                    })
                else:
                    validation_errors.append(f"{campaign_file}: Invalid structure")
            except Exception as e:
                validation_errors.append(f"{campaign_file}: {str(e)}")
        
        logger.info(f"Batch validation: {len(valid_campaigns)} valid, {len(validation_errors)} errors")
        
        if not valid_campaigns:
            return {
                'success': False,
                'error': 'No valid campaigns to process',
                'validation_errors': validation_errors
            }
        
        # Process campaigns with concurrency control
        results = await self._process_campaigns_concurrent(
            valid_campaigns, output_dir, skip_compliance
        )
        
        # Generate batch report
        batch_duration = datetime.now() - batch_start
        batch_report = self._generate_batch_report(results, batch_duration, validation_errors)
        
        # Save batch report
        report_path = Path(output_dir) / f"batch_report_{batch_start.strftime('%Y%m%d_%H%M%S')}.json"
        report_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(report_path, 'w') as f:
            json.dump(batch_report, f, indent=2, default=str)
        
        logger.info(f"Batch processing complete: {report_path}")
        
        return {
            'success': True,
            'report_path': str(report_path),
            'processed': len([r for r in results if r['success']]),
            'failed': len([r for r in results if not r['success']]),
            'total_duration': batch_duration.total_seconds(),
            'validation_errors': validation_errors
        }
    
    async def _process_campaigns_concurrent(
        self,
        campaigns: List[Dict],
        output_dir: str,
        skip_compliance: bool
    ) -> List[Dict[str, Any]]:
        """Process campaigns with controlled concurrency."""
        
        semaphore = asyncio.Semaphore(self.max_concurrent)
        
        async def process_single_campaign(campaign_data):
            async with semaphore:
                return await self._process_single_campaign(
                    campaign_data, output_dir, skip_compliance
                )
        
        # Create tasks for all campaigns
        tasks = [
            process_single_campaign(campaign_data)
            for campaign_data in campaigns
        ]
        
        # Execute with progress tracking
        results = []
        for i, task in enumerate(asyncio.as_completed(tasks)):
            result = await task
            results.append(result)
            logger.info(f"Completed campaign {i+1}/{len(campaigns)}: {result['campaign_id']}")
        
        return results
    
    async def _process_single_campaign(
        self,
        campaign_data: Dict,
        output_dir: str,
        skip_compliance: bool
    ) -> Dict[str, Any]:
        """Process a single campaign with error handling."""
        
        start_time = datetime.now()
        campaign_file = campaign_data['file']
        campaign_brief = campaign_data['brief']
        localize_to = campaign_data['localize_to']
        
        try:
            # Apply localization if requested
            original_brief = campaign_brief.copy()
            if localize_to:
                campaign_brief = self.localization_manager.localize_campaign_brief(
                    campaign_brief, localize_to
                )
            
            campaign_id = campaign_brief.get('campaign_brief', {}).get('campaign_id', 'unknown')
            if localize_to:
                campaign_id = f"{campaign_id}_{localize_to.lower()}"
            
            # Run compliance check
            compliance_result = None
            if not skip_compliance:
                compliance_result = self.compliance_checker.check_campaign_brief(campaign_brief)
                
                if compliance_result['issues']['critical']:
                    return {
                        'success': False,
                        'campaign_id': campaign_id,
                        'campaign_file': campaign_file,
                        'error': 'Critical compliance violations',
                        'compliance_issues': compliance_result['issues']['critical'],
                        'duration': (datetime.now() - start_time).total_seconds()
                    }
            
            # Create output directory
            campaign_output = Path(output_dir) / campaign_id
            campaign_output.mkdir(parents=True, exist_ok=True)
            
            # Process products
            products = campaign_brief['campaign_brief']['products']
            aspect_ratios = campaign_brief['campaign_brief']['output_requirements']['aspect_ratios']
            
            generated_assets = []
            total_api_calls = 0
            
            for product in products:
                product_name = product['name']
                product_output = campaign_output / product_name.replace(' ', '_').lower()
                product_output.mkdir(exist_ok=True)
                
                # Find or generate base image
                existing_asset = self.asset_manager.find_product_asset(product_name)
                
                if existing_asset:
                    base_image_path = existing_asset
                else:
                    # Rate limit API calls
                    await self._wait_for_rate_limit()
                    
                    base_image_path = self.image_generator.generate_product_image(
                        product, campaign_brief['campaign_brief']
                    )
                    total_api_calls += 1
                    self.api_call_timestamps.append(datetime.now())
                
                # Generate assets for each aspect ratio
                for aspect_ratio in aspect_ratios:
                    output_file = product_output / f"{aspect_ratio.replace(':', 'x')}.jpg"
                    
                    # Compose final creative
                    final_creative = self.creative_composer.compose_creative(
                        base_image_path,
                        campaign_brief['campaign_brief'],
                        product,
                        aspect_ratio
                    )
                    
                    # Save asset
                    final_creative.save(output_file, format='JPEG', quality=95)
                    generated_assets.append(str(output_file.relative_to(campaign_output)))
            
            # Save reports
            if compliance_result:
                compliance_report_path = campaign_output / 'compliance_report.txt'
                with open(compliance_report_path, 'w') as f:
                    f.write(self.compliance_checker.generate_compliance_report(campaign_brief))
            
            if localize_to:
                localization_report_path = campaign_output / 'localization_report.txt'
                with open(localization_report_path, 'w') as f:
                    f.write(self.localization_manager.generate_localization_report(
                        original_brief, campaign_brief, localize_to
                    ))
            
            # Generate campaign report
            campaign_report = {
                'campaign_id': campaign_id,
                'generated_at': datetime.now().isoformat(),
                'products': len(products),
                'aspect_ratios': aspect_ratios,
                'generated_files': generated_assets,
                'api_calls_made': total_api_calls,
                'localized_for': localize_to,
                'compliance_score': compliance_result['compliance_score'] if compliance_result else None
            }
            
            report_path = campaign_output / 'generation_report.json'
            with open(report_path, 'w') as f:
                json.dump(campaign_report, f, indent=2)
            
            duration = (datetime.now() - start_time).total_seconds()
            
            return {
                'success': True,
                'campaign_id': campaign_id,
                'campaign_file': campaign_file,
                'output_path': str(campaign_output),
                'assets_generated': len(generated_assets),
                'api_calls': total_api_calls,
                'duration': duration,
                'compliance_score': compliance_result['compliance_score'] if compliance_result else None,
                'localized_for': localize_to
            }
            
        except Exception as e:
            logger.error(f"Error processing campaign {campaign_file}: {e}")
            
            return {
                'success': False,
                'campaign_id': campaign_data.get('brief', {}).get('campaign_brief', {}).get('campaign_id', 'unknown'),
                'campaign_file': campaign_file,
                'error': str(e),
                'duration': (datetime.now() - start_time).total_seconds()
            }
    
    async def _wait_for_rate_limit(self):
        """Wait if necessary to respect API rate limits."""
        
        # Clean old timestamps
        cutoff = datetime.now() - timedelta(minutes=1)
        self.api_call_timestamps = [
            ts for ts in self.api_call_timestamps if ts > cutoff
        ]
        
        # Check if we need to wait
        if len(self.api_call_timestamps) >= self.max_api_calls_per_minute:
            oldest_call = min(self.api_call_timestamps)
            wait_time = 60 - (datetime.now() - oldest_call).total_seconds()
            
            if wait_time > 0:
                logger.info(f"Rate limiting: waiting {wait_time:.1f} seconds")
                await asyncio.sleep(wait_time)
    
    def _load_campaign_brief(self, file_path: str) -> Dict[str, Any]:
        """Load campaign brief from file."""
        
        file_path = Path(file_path)
        
        if not file_path.exists():
            raise FileNotFoundError(f"Campaign brief not found: {file_path}")
        
        with open(file_path, 'r') as f:
            if file_path.suffix.lower() in ['.yaml', '.yml']:
                return yaml.safe_load(f)
            else:
                return json.load(f)
    
    def _generate_batch_report(
        self,
        results: List[Dict[str, Any]],
        batch_duration: timedelta,
        validation_errors: List[str]
    ) -> Dict[str, Any]:
        """Generate comprehensive batch processing report."""
        
        successful_results = [r for r in results if r['success']]
        failed_results = [r for r in results if not r['success']]
        
        # Calculate statistics
        total_assets = sum(r.get('assets_generated', 0) for r in successful_results)
        total_api_calls = sum(r.get('api_calls', 0) for r in successful_results)
        avg_duration = sum(r['duration'] for r in results) / len(results) if results else 0
        
        # Compliance statistics
        compliance_scores = [r.get('compliance_score') for r in successful_results if r.get('compliance_score')]
        avg_compliance = sum(compliance_scores) / len(compliance_scores) if compliance_scores else None
        
        # Localization statistics
        localized_campaigns = [r for r in successful_results if r.get('localized_for')]
        
        return {
            'batch_summary': {
                'total_campaigns': len(results) + len(validation_errors),
                'successful': len(successful_results),
                'failed': len(failed_results),
                'validation_errors': len(validation_errors),
                'batch_duration_seconds': batch_duration.total_seconds(),
                'avg_campaign_duration_seconds': avg_duration
            },
            'generation_statistics': {
                'total_assets_generated': total_assets,
                'total_api_calls': total_api_calls,
                'avg_compliance_score': avg_compliance,
                'localized_campaigns': len(localized_campaigns)
            },
            'successful_campaigns': [
                {
                    'campaign_id': r['campaign_id'],
                    'campaign_file': r['campaign_file'],
                    'assets_generated': r.get('assets_generated', 0),
                    'duration_seconds': r['duration'],
                    'localized_for': r.get('localized_for')
                }
                for r in successful_results
            ],
            'failed_campaigns': [
                {
                    'campaign_id': r['campaign_id'],
                    'campaign_file': r['campaign_file'],
                    'error': r['error'],
                    'duration_seconds': r['duration']
                }
                for r in failed_results
            ],
            'validation_errors': validation_errors,
            'performance_metrics': {
                'campaigns_per_minute': len(results) / (batch_duration.total_seconds() / 60),
                'assets_per_minute': total_assets / (batch_duration.total_seconds() / 60),
                'api_calls_per_campaign': total_api_calls / len(successful_results) if successful_results else 0
            }
        }
    
    def schedule_batch(
        self,
        campaign_files: List[str],
        schedule_time: datetime,
        output_dir: str = "scheduled_output",
        localization_map: Optional[Dict[str, str]] = None
    ) -> str:
        """Schedule a batch for future execution."""
        
        # Create schedule entry
        schedule_id = f"batch_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        schedule_entry = {
            'schedule_id': schedule_id,
            'scheduled_for': schedule_time.isoformat(),
            'campaign_files': campaign_files,
            'output_dir': output_dir,
            'localization_map': localization_map or {},
            'status': 'scheduled',
            'created_at': datetime.now().isoformat()
        }
        
        # Save to schedule file
        schedule_dir = Path('batch_schedules')
        schedule_dir.mkdir(exist_ok=True)
        
        schedule_file = schedule_dir / f"{schedule_id}.json"
        with open(schedule_file, 'w') as f:
            json.dump(schedule_entry, f, indent=2)
        
        logger.info(f"Batch scheduled: {schedule_id} for {schedule_time}")
        
        return schedule_id
    
    def get_batch_queue_status(self) -> Dict[str, Any]:
        """Get status of scheduled and running batches."""
        
        schedule_dir = Path('batch_schedules')
        
        if not schedule_dir.exists():
            return {
                'scheduled_batches': 0,
                'queue': []
            }
        
        queue = []
        
        for schedule_file in schedule_dir.glob('*.json'):
            try:
                with open(schedule_file, 'r') as f:
                    schedule_entry = json.load(f)
                
                queue.append({
                    'schedule_id': schedule_entry['schedule_id'],
                    'scheduled_for': schedule_entry['scheduled_for'],
                    'campaign_count': len(schedule_entry['campaign_files']),
                    'status': schedule_entry['status']
                })
                
            except Exception as e:
                logger.error(f"Error reading schedule file {schedule_file}: {e}")
        
        # Sort by scheduled time
        queue.sort(key=lambda x: x['scheduled_for'])
        
        return {
            'scheduled_batches': len(queue),
            'queue': queue
        }