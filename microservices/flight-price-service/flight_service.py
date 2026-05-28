"""
Flight Service Module
Core flight comparison logic for the microservice
"""
import asyncio
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
import aiohttp
import json
import random

logger = logging.getLogger(__name__)


class TripType(Enum):
    ONE_WAY = "one_way"
    ROUND_TRIP = "round_trip"


class CabinClass(Enum):
    ECONOMY = "economy"
    PREMIUM_ECONOMY = "premium_economy"
    BUSINESS = "business"
    FIRST = "first"


@dataclass
class FlightSegment:
    airline: str
    flight_number: str
    departure_airport: str
    arrival_airport: str
    departure_time: datetime
    arrival_time: datetime
    duration_minutes: int
    aircraft_type: Optional[str] = None
    stops: int = 0


@dataclass
class FlightOffer:
    id: str
    provider: str
    price: float
    currency: str
    trip_type: TripType
    cabin_class: CabinClass
    outbound_segments: List[FlightSegment]
    return_segments: Optional[List[FlightSegment]] = None
    baggage_included: bool = False
    refundable: bool = False
    booking_url: Optional[str] = None


@dataclass
class FlightSearchRequest:
    origin: str
    destination: str
    departure_date: datetime
    return_date: Optional[datetime] = None
    passengers: int = 1
    cabin_class: CabinClass = CabinClass.ECONOMY
    trip_type: TripType = TripType.ONE_WAY


class FlightComparisonService:
    """Flight comparison service"""

    def __init__(self):
        self.api_key = None
        self.cache = {}  # Simple in-memory cache
        self.cache_ttl = 1800  # 30 minutes

    async def initialize(self, api_key: Optional[str] = None):
        """Initialize with API key"""
        self.api_key = api_key
        if api_key:
            logger.info("Flight service initialized with API key")
        else:
            logger.info("Flight service initialized (mock mode)")

    async def search_flights(self, request: FlightSearchRequest) -> List[FlightOffer]:
        """Search flights"""
        try:
            # Check cache
            cache_key = self._generate_cache_key(request)
            if cache_key in self.cache:
                cached_data, timestamp = self.cache[cache_key]
                if datetime.utcnow().timestamp() - timestamp < self.cache_ttl:
                    return cached_data

            # If API key available, use real API
            if self.api_key:
                results = await self._search_skyscanner(request)
            else:
                results = self._generate_mock_results(request)

            # Cache results
            self.cache[cache_key] = (results, datetime.utcnow().timestamp())

            return results

        except Exception as e:
            logger.error(f"Flight search error: {e}")
            return self._generate_mock_results(request)

    def _generate_cache_key(self, request: FlightSearchRequest) -> str:
        """Generate cache key"""
        return f"{request.origin}:{request.destination}:{request.departure_date.strftime('%Y%m%d')}:{request.cabin_class.value}"

    async def _search_skyscanner(self, request: FlightSearchRequest) -> List[FlightOffer]:
        """Search Skyscanner API"""
        # Placeholder for actual API integration
        return self._generate_mock_results(request)

    def _generate_mock_results(self, request: FlightSearchRequest) -> List[FlightOffer]:
        """Generate mock flight data"""
        airlines = [
            ("IndiGo", "6E", 1.0),
            ("Air India", "AI", 1.2),
            ("Vistara", "UK", 1.3),
            ("SpiceJet", "SG", 0.9),
            ("GoAir", "G8", 0.85)
        ]

        # Base price calculation
        distance_multiplier = 1.5  # Approximate distance factor
        base_price = 3000 * distance_multiplier

        if request.cabin_class == CabinClass.BUSINESS:
            base_price *= 3
        elif request.cabin_class == CabinClass.FIRST:
            base_price *= 5

        offers = []
        for i, (airline, code, price_factor) in enumerate(airlines):
            price = base_price * price_factor * (1 + random.uniform(-0.1, 0.1))

            flight_number = f"{code}{random.randint(100, 999)}"
            duration = 150 + random.randint(-30, 60)

            segment = FlightSegment(
                airline=airline,
                flight_number=flight_number,
                departure_airport=request.origin,
                arrival_airport=request.destination,
                departure_time=request.departure_date,
                arrival_time=request.departure_date + timedelta(minutes=duration),
                duration_minutes=duration,
                stops=random.randint(0, 1)
            )

            offer = FlightOffer(
                id=f"{code}_{i}_{datetime.utcnow().timestamp()}",
                provider=airline,
                price=round(price, 2),
                currency="INR",
                trip_type=request.trip_type,
                cabin_class=request.cabin_class,
                outbound_segments=[segment],
                baggage_included=i < 2,
                refundable=i == 0,
                booking_url=f"https://www.{airline.lower().replace(' ', '')}.com/book/{flight_number}"
            )
            offers.append(offer)

        offers.sort(key=lambda x: x.price)
        return offers

    def get_cheapest_offer(self, offers: List[FlightOffer]) -> Optional[FlightOffer]:
        """Get cheapest offer"""
        if not offers:
            return None
        return min(offers, key=lambda x: x.price)

    def get_fastest_offer(self, offers: List[FlightOffer]) -> Optional[FlightOffer]:
        """Get fastest offer"""
        if not offers:
            return None
        return min(offers, key=lambda x: sum(s.duration_minutes for s in x.outbound_segments))

    def filter_by_airline(self, offers: List[FlightOffer], airlines: List[str]) -> List[FlightOffer]:
        """Filter by airline"""
        return [o for o in offers if any(a.lower() in o.provider.lower() for a in airlines)]

    def filter_by_stops(self, offers: List[FlightOffer], max_stops: int) -> List[FlightOffer]:
        """Filter by stops"""
        return [o for o in offers if all(s.stops <= max_stops for s in o.outbound_segments)]
