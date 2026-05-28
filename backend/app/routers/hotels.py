"""
Hotels Router
API endpoints for hotel search and booking (Booking.com, Agoda, TripAdvisor)
Includes: rate limiting, input validation, Redis caching, ownership checks, auto-lead generation
"""
from fastapi import APIRouter, Depends, HTTPException, Request
from typing import Optional
from pydantic import BaseModel, validator
import re
import hashlib
import logging

from app.auth import get_current_user
from app.security import limiter

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/hotels", tags=["hotels"])

DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
VALID_ROOM_TYPES = {"standard", "deluxe", "suite", "executive", "family", "twin"}


class HotelSearchRequest(BaseModel):
    city: str
    check_in: str
    check_out: str
    adults: int = 2
    rooms: int = 1
    min_stars: Optional[int] = None
    max_price: Optional[float] = None

    @validator("city")
    def validate_city(cls, v):
        v = v.strip()
        if len(v) < 2 or len(v) > 100:
            raise ValueError("City name must be 2-100 characters")
        return v

    @validator("check_in", "check_out")
    def validate_date(cls, v):
        if not DATE_RE.match(v):
            raise ValueError("Date must be YYYY-MM-DD")
        return v

    @validator("adults")
    def validate_adults(cls, v):
        if not (1 <= v <= 10):
            raise ValueError("Adults must be between 1 and 10")
        return v

    @validator("rooms")
    def validate_rooms(cls, v):
        if not (1 <= v <= 10):
            raise ValueError("Rooms must be between 1 and 10")
        return v

    @validator("min_stars")
    def validate_stars(cls, v):
        if v is not None and v not in {1, 2, 3, 4, 5}:
            raise ValueError("min_stars must be 1-5")
        return v


class HotelBookRequest(BaseModel):
    hotel_id: str
    hotel_name: str
    hotel_address: str
    room_type: str
    room_name: str
    check_in: str
    check_out: str
    guests: int
    price_per_night: float
    total_price: float
    provider: str
    guest_name: str
    guest_email: str
    guest_phone: str
    special_requests: Optional[str] = None

    @validator("room_type")
    def validate_room_type(cls, v):
        if v.lower() not in VALID_ROOM_TYPES:
            raise ValueError(f"room_type must be one of: {VALID_ROOM_TYPES}")
        return v.lower()

    @validator("check_in", "check_out")
    def validate_date(cls, v):
        if not DATE_RE.match(v):
            raise ValueError("Date must be YYYY-MM-DD")
        return v

    @validator("guests")
    def validate_guests(cls, v):
        if not (1 <= v <= 20):
            raise ValueError("Guests must be between 1 and 20")
        return v

    @validator("price_per_night", "total_price")
    def validate_price(cls, v):
        if v <= 0 or v > 1000000:
            raise ValueError("Price must be between 1 and 1000000")
        return v

    @validator("guest_email")
    def validate_email(cls, v):
        if "@" not in v or "." not in v:
            raise ValueError("Invalid email address")
        return v.lower()


