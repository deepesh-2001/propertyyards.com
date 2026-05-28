"""
Future Prediction Module
Handles predictive analytics for property values, market trends, and sales forecasts
"""
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import logging
import statistics
from collections import defaultdict

from app.schemas import (
    PredictionType,
    PredictionModel,
    PredictionStatus
)

logger = logging.getLogger(__name__)


class PredictionEngine:
    """Prediction engine using various models"""
    
    def __init__(self):
        self.models = {
            PredictionModel.LINEAR_REGRESSION: self._linear_regression,
            PredictionModel.ARIMA: self._arima,
            PredictionModel.RANDOM_FOREST: self._random_forest,
            PredictionModel.PROPHET: self._prophet
        }
    
    async def predict(
        self,
        historical_data: List[Dict[str, Any]],
        prediction_type: PredictionType,
        model: PredictionModel,
        forecast_days: int,
        parameters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Generate predictions using specified model"""
        try:
            prediction_func = self.models.get(model, self._linear_regression)
            predictions = await prediction_func(historical_data, forecast_days, parameters or {})
            
            return {
                "predictions": predictions,
                "model": model,
                "confidence_interval": self._calculate_confidence_interval(predictions),
                "accuracy_score": self._calculate_accuracy(historical_data, predictions)
            }
        except Exception as e:
            logger.error(f"Prediction error: {e}")
            raise
    
    def _linear_regression(
        self,
        historical_data: List[Dict[str, Any]],
        forecast_days: int,
        parameters: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Simple linear regression prediction"""
        if len(historical_data) < 2:
            raise ValueError("Insufficient historical data")
        
        # Extract values and dates
        values = [float(d.get("value", d.get("price", d.get("amount", 0)))) for d in historical_data]
        
        # Calculate trend
        n = len(values)
        x = list(range(n))
        
        # Calculate slope and intercept
        sum_x = sum(x)
        sum_y = sum(values)
        sum_xy = sum(x[i] * values[i] for i in range(n))
        sum_x2 = sum(xi ** 2 for xi in x)
        
        slope = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x ** 2)
        intercept = (sum_y - slope * sum_x) / n
        
        # Generate predictions
        predictions = []
        last_value = values[-1]
        last_date = historical_data[-1].get("date", datetime.utcnow())
        
        for i in range(1, forecast_days + 1):
            predicted_value = intercept + slope * (n + i - 1)
            predicted_date = last_date + timedelta(days=i)
            
            predictions.append({
                "date": predicted_date,
                "predicted_value": max(0, predicted_value),
                "trend": "up" if slope > 0 else "down",
                "change_percent": ((predicted_value - last_value) / last_value * 100) if last_value > 0 else 0
            })
        
        return predictions
    
    def _arima(
        self,
        historical_data: List[Dict[str, Any]],
        forecast_days: int,
        parameters: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """ARIMA-based prediction (simplified)"""
        # For simplicity, using moving average with trend
        values = [float(d.get("value", d.get("price", 0))) for d in historical_data]
        
        window_size = parameters.get("window_size", 7)
        if len(values) < window_size:
            window_size = len(values)
        
        predictions = []
        last_date = historical_data[-1].get("date", datetime.utcnow())
        
        for i in range(1, forecast_days + 1):
            # Calculate moving average
            recent_values = values[-window_size:]
            ma = statistics.mean(recent_values)
            
            # Add trend component
            if len(values) >= window_size * 2:
                prev_ma = statistics.mean(values[-window_size*2:-window_size])
                trend = ma - prev_ma
            else:
                trend = 0
            
            predicted_value = ma + (trend * i)
            predicted_date = last_date + timedelta(days=i)
            
            predictions.append({
                "date": predicted_date,
                "predicted_value": max(0, predicted_value),
                "trend": "up" if trend > 0 else "down",
                "change_percent": (trend / ma * 100) if ma > 0 else 0
            })
        
        return predictions
    
    def _random_forest(
        self,
        historical_data: List[Dict[str, Any]],
        forecast_days: int,
        parameters: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Random forest-style prediction (simplified ensemble)"""
        # Use multiple methods and average
        lr_predictions = self._linear_regression(historical_data, forecast_days, parameters)
        arima_predictions = self._arima(historical_data, forecast_days, parameters)
        
        # Ensemble predictions
        predictions = []
        for i in range(forecast_days):
            avg_value = (lr_predictions[i]["predicted_value"] + arima_predictions[i]["predicted_value"]) / 2
            predictions.append({
                "date": lr_predictions[i]["date"],
                "predicted_value": avg_value,
                "trend": lr_predictions[i]["trend"],
                "change_percent": (lr_predictions[i]["change_percent"] + arima_predictions[i]["change_percent"]) / 2
            })
        
        return predictions
    
    def _prophet(
        self,
        historical_data: List[Dict[str, Any]],
        forecast_days: int,
        parameters: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Prophet-style prediction (simplified)"""
        # Add seasonality and trend components
        values = [float(d.get("value", d.get("price", 0))) for d in historical_data]
        
        # Calculate trend
        n = len(values)
        x = list(range(n))
        slope = (values[-1] - values[0]) / n if n > 1 else 0
        
        # Calculate seasonality (weekly pattern)
        seasonality = []
        if len(values) >= 7:
            for i in range(7):
                week_values = [values[j] for j in range(i, len(values), 7)]
                seasonality.append(statistics.mean(week_values) - statistics.mean(values))
        
        predictions = []
        last_date = historical_data[-1].get("date", datetime.utcnow())
        base_value = values[-1]
        
        for i in range(1, forecast_days + 1):
            # Trend component
            trend_component = slope * i
            
            # Seasonality component
            seasonality_index = (i - 1) % 7 if seasonality else 0
            seasonality_component = seasonality[seasonality_index] if seasonality else 0
            
            predicted_value = base_value + trend_component + seasonality_component
            predicted_date = last_date + timedelta(days=i)
            
            predictions.append({
                "date": predicted_date,
                "predicted_value": max(0, predicted_value),
                "trend": "up" if slope > 0 else "down",
                "change_percent": (trend_component / base_value * 100) if base_value > 0 else 0
            })
        
        return predictions
    
    def _calculate_confidence_interval(self, predictions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate confidence interval for predictions"""
        values = [p["predicted_value"] for p in predictions]
        if not values:
            return {"lower": [], "upper": []}
        
        std_dev = statistics.stdev(values) if len(values) > 1 else 0
        confidence = 1.96  # 95% confidence
        
        lower = [v - confidence * std_dev for v in values]
        upper = [v + confidence * std_dev for v in values]
        
        return {"lower": lower, "upper": upper}
    
    def _calculate_accuracy(
        self,
        historical_data: List[Dict[str, Any]],
        predictions: List[Dict[str, Any]]
    ) -> float:
        """Calculate prediction accuracy score"""
        if len(historical_data) < 2 or not predictions:
            return 0.0
        
        # Simple accuracy based on trend direction
        actual_values = [float(d.get("value", d.get("price", 0))) for d in historical_data[-10:]]
        if len(actual_values) < 2:
            return 0.0
        
        actual_trend = 1 if actual_values[-1] > actual_values[0] else -1
        predicted_trend = 1 if predictions[0]["trend"] == "up" else -1
        
        return 1.0 if actual_trend == predicted_trend else 0.0


class PropertyPredictor:
    """Property value prediction"""
    
    def __init__(self):
        self.engine = PredictionEngine()
    
    async def predict_property_value(
        self,
        property_id: str,
        historical_data: List[Dict[str, Any]],
        database,
        timeframe: str = "6 months"
    ) -> Dict[str, Any]:
        """Predict property value for a specific property"""
        try:
            # Get property details
            property_data = await database.properties.find_one({"_id": property_id})
            if not property_data:
                raise ValueError("Property not found")
            
            current_value = property_data.get("price", 0)
            
            # Generate predictions
            forecast_days = self._timeframe_to_days(timeframe)
            predictions = await self.engine.predict(
                historical_data=historical_data,
                prediction_type=PredictionType.PROPERTY_VALUE,
                model=PredictionModel.LINEAR_REGRESSION,
                forecast_days=forecast_days
            )
            
            final_prediction = predictions["predictions"][-1]
            predicted_value = final_prediction["predicted_value"]
            change_percent = final_prediction["change_percent"]
            change_amount = predicted_value - current_value
            
            # Analyze factors
            factors = self._analyze_factors(property_data, historical_data)
            
            return {
                "property_id": property_id,
                "current_value": current_value,
                "predicted_value": predicted_value,
                "predicted_change_percent": change_percent,
                "predicted_change_amount": change_amount,
                "confidence": predictions["accuracy_score"],
                "timeframe": timeframe,
                "factors": factors,
                "generated_at": datetime.utcnow()
            }
            
        except Exception as e:
            logger.error(f"Property value prediction error: {e}")
            raise
    
    def _timeframe_to_days(self, timeframe: str) -> int:
        """Convert timeframe string to days"""
        mapping = {
            "1 month": 30,
            "3 months": 90,
            "6 months": 180,
            "1 year": 365
        }
        return mapping.get(timeframe, 180)
    
    def _analyze_factors(
        self,
        property_data: Dict[str, Any],
        historical_data: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Analyze factors affecting property value"""
        factors = []
        
        # Location factor
        location = property_data.get("location", "")
        if location:
            factors.append({
                "factor": "Location",
                "impact": "positive" if "prime" in location.lower() else "neutral",
                "description": f"Property located in {location}"
            })
        
        # Property type factor
        property_type = property_data.get("property_type", "")
        factors.append({
            "factor": "Property Type",
            "impact": "neutral",
            "description": f"{property_type} property"
        })
        
        # Historical trend factor
        if len(historical_data) >= 2:
            recent_values = [float(d.get("value", 0)) for d in historical_data[-5:]]
            trend = "up" if recent_values[-1] > recent_values[0] else "down"
            factors.append({
                "factor": "Historical Trend",
                "impact": trend,
                "description": f"Recent trend is {trend}"
            })
        
        return factors


class MarketPredictor:
    """Market trend prediction"""
    
    def __init__(self):
        self.engine = PredictionEngine()
    
    async def predict_market_trend(
        self,
        location: str,
        historical_data: List[Dict[str, Any]],
        database,
        timeframe: str = "6 months"
    ) -> Dict[str, Any]:
        """Predict market trend for a location"""
        try:
            forecast_days = self._timeframe_to_days(timeframe)
            predictions = await self.engine.predict(
                historical_data=historical_data,
                prediction_type=PredictionType.MARKET_TREND,
                model=PredictionModel.PROPHET,
                forecast_days=forecast_days
            )
            
            final_prediction = predictions["predictions"][-1]
            predicted_trend = final_prediction["trend"]
            price_change = final_prediction["change_percent"]
            
            # Calculate volume change (simplified)
            volume_change = price_change * 0.8  # Assume volume correlates with price
            
            # Determine market sentiment
            if price_change > 5:
                sentiment = "bullish"
            elif price_change < -5:
                sentiment = "bearish"
            else:
                sentiment = "neutral"
            
            # Identify key factors
            key_factors = self._identify_market_factors(historical_data, predictions)
            
            return {
                "location": location,
                "current_trend": "up" if historical_data[-1].get("value", 0) > historical_data[0].get("value", 0) else "down",
                "predicted_trend": predicted_trend,
                "market_sentiment": sentiment,
                "price_change_percent": price_change,
                "volume_change_percent": volume_change,
                "key_factors": key_factors,
                "timeframe": timeframe,
                "generated_at": datetime.utcnow()
            }
            
        except Exception as e:
            logger.error(f"Market trend prediction error: {e}")
            raise
    
    def _timeframe_to_days(self, timeframe: str) -> int:
        """Convert timeframe string to days"""
        mapping = {
            "1 month": 30,
            "3 months": 90,
            "6 months": 180,
            "1 year": 365
        }
        return mapping.get(timeframe, 180)
    
    def _identify_market_factors(
        self,
        historical_data: List[Dict[str, Any]],
        predictions: Dict[str, Any]
    ) -> List[str]:
        """Identify key factors affecting market"""
        factors = []
        
        # Price momentum
        if len(historical_data) >= 7:
            recent_avg = statistics.mean([d.get("value", 0) for d in historical_data[-7:]])
            older_avg = statistics.mean([d.get("value", 0) for d in historical_data[-14:-7]])
            if recent_avg > older_avg:
                factors.append("Positive price momentum")
            else:
                factors.append("Negative price momentum")
        
        # Volatility
        values = [d.get("value", 0) for d in historical_data[-30:]]
        if len(values) > 1:
            std_dev = statistics.stdev(values)
            mean = statistics.mean(values)
            volatility = (std_dev / mean * 100) if mean > 0 else 0
            if volatility > 10:
                factors.append("High market volatility")
            else:
                factors.append("Low market volatility")
        
        return factors


class SalesForecaster:
    """Sales forecasting"""
    
    def __init__(self):
        self.engine = PredictionEngine()
    
    async def forecast_sales(
        self,
        period: str,
        historical_sales: List[Dict[str, Any]],
        database,
        forecast_months: int = 3
    ) -> Dict[str, Any]:
        """Forecast sales for a period"""
        try:
            # Prepare data
            historical_data = [
                {"date": d.get("date", datetime.utcnow()), "value": d.get("sales", 0)}
                for d in historical_sales
            ]
            
            forecast_days = forecast_months * 30
            predictions = await self.engine.predict(
                historical_data=historical_data,
                prediction_type=PredictionType.SALES_FORECAST,
                model=PredictionModel.RANDOM_FOREST,
                forecast_days=forecast_days
            )
            
            # Calculate totals
            predicted_sales = sum(p["predicted_value"] for p in predictions["predictions"])
            avg_price = historical_sales[-1].get("avg_price", 100000) if historical_sales else 100000
            predicted_revenue = predicted_sales * avg_price
            
            # Calculate confidence
            confidence_level = predictions["accuracy_score"]
            
            # Best and worst case scenarios
            best_case = {
                "predicted_sales": predicted_sales * 1.2,
                "predicted_revenue": predicted_revenue * 1.2
            }
            worst_case = {
                "predicted_sales": predicted_sales * 0.8,
                "predicted_revenue": predicted_revenue * 0.8
            }
            
            # Identify factors
            factors = self._identify_sales_factors(historical_sales)
            
            forecast_period_start = datetime.utcnow()
            forecast_period_end = forecast_period_start + timedelta(days=forecast_days)
            
            return {
                "period": period,
                "forecast_period_start": forecast_period_start,
                "forecast_period_end": forecast_period_end,
                "predicted_sales": int(predicted_sales),
                "predicted_revenue": predicted_revenue,
                "confidence_level": confidence_level,
                "best_case": best_case,
                "worst_case": worst_case,
                "factors": factors,
                "generated_at": datetime.utcnow()
            }
            
        except Exception as e:
            logger.error(f"Sales forecast error: {e}")
            raise
    
    def _identify_sales_factors(self, historical_sales: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Identify factors affecting sales"""
        factors = []
        
        if len(historical_sales) >= 3:
            # Recent trend
            recent_sales = [d.get("sales", 0) for d in historical_sales[-3:]]
            if recent_sales[-1] > recent_sales[0]:
                factors.append({
                    "factor": "Recent Trend",
                    "impact": "positive",
                    "description": "Sales have been increasing"
                })
            else:
                factors.append({
                    "factor": "Recent Trend",
                    "impact": "negative",
                    "description": "Sales have been decreasing"
                })
        
        return factors


# Global predictor instances
property_predictor = PropertyPredictor()
market_predictor = MarketPredictor()
sales_forecaster = SalesForecaster()
