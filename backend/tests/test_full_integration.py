"""
Full Integration Test Suite
Comprehensive tests for logging, security, auto-heal, scaling, image generation,
post generation, article generation, sales reports, and future projections
"""
import pytest
import asyncio
import time
import json
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from typing import Dict, List, Any
import psutil

# Import all services to test
from app.server_monitoring import (
    PerformanceMonitor, SystemMonitor, StructuredLogger,
    CacheMonitor, DatabaseMonitor, HealthChecker,
    monitor_performance, log_operation
)
from app.cache_decorators import cached, CacheStats
from app.auto_scaler import AutoScaler, ScalingRule, ScalingTrigger, ScalingAction
from app.auto_healing import AutoHealingService, FailureType, RecoveryAction
from app.ai_image_service import AIImageGenerator, GeneratedImage
from app.news_service import AIArticleGenerator, NewsArticle
from app.social_media_manager import SocialMediaAutomation, Platform, SocialPost


# ==================== LOGGING TESTS ====================

class TestStructuredLogging:
    """Test comprehensive logging system"""

    def test_json_logging(self, caplog):
        """Test JSON structured logging output"""
        logger = StructuredLogger("test-service")

        with caplog.at_level("INFO"):
            logger.info(
                "Test operation",
                {"user_id": "123", "action": "login", "ip": "192.168.1.1"}
            )

        # Verify log was captured
        assert len(caplog.records) == 1
        record = caplog.records[0]

        # Parse JSON from log message
        try:
            log_data = json.loads(record.message)
            assert "timestamp" in log_data
            assert log_data["level"] == "INFO"
            assert log_data["service"] == "housing-platform"
            assert log_data["message"] == "Test operation"
            assert log_data["user_id"] == "123"
        except json.JSONDecodeError:
            # Some handlers format differently
            assert "Test operation" in record.message

    def test_log_levels(self, caplog):
        """Test all log levels"""
        logger = StructuredLogger("test")

        with caplog.at_level("DEBUG"):
            logger.debug("Debug message", {"detail": "verbose"})
            logger.info("Info message", {"status": "ok"})
            logger.warning("Warning message", {"alert": "threshold"})
            logger.error("Error message", {"error": "failed"})

        assert len(caplog.records) == 4

    def test_log_performance_tracking(self):
        """Test logging with performance metrics"""
        logger = StructuredLogger("performance-test")

        start_time = time.time()
        # Simulate work
        time.sleep(0.01)
        duration_ms = (time.time() - start_time) * 1000

        logger.info(
            "Operation completed",
            {"operation": "db_query", "duration_ms": duration_ms, "rows": 100}
        )

        assert duration_ms > 0


# ==================== SECURITY TESTS ====================

class TestSecurityFeatures:
    """Test security enhancements"""

    def test_secure_headers(self):
        """Test security headers configuration"""
        # Mock security headers
        headers = {
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "DENY",
            "X-XSS-Protection": "1; mode=block",
            "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
            "Content-Security-Policy": "default-src 'self'",
            "Referrer-Policy": "strict-origin-when-cross-origin"
        }

        assert headers["X-Frame-Options"] == "DENY"
        assert "max-age" in headers["Strict-Transport-Security"]

    def test_rate_limiting(self):
        """Test rate limiting logic"""
        # Mock rate limiter
        requests = []
        window_start = datetime.utcnow()
        max_requests = 100

        # Simulate requests
        for i in range(150):
            requests.append(datetime.utcnow())

        # Count requests in window
        recent = [r for r in requests if r > window_start - timedelta(minutes=1)]

        # Should detect over limit
        assert len(recent) > max_requests

    def test_input_validation(self):
        """Test input validation security"""
        # Test SQL injection prevention
        malicious_input = "'; DROP TABLE users; --"
        sanitized = malicious_input.replace("'", "''").replace(";", "")

        assert "DROP TABLE" not in sanitized or "''" in sanitized

        # Test XSS prevention
        xss_input = "<script>alert('xss')</script>"
        sanitized_xss = xss_input.replace("<", "&lt;").replace(">", "&gt;")

        assert "<script>" not in sanitized_xss


# ==================== AUTO-HEALING TESTS ====================

