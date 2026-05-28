"""
Test Cases for Caching, Monitoring, and Logging
Comprehensive tests for server monitoring, caching, and logging systems
"""
import pytest
import asyncio
import time
import json
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, AsyncMock
from collections import deque

# Import test subjects
from app.server_monitoring import (
    PerformanceMonitor, SystemMonitor, CacheMonitor,
    DatabaseMonitor, StructuredLogger, HealthChecker,
    performance_monitor, system_monitor, cache_monitor,
    database_monitor, monitor_performance, log_operation
)
from app.cache_decorators import (
    CacheStats, cached_with_stats, cache_invalidate,
    cached, cached_list, cached_detail
)


# ==================== CACHE TESTS ====================

class TestCacheDecorators:
    """Test cache decorator functionality"""

    @pytest.mark.asyncio
    async def test_cached_decorator_basic(self):
        """Test basic caching functionality"""
        call_count = 0

        @cached(ttl=300, key_prefix="test")
        async def test_function(user_id: str = "1"):
            nonlocal call_count
            call_count += 1
            return {"data": f"user_{user_id}", "count": call_count}

        # First call - should execute function
        result1 = await test_function(user_id="1")
        assert result1["count"] == 1
        assert call_count == 1

    @pytest.mark.asyncio
    async def test_cache_stats_tracking(self):
        """Test cache statistics tracking"""
        stats = CacheStats()

        # Record some hits and misses
        stats.record_hit("local")
        stats.record_hit("redis")
        stats.record_hit("redis")
        stats.record_miss()
        stats.record_miss()

        result = stats.get_stats()
        assert result["hits"] == 3
        assert result["misses"] == 2
        assert result["total_requests"] == 5
        assert result["hit_rate"] == "60.00%"
        assert result["local_hits"] == 1
        assert result["redis_hits"] == 2

    @pytest.mark.asyncio
    async def test_cached_list_decorator(self):
        """Test list caching decorator"""
        call_count = 0

        @cached_list(ttl=300, key_prefix="test_list")
        async def get_items(page: int = 1, limit: int = 10):
            nonlocal call_count
            call_count += 1
            return [{"id": i} for i in range(limit)]

        # Test function execution
        result = await get_items(page=1, limit=5)
        assert len(result) == 5
        assert call_count == 1

    @pytest.mark.asyncio
    async def test_cached_detail_decorator(self):
        """Test detail caching decorator"""
        call_count = 0

        @cached_detail(ttl=600, key_prefix="test_detail")
        async def get_item(id: str = "1"):
            nonlocal call_count
            call_count += 1
            return {"id": id, "name": f"Item {id}"}

        # Test function execution
        result = await get_item(id="123")
        assert result["id"] == "123"
        assert call_count == 1

    @pytest.mark.asyncio
    async def test_cache_invalidate_decorator(self):
        """Test cache invalidation decorator"""

        @cache_invalidate(pattern="test_pattern:*")
        async def update_data():
            return {"updated": True}

        result = await update_data()
        assert result["updated"] is True


# ==================== PERFORMANCE MONITOR TESTS ====================

class TestPerformanceMonitor:
    """Test performance monitoring functionality"""

    def test_record_request(self):
        """Test recording API requests"""
        monitor = PerformanceMonitor(max_history=100)

        # Record multiple requests
        monitor.record_request("/api/users", 50.0, 200)
        monitor.record_request("/api/properties", 100.0, 200)
        monitor.record_request("/api/error", 200.0, 500)

        stats = monitor.get_stats()
        assert stats["total_requests"] == 3
        assert stats["error_count"] == 1
        assert "avg_response_time" in stats
        assert "p95_response_time" in stats

    def test_percentile_calculation(self):
        """Test percentile calculations"""
        monitor = PerformanceMonitor()

        # Record requests with known durations
        for i in range(100):
            monitor.record_request("/api/test", float(i), 200)

        stats = monitor.get_stats()
        assert stats["p50_response_time"] == "49.50ms"
        assert stats["p95_response_time"] == "94.50ms"

    def test_endpoint_breakdown(self):
        """Test endpoint-specific statistics"""
        monitor = PerformanceMonitor()

        # Record requests for different endpoints
        for _ in range(5):
            monitor.record_request("/api/users", 50.0, 200)

        for _ in range(3):
            monitor.record_request("/api/properties", 100.0, 200)

        stats = monitor.get_stats()
        assert "/api/users" in stats["endpoint_breakdown"]
        assert stats["endpoint_breakdown"]["/api/users"]["count"] == 5
        assert stats["endpoint_breakdown"]["/api/properties"]["count"] == 3


