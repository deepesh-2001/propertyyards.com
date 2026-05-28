"""
Predictive Analytics & Future Projections
Forecasting models for properties, users, revenue, and market trends
"""
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
from collections import deque
import logging
import statistics
import math

logger = logging.getLogger(__name__)


class TrendAnalyzer:
    """Analyze trends from historical data"""

    @staticmethod
    def calculate_trend_line(data: List[float]) -> Tuple[float, float]:
        """
        Calculate linear trend line (slope, intercept)
        Returns trend coefficients for y = mx + b
        """
        n = len(data)
        if n < 2:
            return 0.0, 0.0

        x = list(range(n))
        x_mean = statistics.mean(x)
        y_mean = statistics.mean(data)

        # Calculate slope (m)
        numerator = sum((x[i] - x_mean) * (data[i] - y_mean) for i in range(n))
        denominator = sum((x[i] - x_mean) ** 2 for i in range(n))

        if denominator == 0:
            return 0.0, y_mean

        slope = numerator / denominator
        intercept = y_mean - slope * x_mean

        return slope, intercept

    @staticmethod
    def moving_average(data: List[float], window: int = 7) -> List[float]:
        """Calculate moving average"""
        if len(data) < window:
            return data

        result = []
        for i in range(len(data) - window + 1):
            window_data = data[i:i + window]
            result.append(statistics.mean(window_data))

        return result

    @staticmethod
    def exponential_smoothing(data: List[float], alpha: float = 0.3) -> List[float]:
        """Apply exponential smoothing"""
        if not data:
            return []

        result = [data[0]]
        for i in range(1, len(data)):
            smoothed = alpha * data[i] + (1 - alpha) * result[i - 1]
            result.append(smoothed)

        return result

    @staticmethod
    def detect_seasonality(data: List[float], period: int = 7) -> Dict[str, Any]:
        """Detect seasonal patterns in data"""
        if len(data) < period * 2:
            return {"detected": False, "reason": "Insufficient data"}

        # Calculate seasonal indices
        seasonal_averages = []
        for i in range(period):
            indices = list(range(i, len(data), period))
            if indices:
                values = [data[j] for j in indices if j < len(data)]
                seasonal_averages.append(statistics.mean(values))

        overall_average = statistics.mean(data)

        seasonal_indices = [
            avg / overall_average if overall_average > 0 else 1.0
            for avg in seasonal_averages
        ]

        # Detect strength of seasonality
        variance = statistics.variance(seasonal_indices) if len(seasonal_indices) > 1 else 0

        return {
            "detected": variance > 0.1,
            "period": period,
            "indices": seasonal_indices,
            "strength": variance,
            "peak_season": seasonal_indices.index(max(seasonal_indices)),
            "low_season": seasonal_indices.index(min(seasonal_indices))
        }


