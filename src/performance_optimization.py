"""
Free Performance Optimization with Caching Layers
Implements Redis-alternative caching, image optimization, and CDN simulation
"""

import json
import os
import hashlib
import pickle
import time
import gzip
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass, asdict
from pathlib import Path
import threading
import logging
from PIL import Image, ImageOps
import sqlite3
from contextlib import contextmanager
import shutil
from enum import Enum


class CacheLevel(Enum):
    MEMORY = "memory"
    DISK = "disk"
    DISTRIBUTED = "distributed"


@dataclass
class CacheEntry:
    """Cache entry with metadata"""
    key: str
    value: Any
    created_at: datetime
    expires_at: Optional[datetime]
    access_count: int = 0
    last_accessed: Optional[datetime] = None
    size_bytes: int = 0
    tags: List[str] = None
    
    def __post_init__(self):
        if self.tags is None:
            self.tags = []
    
    def is_expired(self) -> bool:
        """Check if cache entry has expired"""
        if self.expires_at is None:
            return False
        return datetime.now() > self.expires_at
    
    def touch(self):
        """Update access statistics"""
        self.access_count += 1
        self.last_accessed = datetime.now()


class MemoryCache:
    """High-performance in-memory cache with LRU eviction"""
    
    def __init__(self, max_size_mb: int = 100, max_entries: int = 1000):
        self.max_size_bytes = max_size_mb * 1024 * 1024
        self.max_entries = max_entries
        self.cache: Dict[str, CacheEntry] = {}
        self.current_size = 0
        self._lock = threading.RLock()
        self.stats = {
            "hits": 0,
            "misses": 0,
            "evictions": 0,
            "sets": 0
        }
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        with self._lock:
            entry = self.cache.get(key)
            if entry is None:
                self.stats["misses"] += 1
                return None
            
            if entry.is_expired():
                self._remove_entry(key)
                self.stats["misses"] += 1
                return None
            
            entry.touch()
            self.stats["hits"] += 1
            return entry.value
    
    def set(self, key: str, value: Any, ttl_seconds: Optional[int] = None, tags: List[str] = None) -> bool:
        """Set value in cache"""
        with self._lock:
            # Calculate size
            try:
                serialized = pickle.dumps(value)
                size_bytes = len(serialized)
            except (pickle.PicklingError, TypeError, AttributeError):
                return False
            
            # Check if we need to evict
            if len(self.cache) >= self.max_entries or self.current_size + size_bytes > self.max_size_bytes:
                self._evict_lru()
            
            # Create entry
            expires_at = None
            if ttl_seconds:
                expires_at = datetime.now() + timedelta(seconds=ttl_seconds)
            
            entry = CacheEntry(
                key=key,
                value=value,
                created_at=datetime.now(),
                expires_at=expires_at,
                size_bytes=size_bytes,
                tags=tags or []
            )
            
            # Remove existing entry if present
            if key in self.cache:
                self._remove_entry(key)
            
            # Add new entry
            self.cache[key] = entry
            self.current_size += size_bytes
            self.stats["sets"] += 1
            
            return True
    
    def delete(self, key: str) -> bool:
        """Delete entry from cache"""
        with self._lock:
            if key in self.cache:
                self._remove_entry(key)
                return True
            return False
    
    def clear_by_tags(self, tags: List[str]) -> int:
        """Clear entries with specific tags"""
        with self._lock:
            keys_to_remove = []
            for key, entry in self.cache.items():
                if any(tag in entry.tags for tag in tags):
                    keys_to_remove.append(key)
            
            for key in keys_to_remove:
                self._remove_entry(key)
            
            return len(keys_to_remove)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        with self._lock:
            total_requests = self.stats["hits"] + self.stats["misses"]
            hit_rate = (self.stats["hits"] / total_requests * 100) if total_requests > 0 else 0
            
            return {
                "hits": self.stats["hits"],
                "misses": self.stats["misses"],
                "hit_rate_percent": hit_rate,
                "evictions": self.stats["evictions"],
                "sets": self.stats["sets"],
                "current_entries": len(self.cache),
                "max_entries": self.max_entries,
                "current_size_mb": self.current_size / (1024 * 1024),
                "max_size_mb": self.max_size_bytes / (1024 * 1024),
                "utilization_percent": (len(self.cache) / self.max_entries * 100)
            }
    
    def _remove_entry(self, key: str):
        """Remove entry and update size"""
        if key in self.cache:
            entry = self.cache[key]
            self.current_size -= entry.size_bytes
            del self.cache[key]
    
    def _evict_lru(self):
        """Evict least recently used entries"""
        if not self.cache:
            return
        
        # Sort by last accessed time (oldest first)
        sorted_entries = sorted(
            self.cache.items(),
            key=lambda x: x[1].last_accessed or x[1].created_at
        )
        
        # Evict oldest 10% or until under limits
        eviction_count = max(1, len(self.cache) // 10)
        for i in range(eviction_count):
            if i < len(sorted_entries):
                key = sorted_entries[i][0]
                self._remove_entry(key)
                self.stats["evictions"] += 1


class DiskCache:
    """Persistent disk-based cache with compression"""
    
    def __init__(self, cache_dir: str = "cache", max_size_mb: int = 1000):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
        self.max_size_bytes = max_size_mb * 1024 * 1024
        self.db_path = self.cache_dir / "cache_metadata.db"
        self._init_database()
        self._lock = threading.RLock()
    
    def _init_database(self):
        """Initialize SQLite database for metadata"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS cache_entries (
                    key TEXT PRIMARY KEY,
                    file_path TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    expires_at TEXT,
                    access_count INTEGER DEFAULT 0,
                    last_accessed TEXT,
                    size_bytes INTEGER DEFAULT 0,
                    tags TEXT
                )
            """)
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from disk cache"""
        with self._lock:
            try:
                with sqlite3.connect(self.db_path) as conn:
                    cursor = conn.execute(
                        "SELECT file_path, expires_at FROM cache_entries WHERE key = ?",
                        (key,)
                    )
                    row = cursor.fetchone()
                    
                    if not row:
                        return None
                    
                    file_path, expires_at = row
                    
                    # Check expiration
                    if expires_at and datetime.fromisoformat(expires_at) < datetime.now():
                        self.delete(key)
                        return None
                    
                    # Load from file
                    full_path = self.cache_dir / file_path
                    if not full_path.exists():
                        self.delete(key)
                        return None
                    
                    # Update access stats
                    conn.execute(
                        "UPDATE cache_entries SET access_count = access_count + 1, last_accessed = ? WHERE key = ?",
                        (datetime.now().isoformat(), key)
                    )
                    
                    # Load and decompress
                    with gzip.open(full_path, 'rb') as f:
                        return pickle.load(f)
                        
            except Exception as e:
                logging.error(f"Error reading from disk cache: {e}")
                return None
    
    def set(self, key: str, value: Any, ttl_seconds: Optional[int] = None, tags: List[str] = None) -> bool:
        """Set value in disk cache"""
        with self._lock:
            try:
                # Create file path
                safe_key = hashlib.md5(key.encode()).hexdigest()
                file_path = f"{safe_key}.cache"
                full_path = self.cache_dir / file_path
                
                # Serialize and compress
                with gzip.open(full_path, 'wb') as f:
                    pickle.dump(value, f)
                
                size_bytes = full_path.stat().st_size
                
                # Calculate expiration
                expires_at = None
                if ttl_seconds:
                    expires_at = (datetime.now() + timedelta(seconds=ttl_seconds)).isoformat()
                
                # Store metadata
                with sqlite3.connect(self.db_path) as conn:
                    conn.execute("""
                        INSERT OR REPLACE INTO cache_entries 
                        (key, file_path, created_at, expires_at, size_bytes, tags)
                        VALUES (?, ?, ?, ?, ?, ?)
                    """, (
                        key, file_path, datetime.now().isoformat(), 
                        expires_at, size_bytes, json.dumps(tags or [])
                    ))
                
                # Check size limits and evict if necessary
                self._evict_if_needed()
                
                return True
                
            except Exception as e:
                logging.error(f"Error writing to disk cache: {e}")
                return False
    
    def delete(self, key: str) -> bool:
        """Delete entry from disk cache"""
        with self._lock:
            try:
                with sqlite3.connect(self.db_path) as conn:
                    cursor = conn.execute("SELECT file_path FROM cache_entries WHERE key = ?", (key,))
                    row = cursor.fetchone()
                    
                    if row:
                        file_path = row[0]
                        full_path = self.cache_dir / file_path
                        
                        # Remove file
                        if full_path.exists():
                            full_path.unlink()
                        
                        # Remove metadata
                        conn.execute("DELETE FROM cache_entries WHERE key = ?", (key,))
                        return True
                
                return False
                
            except Exception as e:
                logging.error(f"Error deleting from disk cache: {e}")
                return False
    
    def _evict_if_needed(self):
        """Evict old entries if cache is too large"""
        try:
            # Get current cache size
            total_size = sum(
                (self.cache_dir / f).stat().st_size 
                for f in os.listdir(self.cache_dir) 
                if f.endswith('.cache')
            )
            
            if total_size > self.max_size_bytes:
                # Get oldest entries
                with sqlite3.connect(self.db_path) as conn:
                    cursor = conn.execute("""
                        SELECT key FROM cache_entries 
                        ORDER BY last_accessed ASC, created_at ASC
                        LIMIT 100
                    """)
                    
                    old_keys = [row[0] for row in cursor.fetchall()]
                    
                    # Delete until under limit
                    for key in old_keys:
                        self.delete(key)
                        
                        # Recalculate size
                        total_size = sum(
                            (self.cache_dir / f).stat().st_size 
                            for f in os.listdir(self.cache_dir) 
                            if f.endswith('.cache')
                        )
                        
                        if total_size <= self.max_size_bytes * 0.8:  # Leave some headroom
                            break
                            
        except Exception as e:
            logging.error(f"Error during cache eviction: {e}")


class ImageOptimizer:
    """Image optimization for faster loading and reduced storage"""
    
    def __init__(self, output_dir: str = "optimized_images"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        # Optimization settings
        self.quality_settings = {
            "thumbnail": {"size": (150, 150), "quality": 75},
            "small": {"size": (400, 400), "quality": 80},
            "medium": {"size": (800, 800), "quality": 85},
            "large": {"size": (1200, 1200), "quality": 90},
            "original": {"quality": 95}
        }
    
    def optimize_image(self, input_path: str, output_formats: List[str] = None) -> Dict[str, str]:
        """Optimize image in multiple formats and sizes"""
        if output_formats is None:
            output_formats = ["thumbnail", "small", "medium", "large"]
        
        input_path = Path(input_path)
        if not input_path.exists():
            raise FileNotFoundError(f"Input image not found: {input_path}")
        
        optimized_paths = {}
        
        try:
            with Image.open(input_path) as img:
                # Convert to RGB if necessary
                if img.mode in ('RGBA', 'LA', 'P'):
                    img = img.convert('RGB')
                
                # Create base filename
                base_name = input_path.stem
                
                for format_name in output_formats:
                    if format_name not in self.quality_settings:
                        continue
                    
                    settings = self.quality_settings[format_name]
                    
                    # Create optimized version
                    optimized_img = img.copy()
                    
                    # Resize if size specified
                    if "size" in settings:
                        optimized_img.thumbnail(settings["size"], Image.Resampling.LANCZOS)
                    
                    # Generate output path
                    output_path = self.output_dir / f"{base_name}_{format_name}.jpg"
                    
                    # Save with optimization
                    optimized_img.save(
                        output_path,
                        "JPEG",
                        quality=settings["quality"],
                        optimize=True,
                        progressive=True
                    )
                    
                    optimized_paths[format_name] = str(output_path)
                
                return optimized_paths
                
        except Exception as e:
            logging.error(f"Error optimizing image {input_path}: {e}")
            raise
    
    def get_optimization_stats(self, original_path: str, optimized_paths: Dict[str, str]) -> Dict[str, Any]:
        """Get optimization statistics"""
        original_size = Path(original_path).stat().st_size
        
        stats = {
            "original_size_bytes": original_size,
            "original_size_mb": original_size / (1024 * 1024),
            "optimized_versions": {}
        }
        
        for format_name, path in optimized_paths.items():
            if Path(path).exists():
                opt_size = Path(path).stat().st_size
                compression_ratio = (1 - opt_size / original_size) * 100
                
                stats["optimized_versions"][format_name] = {
                    "size_bytes": opt_size,
                    "size_mb": opt_size / (1024 * 1024),
                    "compression_ratio_percent": compression_ratio
                }
        
        return stats


class CDNSimulator:
    """Simulates CDN behavior with geographic distribution"""
    
    def __init__(self, base_dir: str = "cdn_cache"):
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(exist_ok=True)
        
        # Simulate edge locations
        self.edge_locations = {
            "us-east": {"latency_ms": 20, "path": "us-east"},
            "us-west": {"latency_ms": 50, "path": "us-west"},
            "eu-west": {"latency_ms": 100, "path": "eu-west"},
            "asia-pacific": {"latency_ms": 150, "path": "asia-pacific"}
        }
        
        # Create edge location directories
        for location_info in self.edge_locations.values():
            (self.base_dir / location_info["path"]).mkdir(exist_ok=True)
    
    def upload_to_cdn(self, local_path: str, cdn_path: str) -> Dict[str, str]:
        """Simulate uploading file to CDN edge locations"""
        local_path = Path(local_path)
        if not local_path.exists():
            raise FileNotFoundError(f"Local file not found: {local_path}")
        
        cdn_urls = {}
        
        for location, info in self.edge_locations.items():
            edge_dir = self.base_dir / info["path"]
            edge_file = edge_dir / cdn_path
            
            # Create subdirectories if needed
            edge_file.parent.mkdir(parents=True, exist_ok=True)
            
            # Copy file to edge location
            shutil.copy2(local_path, edge_file)
            
            # Generate CDN URL
            cdn_urls[location] = f"https://cdn-{location}.example.com/{cdn_path}"
        
        return cdn_urls
    
    def get_optimal_url(self, user_location: str, cdn_urls: Dict[str, str]) -> Dict[str, Any]:
        """Get optimal CDN URL based on user location"""
        # Simple location mapping
        location_mapping = {
            "US": "us-east",
            "CA": "us-west", 
            "UK": "eu-west",
            "DE": "eu-west",
            "JP": "asia-pacific",
            "FR": "eu-west"
        }
        
        optimal_edge = location_mapping.get(user_location, "us-east")
        
        return {
            "optimal_url": cdn_urls.get(optimal_edge, list(cdn_urls.values())[0]),
            "edge_location": optimal_edge,
            "estimated_latency_ms": self.edge_locations[optimal_edge]["latency_ms"],
            "all_urls": cdn_urls
        }


class PerformanceOptimizer:
    """Main performance optimization orchestrator"""
    
    def __init__(self):
        self.memory_cache = MemoryCache(max_size_mb=100)
        self.disk_cache = DiskCache(max_size_mb=500)
        self.image_optimizer = ImageOptimizer()
        self.cdn_simulator = CDNSimulator()
        self.logger = logging.getLogger(__name__)
        
        # Performance metrics
        self.metrics = {
            "cache_operations": 0,
            "image_optimizations": 0,
            "cdn_uploads": 0,
            "total_time_saved_seconds": 0
        }
    
    def cache_campaign_result(self, campaign_id: str, result: Dict[str, Any], ttl_seconds: int = 3600) -> bool:
        """Cache campaign generation result"""
        cache_key = f"campaign:{campaign_id}"
        
        # Try memory cache first
        if self.memory_cache.set(cache_key, result, ttl_seconds, tags=["campaign"]):
            self.logger.info(f"Cached campaign {campaign_id} in memory")
            
        # Also cache to disk for persistence
        if self.disk_cache.set(cache_key, result, ttl_seconds, tags=["campaign"]):
            self.logger.info(f"Cached campaign {campaign_id} to disk")
            
        self.metrics["cache_operations"] += 1
        return True
    
    def get_cached_campaign(self, campaign_id: str) -> Optional[Dict[str, Any]]:
        """Get cached campaign result"""
        cache_key = f"campaign:{campaign_id}"
        
        # Try memory cache first
        result = self.memory_cache.get(cache_key)
        if result:
            self.logger.info(f"Cache HIT (memory): {campaign_id}")
            return result
        
        # Try disk cache
        result = self.disk_cache.get(cache_key)
        if result:
            self.logger.info(f"Cache HIT (disk): {campaign_id}")
            # Promote to memory cache
            self.memory_cache.set(cache_key, result, 3600, tags=["campaign"])
            return result
        
        self.logger.info(f"Cache MISS: {campaign_id}")
        return None
    
    def optimize_campaign_assets(self, asset_paths: List[str]) -> Dict[str, Any]:
        """Optimize all assets in a campaign"""
        optimization_results = {
            "optimized_assets": {},
            "cdn_urls": {},
            "total_size_reduction_percent": 0,
            "performance_improvement": {}
        }
        
        total_original_size = 0
        total_optimized_size = 0
        
        for asset_path in asset_paths:
            try:
                # Optimize image
                optimized_paths = self.image_optimizer.optimize_image(asset_path)
                optimization_stats = self.image_optimizer.get_optimization_stats(asset_path, optimized_paths)
                
                optimization_results["optimized_assets"][asset_path] = {
                    "paths": optimized_paths,
                    "stats": optimization_stats
                }
                
                # Upload to CDN simulator
                cdn_urls = {}
                for format_name, opt_path in optimized_paths.items():
                    cdn_path = f"campaigns/{Path(asset_path).stem}/{format_name}.jpg"
                    urls = self.cdn_simulator.upload_to_cdn(opt_path, cdn_path)
                    cdn_urls[format_name] = urls
                
                optimization_results["cdn_urls"][asset_path] = cdn_urls
                
                # Update size metrics
                total_original_size += optimization_stats["original_size_bytes"]
                for version_stats in optimization_stats["optimized_versions"].values():
                    total_optimized_size += version_stats["size_bytes"]
                
                self.metrics["image_optimizations"] += 1
                self.metrics["cdn_uploads"] += len(optimized_paths)
                
            except Exception as e:
                self.logger.error(f"Error optimizing asset {asset_path}: {e}")
        
        # Calculate overall improvement
        if total_original_size > 0:
            size_reduction = (1 - total_optimized_size / total_original_size) * 100
            optimization_results["total_size_reduction_percent"] = size_reduction
            
            # Estimate performance improvement
            estimated_load_time_improvement = size_reduction * 0.7  # Conservative estimate
            optimization_results["performance_improvement"] = {
                "estimated_load_time_reduction_percent": estimated_load_time_improvement,
                "bandwidth_savings_mb": (total_original_size - total_optimized_size) / (1024 * 1024)
            }
        
        return optimization_results
    
    def get_performance_report(self) -> Dict[str, Any]:
        """Generate comprehensive performance report"""
        memory_stats = self.memory_cache.get_stats()
        
        return {
            "timestamp": datetime.now().isoformat(),
            "cache_performance": {
                "memory_cache": memory_stats,
                "memory_hit_rate": memory_stats["hit_rate_percent"],
                "memory_utilization": memory_stats["utilization_percent"]
            },
            "optimization_metrics": self.metrics,
            "recommendations": self._generate_performance_recommendations(memory_stats)
        }
    
    def _generate_performance_recommendations(self, cache_stats: Dict[str, Any]) -> List[str]:
        """Generate performance optimization recommendations"""
        recommendations = []
        
        hit_rate = cache_stats["hit_rate_percent"]
        if hit_rate < 50:
            recommendations.append("Consider increasing cache size - low hit rate indicates frequent cache misses")
        elif hit_rate > 90:
            recommendations.append("Excellent cache performance - consider implementing more caching layers")
        
        utilization = cache_stats["utilization_percent"]
        if utilization > 80:
            recommendations.append("Cache is near capacity - consider increasing cache size or implementing better eviction")
        
        if self.metrics["image_optimizations"] > 0:
            recommendations.append("Image optimization is active - consider implementing WebP format for modern browsers")
        
        if self.metrics["cdn_uploads"] > 0:
            recommendations.append("CDN simulation active - implement real CDN integration for production")
        
        return recommendations
    
    def clear_campaign_cache(self, campaign_id: str = None) -> Dict[str, int]:
        """Clear cache entries"""
        if campaign_id:
            # Clear specific campaign
            cache_key = f"campaign:{campaign_id}"
            memory_cleared = 1 if self.memory_cache.delete(cache_key) else 0
            disk_cleared = 1 if self.disk_cache.delete(cache_key) else 0
        else:
            # Clear all campaign caches
            memory_cleared = self.memory_cache.clear_by_tags(["campaign"])
            # Disk cache would need similar implementation
            disk_cleared = 0
        
        return {
            "memory_entries_cleared": memory_cleared,
            "disk_entries_cleared": disk_cleared
        }


# Global performance optimizer instance
performance_optimizer = PerformanceOptimizer()