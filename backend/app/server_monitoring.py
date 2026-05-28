"""
Server Monitoring & Logging System
Comprehensive monitoring for performance, health, and logging
"""
import logging
import time
import psutil
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from functools import wraps
from collections import deque
import json

from app.cache import set_in_cache, get_from_cache
from app.database import get_db

logger = logging.getLogger(__name__)


class PerformanceMonitor:
    """Monitor API performance and response times"""

    def __init__(self, max_history: int = 1000):
        self.request_times: deque = deque(maxlen=max_history)
        self.error_counts: Dict[str, int] = {}
        self.endpoint_stats: Dict[str, Dict] = {}
        self.start_time = datetime.utcnow()

    def record_request(self, endpoint: str, duration_ms: float, status_code: int):
        """Record API request metrics"""
        self.request_times.append({
            "endpoint": endpoint,
            "duration_ms": duration_ms,
            "status_code": status_code,
            "timestamp": datetime.utcnow()
        })

        # Update endpoint stats
        if endpoint not in self.endpoint_stats:
            self.endpoint_stats[endpoint] = {
                "count": 0,
                "total_time": 0,
                "errors": 0,
                "avg_time": 0
            }

        stats = self.endpoint_stats[endpoint]
        stats["count"] += 1
        stats["total_time"] += duration_ms
        stats["avg_time"] = stats["total_time"] / stats["count"]

        if status_code >= 400:
            stats["errors"] += 1
            self.error_counts[endpoint] = self.error_counts.get(endpoint, 0) + 1

    def get_stats(self) -> Dict:
        """Get performance statistics"""
        if not self.request_times:
            return {"message": "No requests recorded yet"}

        times = [r["duration_ms"] for r in self.request_times]
        total_requests = len(times)
        error_count = sum(1 for r in self.request_times if r["status_code"] >= 400)

        return {
            "total_requests": total_requests,
            "error_count": error_count,
            "error_rate": f"{(error_count / total_requests * 100):.2f}%" if total_requests > 0 else "0%",
            "avg_response_time": f"{sum(times) / len(times):.2f}ms",
            "p50_response_time": f"{self._percentile(times, 50):.2f}ms",
            "p95_response_time": f"{self._percentile(times, 95):.2f}ms",
            "p99_response_time": f"{self._percentile(times, 99):.2f}ms",
            "uptime_seconds": (datetime.utcnow() - self.start_time).total_seconds(),
            "endpoint_breakdown": self.endpoint_stats
        }

    def _percentile(self, data: List[float], percentile: int) -> float:
        """Calculate percentile"""
        if not data:
            return 0
        sorted_data = sorted(data)
        index = int(len(sorted_data) * percentile / 100)
        return sorted_data[min(index, len(sorted_data) - 1)]


class SystemMonitor:
    """Monitor system resources (CPU, Memory, Disk)"""

    def __init__(self):
        self.alert_thresholds = {
            "cpu_percent": 80,
            "memory_percent": 85,
            "disk_percent": 90
        }

    def get_system_stats(self) -> Dict:
        """Get current system statistics"""
        try:
            cpu_percent = psutil.cpu_percent(interval=0.1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')

            return {
                "timestamp": datetime.utcnow().isoformat(),
                "cpu": {
                    "percent": cpu_percent,
                    "cores": psutil.cpu_count(),
                    "alert": cpu_percent > self.alert_thresholds["cpu_percent"]
                },
                "memory": {
                    "total_gb": round(memory.total / (1024**3), 2),
                    "used_gb": round(memory.used / (1024**3), 2),
                    "percent": memory.percent,
                    "available_gb": round(memory.available / (1024**3), 2),
                    "alert": memory.percent > self.alert_thresholds["memory_percent"]
                },
                "disk": {
                    "total_gb": round(disk.total / (1024**3), 2),
                    "used_gb": round(disk.used / (1024**3), 2),
                    "percent": round(disk.percent, 2),
                    "alert": disk.percent > self.alert_thresholds["disk_percent"]
                }
            }
        except Exception as e:
            logger.error(f"Error getting system stats: {e}")
            return {"error": str(e)}

    async def check_alerts(self) -> List[Dict]:
        """Check for system alerts"""
        stats = self.get_system_stats()
        alerts = []

        if stats.get("cpu", {}).get("alert"):
            alerts.append({
                "type": "cpu_high",
                "message": f"CPU usage is {stats['cpu']['percent']}%",
                "severity": "warning"
            })

        if stats.get("memory", {}).get("alert"):
            alerts.append({
                "type": "memory_high",
                "message": f"Memory usage is {stats['memory']['percent']}%",
                "severity": "warning"
            })

        if stats.get("disk", {}).get("alert"):
            alerts.append({
                "type": "disk_high",
                "message": f"Disk usage is {stats['disk']['percent']}%",
                "severity": "critical"
            })

        return alerts


class StructuredLogger:
    """Structured logging with JSON format for better parsing"""

    def __init__(self, name: str):
        self.logger = logging.getLogger(name)

    def log(self, level: str, message: str, extra: Dict = None):
        """Log with structured data"""
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": level.upper(),
            "message": message,
            "service": "housing-platform"
        }

        if extra:
            log_data.update(extra)

        log_json = json.dumps(log_data)

        if level.lower() == "error":
            self.logger.error(log_json)
        elif level.lower() == "warning":
            self.logger.warning(log_json)
        elif level.lower() == "info":
            self.logger.info(log_json)
        elif level.lower() == "debug":
            self.logger.debug(log_json)

    def info(self, message: str, extra: Dict = None):
        self.log("info", message, extra)

    def error(self, message: str, extra: Dict = None):
        self.log("error", message, extra)

    def warning(self, message: str, extra: Dict = None):
        self.log("warning", message, extra)

    def debug(self, message: str, extra: Dict = None):
        self.log("debug", message, extra)


