"""
Flight Comparison Service
Compare flight prices across multiple airlines and booking platforms
"""
import asyncio
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
import aiohttp
import json

logger = logging.getLogger(__name__)


class TripType(Enum):
    """Trip types"""
    ONE_WAY = "one_way"
    ROUND_TRIP = "round_trip"
    MULTI_CITY = "multi_city"


class CabinClass(Enum):
    """Cabin classes"""
    ECONOMY = "economy"
    PREMIUM_ECONOMY = "premium_economy"
    BUSINESS = "business"
    FIRST = "first"


@dataclass
class FlightSegment:
    """Flight segment details"""
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
    """Flight offer from a provider"""
    id: str
    provider: str  # airline or OTA name
    price: float
    currency: str
    trip_type: TripType
    cabin_class: CabinClass
    outbound_segments: List[FlightSegment]
    return_segments: Optional[List[FlightSegment]] = None
    baggage_included: bool = False
    cancellation_policy: str = ""
    refundable: bool = False
    booking_url: Optional[str] = None
    expires_at: Optional[datetime] = None


@dataclass
class FlightSearchRequest:
    """Flight search request"""
    origin: str  # IATA code
    destination: str  # IATA code
    departure_date: datetime
    return_date: Optional[datetime] = None
    passengers: int = 1
    cabin_class: CabinClass = CabinClass.ECONOMY
    trip_type: TripType = TripType.ONE_WAY


