"""
Real-Time Analytics System
Minute-by-minute analytics with WebSocket support and live dashboards
"""
from typing import Dict, Any, Optional, List, Callable
from datetime import datetime, timedelta
from collections import deque
import asyncio
import logging
import json
from dataclasses import dataclass, asdict

from app.timeseries import timeseries_manager, TimeSeriesGranularity
from app.cache_pipeline import redis_pipeline, local_cache
from app.background_tasks import background_processor

logger = logging.getLogger(__name__)


@dataclass
class MinuteMetrics:
    """Metrics for a single minute"""
    timestamp: datetime
    page_views: int = 0
    api_calls: int = 0
    new_users: int = 0
    new_properties: int = 0
    new_inquiries: int = 0
    active_sessions: int = 0
    avg_response_time_ms: float = 0.0
    error_count: int = 0
    revenue: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestamp": self.timestamp.isoformat(),
            "page_views": self.page_views,
            "api_calls": self.api_calls,
            "new_users": self.new_users,
            "new_properties": self.new_properties,
            "new_inquiries": self.new_inquiries,
            "active_sessions": self.active_sessions,
            "avg_response_time_ms": self.avg_response_time_ms,
            "error_count": self.error_count,
            "revenue": self.revenue
        }


class RealtimeAnalyticsCollector:
    """Collects real-time minute-by-minute analytics"""

    def __init__(self, retention_minutes: int = 60):
        self.retention_minutes = retention_minutes
        self.current_minute = MinuteMetrics(timestamp=datetime.utcnow().replace(second=0, microsecond=0))
        self.history: deque = deque(maxlen=retention_minutes)
        self.subscribers: List[Callable] = []
        self.running = False
        self._lock = asyncio.Lock()

    async def start(self):
        """Start the real-time collector"""
        self.running = True
        asyncio.create_task(self._minute_rollover_task())
        logger.info("Real-time analytics collector started")

    async def stop(self):
        """Stop the collector"""
        self.running = False
        logger.info("Real-time analytics collector stopped")

    async def _minute_rollover_task(self):
        """Task to rollover to next minute every 60 seconds"""
        while self.running:
            await asyncio.sleep(60)
            await self._rollover_minute()

    async def _rollover_minute(self):
        """Save current minute and start new one"""
        async with self._lock:
            # Store completed minute
            self.history.append(self.current_minute)

            # Notify subscribers
            await self._notify_subscribers(self.current_minute)

            # Store in time-series database
            await self._store_to_timeseries(self.current_minute)

            # Start new minute
            self.current_minute = MinuteMetrics(
                timestamp=datetime.utcnow().replace(second=0, microsecond=0)
            )

            logger.debug(f"Minute rollover: {len(self.history)} minutes in history")

    async def _store_to_timeseries(self, metrics: MinuteMetrics):
        """Store minute metrics to time-series database"""
        try:
            from app.database import get_db
            database = get_db()

            # Store each metric separately for flexibility
            await timeseries_manager.store_metric(
                "page_views_per_minute",
                float(metrics.page_views),
                {},
                TimeSeriesGranularity.MINUTE,
                database
            )

            await timeseries_manager.store_metric(
                "api_calls_per_minute",
                float(metrics.api_calls),
                {},
                TimeSeriesGranularity.MINUTE,
                database
            )

            await timeseries_manager.store_metric(
                "revenue_per_minute",
                metrics.revenue,
                {},
                TimeSeriesGranularity.MINUTE,
                database
            )

        except Exception as e:
            logger.error(f"Time-series store error: {e}")

    async def _notify_subscribers(self, metrics: MinuteMetrics):
        """Notify all subscribers of new minute data"""
        for subscriber in self.subscribers:
            try:
                if asyncio.iscoroutinefunction(subscriber):
                    await subscriber(metrics)
                else:
                    subscriber(metrics)
            except Exception as e:
                logger.error(f"Subscriber notification error: {e}")

    def subscribe(self, callback: Callable):
        """Subscribe to minute updates"""
        self.subscribers.append(callback)

    def unsubscribe(self, callback: Callable):
        """Unsubscribe from updates"""
        if callback in self.subscribers:
            self.subscribers.remove(callback)

    # Metric recording methods
    async def record_page_view(self, count: int = 1):
        async with self._lock:
            self.current_minute.page_views += count

    async def record_api_call(self, response_time_ms: float):
        async with self._lock:
            self.current_minute.api_calls += 1
            # Update running average
            n = self.current_minute.api_calls
            current_avg = self.current_minute.avg_response_time_ms
            self.current_minute.avg_response_time_ms = (
                (current_avg * (n - 1) + response_time_ms) / n
            )

    async def record_new_user(self):
        async with self._lock:
            self.current_minute.new_users += 1

    async def record_new_property(self):
        async with self._lock:
            self.current_minute.new_properties += 1

    async def record_new_inquiry(self):
        async with self._lock:
            self.current_minute.new_inquiries += 1

    async def record_error(self):
        async with self._lock:
            self.current_minute.error_count += 1

    async def record_revenue(self, amount: float):
        async with self._lock:
            self.current_minute.revenue += amount

    async def update_active_sessions(self, count: int):
        async with self._lock:
            self.current_minute.active_sessions = count

    def get_current_minute(self) -> MinuteMetrics:
        """Get current minute metrics"""
        return self.current_minute

    def get_history(self, minutes: int = 60) -> List[MinuteMetrics]:
        """Get historical minute data"""
        return list(self.history)[-minutes:]

    def get_live_dashboard_data(self) -> Dict[str, Any]:
        """Get data for live dashboard"""
        history_list = list(self.history)

        # Calculate trends
        if len(history_list) >= 2:
            last_minute = history_list[-1]
            prev_minute = history_list[-2]

            page_view_trend = self._calc_trend(last_minute.page_views, prev_minute.page_views)
            api_call_trend = self._calc_trend(last_minute.api_calls, prev_minute.api_calls)
            error_trend = self._calc_trend(last_minute.error_count, prev_minute.error_count)
        else:
            page_view_trend = api_call_trend = error_trend = 0

        # Calculate averages over last hour
        if history_list:
            avg_page_views = sum(m.page_views for m in history_list) / len(history_list)
            avg_api_calls = sum(m.api_calls for m in history_list) / len(history_list)
            avg_response_time = sum(m.avg_response_time_ms for m in history_list) / len(history_list)
            total_revenue = sum(m.revenue for m in history_list)
        else:
            avg_page_views = avg_api_calls = avg_response_time = total_revenue = 0

        return {
            "current_minute": self.current_minute.to_dict(),
            "history": [m.to_dict() for m in history_list[-30:]],  # Last 30 minutes
            "trends": {
                "page_views": page_view_trend,
                "api_calls": api_call_trend,
                "errors": error_trend
            },
            "hourly_averages": {
                "page_views": round(avg_page_views, 2),
                "api_calls": round(avg_api_calls, 2),
                "response_time_ms": round(avg_response_time, 2),
                "revenue": round(total_revenue, 2)
            },
            "last_updated": datetime.utcnow().isoformat()
        }

    def _calc_trend(self, current: float, previous: float) -> float:
        """Calculate percentage trend"""
        if previous == 0:
            return 100.0 if current > 0 else 0.0
        return round(((current - previous) / previous) * 100, 2)