class CacheMonitor:
    """Monitor cache performance and statistics"""

    def __init__(self):
        self.hits = 0
        self.misses = 0
        self.evictions = 0

    def record_hit(self):
        self.hits += 1

    def record_miss(self):
        self.misses += 1

    def record_eviction(self):
        self.evictions += 1

    def get_stats(self) -> Dict:
        total = self.hits + self.misses
        hit_rate = (self.hits / total * 100) if total > 0 else 0

        return {
            "hits": self.hits,
            "misses": self.misses,
            "evictions": self.evictions,
            "total_requests": total,
            "hit_rate": f"{hit_rate:.2f}%"
        }


class DatabaseMonitor:
    """Monitor database performance"""

    def __init__(self):
        self.query_times: deque = deque(maxlen=100)
        self.slow_queries: deque = deque(maxlen=50)
        self.slow_query_threshold_ms = 100

    def record_query(self, operation: str, collection: str, duration_ms: float):
        """Record database query metrics"""
        query_info = {
            "operation": operation,
            "collection": collection,
            "duration_ms": duration_ms,
            "timestamp": datetime.utcnow()
        }

        self.query_times.append(query_info)

        if duration_ms > self.slow_query_threshold_ms:
            self.slow_queries.append(query_info)
            logger.warning(f"Slow query detected: {operation} on {collection} took {duration_ms:.2f}ms")

    def get_stats(self) -> Dict:
        if not self.query_times:
            return {"message": "No queries recorded"}

        times = [q["duration_ms"] for q in self.query_times]

        return {
            "total_queries": len(self.query_times),
            "avg_query_time": f"{sum(times) / len(times):.2f}ms",
            "max_query_time": f"{max(times):.2f}ms",
            "slow_query_threshold": f"{self.slow_query_threshold_ms}ms",
            "slow_queries_count": len(self.slow_queries),
            "recent_slow_queries": list(self.slow_queries)[-5:]
        }


# Global monitoring instances
performance_monitor = PerformanceMonitor()
system_monitor = SystemMonitor()
cache_monitor = CacheMonitor()
database_monitor = DatabaseMonitor()
structured_logger = StructuredLogger("housing-platform")


def monitor_performance(endpoint_name: str = None):
    """Decorator to monitor endpoint performance"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = time.time()
            endpoint = endpoint_name or func.__name__

            try:
                result = await func(*args, **kwargs)
                duration_ms = (time.time() - start_time) * 1000
                performance_monitor.record_request(endpoint, duration_ms, 200)
                return result

            except Exception as e:
                duration_ms = (time.time() - start_time) * 1000
                performance_monitor.record_request(endpoint, duration_ms, 500)
                structured_logger.error(
                    f"Error in {endpoint}",
                    {"endpoint": endpoint, "error": str(e), "duration_ms": duration_ms}
                )
                raise

        return wrapper
    return decorator


def log_operation(operation_type: str):
    """Decorator to log operations"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = time.time()
            user_id = kwargs.get("current_user", {}).get("user_id", "anonymous")

            structured_logger.info(
                f"Starting {operation_type}",
                {"operation": operation_type, "user_id": user_id}
            )

            try:
                result = await func(*args, **kwargs)
                duration_ms = (time.time() - start_time) * 1000

                structured_logger.info(
                    f"Completed {operation_type}",
                    {"operation": operation_type, "duration_ms": duration_ms, "user_id": user_id}
                )
                return result

            except Exception as e:
                structured_logger.error(
                    f"Failed {operation_type}",
                    {"operation": operation_type, "error": str(e), "user_id": user_id}
                )
                raise

        return wrapper
    return decorator


class HealthChecker:
    """Comprehensive health check system"""

    @staticmethod
    async def check_database() -> Dict:
        """Check database health"""
        try:
            db = get_db()
            start_time = time.time()
            await db.command("ping")
            response_time = (time.time() - start_time) * 1000

            return {
                "status": "healthy",
                "response_time_ms": round(response_time, 2)
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e)
            }

    @staticmethod
    async def check_cache() -> Dict:
        """Check cache health"""
        try:
            from app.cache import cache
            if cache:
                await cache.ping()
                return {"status": "healthy"}
            return {"status": "not_configured"}
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e)
            }

    @staticmethod
    def check_system() -> Dict:
        """Check system health"""
        return system_monitor.get_system_stats()

    @staticmethod
    async def full_health_check() -> Dict:
        """Run complete health check"""
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "database": await HealthChecker.check_database(),
            "cache": await HealthChecker.check_cache(),
            "system": HealthChecker.check_system(),
            "performance": performance_monitor.get_stats()
        }


# Background monitoring task
async def monitoring_loop():
    """Background task for continuous monitoring"""
    while True:
        try:
            # Check system alerts
            alerts = await system_monitor.check_alerts()
            if alerts:
                for alert in alerts:
                    structured_logger.warning(
                        f"System alert: {alert['message']}",
                        {"alert_type": alert["type"], "severity": alert["severity"]}
                    )

            # Cache monitoring stats periodically
            cache_stats = cache_monitor.get_stats()
            await set_in_cache("monitoring:cache_stats", cache_stats, ttl=300)

            # Performance stats
            perf_stats = performance_monitor.get_stats()
            await set_in_cache("monitoring:performance", perf_stats, ttl=300)

            await asyncio.sleep(60)  # Run every minute

        except Exception as e:
            logger.error(f"Monitoring loop error: {e}")
            await asyncio.sleep(60)
