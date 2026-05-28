"""
Trains Router
API endpoints for train search and booking (IRCTC, RailYatri, ConfirmTkt)
Includes: rate limiting, input validation, Redis caching, ownership checks, auto-lead generation
"""
from fastapi import APIRouter, Depends, HTTPException, Request
from typing import Optional, List
from pydantic import BaseModel, validator
import re
import hashlib
import logging

from app.auth import get_current_user
from app.security import limiter

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/trains", tags=["trains"])

VALID_CLASSES = {"SL", "3A", "2A", "1A", "CC", "2S", "GN"}
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
STATION_RE = re.compile(r"^[A-Za-z0-9]{2,7}$")


class TrainSearchRequest(BaseModel):
    from_station: str
    to_station: str
    travel_date: str
    travel_class: Optional[str] = None

    @validator("from_station", "to_station")
    def validate_station(cls, v):
        v = v.strip().upper()
        if not STATION_RE.match(v):
            raise ValueError("Station code must be 2-7 alphanumeric characters")
        return v

    @validator("travel_date")
    def validate_date(cls, v):
        if not DATE_RE.match(v):
            raise ValueError("Date must be YYYY-MM-DD")
        return v

    @validator("travel_class")
    def validate_class(cls, v):
        if v and v.upper() not in VALID_CLASSES:
            raise ValueError(f"Class must be one of: {VALID_CLASSES}")
        return v.upper() if v else v


class PassengerModel(BaseModel):
    name: str
    age: int
    gender: str
    berth_preference: Optional[str] = "no_preference"

    @validator("name")
    def validate_name(cls, v):
        if not v.strip() or len(v.strip()) < 2:
            raise ValueError("Passenger name must be at least 2 characters")
        return v.strip()

    @validator("age")
    def validate_age(cls, v):
        if not (1 <= v <= 120):
            raise ValueError("Age must be between 1 and 120")
        return v

    @validator("gender")
    def validate_gender(cls, v):
        if v.upper() not in {"M", "F", "O"}:
            raise ValueError("Gender must be M, F, or O")
        return v.upper()


class TrainBookRequest(BaseModel):
    train_number: str
    train_name: str
    travel_date: str
    from_station: str
    to_station: str
    travel_class: str
    passengers: List[PassengerModel]
    total_fare: float
    contact_email: str
    contact_phone: str

    @validator("travel_date")
    def validate_date(cls, v):
        if not DATE_RE.match(v):
            raise ValueError("Date must be YYYY-MM-DD")
        return v

    @validator("travel_class")
    def validate_class(cls, v):
        if v.upper() not in VALID_CLASSES:
            raise ValueError(f"Class must be one of: {VALID_CLASSES}")
        return v.upper()

    @validator("total_fare")
    def validate_fare(cls, v):
        if v <= 0 or v > 100000:
            raise ValueError("Fare must be between 1 and 100000")
        return v

    @validator("passengers")
    def validate_passengers(cls, v):
        if not v or len(v) > 6:
            raise ValueError("Passengers must be 1-6")
        return v

    @validator("contact_email")
    def validate_email(cls, v):
        if "@" not in v or "." not in v:
            raise ValueError("Invalid email address")
        return v.lower()


class AvailabilityRequest(BaseModel):
    train_number: str
    from_station: str
    to_station: str
    travel_date: str
    travel_class: str

    @validator("travel_date")
    def validate_date(cls, v):
        if not DATE_RE.match(v):
            raise ValueError("Date must be YYYY-MM-DD")
        return v

    @validator("travel_class")
    def validate_class(cls, v):
        if v.upper() not in VALID_CLASSES:
            raise ValueError(f"Class must be one of: {VALID_CLASSES}")
        return v.upper()