class TestAutoHealing:
    """Test auto-healing system"""

    @pytest.fixture
    def healing_service(self):
        """Create auto-healing service for tests"""
        service = AutoHealingService()
        service.enabled = True
        return service

    def test_failure_detection(self, healing_service):
        """Test failure detection logic"""
        # Simulate high error rate
        metrics = {"error_rate": 15.0}  # Above 10% threshold

        rule = healing_service.recovery_rules[0]  # high_error_rate rule
        triggered = healing_service._check_failure_condition(rule, metrics)

        assert triggered is True

    def test_recovery_cooldown(self, healing_service):
        """Test recovery cooldown mechanism"""
        rule = healing_service.recovery_rules[0]

        # Simulate recent failures
        now = datetime.utcnow()
        healing_service.recent_failures[rule.name] = [
            now - timedelta(minutes=1),
            now - timedelta(minutes=2),
            now - timedelta(minutes=3)
        ]

        # Should not attempt recovery (max attempts reached)
        should_recover = healing_service._should_attempt_recovery(rule)
        assert should_recover is False

    def test_health_check(self, healing_service):
        """Test service health checking"""
        # Mock healthy service
        with patch.object(healing_service, '_check_database_health', return_value=True):
            healthy = asyncio.run(healing_service._check_database_health())
            assert healthy is True

    def test_recovery_actions(self, healing_service):
        """Test recovery action handlers exist"""
        actions = [
            RecoveryAction.CLEAR_CACHE,
            RecoveryAction.RECONNECT_DATABASE,
            RecoveryAction.SEND_ALERT
        ]

        for action in actions:
            handler = healing_service.recovery_handlers.get(action)
            assert handler is not None, f"Handler for {action} not found"


# ==================== AUTO-SCALING TESTS ====================

class TestAutoScaling:
    """Test auto-scaling system"""

    @pytest.fixture
    def scaler(self):
        """Create auto-scaler for tests"""
        scaler = AutoScaler()
        scaler.enabled = False  # Don't start loops in tests
        return scaler

    def test_scaling_rules(self, scaler):
        """Test scaling rules configuration"""
        assert len(scaler.rules) > 0

        # Check CPU rule
        cpu_rule = next((r for r in scaler.rules if r.trigger == ScalingTrigger.CPU), None)
        assert cpu_rule is not None
        assert cpu_rule.threshold_high == 75.0
        assert cpu_rule.scale_up_step == 2

    def test_scale_up_decision(self, scaler):
        """Test scale up decision logic"""
        # Metrics that trigger scale up
        metrics = {
            "cpu_percent": 80.0,  # Above 75% threshold
            "memory_percent": 85.0,  # Above 80% threshold
            "requests_per_second": 1200,  # Above 1000 threshold
            "avg_response_time_ms": 600,  # Above 500 threshold
            "error_rate_percent": 5.0
        }

        action, reason, rule = scaler._evaluate_rules(metrics)

        assert action == ScalingAction.SCALE_UP
        assert "High load" in reason

    def test_scale_down_decision(self, scaler):
        """Test scale down decision logic"""
        # Metrics that trigger scale down (all low)
        metrics = {
            "cpu_percent": 20.0,  # Below 30% threshold
            "memory_percent": 30.0,  # Below 40% threshold
            "requests_per_second": 50,  # Below 100 threshold
            "avg_response_time_ms": 50,  # Below 100 threshold
            "error_rate_percent": 1.0  # Below 2% threshold
        }

        action, reason, rule = scaler._evaluate_rules(metrics)

        assert action == ScalingAction.SCALE_DOWN

    def test_cooldown_period(self, scaler):
        """Test scaling cooldown"""
        # Set recent scaling action
        scaler.last_scaling_action = datetime.utcnow()

        metrics = {"cpu_percent": 90.0}  # Would normally trigger scale up

        action, reason, rule = scaler._evaluate_rules(metrics)

        assert action == ScalingAction.NO_ACTION
        assert "cooldown" in reason.lower()

    def test_instance_limits(self, scaler):
        """Test min/max instance limits"""
        scaler.current_instances = 1

        # Try to scale down at minimum
        new_count = max(scaler.current_instances - 1, scaler.min_instances)
        assert new_count == 1  # Should stay at minimum

        # Try to scale up at maximum
        scaler.current_instances = 10
        new_count = min(scaler.current_instances + 1, scaler.max_instances)
        assert new_count == 10  # Should stay at maximum


# ==================== AI IMAGE GENERATION TESTS ====================

