"""
Tests for Real-Time Analytics System
"""
import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock
import sys

sys.path.insert(0, 'C:/Users/deepe/PyCharmMiscProject/housing_platform/backend')

from app.realtime_analytics import (
    RealtimeAnalyticsCollector,
    MinuteMetrics,
    ChangeDetector,
    RealtimeAlertManager,
    realtime_collector
)


@pytest.fixture
def collector():
    """Create a fresh collector instance"""
    return RealtimeAnalyticsCollector(retention_minutes=10)


@pytest.fixture
def sample_metrics():
    """Create sample minute metrics"""
    return MinuteMetrics(
        timestamp=datetime.utcnow(),
        page_views=100,
        api_calls=50,
        new_users=5,
        new_properties=2,
        new_inquiries=3,
        active_sessions=25,
        avg_response_time_ms=150.0,
        error_count=1,
        revenue=5000.0
    )


@pytest.mark.asyncio
async def test_minute_metrics_creation():
    """Test MinuteMetrics dataclass"""
    metrics = MinuteMetrics(timestamp=datetime.utcnow())

    assert metrics.page_views == 0
    assert metrics.api_calls == 0
    assert metrics.new_users == 0
    assert metrics.timestamp is not None


@pytest.mark.asyncio
async def test_record_page_view(collector):
    """Test recording page views"""
    await collector.record_page_view(5)
    await collector.record_page_view(3)

    current = collector.get_current_minute()
    assert current.page_views == 8


@pytest.mark.asyncio
async def test_record_api_call(collector):
    """Test recording API calls with response time"""
    await collector.record_api_call(100.0)
    await collector.record_api_call(200.0)
    await collector.record_api_call(300.0)

    current = collector.get_current_minute()
    assert current.api_calls == 3
    assert current.avg_response_time_ms == 200.0  # Average


@pytest.mark.asyncio
async def test_record_revenue(collector):
    """Test recording revenue"""
    await collector.record_revenue(1000.0)
    await collector.record_revenue(2500.0)

    current = collector.get_current_minute()
    assert current.revenue == 3500.0


@pytest.mark.asyncio
async def test_minute_rollover(collector):
    """Test minute rollover functionality"""
    # Record some data
    await collector.record_page_view(10)
    await collector.record_api_call(100.0)

    # Manually trigger rollover
    await collector._rollover_minute()

    # Check history
    history = collector.get_history()
    assert len(history) == 1
    assert history[0].page_views == 10

    # Check new minute started
    current = collector.get_current_minute()
    assert current.page_views == 0
    assert current.api_calls == 0


@pytest.mark.asyncio
async def test_subscriber_notification(collector):
    """Test subscriber callback"""
    received_data = []

    async def test_callback(metrics):
        received_data.append(metrics)

    collector.subscribe(test_callback)

    # Record and rollover
    await collector.record_page_view(5)
    await collector._rollover_minute()

    # Wait for callback
    await asyncio.sleep(0.1)

    assert len(received_data) == 1
    assert received_data[0].page_views == 5


@pytest.mark.asyncio
async def test_get_live_dashboard_data(collector):
    """Test live dashboard data generation"""
    # Add some history
    for i in range(5):
        await collector.record_page_view(10 + i)
        await collector.record_api_call(100.0 + i * 10)
        await collector._rollover_minute()

    dashboard = collector.get_live_dashboard_data()

    assert "current_minute" in dashboard
    assert "history" in dashboard
    assert "trends" in dashboard
    assert "hourly_averages" in dashboard
    assert "last_updated" in dashboard

    assert len(dashboard["history"]) == 5


class TestChangeDetector:
    """Test ChangeDetector class"""

    def test_update_baseline(self):
        """Test baseline updating"""
        detector = ChangeDetector()

        detector.update_baseline("page_views", 100.0)
        assert detector.baselines["page_views"] == 100.0

        detector.update_baseline("page_views", 120.0)
        # EMA: 0.9 * 100 + 0.1 * 120 = 102
        assert abs(detector.baselines["page_views"] - 102.0) < 0.1

    def test_detect_page_view_spike(self):
        """Test detecting page view spike"""
        detector = ChangeDetector()

        # Establish baseline
        detector.update_baseline("page_views", 100.0)
        detector.update_baseline("api_calls", 50.0)

        # Create metrics with spike
        metrics = MinuteMetrics(
            timestamp=datetime.utcnow(),
            page_views=200,  # 100% increase
            api_calls=50
        )

        changes = detector.detect_changes(metrics)

        assert len(changes) == 1
        assert changes[0]["metric"] == "page_views"
        assert changes[0]["direction"] == "up"
        assert changes[0]["severity"] == "high"

    def test_detect_error_rate_spike(self):
        """Test detecting error rate spike"""
        detector = ChangeDetector()

        detector.update_baseline("page_views", 100.0)
        detector.update_baseline("api_calls", 100.0)

        # Create metrics with high error rate
        metrics = MinuteMetrics(
            timestamp=datetime.utcnow(),
            page_views=100,
            api_calls=100,
            error_count=20  # 20% error rate
        )

        changes = detector.detect_changes(metrics)

        error_change = [c for c in changes if c["metric"] == "error_rate"]
        assert len(error_change) == 1
        assert error_change[0]["severity"] == "critical"


class TestRealtimeAlertManager:
    """Test RealtimeAlertManager"""

    @pytest.mark.asyncio
    async def test_check_and_alert(self):
        """Test alert generation"""
        manager = RealtimeAlertManager()
        received_alerts = []

        def alert_handler(alert):
            received_alerts.append(alert)

        manager.subscribe(alert_handler)

        changes = [{
            "metric": "page_views",
            "current": 200,
            "baseline": 100,
            "deviation": 100.0,
            "direction": "up",
            "severity": "high"
        }]

        await manager.check_and_alert(changes)

        assert len(received_alerts) == 1
        assert received_alerts[0]["type"] == "page_views"
        assert received_alerts[0]["severity"] == "high"
        assert "message" in received_alerts[0]

    def test_get_recent_alerts(self):
        """Test getting recent alerts"""
        manager = RealtimeAlertManager()

        # Manually add alerts
        for i in range(25):
            manager.alerts.append({
                "id": f"alert_{i}",
                "timestamp": datetime.utcnow().isoformat()
            })

        recent = manager.get_recent_alerts(10)
        assert len(recent) == 10


@pytest.mark.asyncio
async def test_full_integration():
    """Test full real-time analytics integration"""
    collector = RealtimeAnalyticsCollector(retention_minutes=5)

    # Simulate 5 minutes of activity
    for minute in range(5):
        # Record some activity
        await collector.record_page_view(10 + minute * 5)
        await collector.record_api_call(100.0 + minute * 10)
        await collector.record_new_user()

        # Rollover to next minute
        await collector._rollover_minute()

    # Check results
    history = collector.get_history()
    assert len(history) == 5

    dashboard = collector.get_live_dashboard_data()
    assert dashboard["history"][0]["page_views"] == 10
    assert dashboard["history"][4]["page_views"] == 30


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
