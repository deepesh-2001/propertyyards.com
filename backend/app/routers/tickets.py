"""
Tickets Router
API endpoints for flight ticket search and booking
"""
from fastapi import APIRouter, Depends, HTTPException
from typing import Optional, List
from pydantic import BaseModel
from datetime import datetime

from app.database import get_db
from app.auth import get_current_user

router = APIRouter(prefix="/api/tickets", tags=["tickets"])


# ========== Request Models ==========

class FlightSearchRequest(BaseModel):
    origin: str
    destination: str
    departure_date: str
    return_date: Optional[str] = None
    passengers: int = 1
    cabin_class: str = "economy"
    trip_type: str = "one_way"


class BookingRequest(BaseModel):
    offer_id: str
    passengers: List[dict]
    contact_email: str
    contact_phone: str


# ========== Endpoints ==========

@router.post("/search")
async def search_flights(
    request: FlightSearchRequest,
    current_user: dict = Depends(get_current_user)
):
    """Search and compare flights across providers"""
    try:
        from app.flight_comparison_service import flight_comparison_service
        from app.flight_comparison_service import FlightSearchRequest as ServiceRequest, CabinClass, TripType

        cabin_map = {
            "economy": CabinClass.ECONOMY,
            "premium_economy": CabinClass.PREMIUM_ECONOMY,
            "business": CabinClass.BUSINESS,
            "first": CabinClass.FIRST
        }
        trip_map = {
            "one_way": TripType.ONE_WAY,
            "round_trip": TripType.ROUND_TRIP,
            "multi_city": TripType.MULTI_CITY
        }

        search = ServiceRequest(
            origin=request.origin.upper(),
            destination=request.destination.upper(),
            departure_date=datetime.strptime(request.departure_date, "%Y-%m-%d"),
            return_date=datetime.strptime(request.return_date, "%Y-%m-%d") if request.return_date else None,
            passengers=request.passengers,
            cabin_class=cabin_map.get(request.cabin_class, CabinClass.ECONOMY),
            trip_type=trip_map.get(request.trip_type, TripType.ONE_WAY)
        )

        results = await flight_comparison_service.search_flights(search)

        return {
            "status": "success",
            "count": len(results),
            "flights": [
                {
                    "id": o.id,
                    "provider": o.provider,
                    "price": o.price,
                    "currency": o.currency,
                    "cabin_class": o.cabin_class.value,
                    "baggage_included": o.baggage_included,
                    "refundable": o.refundable,
                    "booking_url": o.booking_url,
                    "segments": [
                        {
                            "airline": s.airline,
                            "flight_number": s.flight_number,
                            "from": s.departure_airport,
                            "to": s.arrival_airport,
                            "departure": s.departure_time.isoformat(),
                            "arrival": s.arrival_time.isoformat(),
                            "duration_minutes": s.duration_minutes,
                            "stops": s.stops
                        }
                        for s in o.outbound_segments
                    ]
                }
                for o in results
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/bookings")
async def get_bookings(current_user: dict = Depends(get_current_user)):
    """Get current user's ticket bookings"""
    try:
        from app.ticket_booking_service import ticket_booking
        bookings = [
            b for b in ticket_booking.bookings.values()
            if b.contact_email == current_user.get("email")
        ]
        return {"status": "success", "count": len(bookings), "bookings": []}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/bookings/{booking_id}")
async def get_booking(
    booking_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get a specific booking by ID"""
    try:
        from app.ticket_booking_service import ticket_booking
        booking = ticket_booking.bookings.get(booking_id)
        if not booking:
            raise HTTPException(status_code=404, detail="Booking not found")
        return {"status": "success", "booking": booking}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/bookings/{booking_id}")
async def cancel_booking(
    booking_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Cancel a ticket booking"""
    try:
        from app.ticket_booking_service import ticket_booking
        result = await ticket_booking.cancel_booking(booking_id)
        return {"status": "success", "message": "Booking cancelled", "refund": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
