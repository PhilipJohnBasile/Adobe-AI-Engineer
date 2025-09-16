"""
Free Monitoring and Observability System
Using Prometheus metrics, health checks, and performance tracking
"""

import time
import psutil
import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from collections import defaultdict, deque
from dataclasses import dataclass, asdict
import threading
import logging
from functools import wraps
import asyncio


class MetricsRegistry:
    """Free metrics registry compatible with Prometheus format"""
    
    def __init__(self):
        self.counters = defaultdict(int)
        self.gauges = defaultdict(float)
        self.histograms = defaultdict(list)
        self.timers = defaultdict(list)
        self.labels = defaultdict(dict)
        self._lock = threading.Lock()
    
    def increment_counter(self, name: str, value: int = 1, labels: Dict[str, str] = None):
        """Increment a counter metric"""
        with self._lock:
            key = self._make_key(name, labels)
            self.counters[key] += value
            if labels:
                self.labels[key] = labels
    
    def set_gauge(self, name: str, value: float, labels: Dict[str, str] = None):
        """Set a gauge metric value"""
        with self._lock:
            key = self._make_key(name, labels)
            self.gauges[key] = value
            if labels:
                self.labels[key] = labels
    
    def observe_histogram(self, name: str, value: float, labels: Dict[str, str] = None):
        """Add observation to histogram"""
        with self._lock:
            key = self._make_key(name, labels)
            self.histograms[key].append(value)
            # Keep only last 1000 observations to prevent memory bloat
            if len(self.histograms[key]) > 1000:
                self.histograms[key] = self.histograms[key][-1000:]
            if labels:
                self.labels[key] = labels
    
    def time_operation(self, name: str, labels: Dict[str, str] = None):
        """Context manager for timing operations"""
        return TimingContext(self, name, labels)
    
    def _make_key(self, name: str, labels: Dict[str, str] = None) -> str:
        """Create metric key with labels"""
        if not labels:
            return name
        label_str = ",".join(f"{k}={v}" for k, v in sorted(labels.items()))
        return f"{name}{{{label_str}}}"
    
    def export_prometheus_format(self) -> str:
        """Export metrics in Prometheus format"""
        lines = []
        
        # Counters
        for key, value in self.counters.items():
            lines.append(f"# TYPE {key.split('{')[0]} counter")
            lines.append(f"{key} {value}")
        
        # Gauges
        for key, value in self.gauges.items():
            lines.append(f"# TYPE {key.split('{')[0]} gauge")
            lines.append(f"{key} {value}")
        
        # Histograms (simplified)
        for key, values in self.histograms.items():
            if values:
                metric_name = key.split('{')[0]
                lines.append(f"# TYPE {metric_name} histogram")
                lines.append(f"{key}_count {len(values)}")
                lines.append(f"{key}_sum {sum(values)}")
                lines.append(f"{key}_avg {sum(values)/len(values)}")
                lines.append(f"{key}_min {min(values)}")
                lines.append(f"{key}_max {max(values)}")
        
        return "\n".join(lines)
    
    def get_metrics_summary(self) -> Dict[str, Any]:
        """Get human-readable metrics summary"""
        summary = {
            "counters": dict(self.counters),
            "gauges": dict(self.gauges),
            "histograms": {}
        }
        
        for key, values in self.histograms.items():
            if values:
                summary["histograms"][key] = {
                    "count": len(values),
                    "sum": sum(values),
                    "avg": sum(values) / len(values),
                    "min": min(values),
                    "max": max(values)
                }
        
        return summary


class TimingContext:
    """Context manager for timing operations"""
    
    def __init__(self, registry: MetricsRegistry, name: str, labels: Dict[str, str] = None):
        self.registry = registry
        self.name = name
        self.labels = labels
        self.start_time = None
    
    def __enter__(self):
        self.start_time = time.time()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.start_time:
            duration = time.time() - self.start_time
            self.registry.observe_histogram(f"{self.name}_duration_seconds", duration, self.labels)
            
            # Also track success/failure
            status = "success" if exc_type is None else "error"
            labels = dict(self.labels or {})
            labels["status"] = status
            self.registry.increment_counter(f"{self.name}_total", 1, labels)


