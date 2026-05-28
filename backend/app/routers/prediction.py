"""
Prediction Router
Handles property value predictions, market trends, and sales forecasts
"""
from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional
from datetime import datetime

from app.database import get_db
from app.schemas import (
    PredictionRequestCreate,
    PredictionRequestResponse,
    PredictionResult,
    PropertyValuePrediction,
    MarketTrendPrediction,
    SalesForecast,
    PredictionType,
    PredictionModel,
    PredictionStatus
)
from app.prediction import property_predictor, market_predictor, sales_forecaster
from app.auth import get_current_user

router = APIRouter(prefix="/api/predictions", tags=["predictions"])


# ========== Property Value Prediction Endpoints ==========

@router.post("/property-value", response_model=PropertyValuePrediction)
async def predict_property_value(
    property_id: str,
    timeframe: str = "6 months",
    database=Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Predict property value for a specific property"""
    try:
        # Get historical price data for the property
        historical_data = await database.property_prices.find({"property_id": property_id}).sort("date", 1).to_list(length=365)
        
        if not historical_data:
            # Generate sample historical data if none exists
            property_data = await database.properties.find_one({"_id": property_id})
            if not property_data:
                raise HTTPException(status_code=404, detail="Property not found")
            
            current_price = property_data.get("price", 0)
            historical_data = []
            for i in range(365):
                date = datetime.utcnow() - timedelta(days=365 - i)
                historical_data.append({
                    "date": date,
                    "value": current_price * (1 - (365 - i) * 0.001)  # Simulated historical trend
                })
        
        prediction = await property_predictor.predict_property_value(
            property_id=property_id,
            historical_data=historical_data,
            timeframe=timeframe,
            database=database
        )
        
        return PropertyValuePrediction(**prediction)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ========== Market Trend Prediction Endpoints ==========

@router.post("/market-trend", response_model=MarketTrendPrediction)
async def predict_market_trend(
    location: str,
    timeframe: str = "6 months",
    database=Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Predict market trend for a location"""
    try:
        # Get historical market data for the location
        historical_data = await database.market_data.find({"location": location}).sort("date", 1).to_list(length=365)
        
        if not historical_data:
            # Generate sample historical data if none exists
            historical_data = []
            for i in range(365):
                date = datetime.utcnow() - timedelta(days=365 - i)
                historical_data.append({
                    "date": date,
                    "value": 1000000 * (1 + (i / 365) * 0.05)  # Simulated market trend
                })
        
        prediction = await market_predictor.predict_market_trend(
            location=location,
            historical_data=historical_data,
            timeframe=timeframe,
            database=database
        )
        
        return MarketTrendPrediction(**prediction)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ========== Sales Forecast Endpoints ==========

@router.post("/sales-forecast", response_model=SalesForecast)
async def forecast_sales(
    period: str = "monthly",
    forecast_months: int = 3,
    database=Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Forecast sales for a period"""
    try:
        # Get historical sales data
        historical_sales = await database.sales_data.find().sort("date", 1).to_list(length=365)
        
        if not historical_sales:
            # Generate sample historical data if none exists
            historical_sales = []
            for i in range(365):
                date = datetime.utcnow() - timedelta(days=365 - i)
                historical_sales.append({
                    "date": date,
                    "sales": 10 + (i % 30),  # Simulated sales pattern
                    "avg_price": 1000000
                })
        
        forecast = await sales_forecaster.forecast_sales(
            period=period,
            historical_sales=historical_sales,
            forecast_months=forecast_months,
            database=database
        )
        
        return SalesForecast(**forecast)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ========== Prediction Request Endpoints ==========

@router.post("/requests", response_model=PredictionRequestResponse, status_code=status.HTTP_201_CREATED)
async def create_prediction_request(
    request: PredictionRequestCreate,
    database=Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Create a new prediction request"""
    try:
        request_data = request.dict()
        request_data.update({
            "status": PredictionStatus.PENDING,
            "created_at": datetime.utcnow(),
            "completed_at": None
        })
        
        result = await database.prediction_requests.insert_one(request_data)
        request_data["id"] = str(result.inserted_id)
        
        return PredictionRequestResponse(**request_data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/requests/{request_id}", response_model=PredictionRequestResponse)
async def get_prediction_request(
    request_id: str,
    database=Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get a specific prediction request"""
    request = await database.prediction_requests.find_one({"_id": request_id})
    if not request:
        raise HTTPException(status_code=404, detail="Prediction request not found")
    
    request["id"] = str(request["_id"])
    del request["_id"]
    
    return PredictionRequestResponse(**request)


@router.get("/requests", response_model=List[PredictionRequestResponse])
async def get_prediction_requests(
    status: Optional[PredictionStatus] = None,
    prediction_type: Optional[PredictionType] = None,
    database=Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get all prediction requests"""
    query = {}
    if status:
        query["status"] = status
    if prediction_type:
        query["prediction_type"] = prediction_type
    
    cursor = database.prediction_requests.find(query).sort("created_at", -1)
    requests = await cursor.to_list(length=100)
    
    for request in requests:
        request["id"] = str(request["_id"])
        del request["_id"]
    
    return [PredictionRequestResponse(**r) for r in requests]


# ========== Prediction Results Endpoints ==========

@router.get("/results/{result_id}", response_model=PredictionResult)
async def get_prediction_result(
    result_id: str,
    database=Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get a specific prediction result"""
    result = await database.prediction_results.find_one({"_id": result_id})
    if not result:
        raise HTTPException(status_code=404, detail="Prediction result not found")
    
    result["id"] = str(result["_id"])
    del result["_id"]
    
    return PredictionResult(**result)


@router.get("/requests/{request_id}/results", response_model=List[PredictionResult])
async def get_prediction_results_for_request(
    request_id: str,
    database=Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get all results for a prediction request"""
    cursor = database.prediction_results.find({"prediction_request_id": request_id}).sort("generated_at", -1)
    results = await cursor.to_list(length=10)
    
    for result in results:
        result["id"] = str(result["_id"])
        del result["_id"]
    
    return [PredictionResult(**r) for r in results]
