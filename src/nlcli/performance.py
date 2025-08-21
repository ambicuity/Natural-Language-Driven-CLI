"""
Performance Monitoring and Optimization Module.
Implements profiling, caching, resource monitoring, and performance optimization.
"""

import functools
import logging
import threading
import time
from collections import defaultdict, deque
from contextlib import contextmanager
from dataclasses import dataclass, field

from typing import Any, Callable, Dict, List, Optional, Tuple

import psutil


@dataclass
class PerformanceMetrics:
    """Performance metrics for operations."""

    operation: str
    start_time: float
    end_time: float
    duration: float
    cpu_percent: float
    memory_mb: float
    success: bool
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ResourceUsage:
    """Current system resource usage."""

    cpu_percent: float
    memory_percent: float
    memory_used_mb: float
    memory_available_mb: float
    disk_usage_percent: float
    open_files: int
    timestamp: float


class PerformanceCache:
    """Thread-safe LRU cache for expensive operations."""

    def __init__(self, max_size: int = 1000, ttl_seconds: int = 3600):
        self.max_size = max_size
        self.ttl_seconds = ttl_seconds
        self._cache: Dict[str, Tuple[Any, float]] = {}
        self._access_order: deque = deque()
        self._lock = threading.RLock()
        self._hits = 0
        self._misses = 0

    def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        with self._lock:
            if key not in self._cache:
                self._misses += 1
                return None

            value, timestamp = self._cache[key]

            # Check TTL
            if time.time() - timestamp > self.ttl_seconds:
                del self._cache[key]
                try:
                    self._access_order.remove(key)
                except ValueError:
                    pass
                self._misses += 1
                return None

            # Update access order
            try:
                self._access_order.remove(key)
            except ValueError:
                pass
            self._access_order.append(key)

            self._hits += 1
            return value

    def put(self, key: str, value: Any) -> None:
        """Put value in cache."""
        with self._lock:
            current_time = time.time()

            # Remove oldest items if cache is full
            while len(self._cache) >= self.max_size and self._access_order:
                oldest_key = self._access_order.popleft()
                self._cache.pop(oldest_key, None)

            # Add new item
            self._cache[key] = (value, current_time)
            self._access_order.append(key)

    def clear(self) -> None:
        """Clear cache."""
        with self._lock:
            self._cache.clear()
            self._access_order.clear()
            self._hits = 0
            self._misses = 0

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        with self._lock:
            total_requests = self._hits + self._misses
            hit_rate = self._hits / total_requests if total_requests > 0 else 0

            return {
                "size": len(self._cache),
                "max_size": self.max_size,
                "hits": self._hits,
                "misses": self._misses,
                "hit_rate": hit_rate,
                "ttl_seconds": self.ttl_seconds,
            }


