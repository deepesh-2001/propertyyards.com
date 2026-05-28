"""
Tests for Predictive Analytics & Forecasting
"""
import pytest
import statistics
import sys
from datetime import datetime, timedelta

sys.path.insert(0, 'C:/Users/deepe/PyCharmMiscProject/housing_platform/backend')

from app.predictive_analytics import (
    TrendAnalyzer,
    ForecastingModel,
    MarketPredictor,
    PredictiveAnalyticsManager
)


class TestTrendAnalyzer:
    """Test TrendAnalyzer class"""

    def test_calculate_trend_line_increasing(self):
        """Test trend line calculation for increasing data"""
        data = [10, 20, 30, 40, 50]
        slope, intercept = TrendAnalyzer.calculate_trend_line(data)

        assert slope > 0  # Positive trend
        assert abs(slope - 10.0) < 0.01  # Should be approximately 10

    def test_calculate_trend_line_decreasing(self):
        """Test trend line calculation for decreasing data"""
        data = [50, 40, 30, 20, 10]
        slope, intercept = TrendAnalyzer.calculate_trend_line(data)

        assert slope < 0  # Negative trend
        assert abs(slope + 10.0) < 0.01  # Should be approximately -10

    def test_calculate_trend_line_stable(self):
        """Test trend line for stable data"""
        data = [10, 10, 10, 10, 10]
        slope, intercept = TrendAnalyzer.calculate_trend_line(data)

        assert abs(slope) < 0.01  # Should be approximately 0
        assert abs(intercept - 10.0) < 0.01

    def test_moving_average(self):
        """Test moving average calculation"""
        data = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
        result = TrendAnalyzer.moving_average(data, window=3)

        assert len(result) == 8
        assert result[0] == 2.0  # (1+2+3)/3
        assert result[1] == 3.0  # (2+3+4)/3
        assert result[-1] == 9.0  # (8+9+10)/3

    def test_exponential_smoothing(self):
        """Test exponential smoothing"""
        data = [10, 20, 15, 25, 20]
        result = TrendAnalyzer.exponential_smoothing(data, alpha=0.3)

        assert len(result) == len(data)
        assert result[0] == 10  # First value unchanged
        assert result[-1] < max(data)  # Smoothed value

    def test_detect_seasonality_detected(self):
        """Test seasonality detection when pattern exists"""
        # Create data with weekly pattern
        data = [100, 110, 120, 130, 140, 150, 160] * 4

        result = TrendAnalyzer.detect_seasonality(data, period=7)

        assert result["detected"] is True
        assert result["period"] == 7
        assert len(result["indices"]) == 7

    def test_detect_seasonality_not_detected(self):
        """Test seasonality detection when no pattern"""
        # Random data
        data = [10, 50, 20, 80, 30, 40, 60] * 2

        result = TrendAnalyzer.detect_seasonality(data, period=7)

        # May or may not detect depending on randomness
        assert "indices" in result
        assert "period" in result


class TestForecastingModel:
    """Test ForecastingModel class"""

    @pytest.mark.asyncio
    async def test_forecast_linear_increasing(self):
        """Test linear forecast for increasing trend"""
        model = ForecastingModel()
        data = [10, 20, 30, 40, 50]

        result = await model.forecast_linear(data, periods=5)

        assert len(result["forecast"]) == 5
        assert result["trend"] == "increasing"
        assert result["forecast"][0] > 50  # Next value should be higher
        assert result["next_value"] > 50

    @pytest.mark.asyncio
    async def test_forecast_linear_decreasing(self):
        """Test linear forecast for decreasing trend"""
        model = ForecastingModel()
        data = [50, 40, 30, 20, 10]

        result = await model.forecast_linear(data, periods=5)

        assert result["trend"] == "decreasing"
        assert result["forecast"][0] < 10

    @pytest.mark.asyncio
    async def test_forecast_linear_stable(self):
        """Test linear forecast for stable data"""
        model = ForecastingModel()
        data = [10, 10, 10, 10, 10]

        result = await model.forecast_linear(data, periods=5)

        assert result["trend"] == "stable"
        assert abs(result["forecast"][0] - 10) < 1

    @pytest.mark.asyncio
    async def test_forecast_with_seasonality(self):
        """Test forecast with seasonal adjustment"""
        model = ForecastingModel()
        # Weekly pattern data
        data = [100, 110, 120, 130, 140, 150, 160] * 4

        result = await model.forecast_with_seasonality(data, periods=14, season_period=7)

        assert "forecast" in result
        assert "seasonality" in result
        assert result["seasonality"]["detected"] is True

    @pytest.mark.asyncio
    async def test_forecast_revenue(self):
        """Test revenue forecasting"""
        model = ForecastingModel()
        # Daily revenue data
        data = [1000, 1200, 1100, 1300, 1250, 1400, 1350] * 10

        result = await model.forecast_revenue(data, periods=30)

        assert "forecast" in result
        assert "total_forecasted" in result
        assert "avg_daily" in result
        assert "confidence_lower" in result
        assert "confidence_upper" in result
        assert result["currency"] == "INR"

    @pytest.mark.asyncio
    async def test_forecast_insufficient_data(self):
        """Test forecast with insufficient data"""
        model = ForecastingModel()
        data = [10]  # Single data point

        result = await model.forecast_linear(data, periods=5)

        assert len(result["forecast"]) == 5
        assert all(f == 10 for f in result["forecast"])  # Should repeat last value