# ==================== SYSTEM MONITOR TESTS ====================

class TestSystemMonitor:
    """Test system monitoring functionality"""

    def test_get_system_stats(self):
        """Test getting system statistics"""
        monitor = SystemMonitor()
        stats = monitor.get_system_stats()

        assert "timestamp" in stats
        assert "cpu" in stats
        assert "memory" in stats
        assert "disk" in stats

        # Check CPU stats
        assert "percent" in stats["cpu"]
        assert "cores" in stats["cpu"]

        # Check memory stats
        assert "total_gb" in stats["memory"]
        assert "used_gb" in stats["memory"]
        assert "percent" in stats["memory"]

    @pytest.mark.asyncio
    async def test_check_alerts(self):
        """Test system alert detection"""
        monitor = SystemMonitor()
        monitor.alert_thresholds = {
            "cpu_percent": 1,  # Set very low to trigger alert
            "memory_percent": 1,
            "disk_percent": 1
        }

        alerts = await monitor.check_alerts()
        # Should have alerts due to low thresholds
        assert len(alerts) > 0
        assert all("type" in alert for alert in alerts)
        assert all("severity" in alert for alert in alerts)


# ==================== CACHE MONITOR TESTS ====================

class TestCacheMonitor:
    """Test cache monitoring functionality"""

    def test_record_operations(self):
        """Test recording cache operations"""
        monitor = CacheMonitor()

        # Record hits
        for _ in range(10):
            monitor.record_hit()

        # Record misses
        for _ in range(5):
            monitor.record_miss()

        # Record evictions
        monitor.record_eviction()

        stats = monitor.get_stats()
        assert stats["hits"] == 10
        assert stats["misses"] == 5
        assert stats["evictions"] == 1
        assert stats["total_requests"] == 15
        assert stats["hit_rate"] == "66.67%"

    def test_empty_stats(self):
        """Test stats with no operations"""
        monitor = CacheMonitor()
        stats = monitor.get_stats()

        assert stats["hits"] == 0
        assert stats["misses"] == 0
        assert stats["hit_rate"] == "0.00%"


# ==================== DATABASE MONITOR TESTS ====================

class TestDatabaseMonitor:
    """Test database monitoring functionality"""

    def test_record_query(self):
        """Test recording database queries"""
        monitor = DatabaseMonitor()

        # Record normal query
        monitor.record_query("find", "users", 50.0)

        # Record slow query (should trigger warning log)
        monitor.record_query("aggregate", "properties", 150.0)

        stats = monitor.get_stats()
        assert stats["total_queries"] == 2
        assert stats["slow_queries_count"] == 1

    def test_slow_query_detection(self):
        """Test slow query detection"""
        monitor = DatabaseMonitor()
        monitor.slow_query_threshold_ms = 50

        # Record fast query
        monitor.record_query("find", "users", 30.0)

        # Record slow query
        monitor.record_query("aggregate", "logs", 100.0)

        stats = monitor.get_stats()
        assert len(stats["recent_slow_queries"]) == 1
        assert stats["recent_slow_queries"][0]["operation"] == "aggregate"


# ==================== STRUCTURED LOGGER TESTS ====================