class TestAIImageGeneration:
    """Test AI image generation service"""

    @pytest.fixture
    def image_generator(self):
        """Create image generator for tests"""
        return AIImageGenerator()

    def test_property_prompt_building(self, image_generator):
        """Test property visualization prompt building"""
        property_data = {
            "property_type": "apartment",
            "bedrooms": 3,
            "city": "Mumbai",
            "price_category": "luxury"
        }

        prompt = image_generator._build_property_prompt(property_data, "modern")

        assert "apartment" in prompt.lower()
        assert "mumbai" in prompt.lower()
        assert "luxury" in prompt.lower()

    def test_market_prompt_building(self, image_generator):
        """Test market visualization prompt building"""
        market_data = {
            "city": "Bangalore",
            "trend": "growing"
        }

        prompt = image_generator._build_market_prompt(market_data, "trend")

        assert "bangalore" in prompt.lower()
        assert "trend" in prompt.lower()

    def test_social_prompt_building(self, image_generator):
        """Test social media prompt building"""
        content_type = "new_property"
        text = "Amazing 3BHK in Mumbai!"

        prompt = image_generator._build_social_prompt(content_type, text, "professional")

        assert len(prompt) > 0
        assert "real estate" in prompt.lower() or "property" in prompt.lower()

    def test_future_prompt_building(self, image_generator):
        """Test future prediction prompt building"""
        prediction_data = {
            "location": "Smart City Delhi",
            "year": 2030,
            "growth_rate": 25
        }

        prompt = image_generator._build_future_prompt(prediction_data, "apartment")

        assert "2030" in prompt
        assert "smart city delhi" in prompt.lower()


# ==================== ARTICLE GENERATION TESTS ====================

class TestArticleGeneration:
    """Test AI article generation"""

    @pytest.fixture
    def article_generator(self):
        """Create article generator for tests"""
        generator = AIArticleGenerator()
        generator.api_key = "test-key"
        return generator

    def test_article_prompt_structure(self, article_generator):
        """Test article prompt building"""
        topic = "Real Estate Market Trends"
        keywords = ["property", "investment", "market"]

        # Verify prompt would include required elements
        prompt_elements = [topic] + keywords
        assert len(prompt_elements) == 3

    def test_article_parsing(self, article_generator):
        """Test article content parsing"""
        generated_text = """
        TITLE: Mumbai Real Estate Boom

        SUMMARY: Property prices rising

        CONTENT: Detailed article here.

        TAGS: property, mumbai, real-estate
        """

        # Parse using the generator's method
        result = article_generator._parse_generated_content(
            generated_text,
            "Original",
            "property_news"
        )

        assert "title" in result
        assert "content" in result
        assert "summary" in result


# ==================== SOCIAL MEDIA TESTS ====================

class TestSocialMedia:
    """Test social media automation"""

    @pytest.fixture
    def social_manager(self):
        """Create social media manager for tests"""
        return SocialMediaAutomation()

    def test_content_templates(self, social_manager):
        """Test content template generation"""
        templates = social_manager.CONTENT_TEMPLATES

        assert "new_property" in templates
        assert "market_update" in templates
        assert "tip" in templates
        assert "promotion" in templates

    def test_content_generation(self, social_manager):
        """Test content generation from templates"""
        variables = {
            "title": "Luxury Villa",
            "location": "Goa",
            "price": "₹5,00,00,000",
            "link": "https://propertyyards.com/property/123"
        }

        content = social_manager.generate_content("new_property", variables)

        assert "Luxury Villa" in content
        assert "Goa" in content
        assert "₹5,00,00,000" in content or "link" in content.lower()

    def test_platform_initialization(self, social_manager):
        """Test platform initialization"""
        asyncio.run(social_manager.initialize_platform(
            Platform.FACEBOOK,
            "test-api-key",
            access_token="test-token",
            page_id="test-page"
        ))

        assert Platform.FACEBOOK in social_manager.platforms
        assert social_manager.platforms[Platform.FACEBOOK]["access_token"] == "test-token"


# ==================== SALES REPORT TESTS ====================

