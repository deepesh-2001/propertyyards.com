"""
Comparison Router
API endpoints for flight and price comparison
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional
from datetime import datetime, date
from pydantic import BaseModel

from app.database import get_db
from app.auth import get_current_user

router = APIRouter(prefix="/api/comparison", tags=["comparison"])


# ========== Flight Comparison ==========

class FlightSearchRequest(BaseModel):
    """Flight search request"""
    origin: str  # IATA code (e.g., DEL, BOM)
    destination: str  # IATA code
    departure_date: date
    return_date: Optional[date] = None
    passengers: int = 1
    cabin_class: str = "economy"  # economy, premium_economy, business, first
    trip_type: str = "one_way"  # one_way, round_trip


@router.post("/flights/search")
async def search_flights(
    request: FlightSearchRequest,
    database=Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Search and compare flight prices across airlines (via microservice)"""
    try:
        from app.api_gateway import api_gateway

        # Forward request to flight-price microservice
        result = await api_gateway.forward_request(
            service_name="flight-price",
            path="/search",
            method="POST",
            json_data=request.dict()
        )

        return result

    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid parameter: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/flights/cheapest")
async def get_cheapest_flight(
    origin: str,
    destination: str,
    departure_date: date,
    passengers: int = 1,
    cabin_class: str = "economy",
    database=Depends(get_db)
):
    """Get cheapest flight for a route (via microservice)"""
    try:
        from app.api_gateway import api_gateway

        # Forward request to flight-price microservice
        result = await api_gateway.forward_request(
            service_name="flight-price",
            path="/cheapest",
            method="GET",
            params={
                "origin": origin,
                "destination": destination,
                "departure_date": departure_date.isoformat(),
                "passengers": passengers,
                "cabin_class": cabin_class
            }
        )

        return result

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/flights/airports")
async def get_airports(
    country: Optional[str] = "IN",
    current_user: dict = Depends(get_current_user)
):
    """Get list of airports (via microservice)"""
    try:
        from app.api_gateway import api_gateway

        result = await api_gateway.forward_request(
            service_name="flight-price",
            path="/airports",
            method="GET",
            params={"country": country}
        )

        return result

    except Exception:
        # Fallback to local data if microservice unavailable
        airports = [
            {"code": "DEL", "name": "Indira Gandhi International", "city": "New Delhi"},
            {"code": "BOM", "name": "Chhatrapati Shivaji Maharaj", "city": "Mumbai"},
            {"code": "BLR", "name": "Kempegowda International", "city": "Bangalore"},
            {"code": "MAA", "name": "Chennai International", "city": "Chennai"},
            {"code": "HYD", "name": "Rajiv Gandhi International", "city": "Hyderabad"},
        ]
        return {"airports": airports, "source": "fallback"}


# ========== Price Comparison ==========

@router.get("/properties/compare")
async def compare_property_prices(
    location: str,
    property_type: str = "apartment",
    bedrooms: int = 2,
    bathrooms: int = 2,
    max_results: int = 10,
    database=Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Compare property prices across platforms (99acres, MagicBricks, Housing.com)"""
    try:
        from app.price_comparison_service import price_comparison

        results = await price_comparison.compare_property_prices(
            location=location,
            property_type=property_type,
            bedrooms=bedrooms,
            bathrooms=bathrooms,
            max_results=max_results
        )

        # Calculate savings
        savings_analysis = price_comparison.calculate_savings(results)

        return {
            "search_params": {
                "location": location,
                "property_type": property_type,
                "bedrooms": bedrooms,
                "bathrooms": bathrooms
            },
            "total_results": len(results),
            "savings_analysis": savings_analysis,
            "results": [
                {
                    "id": r.id,
                    "provider": r.provider,
                    "price": r.price,
                    "original_price": r.original_price,
                    "discount_percentage": r.discount_percentage,
                    "url": r.url,
                    "rating": r.rating,
                    "reviews_count": r.reviews_count,
                    "location": r.location,
                    "area_sqft": r.area_sqft,
                    "amenities": r.amenities,
                    "features": r.features,
                    "broker_name": r.broker_name
                }
                for r in results
            ]
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/properties/best-deal")
async def get_best_property_deal(
    location: str,
    property_type: str = "apartment",
    bedrooms: int = 2,
    database=Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get the best property deal based on price and rating"""
    try:
        from app.price_comparison_service import price_comparison

        results = await price_comparison.compare_property_prices(
            location=location,
            property_type=property_type,
            bedrooms=bedrooms,
            max_results=10
        )

        best_deal = price_comparison.get_best_deal(results)

        if not best_deal:
            raise HTTPException(status_code=404, detail="No properties found")

        return {
            "best_deal": {
                "id": best_deal.id,
                "provider": best_deal.provider,
                "price": best_deal.price,
                "rating": best_deal.rating,
                "reviews_count": best_deal.reviews_count,
                "url": best_deal.url,
                "features": best_deal.features
            },
            "alternatives": [
                {
                    "provider": r.provider,
                    "price": r.price,
                    "price_difference": r.price - best_deal.price
                }
                for r in results[:5] if r.id != best_deal.id
            ]
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/products/compare")
async def compare_product_prices(
    product_name: str,
    category: Optional[str] = None,
    max_results: int = 10,
    current_user: dict = Depends(get_current_user)
):
    """Compare product prices across e-commerce platforms"""
    try:
        from app.price_comparison_service import price_comparison

        results = await price_comparison.compare_product_prices(
            product_name=product_name,
            category=category,
            max_results=max_results
        )

        savings_analysis = price_comparison.calculate_savings(results)

        return {
            "search_params": {
                "product_name": product_name,
                "category": category
            },
            "total_results": len(results),
            "savings_analysis": savings_analysis,
            "results": [
                {
                    "id": r.id,
                    "provider": r.provider,
                    "price": r.price,
                    "original_price": r.original_price,
                    "discount_percentage": r.discount_percentage,
                    "url": r.url,
                    "rating": r.rating,
                    "in_stock": r.in_stock,
                    "delivery_days": r.delivery_days,
                    "features": r.features
                }
                for r in results
            ]
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/savings-report")
async def get_savings_report(
    location: str,
    property_type: str = "apartment",
    bedrooms: int = 2,
    database=Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get detailed savings report for property comparison"""
    try:
        from app.price_comparison_service import price_comparison

        results = await price_comparison.compare_property_prices(
            location=location,
            property_type=property_type,
            bedrooms=bedrooms,
            max_results=20
        )

        savings = price_comparison.calculate_savings(results)

        # Price range analysis
        prices = [r.price for r in results]
        avg_price = sum(prices) / len(prices) if prices else 0

        return {
            "location": location,
            "property_type": property_type,
            "bedrooms": bedrooms,
            "market_summary": {
                "total_listings": len(results),
                "average_price": round(avg_price, 2),
                "price_range": {
                    "min": min(prices) if prices else 0,
                    "max": max(prices) if prices else 0
                }
            },
            "savings_analysis": savings,
            "platform_comparison": [
                {
                    "provider": r.provider,
                    "avg_price": r.price,
                    "rating": r.rating,
                    "listing_count": len([x for x in results if x.provider == r.provider])
                }
                for r in set(results)
            ]
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
