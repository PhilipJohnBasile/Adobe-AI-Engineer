"""
Asset Manager - Handles input asset discovery and management.
"""

import logging
from pathlib import Path
from typing import Optional, List, Dict
import json

logger = logging.getLogger(__name__)


class AssetManager:
    """Manages input assets and asset discovery."""
    
    def __init__(self, assets_directory: str = "assets"):
        self.assets_dir = Path(assets_directory)
        self.assets_dir.mkdir(exist_ok=True)
        
        # Cache for asset metadata
        self.cache_file = Path('cache.json')
        self.asset_cache = self._load_cache()
        
        # Supported image formats
        self.supported_formats = {'.jpg', '.jpeg', '.png', '.webp', '.bmp'}
        
        logger.info(f"Asset manager initialized with directory: {self.assets_dir}")
    
    def _load_cache(self) -> Dict:
        """Load asset cache from file."""
        if self.cache_file.exists():
            try:
                with open(self.cache_file, 'r') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError) as e:
                logger.warning(f"Failed to load cache: {e}")
        
        return {'assets': {}, 'last_scan': None}
    
    def _save_cache(self) -> None:
        """Save asset cache to file."""
        try:
            with open(self.cache_file, 'w') as f:
                json.dump(self.asset_cache, f, indent=2)
        except IOError as e:
            logger.warning(f"Failed to save cache: {e}")
    
    def scan_assets(self, force_rescan: bool = False) -> None:
        """Scan the assets directory and update cache."""
        from datetime import datetime
        
        if not force_rescan and self.asset_cache.get('last_scan'):
            logger.debug("Using cached asset scan results")
            return
        
        logger.info("Scanning assets directory...")
        self.asset_cache['assets'] = {}
        
        if not self.assets_dir.exists():
            logger.warning(f"Assets directory {self.assets_dir} does not exist")
            return
        
        for file_path in self.assets_dir.rglob('*'):
            if file_path.is_file() and file_path.suffix.lower() in self.supported_formats:
                relative_path = str(file_path.relative_to(self.assets_dir))
                
                # Extract metadata
                asset_info = {
                    'path': str(file_path),
                    'name': file_path.stem,
                    'format': file_path.suffix.lower(),
                    'size': file_path.stat().st_size,
                    'keywords': self._extract_keywords_from_filename(file_path.stem)
                }
                
                self.asset_cache['assets'][relative_path] = asset_info
                logger.debug(f"Found asset: {relative_path}")
        
        self.asset_cache['last_scan'] = datetime.now().isoformat()
        self._save_cache()
        
        logger.info(f"Asset scan completed. Found {len(self.asset_cache['assets'])} assets")
    
    def _extract_keywords_from_filename(self, filename: str) -> List[str]:
        """Extract keywords from filename for matching."""
        import re
        
        # Split on common delimiters and convert to lowercase
        keywords = re.split(r'[_\-\s\.]+', filename.lower())
        
        # Filter out empty strings and single characters
        keywords = [k for k in keywords if len(k) > 1]
        
        return keywords
    
    def find_product_asset(self, product_name: str) -> Optional[Path]:
        """Find the best matching asset for a product."""
        self.scan_assets()
        
        if not self.asset_cache['assets']:
            logger.warning("No assets found in directory")
            return None
        
        # Extract keywords from product name
        product_keywords = self._extract_keywords_from_filename(product_name)
        
        best_match = None
        best_score = 0
        
        for relative_path, asset_info in self.asset_cache['assets'].items():
            asset_keywords = asset_info['keywords']
            
            # Calculate matching score
            score = self._calculate_match_score(product_keywords, asset_keywords)
            
            if score > best_score:
                best_score = score
                best_match = asset_info['path']
        
        if best_match and best_score > 0:
            logger.info(f"Found matching asset for '{product_name}': {best_match} (score: {best_score})")
            return Path(best_match)
        
        logger.info(f"No matching asset found for product: {product_name}")
        return None
    
    def _calculate_match_score(self, product_keywords: List[str], asset_keywords: List[str]) -> float:
        """Calculate similarity score between product and asset keywords."""
        if not product_keywords or not asset_keywords:
            return 0.0
        
        # Count exact matches
        exact_matches = len(set(product_keywords) & set(asset_keywords))
        
        # Count partial matches (substring matches)
        partial_matches = 0
        for prod_keyword in product_keywords:
            for asset_keyword in asset_keywords:
                if prod_keyword in asset_keyword or asset_keyword in prod_keyword:
                    partial_matches += 0.5
                    break
        
        # Calculate score (exact matches weighted more heavily)
        score = (exact_matches * 2 + partial_matches) / len(product_keywords)
        
        return score
    
    def get_asset_list(self) -> List[Dict]:
        """Get list of all available assets."""
        self.scan_assets()
        return list(self.asset_cache['assets'].values())
    
    def add_asset(self, asset_path: Path, product_name: str = None) -> bool:
        """Add a new asset to the managed directory."""
        if not asset_path.exists():
            logger.error(f"Asset file does not exist: {asset_path}")
            return False
        
        if asset_path.suffix.lower() not in self.supported_formats:
            logger.error(f"Unsupported format: {asset_path.suffix}")
            return False
        
        try:
            # Generate destination filename
            if product_name:
                dest_name = f"{self._sanitize_filename(product_name)}{asset_path.suffix}"
            else:
                dest_name = asset_path.name
            
            dest_path = self.assets_dir / dest_name
            
            # Copy file
            import shutil
            shutil.copy2(asset_path, dest_path)
            
            # Invalidate cache
            self.asset_cache['last_scan'] = None
            
            logger.info(f"Added asset: {dest_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to add asset: {e}")
            return False
    
    def _sanitize_filename(self, filename: str) -> str:
        """Sanitize filename for safe storage."""
        import re
        
        # Remove or replace unsafe characters
        filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
        filename = filename.replace(' ', '_')
        filename = re.sub(r'_+', '_', filename)
        filename = filename.strip('_')
        
        return filename.lower()