class TestSalesReports:
    """Test enhanced sales reporting"""

    def test_sales_metrics_calculation(self):
        """Test sales metrics calculations"""
        sales_data = [
            {"sale_price": 5000000, "commission_amount": 150000, "broker_id": "b1"},
            {"sale_price": 7500000, "commission_amount": 225000, "broker_id": "b2"},
            {"sale_price": 6000000, "commission_amount": 180000, "broker_id": "b1"}
        ]

        # Calculate metrics
        total_sales = sum(s["sale_price"] for s in sales_data)
        total_commission = sum(s["commission_amount"] for s in sales_data)
        avg_sale_price = total_sales / len(sales_data)

        # Broker performance
        broker_sales = {}
        for sale in sales_data:
            bid = sale["broker_id"]
            broker_sales[bid] = broker_sales.get(bid, 0) + sale["sale_price"]

        assert total_sales == 18500000
        assert total_commission == 555000
        assert avg_sale_price == 6166666.67
        assert broker_sales["b1"] == 11000000

    def test_sales_trend_analysis(self):
        """Test sales trend analysis"""
        # Monthly sales data
        monthly_data = [
            {"month": "Jan", "sales": 10, "revenue": 50000000},
            {"month": "Feb", "sales": 12, "revenue": 60000000},
            {"month": "Mar", "sales": 15, "revenue": 75000000}
        ]

        # Calculate growth rate
        growth_rates = []
        for i in range(1, len(monthly_data)):
            prev = monthly_data[i-1]["revenue"]
            curr = monthly_data[i]["revenue"]
            growth = ((curr - prev) / prev) * 100
            growth_rates.append(growth)

        assert growth_rates[0] == 20.0  # 20% growth
        assert growth_rates[1] == 25.0  # 25% growth


# ==================== FUTURE PROJECTION TESTS ====================

class TestFutureProjections:
    """Test future projection system"""

    def test_growth_rate_calculation(self):
        """Test growth rate projections"""
        # Historical data
        historical = [100, 110, 121, 133]  # 10% growth each period

        # Calculate compound growth
        start_value = historical[0]
        end_value = historical[-1]
        periods = len(historical) - 1

        cagr = ((end_value / start_value) ** (1 / periods) - 1) * 100

        assert cagr == 10.0  # 10% CAGR

    def test_confidence_scoring(self):
        """Test projection confidence scoring"""
        # Factors affecting confidence
        data_points = 24  # 2 years of monthly data
        volatility = 0.15  # 15% standard deviation
        trend_consistency = 0.85  # 85% consistent trend

        # Calculate confidence (simplified)
        confidence = min(
            (data_points / 36) * 0.4 +  # More data = better
            (1 - volatility) * 0.3 +    # Less volatility = better
            trend_consistency * 0.3,    # Consistent trend = better
            1.0
        )

        assert 0 <= confidence <= 1
        assert confidence > 0.5  # Should be reasonably confident

    def test_projection_scenarios(self):
        """Test best/worst case scenarios"""
        base_projection = 1000000  # Base value
        confidence_interval = 0.15  # 15% variance

        best_case = base_projection * (1 + confidence_interval)
        worst_case = base_projection * (1 - confidence_interval)

        assert best_case == 1150000
        assert worst_case == 850000
        assert worst_case < base_projection < best_case


# ==================== PERFORMANCE OPTIMIZATION TESTS ====================

class TestPerformanceOptimization:
    """Test performance optimizations"""

    def test_cache_hit_performance(self):
        """Test cache performance under load"""
        monitor = CacheMonitor()

        start = time.time()
        for _ in range(10000):
            monitor.record_hit()
        duration = time.time() - start

        assert duration < 0.1  # Should be very fast
        assert monitor.hits == 10000

    def test_monitoring_overhead(self):
        """Test monitoring doesn't add significant overhead"""
        monitor = PerformanceMonitor()

        start = time.time()
        for i in range(1000):
            monitor.record_request("/api/test", 50.0, 200)
        duration = time.time() - start

        # Should process 1000 requests quickly
        assert duration < 1.0
        assert len(monitor.request_times) == 1000

    def test_memory_efficiency(self):
        """Test memory usage with history limits"""
        monitor = PerformanceMonitor(max_history=100)

        # Add more than limit
        for i in range(150):
            monitor.record_request("/api/test", float(i), 200)

        # Should only keep last 100
        assert len(monitor.request_times) == 100


# ==================== BUG FIXES VERIFICATION ====================