@router.post("/search")
@limiter.limit("20/minute")
async def search_hotels(
    request: Request,
    body: HotelSearchRequest,
    current_user: dict = Depends(get_current_user)
):
    """Search hotels — rate limited 20/min, Redis cached 10 min, soft lead on search"""
    try:
        from app.hotel_booking_service import hotel_booking_service
        from app.cache import get_cache, set_cache
        from app.travel_lead_service import travel_lead_service

        cache_key = "hotel:search:" + hashlib.md5(
            f"{body.city}:{body.check_in}:{body.check_out}:{body.adults}:{body.rooms}:{body.min_stars}:{body.max_price}".encode()
        ).hexdigest()

        cached = await get_cache(cache_key)
        if cached:
            cached["cached"] = True
            return cached

        hotels = await hotel_booking_service.search_hotels(
            city=body.city,
            check_in=body.check_in,
            check_out=body.check_out,
            adults=body.adults,
            rooms=body.rooms,
            min_stars=body.min_stars,
            max_price=body.max_price
        )

        def room_dict(r):
            return {
                "room_id": r.room_id,
                "room_type": r.room_type.value,
                "room_name": r.room_name,
                "price_per_night": r.price_per_night,
                "total_price": r.total_price,
                "currency": r.currency,
                "max_guests": r.max_guests,
                "bed_type": r.bed_type,
                "amenities": r.amenities,
                "free_cancellation": r.free_cancellation,
                "free_cancellation_until": r.free_cancellation_until,
                "breakfast_included": r.breakfast_included
            }

        result = {
            "status": "success",
            "count": len(hotels),
            "cached": False,
            "city": body.city,
            "check_in": body.check_in,
            "check_out": body.check_out,
            "hotels": [
                {
                    "hotel_id": h.hotel_id,
                    "provider": h.provider,
                    "name": h.name,
                    "address": h.address,
                    "city": h.city,
                    "star_rating": h.star_rating,
                    "review_score": h.review_score,
                    "review_count": h.review_count,
                    "latitude": h.latitude,
                    "longitude": h.longitude,
                    "nights": h.nights,
                    "amenities": h.amenities,
                    "images": h.images[:3],
                    "distance_from_center_km": h.distance_from_center_km,
                    "booking_url": h.booking_url,
                    "rooms": [room_dict(r) for r in h.rooms]
                }
                for h in hotels
            ]
        }
        await set_cache(cache_key, result, ttl=600)

        user_id = str(current_user.get("user_id", current_user.get("_id", "")))
        await travel_lead_service.create_lead_from_hotel_search(
            user_id=user_id,
            user_email=current_user.get("email"),
            user_phone=current_user.get("phone"),
            city=body.city,
            check_in=body.check_in,
            check_out=body.check_out,
            adults=body.adults
        )

        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Hotel search error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/book")