class ForecastingModel:
    """Forecasting model for future predictions"""

    def __init__(self):
        self.trend_analyzer = TrendAnalyzer()

    async def forecast_linear(
        self,
        historical_data: List[float],
        periods: int = 30
    ) -> Dict[str, Any]:
        """Generate linear forecast"""
        if len(historical_data) < 2:
            return {
                "forecast": [historical_data[-1]] * periods if historical_data else [0] * periods,
                "confidence": "low",
                "trend": "flat"
            }

        slope, intercept = self.trend_analyzer.calculate_trend_line(historical_data)
        n = len(historical_data)

        # Generate forecast
        forecast = []
        for i in range(periods):
            value = slope * (n + i) + intercept
            forecast.append(max(0, value))  # Ensure non-negative

        # Determine trend direction and confidence
        if abs(slope) < 0.01:
            trend = "stable"
        elif slope > 0:
            trend = "increasing"
        else:
            trend = "decreasing"

        confidence = "high" if len(historical_data) > 30 else "medium" if len(historical_data) > 14 else "low"

        return {
            "forecast": forecast,
            "trend": trend,
            "slope": slope,
            "confidence": confidence,
            "next_value": forecast[0] if forecast else 0,
            "growth_rate": (slope / (statistics.mean(historical_data) or 1)) * 100
        }

    async def forecast_with_seasonality(
        self,
        historical_data: List[float],
        periods: int = 30,
        season_period: int = 7
    ) -> Dict[str, Any]:
        """Generate forecast with seasonal adjustments"""
        if len(historical_data) < season_period * 2:
            return await self.forecast_linear(historical_data, periods)

        # Get trend forecast
        linear_result = await self.forecast_linear(historical_data, periods)
        base_forecast = linear_result["forecast"]

        # Detect seasonality
        seasonality = self.trend_analyzer.detect_seasonality(historical_data, season_period)

        if not seasonality["detected"]:
            return linear_result

        # Apply seasonal adjustments
        adjusted_forecast = []
        for i, value in enumerate(base_forecast):
            seasonal_index = seasonality["indices"][i % season_period]
            adjusted = value * seasonal_index
            adjusted_forecast.append(adjusted)

        return {
            "forecast": adjusted_forecast,
            "base_forecast": base_forecast,
            "seasonality": seasonality,
            "trend": linear_result["trend"],
            "confidence": linear_result["confidence"],
            "next_value": adjusted_forecast[0] if adjusted_forecast else 0
        }

    async def forecast_revenue(
        self,
        daily_revenue: List[float],
        periods: int = 30
    ) -> Dict[str, Any]:
        """Specialized revenue forecasting"""
        if not daily_revenue:
            return {"forecast": [0] * periods, "confidence": "none"}

        # Apply exponential smoothing first
        smoothed = self.trend_analyzer.exponential_smoothing(daily_revenue, alpha=0.2)

        # Then forecast
        result = await self.forecast_with_seasonality(smoothed, periods, season_period=7)

        # Calculate revenue-specific metrics
        total_forecasted = sum(result["forecast"])
        avg_daily = statistics.mean(result["forecast"])

        # Confidence intervals (simple)
        std_dev = statistics.stdev(daily_revenue) if len(daily_revenue) > 1 else 0

        return {
            **result,
            "total_forecasted": round(total_forecasted, 2),
            "avg_daily": round(avg_daily, 2),
            "confidence_lower": [max(0, v - 2 * std_dev) for v in result["forecast"]],
            "confidence_upper": [v + 2 * std_dev for v in result["forecast"]],
            "currency": "INR"
        }


class MarketPredictor:
    """Predict market trends and property values"""

    def __init__(self):
        self.forecasting = ForecastingModel()

    async def predict_property_demand(
        self,
        historical_inquiries: List[int],
        historical_views: List[int],
        periods: int = 30
    ) -> Dict[str, Any]:
        """Predict future property demand"""

        # Combine inquiries and views into demand index
        demand_index = [
            inquiries * 2 + views * 0.1
            for inquiries, views in zip(historical_inquiries, historical_views)
        ]

        forecast = await self.forecasting.forecast_with_seasonality(
            demand_index, periods, season_period=7
        )

        # Categorize demand level
        avg_demand = statistics.mean(forecast["forecast"])

        if avg_demand > 1000:
            demand_level = "very_high"
        elif avg_demand > 500:
            demand_level = "high"
        elif avg_demand > 200:
            demand_level = "medium"
        else:
            demand_level = "low"

        return {
            "demand_forecast": forecast["forecast"],
            "demand_level": demand_level,
            "trend": forecast["trend"],
            "confidence": forecast["confidence"],
            "recommendation": self._demand_recommendation(demand_level, forecast["trend"])
        }

    def _demand_recommendation(self, level: str, trend: str) -> str:
        """Generate recommendation based on demand"""
        if level in ["high", "very_high"] and trend == "increasing":
            return "Increase inventory, prices may rise"
        elif level == "low" and trend == "decreasing":
            return "Consider promotions and marketing"
        elif trend == "stable":
            return "Maintain current strategy"
        return "Monitor market closely"

    async def predict_price_trends(
        self,
        price_history: List[float],
        periods: int = 30
    ) -> Dict[str, Any]:
        """Predict future price trends"""

        forecast = await self.forecasting.forecast_linear(price_history, periods)

        current_price = price_history[-1] if price_history else 0
        predicted_price = forecast["next_value"]

        change_pct = ((predicted_price - current_price) / current_price * 100) if current_price > 0 else 0

        return {
            "current_price": round(current_price, 2),
            "predicted_price": round(predicted_price, 2),
            "change_percent": round(change_pct, 2),
            "trend": forecast["trend"],
            "forecast_prices": [round(p, 2) for p in forecast["forecast"]],
            "confidence": forecast["confidence"]
        }