class SystemMetricsCollector:
    """Collects system performance metrics"""
    
    def __init__(self, registry: MetricsRegistry):
        self.registry = registry
        self.collection_interval = 15  # seconds
        self._running = False
        self._thread = None
    
    def start(self):
        """Start background metrics collection"""
        if not self._running:
            self._running = True
            self._thread = threading.Thread(target=self._collect_loop, daemon=True)
            self._thread.start()
    
    def stop(self):
        """Stop background metrics collection"""
        self._running = False
        if self._thread:
            self._thread.join(timeout=5)
    
    def _collect_loop(self):
        """Background collection loop"""
        while self._running:
            try:
                self._collect_system_metrics()
                time.sleep(self.collection_interval)
            except Exception as e:
                logging.error(f"Error collecting system metrics: {e}")
                time.sleep(self.collection_interval)
    
    def _collect_system_metrics(self):
        """Collect current system metrics"""
        # CPU metrics
        cpu_percent = psutil.cpu_percent(interval=1)
        self.registry.set_gauge("system_cpu_usage_percent", cpu_percent)
        
        # Memory metrics
        memory = psutil.virtual_memory()
        self.registry.set_gauge("system_memory_usage_bytes", memory.used)
        self.registry.set_gauge("system_memory_total_bytes", memory.total)
        self.registry.set_gauge("system_memory_usage_percent", memory.percent)
        
        # Disk metrics
        disk = psutil.disk_usage('/')
        self.registry.set_gauge("system_disk_usage_bytes", disk.used)
        self.registry.set_gauge("system_disk_total_bytes", disk.total)
        self.registry.set_gauge("system_disk_usage_percent", (disk.used / disk.total) * 100)
        
        # Process metrics
        process = psutil.Process()
        self.registry.set_gauge("process_memory_usage_bytes", process.memory_info().rss)
        self.registry.set_gauge("process_cpu_usage_percent", process.cpu_percent())
        
        # Network I/O (if available)
        try:
            net_io = psutil.net_io_counters()
            self.registry.set_gauge("system_network_bytes_sent", net_io.bytes_sent)
            self.registry.set_gauge("system_network_bytes_recv", net_io.bytes_recv)
        except:
            pass


@dataclass
class HealthCheck:
    """Individual health check definition"""
    name: str
    description: str
    check_function: callable
    timeout: float = 5.0
    critical: bool = True


class HealthCheckManager:
    """Manages application health checks"""
    
    def __init__(self):
        self.checks: List[HealthCheck] = []
        self.last_results: Dict[str, Any] = {}
        self.registry = None  # Will be injected
    
    def add_check(self, name: str, description: str, check_function: callable, 
                  timeout: float = 5.0, critical: bool = True):
        """Add a health check"""
        check = HealthCheck(name, description, check_function, timeout, critical)
        self.checks.append(check)
    
    async def run_all_checks(self) -> Dict[str, Any]:
        """Run all health checks and return results"""
        results = {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "checks": {},
            "summary": {
                "total": len(self.checks),
                "passed": 0,
                "failed": 0,
                "critical_failed": 0
            }
        }
        
        for check in self.checks:
            try:
                # Run check with timeout
                start_time = time.time()
                check_result = await asyncio.wait_for(
                    asyncio.get_event_loop().run_in_executor(None, check.check_function),
                    timeout=check.timeout
                )
                duration = time.time() - start_time
                
                results["checks"][check.name] = {
                    "status": "pass",
                    "description": check.description,
                    "duration": duration,
                    "critical": check.critical,
                    "details": check_result if isinstance(check_result, dict) else {"result": check_result}
                }
                results["summary"]["passed"] += 1
                
                # Record metrics
                if self.registry:
                    self.registry.observe_histogram("health_check_duration_seconds", duration, 
                                                  {"check": check.name})
                    self.registry.increment_counter("health_check_total", 1, 
                                                  {"check": check.name, "status": "pass"})
                
            except asyncio.TimeoutError:
                results["checks"][check.name] = {
                    "status": "fail",
                    "description": check.description,
                    "error": f"Timeout after {check.timeout}s",
                    "critical": check.critical
                }
                results["summary"]["failed"] += 1
                if check.critical:
                    results["summary"]["critical_failed"] += 1
                
                if self.registry:
                    self.registry.increment_counter("health_check_total", 1, 
                                                  {"check": check.name, "status": "timeout"})
                
            except Exception as e:
                results["checks"][check.name] = {
                    "status": "fail",
                    "description": check.description,
                    "error": str(e),
                    "critical": check.critical
                }
                results["summary"]["failed"] += 1
                if check.critical:
                    results["summary"]["critical_failed"] += 1
                
                if self.registry:
                    self.registry.increment_counter("health_check_total", 1, 
                                                  {"check": check.name, "status": "error"})
        
        # Determine overall status
        if results["summary"]["critical_failed"] > 0:
            results["status"] = "unhealthy"
        elif results["summary"]["failed"] > 0:
            results["status"] = "degraded"
        
        self.last_results = results
        return results
    
    def get_last_results(self) -> Dict[str, Any]:
        """Get last health check results"""
        return self.last_results


