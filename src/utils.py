"""
Utility functions for the creative automation pipeline.
"""

import logging
import sys
from typing import Dict, Any
from pathlib import Path


def setup_logging(level: int = logging.INFO) -> None:
    """Setup logging configuration."""
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('pipeline.log')
        ]
    )


def validate_campaign_brief(brief: Dict[Any, Any]) -> bool:
    """Validate the structure of a campaign brief."""
    
    required_fields = [
        'campaign_brief.campaign_id',
        'campaign_brief.products',
        'campaign_brief.target_region',
        'campaign_brief.target_audience',
        'campaign_brief.campaign_message',
        'campaign_brief.output_requirements.aspect_ratios'
    ]
    
    def get_nested_value(data: Dict, path: str) -> Any:
        """Get nested dictionary value using dot notation."""
        keys = path.split('.')
        current = data
        
        for key in keys:
            if not isinstance(current, dict) or key not in current:
                return None
            current = current[key]
        
        return current
    
    # Check required fields
    for field_path in required_fields:
        if get_nested_value(brief, field_path) is None:
            logging.error(f"Missing required field: {field_path}")
            return False
    
    # Validate products structure
    products = brief['campaign_brief']['products']
    if not isinstance(products, list) or len(products) == 0:
        logging.error("Products must be a non-empty list")
        return False
    
    for i, product in enumerate(products):
        if not isinstance(product, dict):
            logging.error(f"Product {i} must be a dictionary")
            return False
        
        if 'name' not in product or 'description' not in product:
            logging.error(f"Product {i} missing name or description")
            return False
    
    # Validate aspect ratios
    aspect_ratios = brief['campaign_brief']['output_requirements']['aspect_ratios']
    if not isinstance(aspect_ratios, list) or len(aspect_ratios) == 0:
        logging.error("Aspect ratios must be a non-empty list")
        return False
    
    valid_ratios = ['1:1', '9:16', '16:9', '4:5', '3:4']
    for ratio in aspect_ratios:
        if ratio not in valid_ratios:
            logging.warning(f"Unusual aspect ratio: {ratio}")
    
    return True


def calculate_dimensions(aspect_ratio: str, base_size: int = 1080) -> tuple[int, int]:
    """Calculate pixel dimensions for a given aspect ratio."""
    
    dimension_map = {
        '1:1': (1080, 1080),
        '9:16': (1080, 1920),
        '16:9': (1920, 1080),
        '4:5': (1080, 1350),
        '3:4': (1080, 1440)
    }
    
    if aspect_ratio in dimension_map:
        return dimension_map[aspect_ratio]
    
    # Parse custom ratio
    try:
        width_ratio, height_ratio = map(int, aspect_ratio.split(':'))
        if width_ratio >= height_ratio:
            width = base_size
            height = int(base_size * height_ratio / width_ratio)
        else:
            height = base_size
            width = int(base_size * width_ratio / height_ratio)
        
        return (width, height)
    
    except (ValueError, ZeroDivisionError):
        logging.warning(f"Invalid aspect ratio {aspect_ratio}, using 1:1")
        return (1080, 1080)


def ensure_directory(path: Path) -> None:
    """Ensure a directory exists, create if it doesn't."""
    path.mkdir(parents=True, exist_ok=True)


def sanitize_filename(filename: str) -> str:
    """Sanitize a string to be safe for use as a filename."""
    import re
    
    # Remove or replace unsafe characters
    filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
    
    # Replace spaces with underscores
    filename = filename.replace(' ', '_')
    
    # Remove multiple consecutive underscores
    filename = re.sub(r'_+', '_', filename)
    
    # Remove leading/trailing underscores
    filename = filename.strip('_')
    
    return filename.lower()


def load_cost_tracking() -> Dict[str, float]:
    """Load API cost tracking data."""
    cost_file = Path('costs.json')
    
    if cost_file.exists():
        import json
        with open(cost_file, 'r') as f:
            return json.load(f)
    
    return {'total_cost': 0.0, 'api_calls': 0}


def update_cost_tracking(service: str, cost: float, tokens: int = 0) -> None:
    """Update API cost tracking data."""
    import json
    
    costs = load_cost_tracking()
    costs['total_cost'] += cost
    costs['api_calls'] += 1
    
    if service not in costs:
        costs[service] = {'cost': 0.0, 'calls': 0, 'tokens': 0}
    
    costs[service]['cost'] += cost
    costs[service]['calls'] += 1
    costs[service]['tokens'] += tokens
    
    with open('costs.json', 'w') as f:
        json.dump(costs, f, indent=2)