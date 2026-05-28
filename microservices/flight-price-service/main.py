"""
Flight Price Microservice
Standalone service for flight price comparison
"""
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime, date
import asyncio
import logging
import os

from flight_service import FlightComparisonService, TripType, CabinClass

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Flight Price Service",
    description="Microservice for flight price comparison across airlines",
    version="1.0.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize flight service
flight_service = FlightComparisonService()


@app.on_event("startup")
async def startup():
    """Initialize service on startup"""
    skyscanner_key = os.getenv("SKYSCANNER_API_KEY")
    await flight_service.initialize(skyscanner_key)
    logger.info("Flight Price Service started")


@app.on_event("shutdown")
async def shutdown():
    """Cleanup on shutdown"""
    logger.info("Flight Price Service stopped")


# ========== API Models ==========

class FlightSearchRequest(BaseModel):
    origin: str  # IATA code
    destination: str
    departure_date: date
    return_date: Optional[date] = None
    passengers: int = 1
    cabin_class: str = "economy"
    trip_type: str = "one_way"


class FlightSegmentResponse(BaseModel):
    airline: str
    flight_number: str
    departure_airport: str
    arrival_airport: str
    departure_time: datetime
    arrival_time: datetime
    duration_minutes: int
    stops: int


class FlightOfferResponse(BaseModel):
    id: str
    provider: str
    price: float
    currency: str
    cabin_class: str
    trip_type: str
    outbound_segments: List[FlightSegmentResponse]
    baggage_included: bool
    refundable: bool
    booking_url: Optional[str]


# ========== API Endpoints ==========

@app.get("/")
async def root():
    """Service info"""
    return {
        "service": "Flight Price Service",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs"
    }


@app.get("/health")
async def health():
    """Health check"""
    return {
        "status": "healthy",
        "service": "flight-price-service",
        "timestamp": datetime.utcnow().isoformat()
    }


@app.post("/search", response_model=dict)
async def search_flights(request: FlightSearchRequest):
    """Search and compare flight prices"""
    try:
        from flight_service import FlightSearchRequest as FCRequest

        fc_request = FCRequest(
            origin=request.origin.upper(),
            destination=request.destination.upper(),
            departure_date=datetime.combine(request.departure_date, datetime.min.time()),
            return_date=datetime.combine(request.return_date, datetime.min.time()) if request.return_date else None,
            passengers=request.passengers,
            cabin_class=CabinClass(request.cabin_class),
            trip_type=TripType(request.trip_type)
        )

        results = await flight_service.search_flights(fc_request)

        return {
            "search_params": {
                "origin": request.origin,
                "destination": request.destination,
                "departure_date": request.departure_date.isoformat(),
                "passengers": request.passengers,
                "cabin_class": request.cabin_class
            },
            "total_results": len(results),
            "results": [
                {
                    "id": r.id,
                    "provider": r.provider,
                    "price": r.price,
                    "currency": r.currency,
                    "cabin_class": r.cabin_class.value,
                    "outbound_segments": [
                        {
                            "airline": s.airline,
                            "flight_number": s.flight_number,
                            "departure_airport": s.departure_airport,
                            "arrival_airport": s.arrival_airport,
                            "departure_time": s.departure_time.isoformat(),
                            "arrival_time": s.arrival_time.isoformat(),
                            "duration_minutes": s.duration_minutes,
                            "stops": s.stops
                        }
                        for s in r.outbound_segments
                    ],
                    "baggage_included": r.baggage_included,
                    "refundable": r.refundable,
                    "booking_url": r.booking_url
                }
                for r in results[:20]
            ]
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Flight search error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/cheapest")
async def get_cheapest_flight(
    origin: str,
    destination: str,
    departure_date: date,
    passengers: int = 1,
    cabin_class: str = "economy"
):
    """Get cheapest flight for route"""
    try:
        from flight_service import FlightSearchRequest, TripType, CabinClass

        request = FlightSearchRequest(
            origin=origin.upper(),
            destination=destination.upper(),
            departure_date=datetime.combine(departure_date, datetime.min.time()),
            passengers=passengers,
            cabin_class=CabinClass(cabin_class),
            trip_type=TripType.ONE_WAY
        )

        results = await flight_service.search_flights(request)
        cheapest = flight_service.get_cheapest_offer(results)

        if not cheapest:
            raise HTTPException(status_code=404, detail="No flights found")

        return {
            "cheapest_flight": {
                "id": cheapest.id,
                "provider": cheapest.provider,
                "price": cheapest.price,
                "currency": cheapest.currency,
                "departure_time": cheapest.outbound_segments[0].departure_time.isoformat() if cheapest.outbound_segments else None,
                "duration_minutes": sum(s.duration_minutes for s in cheapest.outbound_segments),
                "booking_url": cheapest.booking_url
            },
            "alternatives_count": len(results) - 1
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/airports")
async def get_airports(country: Optional[str] = "IN"):
    """Get list of airports"""
    airports = [
        {"code": "DEL", "name": "Indira Gandhi International", "city": "New Delhi", "country": "IN"},
        {"code": "BOM", "name": "Chhatrapati Shivaji Maharaj", "city": "Mumbai", "country": "IN"},
        {"code": "BLR", "name": "Kempegowda International", "city": "Bangalore", "country": "IN"},
        {"code": "MAA", "name": "Chennai International", "city": "Chennai", "country": "IN"},
        {"code": "HYD", "name": "Rajiv Gandhi International", "city": "Hyderabad", "country": "IN"},
        {"code": "CCU", "name": "Netaji Subhas Chandra Bose", "city": "Kolkata", "country": "IN"},
        {"code": "AMD", "name": "Sardar Vallabhbhai Patel", "city": "Ahmedabad", "country": "IN"},
        {"code": "PNQ", "name": "Pune Airport", "city": "Pune", "country": "IN"},
        {"code": "JAI", "name": "Jaipur International", "city": "Jaipur", "country": "IN"},
        {"code": "COK", "name": "Cochin International", "city": "Kochi", "country": "IN"},
        {"code": "GOI", "name": "Goa International", "city": "Goa", "country": "IN"},
        {"code": "LKO", "name": "Chaudhary Charan Singh", "city": "Lucknow", "country": "IN"},
    ]

    if country and country != "IN":
        airports = [a for a in airports if a["country"] == country]

    return {"airports": airports, "total": len(airports)}


@app.get("/airlines")
async def get_airlines():
    """Get list of supported airlines"""
    airlines = [
        {"code": "AI", "name": "Air India", "logo_url": "https://logo.clearbit.com/airindia.com"},
        {"code": "6E", "name": "IndiGo", "logo_url": "https://logo.clearbit.com/goindigo.in"},
        {"code": "UK", "name": "Vistara", "logo_url": "https://logo.clearbit.com/airvistara.com"},
        {"code": "SG", "name": "SpiceJet", "logo_url": "https://logo.clearbit.com/spicejet.com"},
        {"code": "G8", "name": "GoAir", "logo_url": "https://logo.clearbit.com/goair.in"},
        {"code": "9W", "name": "Jet Airways", "logo_url": None},
    ]

    return {"airlines": airlines}


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8001))
    uvicorn.run(app, host="0.0.0.0", port=port)