class PredictiveAnalyticsManager:
    """Main manager for all predictive analytics"""

    def __init__(self):
        self.forecasting = ForecastingModel()
        self.market_predictor = MarketPredictor()

    async def generate_dashboard_forecasts(
        self,
        database
    ) -> Dict[str, Any]:
        """Generate all forecasts for dashboard"""

        # Get historical data
        from datetime import datetime, timedelta

        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=90)

        # Fetch daily metrics from time-series
        from app.timeseries import timeseries_manager, TimeSeriesGranularity

        # Get property count history
        property_metrics = await timeseries_manager.get_metrics(
            "property_count",
            start_date,
            end_date,
            TimeSeriesGranularity.DAY,
            database=database
        )
        property_counts = [m["value"] for m in property_metrics]

        # Get user count history
        user_metrics = await timeseries_manager.get_metrics(
            "user_count",
            start_date,
            end_date,
            TimeSeriesGranularity.DAY,
            database=database
        )
        user_counts = [m["value"] for m in user_metrics]

        # Get inquiry count history
        inquiry_metrics = await timeseries_manager.get_metrics(
            "inquiry_count",
            start_date,
            end_date,
            TimeSeriesGranularity.DAY,
            database=database
        )
        inquiry_counts = [m["value"] for m in inquiry_metrics]

        # Generate forecasts
        forecasts = {
            "generated_at": datetime.utcnow().isoformat(),
            "forecast_period": "30 days",
            "property_growth": await self.forecasting.forecast_linear(property_counts, 30),
            "user_growth": await self.forecasting.forecast_linear(user_counts, 30),
            "inquiry_forecast": await self.forecasting.forecast_with_seasonality(inquiry_counts, 30, 7),
            "market_demand": await self.market_predictor.predict_property_demand(
                [int(i) for i in inquiry_counts],
                [int(u) for u in user_counts],
                30
            ) if inquiry_counts and user_counts else None
        }

        # Add insights
        forecasts["insights"] = self._generate_insights(forecasts)

        return forecasts

    def _generate_insights(self, forecasts: Dict[str, Any]) -> List[str]:
        """Generate actionable insights from forecasts"""
        insights = []

        # Property growth insight
        if "property_growth" in forecasts:
            growth = forecasts["property_growth"]
            if growth.get("trend") == "increasing":
                insights.append(f"Property listings expected to grow {abs(growth.get('growth_rate', 0)):.1f}% over next 30 days")
            elif growth.get("trend") == "decreasing":
                insights.append("Property listings declining - consider marketing campaigns")

        # User growth insight
        if "user_growth" in forecasts:
            user_growth = forecasts["user_growth"]
            if user_growth.get("trend") == "increasing":
                insights.append(f"User base growing - prepare for {user_growth.get('next_value', 0):.0f} new users")

        # Demand insight
        if forecasts.get("market_demand"):
            demand = forecasts["market_demand"]
            insights.append(f"Market demand: {demand.get('demand_level', 'unknown')} ({demand.get('trend', 'stable')})")
            if demand.get("recommendation"):
                insights.append(f"Recommendation: {demand['recommendation']}")

        return insights


# Global instance
predictive_analytics = PredictiveAnalyticsManager()