@router.post("/search")
@limiter.limit("30/minute")
async def search_trains(
    request: Request,
    body: TrainSearchRequest,
    current_user: dict = Depends(get_current_user)
):
    """Search trains — rate limited 30/min, Redis cached 15 min"""
    try:
        from app.train_booking_service import train_booking_service
        from app.cache import get_cache, set_cache

        cache_key = "train:search:" + hashlib.md5(
            f"{body.from_station}:{body.to_station}:{body.travel_date}:{body.travel_class or 'all'}".encode()
        ).hexdigest()

        cached = await get_cache(cache_key)
        if cached:
            cached["cached"] = True
            return cached

        trains = await train_booking_service.search_trains(
            from_station=body.from_station,
            to_station=body.to_station,
            travel_date=body.travel_date,
            travel_class=body.travel_class
        )
        result = {
            "status": "success",
            "count": len(trains),
            "cached": False,
            "from_station": body.from_station,
            "to_station": body.to_station,
            "travel_date": body.travel_date,
            "trains": [
                {
                    "train_number": t.train_number,
                    "train_name": t.train_name,
                    "departure_time": t.departure_time,
                    "arrival_time": t.arrival_time,
                    "duration": t.duration,
                    "distance_km": t.distance_km,
                    "train_type": t.train_type,
                    "days_of_operation": t.days_of_operation,
                    "provider": t.provider,
                    "available_classes": t.available_classes
                }
                for t in trains
            ]
        }
        await set_cache(cache_key, result, ttl=900)
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Train search error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/availability")
@limiter.limit("30/minute")
async def check_availability(
    request: Request,
    body: AvailabilityRequest,
    current_user: dict = Depends(get_current_user)
):
    """Check seat availability — Redis cached 5 min"""
    try:
        from app.train_booking_service import train_booking_service
        from app.cache import get_cache, set_cache

        cache_key = "train:avail:" + hashlib.md5(
            f"{body.train_number}:{body.from_station}:{body.to_station}:{body.travel_date}:{body.travel_class}".encode()
        ).hexdigest()

        cached = await get_cache(cache_key)
        if cached:
            return {"status": "success", "cached": True, "availability": cached}

        result = await train_booking_service.check_availability(
            train_number=body.train_number,
            from_station=body.from_station,
            to_station=body.to_station,
            travel_date=body.travel_date,
            travel_class=body.travel_class
        )
        await set_cache(cache_key, result, ttl=300)
        return {"status": "success", "cached": False, "availability": result}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Availability check error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/book")