class PerformanceTracker:
    """Tracks application performance metrics"""
    
    def __init__(self, registry: MetricsRegistry):
        self.registry = registry
        self.request_times = deque(maxlen=1000)
        self.error_counts = defaultdict(int)
        self.active_requests = 0
    
    def track_request(self, endpoint: str, method: str = "GET"):
        """Track an incoming request"""
        return RequestTracker(self, endpoint, method)
    
    def record_error(self, error_type: str, endpoint: str = None):
        """Record an application error"""
        labels = {"error_type": error_type}
        if endpoint:
            labels["endpoint"] = endpoint
        
        self.registry.increment_counter("application_errors_total", 1, labels)
        self.error_counts[error_type] += 1
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Get performance summary"""
        if not self.request_times:
            return {"message": "No requests tracked yet"}
        
        times = list(self.request_times)
        return {
            "active_requests": self.active_requests,
            "total_requests": len(times),
            "avg_response_time": sum(times) / len(times),
            "min_response_time": min(times),
            "max_response_time": max(times),
            "error_counts": dict(self.error_counts)
        }


class RequestTracker:
    """Context manager for tracking individual requests"""
    
    def __init__(self, performance_tracker: PerformanceTracker, endpoint: str, method: str):
        self.tracker = performance_tracker
        self.endpoint = endpoint
        self.method = method
        self.start_time = None
    
    def __enter__(self):
        self.start_time = time.time()
        self.tracker.active_requests += 1
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.start_time:
            duration = time.time() - self.start_time
            self.tracker.request_times.append(duration)
            self.tracker.active_requests -= 1
            
            # Record metrics
            labels = {"endpoint": self.endpoint, "method": self.method}
            status = "success" if exc_type is None else "error"
            labels["status"] = status
            
            self.tracker.registry.observe_histogram("http_request_duration_seconds", duration, labels)
            self.tracker.registry.increment_counter("http_requests_total", 1, labels)
            
            if exc_type is not None:
                self.tracker.record_error(exc_type.__name__, self.endpoint)


class MonitoringSystem:
    """Complete monitoring system orchestrator"""
    
    def __init__(self):
        self.registry = MetricsRegistry()
        self.health_checks = HealthCheckManager()
        self.health_checks.registry = self.registry
        self.performance = PerformanceTracker(self.registry)
        self.system_collector = SystemMetricsCollector(self.registry)
        
        # Add default health checks
        self._setup_default_health_checks()
    
    def start(self):
        """Start monitoring system"""
        self.system_collector.start()
        logging.info("Monitoring system started")
    
    def stop(self):
        """Stop monitoring system"""
        self.system_collector.stop()
        logging.info("Monitoring system stopped")
    
    def _setup_default_health_checks(self):
        """Setup default health checks"""
        
        def check_disk_space():
            disk = psutil.disk_usage('/')
            usage_percent = (disk.used / disk.total) * 100
            if usage_percent > 90:
                return {"status": "critical", "usage_percent": usage_percent}
            elif usage_percent > 80:
                return {"status": "warning", "usage_percent": usage_percent}
            return {"status": "ok", "usage_percent": usage_percent}
        
        def check_memory():
            memory = psutil.virtual_memory()
            if memory.percent > 90:
                return {"status": "critical", "usage_percent": memory.percent}
            elif memory.percent > 80:
                return {"status": "warning", "usage_percent": memory.percent}
            return {"status": "ok", "usage_percent": memory.percent}
        
        def check_openai_config():
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                raise Exception("OpenAI API key not configured")
            return {"status": "configured", "key_length": len(api_key)}
        
        def check_file_permissions():
            test_dirs = ["output", "assets", "generated_cache"]
            for dir_name in test_dirs:
                if not os.path.exists(dir_name):
                    os.makedirs(dir_name, exist_ok=True)
                if not os.access(dir_name, os.W_OK):
                    raise Exception(f"No write access to {dir_name}")
            return {"status": "ok", "directories_checked": len(test_dirs)}
        
        # Add health checks
        self.health_checks.add_check("disk_space", "Check available disk space", 
                                   check_disk_space, critical=True)
        self.health_checks.add_check("memory", "Check memory usage", 
                                   check_memory, critical=True)
        self.health_checks.add_check("openai_config", "Check OpenAI API configuration", 
                                   check_openai_config, critical=False)
        self.health_checks.add_check("file_permissions", "Check file system permissions", 
                                   check_file_permissions, critical=True)
    
    def export_metrics(self, format: str = "prometheus") -> str:
        """Export metrics in specified format"""
        if format == "prometheus":
            return self.registry.export_prometheus_format()
        elif format == "json":
            return json.dumps(self.registry.get_metrics_summary(), indent=2)
        else:
            raise ValueError(f"Unsupported format: {format}")
    
    async def get_comprehensive_status(self) -> Dict[str, Any]:
        """Get comprehensive system status"""
        health_results = await self.health_checks.run_all_checks()
        performance_summary = self.performance.get_performance_summary()
        metrics_summary = self.registry.get_metrics_summary()
        
        return {
            "timestamp": datetime.now().isoformat(),
            "overall_status": health_results["status"],
            "health_checks": health_results,
            "performance": performance_summary,
            "metrics_summary": {
                "counters_count": len(metrics_summary["counters"]),
                "gauges_count": len(metrics_summary["gauges"]),
                "histograms_count": len(metrics_summary["histograms"])
            },
            "system_info": {
                "cpu_count": psutil.cpu_count(),
                "memory_total_gb": round(psutil.virtual_memory().total / (1024**3), 2),
                "disk_total_gb": round(psutil.disk_usage('/').total / (1024**3), 2)
            }
        }


# Decorator for automatic monitoring
def monitor_function(name: str = None, labels: Dict[str, str] = None):
    """Decorator to automatically monitor function calls"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            func_name = name or f"{func.__module__}.{func.__name__}"
            
            # Get monitoring system from global context or create one
            monitoring = getattr(wrapper, '_monitoring_system', None)
            if not monitoring:
                monitoring = MonitoringSystem()
                wrapper._monitoring_system = monitoring
            
            with monitoring.registry.time_operation(f"function_{func_name}", labels):
                try:
                    result = func(*args, **kwargs)
                    monitoring.registry.increment_counter(f"function_{func_name}_calls", 1, 
                                                        dict(labels or {}, status="success"))
                    return result
                except Exception as e:
                    monitoring.registry.increment_counter(f"function_{func_name}_calls", 1, 
                                                        dict(labels or {}, status="error"))
                    monitoring.performance.record_error(type(e).__name__, func_name)
                    raise
        
        return wrapper
    return decorator


# Global monitoring instance
monitoring_system = MonitoringSystem()