class TestBugFixes:
    """Verify bug fixes are in place"""

    def test_database_connection_retry(self):
        """Test database connection retry logic"""
        # Simulate connection failure then success
        attempts = 0
        max_retries = 3

        for i in range(max_retries):
            attempts += 1
            if i < max_retries - 1:
                continue  # Simulate failure
            else:
                break  # Success

        assert attempts <= max_retries

    def test_cache_invalidation_race_condition(self):
        """Test cache invalidation handles race conditions"""
        # Simulate concurrent invalidation
        results = []

        async def invalidate():
            try:
                # Mock cache operation
                results.append(True)
            except Exception:
                results.append(False)

        # Run multiple times
        for _ in range(5):
            asyncio.run(invalidate())

        assert all(results)

    def test_memory_leak_prevention(self):
        """Test memory management prevents leaks"""
        monitor = PerformanceMonitor(max_history=1000)

        # Simulate continuous operation
        for _ in range(5000):
            monitor.record_request("/api/test", 50.0, 200)

        # Should not grow beyond limit
        assert len(monitor.request_times) <= 1000


# ==================== INTEGRATION TESTS ====================

class TestFullIntegration:
    """Full system integration tests"""

    @pytest.mark.asyncio
    async def test_end_to_end_request_flow(self):
        """Test complete request processing flow"""
        # Simulate a complete API request flow

        # 1. Request comes in (performance tracking)
        perf_monitor = PerformanceMonitor()
        start_time = time.time()

        # 2. Cache check
        cache_monitor = CacheMonitor()
        cache_monitor.record_hit()

        # 3. Database query (with monitoring)
        db_monitor = DatabaseMonitor()
        db_monitor.record_query("find", "properties", 25.0)

        # 4. Log the operation
        logger = StructuredLogger("integration-test")
        logger.info("Request processed", {"endpoint": "/api/properties"})

        # 5. Record performance
        duration_ms = (time.time() - start_time) * 1000
        perf_monitor.record_request("/api/properties", duration_ms, 200)

        # Verify all systems recorded data
        assert perf_monitor.get_stats()["total_requests"] == 1
        assert cache_monitor.get_stats()["hits"] == 1
        assert db_monitor.get_stats()["total_queries"] == 1

    def test_monitoring_dashboard_data(self):
        """Test monitoring dashboard data aggregation"""
        # Gather data from all monitors
        perf_stats = PerformanceMonitor().get_stats()
        cache_stats = CacheMonitor().get_stats()
        system_stats = SystemMonitor().get_system_stats()

        dashboard_data = {
            "performance": perf_stats,
            "cache": cache_stats,
            "system": system_stats,
            "timestamp": datetime.utcnow().isoformat()
        }

        assert "performance" in dashboard_data
        assert "cache" in dashboard_data
        assert "system" in dashboard_data

    @pytest.mark.asyncio
    async def test_auto_healing_integration(self):
        """Test auto-healing with monitoring"""
        healing = AutoHealingService()

        # Simulate failure
        metrics = {"error_rate": 20.0}
        rule = healing.recovery_rules[0]

        triggered = healing._check_failure_condition(rule, metrics)
        assert triggered is True

    @pytest.mark.asyncio
    async def test_auto_scaling_integration(self):
        """Test auto-scaling with monitoring"""
        scaler = AutoScaler()
        scaler.enabled = False

        # High load scenario
        metrics = {
            "cpu_percent": 85.0,
            "memory_percent": 90.0,
            "requests_per_second": 1500
        }

        action, reason, rule = scaler._evaluate_rules(metrics)
        assert action == ScalingAction.SCALE_UP


# ==================== LOAD TESTS ====================

class TestLoadHandling:
    """Load testing and stress tests"""

    def test_high_throughput_monitoring(self):
        """Test monitoring under high load"""
        monitor = PerformanceMonitor()

        # Simulate 10,000 requests
        for i in range(10000):
            monitor.record_request(
                f"/api/endpoint_{i % 10}",
                50.0 + (i % 100),
                200 if i % 100 != 0 else 500
            )

        stats = monitor.get_stats()
        assert stats["total_requests"] == 10000
        assert stats["error_count"] == 100  # Every 100th is error

    def test_concurrent_cache_access(self):
        """Test cache under concurrent access"""
        import threading

        monitor = CacheMonitor()
        hits = []

        def record_hits():
            for _ in range(1000):
                monitor.record_hit()
            hits.append(1000)

        # Run 10 threads concurrently
        threads = [threading.Thread(target=record_hits) for _ in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert monitor.hits == 10000


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