@limiter.limit("10/minute")
async def book_train(
    request: Request,
    body: TrainBookRequest,
    current_user: dict = Depends(get_current_user)
):
    """Book a train ticket — rate limited 10/min, auto-lead created"""
    try:
        from app.train_booking_service import train_booking_service
        from app.travel_lead_service import travel_lead_service

        user_id = str(current_user.get("user_id", current_user.get("_id", "")))
        passengers = [p.dict() for p in body.passengers]
        booking = await train_booking_service.book_train(
            user_id=user_id,
            train_number=body.train_number,
            train_name=body.train_name,
            travel_date=body.travel_date,
            from_station=body.from_station,
            to_station=body.to_station,
            travel_class=body.travel_class,
            passengers=passengers,
            total_fare=body.total_fare
        )

        await travel_lead_service.create_lead_from_train_booking(
            user_id=user_id,
            user_email=body.contact_email,
            user_phone=body.contact_phone,
            booking_id=booking.booking_id,
            from_station=body.from_station,
            to_station=body.to_station,
            travel_date=body.travel_date,
            train_name=body.train_name,
            total_fare=body.total_fare
        )

        from app.travel_notification_service import travel_notification_service
        user_name = (
            body.passengers[0].name if body.passengers else
            body.contact_email.split("@")[0].replace(".", " ").title()
        )
        await travel_notification_service.notify_train_booking(
            name=user_name,
            email=body.contact_email,
            phone=body.contact_phone,
            booking_id=booking.booking_id,
            pnr=booking.pnr,
            train_name=booking.train_name,
            train_number=booking.train_number,
            from_station=booking.from_station,
            to_station=booking.to_station,
            travel_date=booking.travel_date,
            travel_class=booking.travel_class.value,
            passengers=len(booking.passengers),
            total_fare=booking.total_fare,
            city=booking.to_station
        )

        return {
            "status": "success",
            "booking_id": booking.booking_id,
            "pnr": booking.pnr,
            "train_number": booking.train_number,
            "train_name": booking.train_name,
            "travel_date": booking.travel_date,
            "from_station": booking.from_station,
            "to_station": booking.to_station,
            "travel_class": booking.travel_class.value,
            "passengers": booking.passengers,
            "base_fare": booking.base_fare,
            "service_charge": booking.service_charge,
            "total_fare": booking.total_fare,
            "currency": booking.currency,
            "booking_status": booking.status.value,
            "booked_at": booking.created_at.isoformat()
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Train book error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/bookings")
@limiter.limit("60/minute")
async def get_my_bookings(
    request: Request,
    current_user: dict = Depends(get_current_user)
):
    """Get current user's train bookings"""
    try:
        from app.train_booking_service import train_booking_service
        user_id = str(current_user.get("user_id", current_user.get("_id", "")))
        bookings = [b for b in train_booking_service.bookings.values() if b.user_id == user_id]
        return {
            "status": "success",
            "count": len(bookings),
            "bookings": [
                {
                    "booking_id": b.booking_id,
                    "pnr": b.pnr,
                    "train_number": b.train_number,
                    "train_name": b.train_name,
                    "travel_date": b.travel_date,
                    "from_station": b.from_station,
                    "to_station": b.to_station,
                    "travel_class": b.travel_class.value,
                    "total_fare": b.total_fare,
                    "currency": b.currency,
                    "status": b.status.value,
                    "booked_at": b.created_at.isoformat()
                }
                for b in bookings
            ]
        }
    except Exception as e:
        logger.error(f"Get train bookings error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/bookings/{booking_id}")
@limiter.limit("60/minute")
async def get_booking(
    request: Request,
    booking_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get a specific train booking — ownership enforced"""
    try:
        from app.train_booking_service import train_booking_service
        booking = train_booking_service.bookings.get(booking_id)
        if not booking:
            raise HTTPException(status_code=404, detail="Booking not found")

        user_id = str(current_user.get("user_id", current_user.get("_id", "")))
        if booking.user_id != user_id and current_user.get("role") != "admin":
            raise HTTPException(status_code=403, detail="Access denied")

        return {
            "status": "success",
            "booking_id": booking.booking_id,
            "pnr": booking.pnr,
            "train_number": booking.train_number,
            "train_name": booking.train_name,
            "travel_date": booking.travel_date,
            "from_station": booking.from_station,
            "to_station": booking.to_station,
            "travel_class": booking.travel_class.value,
            "passengers": booking.passengers,
            "total_fare": booking.total_fare,
            "currency": booking.currency,
            "status": booking.status.value,
            "coach": booking.coach,
            "seat_numbers": booking.seat_numbers,
            "booked_at": booking.created_at.isoformat()
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get train booking error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/bookings/{booking_id}")
@limiter.limit("10/minute")
async def cancel_booking(
    request: Request,
    booking_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Cancel a train booking — ownership enforced"""
    try:
        from app.train_booking_service import train_booking_service
        booking = train_booking_service.bookings.get(booking_id)
        if not booking:
            raise HTTPException(status_code=404, detail="Booking not found")

        user_id = str(current_user.get("user_id", current_user.get("_id", "")))
        if booking.user_id != user_id and current_user.get("role") != "admin":
            raise HTTPException(status_code=403, detail="Access denied")

        result = await train_booking_service.cancel_booking(booking_id)

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
            service_type="train",
            booking_id=booking_id,
            refund_amount=result.get("refund_amount"),
            refund_note=result.get("message")
        )

        return {"status": "success", **result}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Cancel train booking error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