class ChangeDetector:
    """Detects significant changes and anomalies in real-time data"""

    def __init__(self):
        self.baselines: Dict[str, float] = {}
        self.thresholds = {
            "page_views": 0.50,  # 50% change
            "api_calls": 0.30,
            "error_rate": 0.10,    # 10% error rate spike
            "response_time": 0.50  # 50% slower
        }

    def update_baseline(self, metric_name: str, value: float):
        """Update baseline with exponential moving average"""
        if metric_name not in self.baselines:
            self.baselines[metric_name] = value
        else:
            # EMA with alpha=0.1
            self.baselines[metric_name] = 0.9 * self.baselines[metric_name] + 0.1 * value

    def detect_changes(self, metrics: MinuteMetrics) -> List[Dict[str, Any]]:
        """Detect significant changes from baseline"""
        changes = []

        self.update_baseline("page_views", metrics.page_views)
        self.update_baseline("api_calls", metrics.api_calls)

        # Check page views
        if metrics.page_views > 0:
            page_view_deviation = abs(metrics.page_views - self.baselines["page_views"]) / self.baselines["page_views"]
            if page_view_deviation > self.thresholds["page_views"]:
                changes.append({
                    "metric": "page_views",
                    "current": metrics.page_views,
                    "baseline": round(self.baselines["page_views"], 2),
                    "deviation": round(page_view_deviation * 100, 2),
                    "direction": "up" if metrics.page_views > self.baselines["page_views"] else "down",
                    "severity": "high" if page_view_deviation > 1.0 else "medium"
                })

        # Check error rate
        if metrics.api_calls > 0:
            error_rate = metrics.error_count / metrics.api_calls
            if error_rate > self.thresholds["error_rate"]:
                changes.append({
                    "metric": "error_rate",
                    "current": round(error_rate * 100, 2),
                    "threshold": self.thresholds["error_rate"] * 100,
                    "error_count": metrics.error_count,
                    "total_calls": metrics.api_calls,
                    "severity": "critical"
                })

        return changes


class RealtimeAlertManager:
    """Manages real-time alerts based on analytics"""

    def __init__(self):
        self.alerts: deque = deque(maxlen=100)
        self.alert_handlers: List[Callable] = []

    async def check_and_alert(self, changes: List[Dict[str, Any]]):
        """Generate alerts for significant changes"""
        for change in changes:
            alert = {
                "id": f"alert_{datetime.utcnow().timestamp()}_{change['metric']}",
                "timestamp": datetime.utcnow().isoformat(),
                "type": change["metric"],
                "severity": change["severity"],
                "message": self._format_alert_message(change),
                "data": change
            }

            self.alerts.append(alert)

            # Notify handlers
            for handler in self.alert_handlers:
                try:
                    if asyncio.iscoroutinefunction(handler):
                        await handler(alert)
                    else:
                        handler(alert)
                except Exception as e:
                    logger.error(f"Alert handler error: {e}")

    def _format_alert_message(self, change: Dict[str, Any]) -> str:
        """Format alert message"""
        metric = change["metric"]

        if metric == "page_views":
            direction = change["direction"]
            return f"Page views {direction} {change['deviation']}% - now {change['current']}/min"

        elif metric == "error_rate":
            return f"High error rate detected: {change['current']}% ({change['error_count']} errors)"

        return f"{metric}: {change}"

    def get_recent_alerts(self, count: int = 20) -> List[Dict[str, Any]]:
        """Get recent alerts"""
        return list(self.alerts)[-count:]

    def subscribe(self, handler: Callable):
        """Subscribe to alerts"""
        self.alert_handlers.append(handler)


# Global instances
realtime_collector = RealtimeAnalyticsCollector(retention_minutes=120)
change_detector = ChangeDetector()
alert_manager = RealtimeAlertManager()


async def on_new_minute(metrics: MinuteMetrics):
    """Callback for new minute data"""
    # Detect changes
    changes = change_detector.detect_changes(metrics)

    if changes:
        await alert_manager.check_and_alert(changes)
        logger.info(f"Detected {len(changes)} significant changes")


# Subscribe to minute updates
realtime_collector.subscribe(on_new_minute)