class PerformanceProfiler:
    """Performance profiler for tracking operation metrics."""

    def __init__(self, max_metrics: int = 10000):
        self.max_metrics = max_metrics
        self.metrics: deque = deque(maxlen=max_metrics)
        self._lock = threading.RLock()
        self.logger = logging.getLogger(f"{__name__}.PerformanceProfiler")

        # Performance thresholds
        self.slow_operation_threshold = 2.0  # seconds
        self.memory_warning_threshold = 100  # MB
        self.cpu_warning_threshold = 80  # percent

    @contextmanager
    def profile_operation(self, operation: str, metadata: Optional[Dict] = None):
        """Context manager for profiling operations."""
        start_time = time.time()
        start_cpu = psutil.cpu_percent()
        process = psutil.Process()
        start_memory = process.memory_info().rss / 1024 / 1024  # MB

        success = True
        error_message = None

        try:
            yield
        except Exception as e:
            success = False
            error_message = str(e)
            raise
        finally:
            end_time = time.time()
            duration = end_time - start_time
            end_cpu = psutil.cpu_percent()
            end_memory = process.memory_info().rss / 1024 / 1024  # MB

            metrics = PerformanceMetrics(
                operation=operation,
                start_time=start_time,
                end_time=end_time,
                duration=duration,
                cpu_percent=max(start_cpu, end_cpu),
                memory_mb=max(start_memory, end_memory),
                success=success,
                error_message=error_message,
                metadata=metadata or {},
            )

            self._record_metrics(metrics)

    def _record_metrics(self, metrics: PerformanceMetrics) -> None:
        """Record performance metrics."""
        with self._lock:
            self.metrics.append(metrics)

            # Log performance warnings
            if metrics.duration > self.slow_operation_threshold:
                self.logger.warning(
                    f"Slow operation detected: {metrics.operation} took {metrics.duration:.2f}s"
                )

            if metrics.memory_mb > self.memory_warning_threshold:
                self.logger.warning(
                    f"High memory usage: {metrics.operation} used {metrics.memory_mb:.2f}MB"
                )

            if metrics.cpu_percent > self.cpu_warning_threshold:
                self.logger.warning(
                    f"High CPU usage: {metrics.operation} used {metrics.cpu_percent:.1f}% CPU"
                )

    def get_metrics_summary(
        self, operation_filter: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get summary of performance metrics."""
        with self._lock:
            if not self.metrics:
                return {"total_operations": 0}

            # Filter metrics if needed
            filtered_metrics = list(self.metrics)
            if operation_filter:
                filtered_metrics = [
                    m for m in filtered_metrics if operation_filter in m.operation
                ]

            if not filtered_metrics:
                return {"total_operations": 0, "filter": operation_filter}

            # Calculate statistics
            durations = [m.duration for m in filtered_metrics]
            memory_usage = [m.memory_mb for m in filtered_metrics]
            cpu_usage = [m.cpu_percent for m in filtered_metrics]
            success_rate = sum(1 for m in filtered_metrics if m.success) / len(
                filtered_metrics
            )

            # Group by operation
            by_operation = defaultdict(list)
            for metric in filtered_metrics:
                by_operation[metric.operation].append(metric)

            operation_stats = {}
            for op, op_metrics in by_operation.items():
                op_durations = [m.duration for m in op_metrics]
                operation_stats[op] = {
                    "count": len(op_metrics),
                    "avg_duration": sum(op_durations) / len(op_durations),
                    "min_duration": min(op_durations),
                    "max_duration": max(op_durations),
                    "success_rate": sum(1 for m in op_metrics if m.success)
                    / len(op_metrics),
                }

            return {
                "total_operations": len(filtered_metrics),
                "success_rate": success_rate,
                "duration_stats": {
                    "avg": sum(durations) / len(durations),
                    "min": min(durations),
                    "max": max(durations),
                    "slow_operations": len(
                        [d for d in durations if d > self.slow_operation_threshold]
                    ),
                },
                "memory_stats": {
                    "avg_mb": sum(memory_usage) / len(memory_usage),
                    "max_mb": max(memory_usage),
                    "high_usage_operations": len(
                        [m for m in memory_usage if m > self.memory_warning_threshold]
                    ),
                },
                "cpu_stats": {
                    "avg_percent": sum(cpu_usage) / len(cpu_usage),
                    "max_percent": max(cpu_usage),
                    "high_usage_operations": len(
                        [c for c in cpu_usage if c > self.cpu_warning_threshold]
                    ),
                },
                "by_operation": operation_stats,
            }

    def get_slowest_operations(self, limit: int = 10) -> List[PerformanceMetrics]:
        """Get the slowest operations."""
        with self._lock:
            sorted_metrics = sorted(
                self.metrics, key=lambda m: m.duration, reverse=True
            )
            return list(sorted_metrics[:limit])

    def clear_metrics(self) -> None:
        """Clear all metrics."""
        with self._lock:
            self.metrics.clear()


class ResourceMonitor:
    """Monitor system resource usage."""

    def __init__(self, sampling_interval: float = 1.0):
        self.sampling_interval = sampling_interval
        self.monitoring = False
        self.resource_history: deque = deque(maxlen=3600)  # Last hour
        self._monitor_thread: Optional[threading.Thread] = None
        self.logger = logging.getLogger(f"{__name__}.ResourceMonitor")

    def start_monitoring(self) -> None:
        """Start resource monitoring."""
        if self.monitoring:
            return

        self.monitoring = True
        self._monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self._monitor_thread.start()
        self.logger.info("Resource monitoring started")

    def stop_monitoring(self) -> None:
        """Stop resource monitoring."""
        self.monitoring = False
        if self._monitor_thread:
            self._monitor_thread.join(timeout=2.0)
        self.logger.info("Resource monitoring stopped")

    def _monitor_loop(self) -> None:
        """Main monitoring loop."""
        while self.monitoring:
            try:
                usage = self._collect_resource_usage()
                self.resource_history.append(usage)

                # Check for resource warnings
                self._check_resource_warnings(usage)

                time.sleep(self.sampling_interval)
            except Exception as e:
                self.logger.error(f"Error in resource monitoring: {e}")
                time.sleep(self.sampling_interval)

    def _collect_resource_usage(self) -> ResourceUsage:
        """Collect current resource usage."""
        # CPU usage
        cpu_percent = psutil.cpu_percent()

        # Memory usage
        memory = psutil.virtual_memory()
        memory_percent = memory.percent
        memory_used_mb = memory.used / 1024 / 1024
        memory_available_mb = memory.available / 1024 / 1024

        # Disk usage
        disk = psutil.disk_usage("/")
        disk_usage_percent = disk.percent

        # Process info
        process = psutil.Process()
        open_files = len(process.open_files())

        return ResourceUsage(
            cpu_percent=cpu_percent,
            memory_percent=memory_percent,
            memory_used_mb=memory_used_mb,
            memory_available_mb=memory_available_mb,
            disk_usage_percent=disk_usage_percent,
            open_files=open_files,
            timestamp=time.time(),
        )

    def _check_resource_warnings(self, usage: ResourceUsage) -> None:
        """Check for resource usage warnings."""
        if usage.cpu_percent > 90:
            self.logger.warning(f"High CPU usage: {usage.cpu_percent:.1f}%")

        if usage.memory_percent > 90:
            self.logger.warning(f"High memory usage: {usage.memory_percent:.1f}%")

        if usage.disk_usage_percent > 90:
            self.logger.warning(f"High disk usage: {usage.disk_usage_percent:.1f}%")

    def get_current_usage(self) -> Optional[ResourceUsage]:
        """Get current resource usage."""
        if not self.resource_history:
            return self._collect_resource_usage()
        return self.resource_history[-1]

    def get_usage_history(self, minutes: int = 60) -> List[ResourceUsage]:
        """Get resource usage history."""
        cutoff_time = time.time() - (minutes * 60)
        return [
            usage for usage in self.resource_history if usage.timestamp >= cutoff_time
        ]


def cached(cache_key_func: Optional[Callable] = None, ttl_seconds: int = 3600):
    """Decorator for caching expensive function calls."""

    def decorator(func: Callable) -> Callable:
        cache = PerformanceCache(ttl_seconds=ttl_seconds)

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Generate cache key
            if cache_key_func:
                cache_key = cache_key_func(*args, **kwargs)
            else:
                cache_key = (
                    f"{func.__name__}:{hash((args, tuple(sorted(kwargs.items()))))}"
                )

            # Try to get from cache
            result = cache.get(cache_key)
            if result is not None:
                return result

            # Compute and cache result
            result = func(*args, **kwargs)
            cache.put(cache_key, result)
            return result

        # Add cache management methods
        wrapper.cache = cache
        wrapper.clear_cache = cache.clear
        wrapper.cache_stats = cache.get_stats

        return wrapper

    return decorator


# Global instances
_performance_profiler: Optional[PerformanceProfiler] = None
_resource_monitor: Optional[ResourceMonitor] = None


def get_performance_profiler() -> PerformanceProfiler:
    """Get global performance profiler instance."""
    global _performance_profiler
    if _performance_profiler is None:
        _performance_profiler = PerformanceProfiler()
    return _performance_profiler


def get_resource_monitor() -> ResourceMonitor:
    """Get global resource monitor instance."""
    global _resource_monitor
    if _resource_monitor is None:
        _resource_monitor = ResourceMonitor()
    return _resource_monitor


def profile_operation(operation_name: str, metadata: Optional[Dict] = None):
    """Decorator/context manager for profiling operations."""
    return get_performance_profiler().profile_operation(operation_name, metadata)


def optimize_startup():
    """Optimize application startup performance."""
    # Start resource monitoring
    monitor = get_resource_monitor()
    monitor.start_monitoring()

    # Pre-warm caches if needed
    # This could be extended to pre-load commonly used tools, etc.
    pass