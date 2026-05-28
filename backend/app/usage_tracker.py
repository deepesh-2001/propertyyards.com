"""
Usage Tracker
Tracks API usage, resource consumption, and system metrics for analytics and billing
"""
import asyncio
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from collections import defaultdict
import time

logger = logging.getLogger(__name__)


@dataclass
class APICall:
    """API call record"""
    timestamp: datetime
    endpoint: str
    method: str
    user_id: Optional[str]
    response_time_ms: float
    status_code: int
    bytes_sent: int
    bytes_received: int
    ip_address: str
    user_agent: str


@dataclass
class ResourceUsage:
    """Resource usage snapshot"""
    timestamp: datetime
    cpu_percent: float
    memory_mb: float
    disk_io_read: int
    disk_io_write: int
    network_in: int
    network_out: int
    active_connections: int
    request_queue_size: int


@dataclass
class UserActivity:
    """User activity summary"""
    user_id: str
    date: str
    api_calls: int = 0
    endpoints_accessed: set = field(default_factory=set)
    total_response_time_ms: float = 0
    errors: int = 0
    bytes_transferred: int = 0
    peak_concurrent_requests: int = 0
    last_active: Optional[datetime] = None


class UsageTracker:
    """Track system usage and performance metrics"""

    def __init__(self):
        self.enabled = True
        self.buffer: List[APICall] = []
        self.buffer_size = 1000
        self.flush_interval = 60  # seconds
        self.is_tracking = False

        # Aggregated stats
        self.endpoint_stats: Dict[str, Dict] = defaultdict(lambda: {
            "count": 0,
            "total_response_time": 0,
            "errors": 0,
            "bytes_transferred": 0
        })

        self.user_stats: Dict[str, UserActivity] = {}
        self.daily_stats: Dict[str, Dict] = {}

        # Resource tracking
        self.resource_snapshots: List[ResourceUsage] = []
        self.max_snapshots = 10000

    async def start(self):
        """Start usage tracking"""
        self.is_tracking = True
        asyncio.create_task(self._flush_loop())
        asyncio.create_task(self._resource_monitoring_loop())
        logger.info("Usage tracker started")

    async def stop(self):
        """Stop usage tracking"""
        self.is_tracking = False
        await self._flush_buffer()
        logger.info("Usage tracker stopped")

    def record_api_call(
        self,
        endpoint: str,
        method: str,
        user_id: Optional[str],
        response_time_ms: float,
        status_code: int,
        bytes_sent: int = 0,
        bytes_received: int = 0,
        ip_address: str = "",
        user_agent: str = ""
    ):
        """Record an API call"""
        if not self.enabled:
            return

        call = APICall(
            timestamp=datetime.utcnow(),
            endpoint=endpoint,
            method=method,
            user_id=user_id,
            response_time_ms=response_time_ms,
            status_code=status_code,
            bytes_sent=bytes_sent,
            bytes_received=bytes_received,
            ip_address=ip_address,
            user_agent=user_agent
        )

        self.buffer.append(call)

        # Update aggregated stats
        self._update_endpoint_stats(call)
        self._update_user_stats(call)

        # Flush if buffer full
        if len(self.buffer) >= self.buffer_size:
            asyncio.create_task(self._flush_buffer())

    def _update_endpoint_stats(self, call: APICall):
        """Update endpoint statistics"""
        key = f"{call.method} {call.endpoint}"
        stats = self.endpoint_stats[key]
        stats["count"] += 1
        stats["total_response_time"] += call.response_time_ms
        if call.status_code >= 400:
            stats["errors"] += 1
        stats["bytes_transferred"] += call.bytes_sent + call.bytes_received

    def _update_user_stats(self, call: APICall):
        """Update user activity statistics"""
        if not call.user_id:
            return

        today = datetime.utcnow().strftime("%Y-%m-%d")
        key = f"{call.user_id}:{today}"

        if key not in self.user_stats:
            self.user_stats[key] = UserActivity(
                user_id=call.user_id,
                date=today
            )

        activity = self.user_stats[key]
        activity.api_calls += 1
        activity.endpoints_accessed.add(call.endpoint)
        activity.total_response_time_ms += call.response_time_ms
        if call.status_code >= 400:
            activity.errors += 1
        activity.bytes_transferred += call.bytes_sent + call.bytes_received
        activity.last_active = call.timestamp

    async def _flush_loop(self):
        """Periodic buffer flush"""
        while self.is_tracking:
            await asyncio.sleep(self.flush_interval)
            if self.buffer:
                await self._flush_buffer()

    async def _flush_buffer(self):
        """Flush buffer to database"""
        if not self.buffer:
            return

        try:
            from app.database import get_db
            database = get_db()

            # Prepare documents
            documents = []
            for call in self.buffer:
                documents.append({
                    "timestamp": call.timestamp,
                    "endpoint": call.endpoint,
                    "method": call.method,
                    "user_id": call.user_id,
                    "response_time_ms": call.response_time_ms,
                    "status_code": call.status_code,
                    "bytes_sent": call.bytes_sent,
                    "bytes_received": call.bytes_received,
                    "ip_address": call.ip_address,
                    "user_agent": call.user_agent
                })

            # Bulk insert
            if documents:
                await database.api_usage.insert_many(documents)
                logger.debug(f"Flushed {len(documents)} API calls to database")

            # Clear buffer
            self.buffer = []

        except Exception as e:
            logger.error(f"Failed to flush usage buffer: {e}")

    async def _resource_monitoring_loop(self):
        """Monitor system resources"""
        while self.is_tracking:
            try:
                usage = await self._collect_resource_usage()
                self.resource_snapshots.append(usage)

                # Keep only recent snapshots
                if len(self.resource_snapshots) > self.max_snapshots:
                    self.resource_snapshots = self.resource_snapshots[-self.max_snapshots:]

                await asyncio.sleep(10)  # Sample every 10 seconds

            except Exception as e:
                logger.error(f"Resource monitoring error: {e}")
                await asyncio.sleep(30)

    async def _collect_resource_usage(self) -> ResourceUsage:
        """Collect current resource usage"""
        import psutil

        # CPU and Memory
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        memory_mb = memory.used / (1024 * 1024)

        # Disk I/O
        disk_io = psutil.disk_io_counters()
        disk_read = disk_io.read_bytes if disk_io else 0
        disk_write = disk_io.write_bytes if disk_io else 0

        # Network
        net_io = psutil.net_io_counters()
        net_in = net_io.bytes_recv
        net_out = net_io.bytes_sent

        return ResourceUsage(
            timestamp=datetime.utcnow(),
            cpu_percent=cpu_percent,
            memory_mb=memory_mb,
            disk_io_read=disk_read,
            disk_io_write=disk_write,
            network_in=net_in,
            network_out=net_out,
            active_connections=0,  # Would need app-specific tracking
            request_queue_size=0   # Would need app-specific tracking
        )

    def get_endpoint_stats(
        self,
        endpoint_filter: Optional[str] = None,
        since: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Get endpoint usage statistics"""
        stats = {}

        for key, values in self.endpoint_stats.items():
            if endpoint_filter and endpoint_filter not in key:
                continue

            count = values["count"]
            avg_response_time = values["total_response_time"] / count if count > 0 else 0
            error_rate = (values["errors"] / count * 100) if count > 0 else 0

            stats[key] = {
                "total_calls": count,
                "avg_response_time_ms": round(avg_response_time, 2),
                "error_count": values["errors"],
                "error_rate": round(error_rate, 2),
                "bytes_transferred": values["bytes_transferred"]
            }

        return stats

    def get_user_stats(self, user_id: str, date: Optional[str] = None) -> Optional[UserActivity]:
        """Get user activity for specific date"""
        if date is None:
            date = datetime.utcnow().strftime("%Y-%m-%d")

        key = f"{user_id}:{date}"
        return self.user_stats.get(key)

    def get_current_load(self) -> Dict[str, float]:
        """Get current system load"""
        if not self.resource_snapshots:
            return {}

        latest = self.resource_snapshots[-1]

        return {
            "cpu_percent": latest.cpu_percent,
            "memory_mb": latest.memory_mb,
            "active_connections": latest.active_connections,
            "timestamp": latest.timestamp.isoformat()
        }

    def get_load_history(self, minutes: int = 60) -> List[Dict[str, Any]]:
        """Get load history for specified minutes"""
        cutoff = datetime.utcnow() - timedelta(minutes=minutes)

        history = [
            {
                "timestamp": snap.timestamp.isoformat(),
                "cpu_percent": snap.cpu_percent,
                "memory_mb": snap.memory_mb,
                "network_in": snap.network_in,
                "network_out": snap.network_out
            }
            for snap in self.resource_snapshots
            if snap.timestamp > cutoff
        ]

        return history

    async def get_daily_summary(self, date: Optional[str] = None, database=None) -> Dict[str, Any]:
        """Get daily usage summary"""
        if date is None:
            date = datetime.utcnow().strftime("%Y-%m-%d")

        try:
            if not database:
                from app.database import get_db
                database = get_db()

            # Aggregate from database
            start = datetime.strptime(date, "%Y-%m-%d")
            end = start + timedelta(days=1)

            pipeline = [
                {"$match": {"timestamp": {"$gte": start, "$lt": end}}},
                {"$group": {
                    "_id": None,
                    "total_calls": {"$sum": 1},
                    "unique_users": {"$addToSet": "$user_id"},
                    "avg_response_time": {"$avg": "$response_time_ms"},
                    "max_response_time": {"$max": "$response_time_ms"},
                    "error_count": {
                        "$sum": {"$cond": [{"$gte": ["$status_code", 400]}, 1, 0]}
                    },
                    "total_bytes": {"$sum": {"$add": ["$bytes_sent", "$bytes_received"]}}
                }}
            ]

            result = await database.api_usage.aggregate(pipeline).to_list(length=1)

            if result:
                data = result[0]
                return {
                    "date": date,
                    "total_api_calls": data["total_calls"],
                    "unique_users": len(data["unique_users"]),
                    "avg_response_time_ms": round(data["avg_response_time"], 2),
                    "max_response_time_ms": round(data["max_response_time"], 2),
                    "error_count": data["error_count"],
                    "error_rate": round(data["error_count"] / data["total_calls"] * 100, 2) if data["total_calls"] > 0 else 0,
                    "total_bytes_transferred": data["total_bytes"]
                }

            return {"date": date, "total_api_calls": 0}

        except Exception as e:
            logger.error(f"Failed to get daily summary: {e}")
            return {"date": date, "error": str(e)}


class RateLimiter:
    """Rate limiting based on usage"""

    def __init__(self):
        self.limits: Dict[str, Dict[str, Any]] = {
            "anonymous": {"requests_per_minute": 30, "requests_per_hour": 100},
            "authenticated": {"requests_per_minute": 120, "requests_per_hour": 1000},
            "premium": {"requests_per_minute": 300, "requests_per_hour": 5000},
        }
        self.usage_window: Dict[str, List[datetime]] = {}

    def check_rate_limit(
        self,
        user_id: Optional[str],
        tier: str = "authenticated"
    ) -> tuple[bool, Dict[str, Any]]:
        """Check if request is within rate limit"""
        key = user_id or "anonymous"
        now = datetime.utcnow()

        # Get limits
        limits = self.limits.get(tier, self.limits["authenticated"])

        # Clean old entries
        if key in self.usage_window:
            cutoff = now - timedelta(hours=1)
            self.usage_window[key] = [
                t for t in self.usage_window[key] if t > cutoff
            ]
        else:
            self.usage_window[key] = []

        # Count recent requests
        minute_ago = now - timedelta(minutes=1)
        hour_ago = now - timedelta(hours=1)

        requests_last_minute = sum(1 for t in self.usage_window[key] if t > minute_ago)
        requests_last_hour = len(self.usage_window[key])

        # Check limits
        allowed = (
            requests_last_minute < limits["requests_per_minute"] and
            requests_last_hour < limits["requests_per_hour"]
        )

        # Record this request
        self.usage_window[key].append(now)

        info = {
            "allowed": allowed,
            "tier": tier,
            "requests_last_minute": requests_last_minute,
            "requests_last_hour": requests_last_hour,
            "limit_per_minute": limits["requests_per_minute"],
            "limit_per_hour": limits["requests_per_hour"],
            "retry_after": 60 if not allowed else 0
        }

        return allowed, info


# Global instances
usage_tracker = UsageTracker()
rate_limiter = RateLimiter()
