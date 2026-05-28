"""
Cabs Router
API endpoints for cab search and booking (Ola, Uber, Rapido)
Includes: rate limiting, input validation, Redis caching, ownership checks, auto-lead generation
"""
from fastapi import APIRouter, Depends, HTTPException, Request
from typing import Optional
from pydantic import BaseModel, validator
import json
import hashlib
import logging

from app.auth import get_current_user
from app.security import limiter

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/cabs", tags=["cabs"])

LAT_MIN, LAT_MAX = -90.0, 90.0
LNG_MIN, LNG_MAX = -180.0, 180.0
FARE_MAX = 50000.0


class EstimateRequest(BaseModel):
    pickup_lat: float
    pickup_lng: float
    drop_lat: float
    drop_lng: float
    pickup_address: Optional[str] = None
    drop_address: Optional[str] = None

    @validator('pickup_lat', 'drop_lat')
    def validate_lat(cls, v):
        if not (LAT_MIN <= v <= LAT_MAX):
            raise ValueError(f'Latitude must be between {LAT_MIN} and {LAT_MAX}')
        return v

    @validator('pickup_lng', 'drop_lng')
    def validate_lng(cls, v):
        if not (LNG_MIN <= v <= LNG_MAX):
            raise ValueError(f'Longitude must be between {LNG_MIN} and {LNG_MAX}')
        return v


class BookCabRequest(BaseModel):
    offer_id: str
    provider: str
    category: str
    pickup_lat: float
    pickup_lng: float
    pickup_address: str
    drop_lat: float
    drop_lng: float
    drop_address: str
    estimated_fare: float

    @validator('estimated_fare')
    def validate_fare(cls, v):
        if v <= 0 or v > FARE_MAX:
            raise ValueError(f'Fare must be between 1 and {FARE_MAX}')
        return v

    @validator('provider')
    def validate_provider(cls, v):
        allowed = {'ola', 'uber', 'rapido', 'Ola', 'Uber', 'Rapido'}
        if v not in allowed:
            raise ValueError(f'Provider must be one of: {allowed}')
        return v

    @validator('category')
    def validate_category(cls, v):
        allowed = {'mini', 'sedan', 'suv', 'auto', 'bike', 'prime'}
        if v.lower() not in allowed:
            raise ValueError(f'Category must be one of: {allowed}')
        return v.lower()


@router.post("/estimates")
@limiter.limit("30/minute")
async def get_estimates(
    request: Request,
    body: EstimateRequest,
    current_user: dict = Depends(get_current_user)
):
    """Get fare estimates — rate limited 30/min, Redis cached 5 min, auto-lead on intent"""
    try:
        from app.cab_booking_service import cab_booking_service
        from app.cache import get_cache, set_cache
        from app.travel_lead_service import travel_lead_service

        cache_key = "cab:estimates:" + hashlib.md5(
            f"{round(body.pickup_lat,3)},{round(body.pickup_lng,3)}"
            f",{round(body.drop_lat,3)},{round(body.drop_lng,3)}".encode()
        ).hexdigest()

        cached = await get_cache(cache_key)
        if cached:
            return cached

        offers = await cab_booking_service.get_estimates(
            body.pickup_lat, body.pickup_lng,
            body.drop_lat, body.drop_lng
        )

        result = {
            "status": "success",
            "count": len(offers),
            "cached": False,
            "estimates": [
                {
                    "id": o.id,
                    "provider": o.provider,
                    "category": o.category.value,
                    "display_name": o.display_name,
                    "estimated_fare": o.estimated_fare,
                    "currency": o.currency,
                    "estimated_duration_minutes": o.estimated_duration_minutes,
                    "estimated_distance_km": o.estimated_distance_km,
                    "surge_multiplier": o.surge_multiplier,
                    "features": o.features,
                    "cancellation_policy": o.cancellation_policy
                }
                for o in offers
            ]
        }
        await set_cache(cache_key, result, ttl=300)

        await travel_lead_service.create_lead_from_cab_estimate(
            user_id=str(current_user.get("user_id", current_user.get("_id", ""))),
            user_email=current_user.get("email"),
            user_phone=current_user.get("phone"),
            pickup_lat=body.pickup_lat,
            pickup_lng=body.pickup_lng,
            drop_lat=body.drop_lat,
            drop_lng=body.drop_lng,
            pickup_address=body.pickup_address,
            drop_address=body.drop_address
        )

        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Cab estimate error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/book")