class TestMarketPredictor:
    """Test MarketPredictor class"""

    @pytest.mark.asyncio
    async def test_predict_property_demand_high(self):
        """Test demand prediction for high demand"""
        predictor = MarketPredictor()

        # High and increasing inquiries/views
        inquiries = [50, 60, 70, 80, 90, 100]
        views = [500, 600, 700, 800, 900, 1000]

        result = await predictor.predict_property_demand(inquiries, views, periods=7)

        assert "demand_forecast" in result
        assert result["demand_level"] in ["high", "very_high"]
        assert "recommendation" in result

    @pytest.mark.asyncio
    async def test_predict_property_demand_low(self):
        """Test demand prediction for low demand"""
        predictor = MarketPredictor()

        # Low and decreasing inquiries/views
        inquiries = [20, 18, 15, 12, 10, 8]
        views = [200, 180, 150, 120, 100, 80]

        result = await predictor.predict_property_demand(inquiries, views, periods=7)

        assert result["demand_level"] == "low"
        assert "recommendation" in result

    @pytest.mark.asyncio
    async def test_predict_price_trends_increasing(self):
        """Test price trend prediction"""
        predictor = MarketPredictor()

        # Increasing prices
        prices = [1000000, 1050000, 1100000, 1150000, 1200000]

        result = await predictor.predict_price_trends(prices, periods=7)

        assert result["current_price"] == 1200000
        assert result["predicted_price"] > 1200000
        assert result["trend"] == "increasing"
        assert "confidence" in result

    @pytest.mark.asyncio
    async def test_predict_price_trends_decreasing(self):
        """Test decreasing price trend"""
        predictor = MarketPredictor()

        prices = [1200000, 1150000, 1100000, 1050000, 1000000]

        result = await predictor.predict_price_trends(prices, periods=7)

        assert result["trend"] == "decreasing"
        assert result["change_percent"] < 0


class TestPredictiveAnalyticsManager:
    """Test PredictiveAnalyticsManager"""

    @pytest.mark.asyncio
    async def test_generate_dashboard_forecasts_mock(self):
        """Test dashboard forecast generation with mock data"""
        manager = PredictiveAnalyticsManager()

        # Mock database
        mock_db = MagicMock()

        # Should handle missing time-series data gracefully
        result = await manager.generate_dashboard_forecasts(mock_db)

        assert "generated_at" in result
        assert "forecast_period" in result
        assert "insights" in result

    def test_generate_insights_growth(self):
        """Test insight generation for growth"""
        manager = PredictiveAnalyticsManager()

        forecasts = {
            "property_growth": {
                "trend": "increasing",
                "growth_rate": 15.5
            },
            "user_growth": {
                "trend": "increasing",
                "next_value": 150
            },
            "market_demand": {
                "demand_level": "high",
                "trend": "increasing",
                "recommendation": "Increase inventory"
            }
        }

        insights = manager._generate_insights(forecasts)

        assert len(insights) > 0
        assert any("15.5%" in i for i in insights)
        assert any("150 new users" in i for i in insights)

    def test_generate_insights_decline(self):
        """Test insight generation for decline"""
        manager = PredictiveAnalyticsManager()

        forecasts = {
            "property_growth": {
                "trend": "decreasing"
            }
        }

        insights = manager._generate_insights(forecasts)

        assert any("declining" in i.lower() for i in insights)


# Mock for tests
from unittest.mock import MagicMock


@pytest.mark.asyncio
async def test_forecast_accuracy():
    """Test forecast accuracy on known data"""
    model = ForecastingModel()

    # Create perfect linear data
    data = [100 + i * 10 for i in range(20)]  # 100, 110, 120, ..., 290

    # Forecast next 5 values
    result = await model.forecast_linear(data, periods=5)

    # Check if forecast is close to actual trend
    expected_next = 300
    forecasted_next = result["next_value"]

    # Allow 5% tolerance
    tolerance = expected_next * 0.05
    assert abs(forecasted_next - expected_next) < tolerance


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