@limiter.limit("10/minute")
async def book_hotel(
    request: Request,
    body: HotelBookRequest,
    current_user: dict = Depends(get_current_user)
):
    """Book a hotel room — rate limited 10/min, HOT lead auto-created"""
    try:
        from app.hotel_booking_service import hotel_booking_service
        from app.travel_lead_service import travel_lead_service
        from app.hotel_booking_service import hotel_booking_service

        user_id = str(current_user.get("user_id", current_user.get("_id", "")))
        booking = await hotel_booking_service.book_hotel(
            user_id=user_id,
            hotel_id=body.hotel_id,
            hotel_name=body.hotel_name,
            hotel_address=body.hotel_address,
            room_type=body.room_type,
            room_name=body.room_name,
            check_in=body.check_in,
            check_out=body.check_out,
            guests=body.guests,
            price_per_night=body.price_per_night,
            total_price=body.total_price,
            provider=body.provider,
            guest_name=body.guest_name,
            guest_email=body.guest_email,
            guest_phone=body.guest_phone,
            special_requests=body.special_requests
        )

        city = body.hotel_address.split(",")[-1].strip() if "," in body.hotel_address else ""

        await travel_lead_service.create_lead_from_hotel_booking(
            user_id=user_id,
            user_email=body.guest_email,
            user_phone=body.guest_phone,
            booking_id=booking.booking_id,
            hotel_name=body.hotel_name,
            hotel_address=body.hotel_address,
            city=city,
            check_in=body.check_in,
            check_out=body.check_out,
            nights=booking.nights,
            guests=body.guests,
            final_price=booking.final_price,
            guest_name=body.guest_name,
            guest_phone=body.guest_phone
        )

        from app.travel_notification_service import travel_notification_service
        await travel_notification_service.notify_hotel_booking(
            name=body.guest_name,
            email=body.guest_email,
            phone=body.guest_phone,
            booking_id=booking.booking_id,
            confirmation_number=booking.confirmation_number,
            hotel_name=booking.hotel_name,
            hotel_address=booking.hotel_address,
            check_in=booking.check_in,
            check_out=booking.check_out,
            nights=booking.nights,
            guests=booking.guests,
            room_type=booking.room_type.value,
            final_price=booking.final_price,
            provider=booking.provider,
            city=city or None
        )

        return {
            "status": "success",
            "booking_id": booking.booking_id,
            "confirmation_number": booking.confirmation_number,
            "hotel_name": booking.hotel_name,
            "hotel_address": booking.hotel_address,
            "room_type": booking.room_type.value,
            "room_name": booking.room_name,
            "check_in": booking.check_in,
            "check_out": booking.check_out,
            "nights": booking.nights,
            "guests": booking.guests,
            "price_per_night": booking.price_per_night,
            "total_price": booking.total_price,
            "taxes": booking.taxes,
            "final_price": booking.final_price,
            "currency": booking.currency,
            "booking_status": booking.status.value,
            "guest_name": booking.guest_name,
            "guest_email": booking.guest_email,
            "provider": booking.provider,
            "booked_at": booking.created_at.isoformat()
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Hotel book error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/bookings")
@limiter.limit("60/minute")
async def get_my_bookings(
    request: Request,
    current_user: dict = Depends(get_current_user)
):
    """Get current user's hotel bookings"""
    try:
        from app.hotel_booking_service import hotel_booking_service
        user_id = str(current_user.get("user_id", current_user.get("_id", "")))
        bookings = [b for b in hotel_booking_service.bookings.values() if b.user_id == user_id]
        return {
            "status": "success",
            "count": len(bookings),
            "bookings": [
                {
                    "booking_id": b.booking_id,
                    "confirmation_number": b.confirmation_number,
                    "hotel_name": b.hotel_name,
                    "check_in": b.check_in,
                    "check_out": b.check_out,
                    "nights": b.nights,
                    "room_type": b.room_type.value,
                    "final_price": b.final_price,
                    "currency": b.currency,
                    "status": b.status.value,
                    "booked_at": b.created_at.isoformat()
                }
                for b in bookings
            ]
        }
    except Exception as e:
        logger.error(f"Get hotel bookings error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/bookings/{booking_id}")
@limiter.limit("60/minute")
async def get_booking(
    request: Request,
    booking_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get a specific hotel booking — ownership enforced"""
    try:
        from app.hotel_booking_service import hotel_booking_service
        booking = hotel_booking_service.bookings.get(booking_id)
        if not booking:
            raise HTTPException(status_code=404, detail="Booking not found")

        user_id = str(current_user.get("user_id", current_user.get("_id", "")))
        if booking.user_id != user_id and current_user.get("role") != "admin":
            raise HTTPException(status_code=403, detail="Access denied")

        return {
            "status": "success",
            "booking_id": booking.booking_id,
            "confirmation_number": booking.confirmation_number,
            "hotel_name": booking.hotel_name,
            "hotel_address": booking.hotel_address,
            "room_type": booking.room_type.value,
            "room_name": booking.room_name,
            "check_in": booking.check_in,
            "check_out": booking.check_out,
            "nights": booking.nights,
            "guests": booking.guests,
            "price_per_night": booking.price_per_night,
            "total_price": booking.total_price,
            "taxes": booking.taxes,
            "final_price": booking.final_price,
            "currency": booking.currency,
            "status": booking.status.value,
            "guest_name": booking.guest_name,
            "guest_email": booking.guest_email,
            "guest_phone": booking.guest_phone,
            "special_requests": booking.special_requests,
            "provider": booking.provider,
            "booked_at": booking.created_at.isoformat()
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get hotel booking error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/bookings/{booking_id}")
@limiter.limit("10/minute")
async def cancel_booking(
    request: Request,
    booking_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Cancel a hotel booking — ownership enforced"""
    try:
        from app.hotel_booking_service import hotel_booking_service
        booking = hotel_booking_service.bookings.get(booking_id)
        if not booking:
            raise HTTPException(status_code=404, detail="Booking not found")

        user_id = str(current_user.get("user_id", current_user.get("_id", "")))
        if booking.user_id != user_id and current_user.get("role") != "admin":
            raise HTTPException(status_code=403, detail="Access denied")

        result = await hotel_booking_service.cancel_booking(booking_id)

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
            service_type="hotel",
            booking_id=booking_id,
            refund_amount=result.get("refund_amount"),
            refund_note=result.get("message")
        )

        return {"status": "success", **result}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Cancel hotel booking error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