class TestStructuredLogger:
    """Test structured logging functionality"""

    def test_log_levels(self, caplog):
        """Test different log levels"""
        logger = StructuredLogger("test")

        with caplog.at_level("DEBUG"):
            logger.info("Test info message", {"user_id": "123"})
            logger.error("Test error message", {"error": "test"})
            logger.warning("Test warning message")
            logger.debug("Test debug message")

        # Check that messages were logged
        assert len(caplog.records) == 4

    def test_log_structure(self, caplog):
        """Test log message structure"""
        logger = StructuredLogger("test")

        with caplog.at_level("INFO"):
            logger.info("Test message", {"extra_field": "value"})

        # Check JSON structure
        record = caplog.records[0]
        assert "timestamp" in record.message
        assert "INFO" in record.message
        assert "Test message" in record.message


# ==================== HEALTH CHECKER TESTS ====================

class TestHealthChecker:
    """Test health checking functionality"""

    @pytest.mark.asyncio
    async def test_check_cache(self):
        """Test cache health check"""
        result = await HealthChecker.check_cache()
        assert "status" in result
        # Status could be healthy, unhealthy, or not_configured

    def test_check_system(self):
        """Test system health check"""
        result = HealthChecker.check_system()

        assert "timestamp" in result
        assert "cpu" in result
        assert "memory" in result
        assert "disk" in result

    @pytest.mark.asyncio
    async def test_full_health_check(self):
        """Test complete health check"""
        result = await HealthChecker.full_health_check()

        assert "timestamp" in result
        assert "database" in result
        assert "cache" in result
        assert "system" in result
        assert "performance" in result


# ==================== DECORATOR TESTS ====================

class TestMonitoringDecorators:
    """Test monitoring decorators"""

    @pytest.mark.asyncio
    async def test_monitor_performance_decorator(self):
        """Test performance monitoring decorator"""

        @monitor_performance(endpoint_name="test_endpoint")
        async def test_function():
            await asyncio.sleep(0.01)  # Small delay
            return {"success": True}

        result = await test_function()
        assert result["success"] is True

    @pytest.mark.asyncio
    async def test_log_operation_decorator(self):
        """Test logging decorator"""

        @log_operation(operation_type="test_operation")
        async def test_function(current_user=None):
            return {"completed": True}

        result = await test_function(current_user={"user_id": "123"})
        assert result["completed"] is True


# ==================== INTEGRATION TESTS ====================

class TestMonitoringIntegration:
    """Integration tests for monitoring system"""

    @pytest.mark.asyncio
    async def test_monitoring_loop(self):
        """Test monitoring background loop"""
        # Just verify the function exists and can be called
        # In real use, this would run continuously
        from app.server_monitoring import monitoring_loop
        assert callable(monitoring_loop)

    def test_global_instances(self):
        """Test that global monitoring instances exist"""
        assert performance_monitor is not None
        assert system_monitor is not None
        assert cache_monitor is not None
        assert database_monitor is not None

    def test_end_to_end_performance_tracking(self):
        """Test end-to-end performance tracking"""
        # Record multiple requests
        for i in range(10):
            performance_monitor.record_request(
                endpoint="/api/test",
                duration_ms=50.0 + i * 10,
                status_code=200 if i < 9 else 500
            )

        stats = performance_monitor.get_stats()
        assert stats["total_requests"] == 10
        assert stats["error_count"] == 1
        assert stats["error_rate"] == "10.00%"


# ==================== PERFORMANCE BENCHMARK TESTS ====================

class TestPerformanceBenchmarks:
    """Benchmark tests for monitoring performance"""

    def test_cache_monitor_performance(self):
        """Benchmark cache monitor performance"""
        monitor = CacheMonitor()

        start_time = time.time()
        for _ in range(10000):
            monitor.record_hit()
        duration = time.time() - start_time

        # Should be very fast (less than 1 second for 10k operations)
        assert duration < 1.0
        assert monitor.hits == 10000

    def test_performance_monitor_history_limit(self):
        """Test that history limit is respected"""
        monitor = PerformanceMonitor(max_history=100)

        # Record more than max_history requests
        for i in range(150):
            monitor.record_request("/api/test", float(i), 200)

        # Should only keep last 100
        assert len(monitor.request_times) == 100


# Run tests
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