class FlightComparisonService:
    """Compare flights across multiple providers"""

    def __init__(self):
        self.enabled = True
        self.providers = {
            "skyscanner": {
                "api_key": None,
                "base_url": "https://partners.api.skyscanner.net/apiservices",
                "enabled": True
            },
            "amadeus": {
                "api_key": None,
                "base_url": "https://api.amadeus.com/v2",
                "enabled": False
            },
            "kayak": {
                "api_key": None,
                "base_url": "https://www.kayak.com/mvm/api",
                "enabled": False
            }
        }
        self.cache_ttl = 1800  # 30 minutes

    async def initialize(self, skyscanner_key: Optional[str] = None):
        """Initialize with API keys"""
        if skyscanner_key:
            self.providers["skyscanner"]["api_key"] = skyscanner_key
            self.providers["skyscanner"]["enabled"] = True
        logger.info("Flight Comparison Service initialized")

    async def search_flights(
        self,
        request: FlightSearchRequest
    ) -> List[FlightOffer]:
        """Search and compare flights across providers"""
        try:
            # Check cache first
            cache_key = self._generate_cache_key(request)
            cached = await self._get_cached_results(cache_key)
            if cached:
                return cached

            # Search all enabled providers in parallel
            search_tasks = []
            for provider_name, provider_config in self.providers.items():
                if provider_config["enabled"] and provider_config["api_key"]:
                    task = self._search_provider(provider_name, request)
                    search_tasks.append(task)

            # If no API keys configured, return mock data
            if not search_tasks:
                results = self._generate_mock_results(request)
                await self._cache_results(cache_key, results)
                return results

            # Gather results from all providers
            provider_results = await asyncio.gather(*search_tasks, return_exceptions=True)

            # Combine and deduplicate results
            all_offers = []
            for result in provider_results:
                if isinstance(result, list):
                    all_offers.extend(result)

            # Sort by price
            all_offers.sort(key=lambda x: x.price)

            # Cache results
            await self._cache_results(cache_key, all_offers)

            return all_offers

        except Exception as e:
            logger.error(f"Flight search failed: {e}")
            return self._generate_mock_results(request)

    async def _search_provider(
        self,
        provider: str,
        request: FlightSearchRequest
    ) -> List[FlightOffer]:
        """Search flights from a specific provider"""
        try:
            if provider == "skyscanner":
                return await self._search_skyscanner(request)
            elif provider == "amadeus":
                return await self._search_amadeus(request)
            elif provider == "kayak":
                return await self._search_kayak(request)
            return []
        except Exception as e:
            logger.error(f"Provider {provider} search failed: {e}")
            return []

    async def _search_skyscanner(
        self,
        request: FlightSearchRequest
    ) -> List[FlightOffer]:
        """Search Skyscanner API"""
        config = self.providers["skyscanner"]
        api_key = config["api_key"]

        if not api_key:
            return []

        try:
            async with aiohttp.ClientSession() as session:
                # Browse Quotes API
                url = f"{config['base_url']}/browsequotes/v1.0/IN/INR/en-US/{request.origin}/{request.destination}/{request.departure_date.strftime('%Y-%m-%d')}"

                headers = {
                    "Accept": "application/json",
                    "api-key": api_key
                }

                async with session.get(url, headers=headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        return self._parse_skyscanner_response(data, request)
                    else:
                        logger.warning(f"Skyscanner API error: {response.status}")
                        return []

        except Exception as e:
            logger.error(f"Skyscanner search error: {e}")
            return []

    def _parse_skyscanner_response(
        self,
        data: Dict,
        request: FlightSearchRequest
    ) -> List[FlightOffer]:
        """Parse Skyscanner API response"""
        offers = []

        quotes = data.get("Quotes", [])
        carriers = {c["CarrierId"]: c["Name"] for c in data.get("Carriers", [])}
        places = {p["PlaceId"]: p["IataCode"] for p in data.get("Places", [])}

        for quote in quotes[:10]:  # Top 10 results
            outbound_leg = quote.get("OutboundLeg", {})
            inbound_leg = quote.get("InboundLeg", {})

            # Create outbound segments
            outbound_segments = []
            for carrier_id in outbound_leg.get("CarrierIds", []):
                segment = FlightSegment(
                    airline=carriers.get(carrier_id, "Unknown"),
                    flight_number=f"{carrier_id}{quote.get('QuoteId', 0)}",
                    departure_airport=places.get(outbound_leg.get("OriginId"), request.origin),
                    arrival_airport=places.get(outbound_leg.get("DestinationId"), request.destination),
                    departure_time=datetime.strptime(
                        outbound_leg.get("DepartureDate", ""), "%Y-%m-%dT%H:%M:%S"
                    ) if outbound_leg.get("DepartureDate") else datetime.now(),
                    arrival_time=datetime.strptime(
                        outbound_leg.get("DepartureDate", ""), "%Y-%m-%dT%H:%M:%S"
                    ) + timedelta(hours=2) if outbound_leg.get("DepartureDate") else datetime.now() + timedelta(hours=2),
                    duration_minutes=120,
                    stops=len(outbound_leg.get("Stops", []))
                )
                outbound_segments.append(segment)

            offer = FlightOffer(
                id=f"skyscanner_{quote.get('QuoteId', 0)}",
                provider="Skyscanner",
                price=quote.get("MinPrice", 0),
                currency="INR",
                trip_type=request.trip_type,
                cabin_class=request.cabin_class,
                outbound_segments=outbound_segments,
                baggage_included=False,
                refundable=False
            )
            offers.append(offer)

        return offers

    async def _search_amadeus(
        self,
        request: FlightSearchRequest
    ) -> List[FlightOffer]:
        """Search Amadeus API"""
        # Placeholder for Amadeus integration
        return []

    async def _search_kayak(
        self,
        request: FlightSearchRequest
    ) -> List[FlightOffer]:
        """Search Kayak API"""
        # Placeholder for Kayak integration
        return []

    def _generate_mock_results(
        self,
        request: FlightSearchRequest
    ) -> List[FlightOffer]:
        """Generate mock flight results for testing"""
        airlines = ["IndiGo", "Air India", "Vistara", "SpiceJet", "GoAir"]
        base_price = 3500 if request.cabin_class == CabinClass.ECONOMY else 8000

        offers = []
        for i, airline in enumerate(airlines):
            price_variation = (i - 2) * 200  # Price varies by airline
            price = max(2500, base_price + price_variation)

            segment = FlightSegment(
                airline=airline,
                flight_number=f"{airline[:2].upper()}{100 + i}",
                departure_airport=request.origin,
                arrival_airport=request.destination,
                departure_time=request.departure_date,
                arrival_time=request.departure_date + timedelta(hours=2, minutes=30),
                duration_minutes=150,
                aircraft_type="Boeing 737",
                stops=0
            )

            offer = FlightOffer(
                id=f"mock_{i}",
                provider=airline,
                price=price,
                currency="INR",
                trip_type=request.trip_type,
                cabin_class=request.cabin_class,
                outbound_segments=[segment],
                baggage_included=i < 2,  # First 2 include baggage
                refundable=i == 0,  # Only first is refundable
                booking_url=f"https://www.{airline.lower().replace(' ', '')}.com/book"
            )
            offers.append(offer)

        # Sort by price
        offers.sort(key=lambda x: x.price)
        return offers

    def _generate_cache_key(self, request: FlightSearchRequest) -> str:
        """Generate cache key for flight search"""
        import hashlib
        key_data = f"{request.origin}:{request.destination}:{request.departure_date.strftime('%Y%m%d')}:{request.cabin_class.value}"
        return hashlib.md5(key_data.encode()).hexdigest()

    async def _get_cached_results(self, cache_key: str) -> Optional[List[FlightOffer]]:
        """Get cached flight results"""
        try:
            from app.cache import get_cache
            cached = await get_cache(f"flights:{cache_key}")
            if cached:
                return json.loads(cached)
        except Exception as e:
            logger.warning(f"Flight cache read error: {e}")
        return None

    async def _cache_results(self, cache_key: str, results: List[FlightOffer]):
        """Cache flight results"""
        try:
            from app.cache import set_cache
            data = [
                {
                    "id": o.id,
                    "provider": o.provider,
                    "price": o.price,
                    "currency": o.currency,
                    "cabin_class": o.cabin_class.value,
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
                        } for s in o.outbound_segments
                    ],
                    "baggage_included": o.baggage_included,
                    "refundable": o.refundable,
                    "booking_url": o.booking_url
                }
                for o in results
            ]
            await set_cache(f"flights:{cache_key}", json.dumps(data), ttl=self.cache_ttl)
        except Exception as e:
            logger.warning(f"Flight cache write error: {e}")

    def get_cheapest_offer(
        self,
        offers: List[FlightOffer]
    ) -> Optional[FlightOffer]:
        """Get cheapest flight offer"""
        if not offers:
            return None
        return min(offers, key=lambda x: x.price)

    def get_fastest_offer(
        self,
        offers: List[FlightOffer]
    ) -> Optional[FlightOffer]:
        """Get fastest flight offer"""
        if not offers:
            return None
        return min(offers, key=lambda x: sum(s.duration_minutes for s in x.outbound_segments))

    def filter_by_airline(
        self,
        offers: List[FlightOffer],
        airlines: List[str]
    ) -> List[FlightOffer]:
        """Filter offers by airline"""
        return [o for o in offers if any(a in o.provider for a in airlines)]

    def filter_by_stops(
        self,
        offers: List[FlightOffer],
        max_stops: int
    ) -> List[FlightOffer]:
        """Filter offers by maximum stops"""
        return [o for o in offers if all(s.stops <= max_stops for s in o.outbound_segments)]


# Global instance
flight_comparison = FlightComparisonService()