@limiter.limit("10/minute")
async def book_cab(
    request: Request,
    body: BookCabRequest,
    current_user: dict = Depends(get_current_user)
):
    """Book a cab — rate limited 10/min, auto-lead created on booking"""
    try:
        from app.cab_booking_service import cab_booking_service
        from app.travel_lead_service import travel_lead_service

        user_id = str(current_user.get("user_id", current_user.get("_id", "")))
        booking = await cab_booking_service.book_cab(
            user_id=user_id,
            offer_id=body.offer_id,
            pickup_lat=body.pickup_lat,
            pickup_lng=body.pickup_lng,
            pickup_address=body.pickup_address,
            drop_lat=body.drop_lat,
            drop_lng=body.drop_lng,
            drop_address=body.drop_address,
            estimated_fare=body.estimated_fare,
            provider=body.provider,
            category=body.category
        )

        await travel_lead_service.create_lead_from_cab_booking(
            user_id=user_id,
            user_email=current_user.get("email"),
            user_phone=current_user.get("phone"),
            booking_id=booking.booking_id,
            pickup_address=body.pickup_address,
            pickup_lat=body.pickup_lat,
            pickup_lng=body.pickup_lng,
            drop_address=body.drop_address,
            drop_lat=body.drop_lat,
            drop_lng=body.drop_lng,
            estimated_fare=body.estimated_fare,
            provider=body.provider,
            category=body.category
        )

        from app.travel_notification_service import travel_notification_service
        user_name = (
            current_user.get("name") or
            (current_user.get("email", "").split("@")[0].replace(".", " ").title()) or
            "Valued Guest"
        )
        await travel_notification_service.notify_cab_booking(
            name=user_name,
            email=current_user.get("email"),
            phone=current_user.get("phone"),
            booking_id=booking.booking_id,
            provider=booking.provider,
            category=booking.category.value,
            pickup=booking.pickup_address,
            drop=booking.drop_address,
            fare=booking.estimated_fare,
            otp=booking.otp
        )

        return {
            "status": "success",
            "booking_id": booking.booking_id,
            "otp": booking.otp,
            "booking_status": booking.status.value,
            "provider": booking.provider,
            "category": booking.category.value,
            "pickup": booking.pickup_address,
            "drop": booking.drop_address,
            "estimated_fare": booking.estimated_fare,
            "currency": booking.currency
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Cab book error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/bookings")
@limiter.limit("60/minute")
async def get_my_bookings(
    request: Request,
    current_user: dict = Depends(get_current_user)
):
    """Get current user's cab bookings"""
    try:
        from app.cab_booking_service import cab_booking_service
        user_id = str(current_user.get("user_id", current_user.get("_id", "")))
        bookings = [b for b in cab_booking_service.bookings.values() if b.user_id == user_id]
        return {
            "status": "success",
            "count": len(bookings),
            "bookings": [
                {
                    "booking_id": b.booking_id,
                    "provider": b.provider,
                    "category": b.category.value,
                    "pickup": b.pickup_address,
                    "drop": b.drop_address,
                    "estimated_fare": b.estimated_fare,
                    "final_fare": b.final_fare,
                    "currency": b.currency,
                    "status": b.status.value,
                    "created_at": b.created_at.isoformat()
                }
                for b in bookings
            ]
        }
    except Exception as e:
        logger.error(f"Get bookings error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/bookings/{booking_id}")
@limiter.limit("60/minute")
async def get_booking(
    request: Request,
    booking_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get booking details — ownership enforced"""
    try:
        from app.cab_booking_service import cab_booking_service
        booking = cab_booking_service.bookings.get(booking_id)
        if not booking:
            raise HTTPException(status_code=404, detail="Booking not found")

        user_id = str(current_user.get("user_id", current_user.get("_id", "")))
        if booking.user_id != user_id and current_user.get("role") != "admin":
            raise HTTPException(status_code=403, detail="Access denied")

        return {
            "status": "success",
            "booking_id": booking.booking_id,
            "provider": booking.provider,
            "category": booking.category.value,
            "pickup": booking.pickup_address,
            "drop": booking.drop_address,
            "estimated_fare": booking.estimated_fare,
            "final_fare": booking.final_fare,
            "currency": booking.currency,
            "booking_status": booking.status.value,
            "otp": booking.otp,
            "driver": {
                "name": booking.driver_name,
                "phone": booking.driver_phone,
                "rating": booking.driver_rating,
                "vehicle_number": booking.vehicle_number,
                "vehicle_model": booking.vehicle_model
            },
            "created_at": booking.created_at.isoformat()
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get booking error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/bookings/{booking_id}")
@limiter.limit("10/minute")
async def cancel_booking(
    request: Request,
    booking_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Cancel a cab booking — ownership enforced"""
    try:
        from app.cab_booking_service import cab_booking_service
        booking = cab_booking_service.bookings.get(booking_id)
        if not booking:
            raise HTTPException(status_code=404, detail="Booking not found")

        user_id = str(current_user.get("user_id", current_user.get("_id", "")))
        if booking.user_id != user_id and current_user.get("role") != "admin":
            raise HTTPException(status_code=403, detail="Access denied")

        result = await cab_booking_service.cancel_booking(booking_id)

        from app.travel_notification_service import travel_notification_service
        user_name = (
            current_user.get("name") or
            (current_user.get("email", "").split("@")[0].replace(".", " ").title()) or
            "Valued Guest"
        )
        await travel_notification_service.notify_cancellation(
            name=user_name,
            email=current_user.get("email"),
            phone=current_user.get("phone"),
            service_type="cab",
            booking_id=booking_id,
            refund_amount=result.get("refund_amount"),
            refund_note=result.get("message")
        )

        return {"status": "success", **result}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Cancel booking error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
