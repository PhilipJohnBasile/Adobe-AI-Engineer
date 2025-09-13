"""
Cost Tracking Module

Monitors and controls API costs during pipeline execution to stay within budget limits.
Perfect for demo environments where cost control is critical.
"""

import os
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from pathlib import Path
import threading

logger = logging.getLogger(__name__)


class CostTracker:
    """Track API costs and enforce budget limits for demo environments."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize cost tracker with budget configuration."""
        self.config = config.get("cost_tracking", {})
        self.daily_budget = self.config.get("daily_budget_limit", 5.00)
        self.alert_threshold = self.config.get("alert_threshold", 0.80)
        
        # Cost tracking storage
        self.costs_file = Path(__file__).parent.parent.parent / "costs.json"
        self.costs = self._load_costs()
        self.lock = threading.Lock()
        
        # Service pricing (per unit)
        self.pricing = {
            "openai": {
                "dall-e-2": {"1024x1024": 0.020, "512x512": 0.016},
                "dall-e-3": {"1024x1024": 0.040, "1792x1024": 0.080, "1024x1792": 0.080},
                "gpt-4o-mini": {"input": 0.15 / 1_000_000, "output": 0.60 / 1_000_000},
                "gpt-3.5-turbo": {"input": 0.50 / 1_000_000, "output": 1.50 / 1_000_000}
            }
        }
        
        logger.info(f"CostTracker initialized with ${self.daily_budget:.2f} daily budget")
    
    def _load_costs(self) -> Dict[str, Any]:
        """Load cost history from storage."""
        if self.costs_file.exists():
            try:
                with open(self.costs_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Failed to load cost history: {e}")
        
        return {
            "daily_totals": {},
            "transactions": [],
            "alerts_sent": []
        }
    
    def _save_costs(self):
        """Save cost history to storage."""
        try:
            with open(self.costs_file, 'w') as f:
                json.dump(self.costs, f, indent=2, default=str)
        except Exception as e:
            logger.error(f"Failed to save cost history: {e}")
    
    def get_today_date(self) -> str:
        """Get today's date string for tracking."""
        return datetime.now().strftime("%Y-%m-%d")
    
    def get_daily_spend(self, date: Optional[str] = None) -> float:
        """Get total spending for a specific date."""
        if date is None:
            date = self.get_today_date()
        
        return self.costs["daily_totals"].get(date, 0.0)
    
    def check_budget_available(self, estimated_cost: float = 0.0) -> Dict[str, Any]:
        """Check if there's budget available for a request."""
        with self.lock:
            today = self.get_today_date()
            current_spend = self.get_daily_spend(today)
            remaining_budget = self.daily_budget - current_spend
            
            result = {
                "budget_available": remaining_budget >= estimated_cost,
                "current_spend": current_spend,
                "remaining_budget": remaining_budget,
                "daily_budget": self.daily_budget,
                "estimated_cost": estimated_cost,
                "would_exceed": (current_spend + estimated_cost) > self.daily_budget
            }
            
            # Check for alert threshold
            usage_percentage = (current_spend + estimated_cost) / self.daily_budget
            if usage_percentage >= self.alert_threshold:
                result["alert_needed"] = True
                result["usage_percentage"] = usage_percentage
            
            return result
    
    def track_openai_image(self, model: str, size: str, success: bool = True) -> float:
        """Track OpenAI image generation cost."""
        if not success:
            return 0.0
        
        cost = self.pricing["openai"].get(model, {}).get(size, 0.020)  # Default to $0.02
        
        transaction = {
            "timestamp": datetime.now().isoformat(),
            "service": "openai",
            "type": "image_generation",
            "model": model,
            "size": size,
            "cost": cost,
            "success": success
        }
        
        return self._record_transaction(transaction)
    
    def track_openai_text(self, model: str, tokens_in: int, tokens_out: int, success: bool = True) -> float:
        """Track OpenAI text generation cost."""
        if not success:
            return 0.0
        
        model_pricing = self.pricing["openai"].get(model, {})
        input_cost = tokens_in * model_pricing.get("input", 0.0)
        output_cost = tokens_out * model_pricing.get("output", 0.0)
        total_cost = input_cost + output_cost
        
        transaction = {
            "timestamp": datetime.now().isoformat(),
            "service": "openai",
            "type": "text_generation",
            "model": model,
            "tokens_in": tokens_in,
            "tokens_out": tokens_out,
            "cost": total_cost,
            "success": success
        }
        
        return self._record_transaction(transaction)
    
    def _record_transaction(self, transaction: Dict[str, Any]) -> float:
        """Record a transaction and update daily totals."""
        with self.lock:
            # Add transaction to history
            self.costs["transactions"].append(transaction)
            
            # Update daily total
            today = self.get_today_date()
            if today not in self.costs["daily_totals"]:
                self.costs["daily_totals"][today] = 0.0
            
            self.costs["daily_totals"][today] += transaction["cost"]
            
            # Save to file
            self._save_costs()
            
            # Log transaction
            logger.info(f"Cost tracked: {transaction['service']} {transaction['type']} "
                       f"${transaction['cost']:.4f} (Daily total: ${self.costs['daily_totals'][today]:.4f})")
            
            return transaction["cost"]
    
    def should_proceed_with_generation(self, service: str, model: str, estimated_items: int = 1) -> Dict[str, Any]:
        """Check if generation should proceed based on budget."""
        # Estimate cost
        if service == "openai" and "dall-e" in model:
            estimated_cost = estimated_items * self.pricing["openai"].get(model, {}).get("1024x1024", 0.020)
        else:
            estimated_cost = estimated_items * 0.02  # Conservative estimate
        
        budget_check = self.check_budget_available(estimated_cost)
        
        if not budget_check["budget_available"]:
            logger.warning(f"Budget exceeded: ${budget_check['current_spend']:.2f} + ${estimated_cost:.2f} "
                          f"> ${self.daily_budget:.2f}")
            return {
                "proceed": False,
                "reason": "daily_budget_exceeded",
                "budget_info": budget_check
            }
        
        return {
            "proceed": True,
            "estimated_cost": estimated_cost,
            "budget_info": budget_check
        }
    
    def get_cost_summary(self, days: int = 7) -> Dict[str, Any]:
        """Get cost summary for the last N days."""
        today = datetime.now()
        summary = {
            "period_days": days,
            "daily_breakdown": {},
            "total_cost": 0.0,
            "daily_budget": self.daily_budget,
            "average_daily_spend": 0.0
        }
        
        for i in range(days):
            date = (today - timedelta(days=i)).strftime("%Y-%m-%d")
            daily_cost = self.get_daily_spend(date)
            summary["daily_breakdown"][date] = daily_cost
            summary["total_cost"] += daily_cost
        
        summary["average_daily_spend"] = summary["total_cost"] / days if days > 0 else 0
        
        return summary
    
    def reset_daily_costs(self, date: Optional[str] = None):
        """Reset costs for a specific date (for testing)."""
        if date is None:
            date = self.get_today_date()
        
        with self.lock:
            if date in self.costs["daily_totals"]:
                del self.costs["daily_totals"][date]
            
            # Remove transactions for that date
            self.costs["transactions"] = [
                t for t in self.costs["transactions"]
                if not t["timestamp"].startswith(date)
            ]
            
            self._save_costs()
            logger.info(f"Reset costs for {date}")


class CacheManager:
    """Semantic caching to reduce API costs during demos."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize cache manager."""
        self.config = config.get("cache", {})
        self.enabled = self.config.get("enabled", True)
        self.ttl = self.config.get("ttl", 3600)  # 1 hour default
        self.similarity_threshold = self.config.get("semantic_similarity_threshold", 0.90)
        
        self.cache_file = Path(__file__).parent.parent.parent / "cache.json"
        self.cache = self._load_cache()
        self.lock = threading.Lock()
    
    def _load_cache(self) -> Dict[str, Any]:
        """Load cache from storage."""
        if self.cache_file.exists():
            try:
                with open(self.cache_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Failed to load cache: {e}")
        
        return {"entries": {}}
    
    def _save_cache(self):
        """Save cache to storage."""
        if not self.enabled:
            return
        
        try:
            with open(self.cache_file, 'w') as f:
                json.dump(self.cache, f, indent=2, default=str)
        except Exception as e:
            logger.error(f"Failed to save cache: {e}")
    
    def _is_expired(self, timestamp: str) -> bool:
        """Check if cache entry is expired."""
        try:
            cached_time = datetime.fromisoformat(timestamp)
            return (datetime.now() - cached_time).total_seconds() > self.ttl
        except:
            return True
    
    def get_cached_result(self, prompt: str, generation_type: str = "image") -> Optional[Any]:
        """Get cached result for a prompt if available."""
        if not self.enabled:
            return None
        
        with self.lock:
            cache_key = f"{generation_type}:{hash(prompt)}"
            
            if cache_key in self.cache["entries"]:
                entry = self.cache["entries"][cache_key]
                
                if not self._is_expired(entry["timestamp"]):
                    logger.info(f"Cache hit for {generation_type} prompt")
                    entry["hit_count"] = entry.get("hit_count", 0) + 1
                    return entry["result"]
                else:
                    # Remove expired entry
                    del self.cache["entries"][cache_key]
        
        return None
    
    def cache_result(self, prompt: str, result: Any, generation_type: str = "image"):
        """Cache a generation result."""
        if not self.enabled:
            return
        
        with self.lock:
            cache_key = f"{generation_type}:{hash(prompt)}"
            
            entry = {
                "timestamp": datetime.now().isoformat(),
                "prompt": prompt[:200],  # Store truncated prompt for reference
                "result": result,
                "generation_type": generation_type,
                "hit_count": 0
            }
            
            self.cache["entries"][cache_key] = entry
            self._save_cache()
            
            logger.info(f"Cached {generation_type} result for future use")
    
    def cleanup_expired(self):
        """Remove expired cache entries."""
        if not self.enabled:
            return
        
        with self.lock:
            expired_keys = [
                key for key, entry in self.cache["entries"].items()
                if self._is_expired(entry["timestamp"])
            ]
            
            for key in expired_keys:
                del self.cache["entries"][key]
            
            if expired_keys:
                self._save_cache()
                logger.info(f"Cleaned up {len(expired_keys)} expired cache entries")
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache performance statistics."""
        if not self.enabled:
            return {"enabled": False}
        
        entries = self.cache["entries"]
        total_hits = sum(entry.get("hit_count", 0) for entry in entries.values())
        
        return {
            "enabled": True,
            "total_entries": len(entries),
            "total_hits": total_hits,
            "ttl_seconds": self.ttl,
            "similarity_threshold": self.similarity_threshold,
            "cache_file_size": self.cache_file.stat().st_size if self.cache_file.exists() else 0
        }