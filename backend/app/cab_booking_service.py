"""
Cab Booking Service
Integrates with Ola, Uber, and Rapido APIs for cab bookings
"""
import asyncio
import logging
import uuid
from typing import Dict, List, Optional, Any
from datetime import datetime
from dataclasses import dataclass, field
from enum import Enum
import aiohttp
import json

logger = logging.getLogger(__name__)


class CabCategory(Enum):
    MINI = "mini"
    SEDAN = "sedan"
    SUV = "suv"
    AUTO = "auto"
    BIKE = "bike"
    PRIME = "prime"


class CabStatus(Enum):
    SEARCHING = "searching"
    DRIVER_ASSIGNED = "driver_assigned"
    ARRIVED = "arrived"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


@dataclass
class CabOffer:
    id: str
    provider: str
    category: CabCategory
    display_name: str
    base_fare: float
    per_km_rate: float
    per_min_rate: float
    surge_multiplier: float
    estimated_fare: float
    currency: str
    estimated_duration_minutes: int
    estimated_distance_km: float
    available: bool = True
    provider_logo: Optional[str] = None
    features: List[str] = field(default_factory=list)
    cancellation_policy: str = "Free cancellation within 5 minutes"


@dataclass
class CabBooking:
    booking_id: str
    user_id: str
    provider: str
    category: CabCategory
    pickup_lat: float
    pickup_lng: float
    pickup_address: str
    drop_lat: float
    drop_lng: float
    drop_address: str
    estimated_fare: float
    final_fare: Optional[float]
    currency: str
    status: CabStatus
    driver_name: Optional[str] = None
    driver_phone: Optional[str] = None
    driver_rating: Optional[float] = None
    vehicle_number: Optional[str] = None
    vehicle_model: Optional[str] = None
    otp: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    provider_booking_id: Optional[str] = None


class CabBookingService:
    """Cab booking via Ola, Uber, Rapido APIs"""

    def __init__(self):
        self.providers = {
            "ola": {
                "api_key": None,
                "base_url": "https://devapi.olacabs.com",
                "enabled": False,
                "headers": {"X-APP-TOKEN": None}
            },
            "uber": {
                "api_key": None,
                "server_token": None,
                "base_url": "https://api.uber.com/v1.2",
                "enabled": False
            },
            "rapido": {
                "api_key": None,
                "base_url": "https://api.rapido.bike/v1",
                "enabled": False
            }
        }
        self.bookings: Dict[str, CabBooking] = {}

    async def initialize(
        self,
        ola_api_key: Optional[str] = None,
        uber_server_token: Optional[str] = None,
        rapido_api_key: Optional[str] = None
    ):
        if ola_api_key:
            self.providers["ola"]["api_key"] = ola_api_key
            self.providers["ola"]["headers"]["X-APP-TOKEN"] = ola_api_key
            self.providers["ola"]["enabled"] = True

        if uber_server_token:
            self.providers["uber"]["server_token"] = uber_server_token
            self.providers["uber"]["enabled"] = True

        if rapido_api_key:
            self.providers["rapido"]["api_key"] = rapido_api_key
            self.providers["rapido"]["enabled"] = True

        active = [p for p, c in self.providers.items() if c["enabled"]]
        logger.info(f"Cab Booking Service initialized. Active: {active or ['mock mode']}")

    async def get_estimates(
        self,
        pickup_lat: float,
        pickup_lng: float,
        drop_lat: float,
        drop_lng: float
    ) -> List[CabOffer]:
        """Get fare estimates from all providers"""
        tasks = []
        for provider, config in self.providers.items():
            if config["enabled"]:
                tasks.append(self._get_provider_estimates(
                    provider, pickup_lat, pickup_lng, drop_lat, drop_lng
                ))

        if not tasks:
            return self._mock_estimates(pickup_lat, pickup_lng, drop_lat, drop_lng)

        results = await asyncio.gather(*tasks, return_exceptions=True)
        offers = []
        for r in results:
            if isinstance(r, list):
                offers.extend(r)

        return sorted(offers, key=lambda x: x.estimated_fare) if offers else \
            self._mock_estimates(pickup_lat, pickup_lng, drop_lat, drop_lng)

    async def _get_provider_estimates(
        self,
        provider: str,
        pickup_lat: float,
        pickup_lng: float,
        drop_lat: float,
        drop_lng: float
    ) -> List[CabOffer]:
        try:
            if provider == "ola":
                return await self._ola_estimates(pickup_lat, pickup_lng, drop_lat, drop_lng)
            elif provider == "uber":
                return await self._uber_estimates(pickup_lat, pickup_lng, drop_lat, drop_lng)
            elif provider == "rapido":
                return await self._rapido_estimates(pickup_lat, pickup_lng, drop_lat, drop_lng)
            return []
        except Exception as e:
            logger.error(f"{provider} estimates error: {e}")
            return []

    async def _ola_estimates(self, pickup_lat, pickup_lng, drop_lat, drop_lng) -> List[CabOffer]:
        """Ola Cabs fare estimate API"""
        config = self.providers["ola"]
        try:
            async with aiohttp.ClientSession(headers=config["headers"]) as session:
                url = f"{config['base_url']}/v1/products"
                params = {
                    "pickup_lat": pickup_lat,
                    "pickup_lng": pickup_lng,
                    "drop_lat": drop_lat,
                    "drop_lng": drop_lng
                }
                async with session.get(url, params=params) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        return self._parse_ola_response(data)
                    logger.warning(f"Ola API status: {resp.status}")
                    return []
        except Exception as e:
            logger.error(f"Ola API error: {e}")
            return []

    def _parse_ola_response(self, data: Dict) -> List[CabOffer]:
        offers = []
        for cat in data.get("categories", []):
            offers.append(CabOffer(
                id=f"ola_{cat.get('id', uuid.uuid4().hex[:8])}",
                provider="Ola",
                category=self._map_ola_category(cat.get("id", "")),
                display_name=cat.get("display_name", "Ola Cab"),
                base_fare=cat.get("fare_breakup", {}).get("base_fare", 50),
                per_km_rate=cat.get("fare_breakup", {}).get("per_km", 12),
                per_min_rate=cat.get("fare_breakup", {}).get("per_minute", 1),
                surge_multiplier=cat.get("surge_multiplier", 1.0),
                estimated_fare=cat.get("estimate", 0),
                currency="INR",
                estimated_duration_minutes=cat.get("duration", 30),
                estimated_distance_km=cat.get("distance", 5),
                features=["GPS Tracked", "Insured Ride"]
            ))
        return offers

    def _map_ola_category(self, cat_id: str) -> CabCategory:
        mapping = {
            "mini": CabCategory.MINI,
            "sedan": CabCategory.SEDAN,
            "prime_sedan": CabCategory.PRIME,
            "prime_suv": CabCategory.SUV,
            "auto": CabCategory.AUTO,
            "bike": CabCategory.BIKE
        }
        return mapping.get(cat_id.lower(), CabCategory.MINI)

    async def _uber_estimates(self, pickup_lat, pickup_lng, drop_lat, drop_lng) -> List[CabOffer]:
        """Uber Price Estimates API"""
        config = self.providers["uber"]
        try:
            async with aiohttp.ClientSession() as session:
                url = f"{config['base_url']}/estimates/price"
                headers = {"Authorization": f"Token {config['server_token']}"}
                params = {
                    "start_latitude": pickup_lat,
                    "start_longitude": pickup_lng,
                    "end_latitude": drop_lat,
                    "end_longitude": drop_lng
                }
                async with session.get(url, headers=headers, params=params) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        return self._parse_uber_response(data)
                    return []
        except Exception as e:
            logger.error(f"Uber API error: {e}")
            return []

    def _parse_uber_response(self, data: Dict) -> List[CabOffer]:
        offers = []
        for price in data.get("prices", []):
            offers.append(CabOffer(
                id=f"uber_{price.get('product_id', uuid.uuid4().hex[:8])}",
                provider="Uber",
                category=self._map_uber_category(price.get("display_name", "")),
                display_name=price.get("display_name", "Uber"),
                base_fare=price.get("low_estimate", 0),
                per_km_rate=12,
                per_min_rate=1,
                surge_multiplier=price.get("surge_multiplier", 1.0),
                estimated_fare=price.get("high_estimate", price.get("low_estimate", 0)),
                currency=price.get("currency_code", "INR"),
                estimated_duration_minutes=price.get("duration", 30) // 60,
                estimated_distance_km=price.get("distance", 5),
                features=["GPS Tracked", "24/7 Support", "In-app payment"]
            ))
        return offers

    def _map_uber_category(self, name: str) -> CabCategory:
        name = name.lower()
        if "xl" in name or "suv" in name:
            return CabCategory.SUV
        if "premium" in name or "black" in name:
            return CabCategory.PRIME
        if "auto" in name:
            return CabCategory.AUTO
        if "moto" in name or "bike" in name:
            return CabCategory.BIKE
        return CabCategory.SEDAN

    async def _rapido_estimates(self, pickup_lat, pickup_lng, drop_lat, drop_lng) -> List[CabOffer]:
        """Rapido fare estimate — bike taxis"""
        config = self.providers["rapido"]
        try:
            async with aiohttp.ClientSession() as session:
                url = f"{config['base_url']}/estimate"
                headers = {"Authorization": f"Bearer {config['api_key']}"}
                payload = {
                    "pickup": {"lat": pickup_lat, "lng": pickup_lng},
                    "drop": {"lat": drop_lat, "lng": drop_lng}
                }
                async with session.post(url, json=payload, headers=headers) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        return self._parse_rapido_response(data)
                    return []
        except Exception as e:
            logger.error(f"Rapido API error: {e}")
            return []

    def _parse_rapido_response(self, data: Dict) -> List[CabOffer]:
        estimate = data.get("estimate", {})
        return [CabOffer(
            id=f"rapido_{uuid.uuid4().hex[:8]}",
            provider="Rapido",
            category=CabCategory.BIKE,
            display_name="Rapido Bike",
            base_fare=estimate.get("base_fare", 20),
            per_km_rate=estimate.get("per_km", 5),
            per_min_rate=0.5,
            surge_multiplier=estimate.get("surge", 1.0),
            estimated_fare=estimate.get("total_fare", 60),
            currency="INR",
            estimated_duration_minutes=estimate.get("duration_mins", 20),
            estimated_distance_km=estimate.get("distance_km", 4),
            features=["Fastest", "Budget Friendly", "Helmet Provided"]
        )]

    async def book_cab(
        self,
        user_id: str,
        offer_id: str,
        pickup_lat: float,
        pickup_lng: float,
        pickup_address: str,
        drop_lat: float,
        drop_lng: float,
        drop_address: str,
        estimated_fare: float,
        provider: str,
        category: str
    ) -> CabBooking:
        """Book a cab"""
        booking_id = str(uuid.uuid4())
        booking = CabBooking(
            booking_id=booking_id,
            user_id=user_id,
            provider=provider,
            category=CabCategory(category),
            pickup_lat=pickup_lat,
            pickup_lng=pickup_lng,
            pickup_address=pickup_address,
            drop_lat=drop_lat,
            drop_lng=drop_lng,
            drop_address=drop_address,
            estimated_fare=estimated_fare,
            final_fare=None,
            currency="INR",
            status=CabStatus.SEARCHING,
            otp=str(uuid.uuid4().int)[:4]
        )
        self.bookings[booking_id] = booking
        logger.info(f"Cab booked: {booking_id} via {provider}")
        return booking

    async def cancel_booking(self, booking_id: str) -> Dict:
        booking = self.bookings.get(booking_id)
        if not booking:
            return {"success": False, "message": "Booking not found"}
        booking.status = CabStatus.CANCELLED
        return {"success": True, "refund_applicable": True}

    def _mock_estimates(
        self,
        pickup_lat: float,
        pickup_lng: float,
        drop_lat: float,
        drop_lng: float
    ) -> List[CabOffer]:
        import math
        dist = math.sqrt((drop_lat - pickup_lat) ** 2 + (drop_lng - pickup_lng) ** 2) * 111
        dist = max(2, dist)
        mock_data = [
            ("Ola Mini", CabCategory.MINI, "Ola", 50, 10, 0.8, dist * 10 + 50),
            ("Ola Sedan", CabCategory.SEDAN, "Ola", 70, 14, 1.0, dist * 14 + 70),
            ("Uber Go", CabCategory.MINI, "Uber", 55, 11, 0.9, dist * 11 + 55),
            ("Uber Premier", CabCategory.SEDAN, "Uber", 80, 16, 1.2, dist * 16 + 80),
            ("Ola SUV", CabCategory.SUV, "Ola", 100, 18, 1.5, dist * 18 + 100),
            ("Rapido Bike", CabCategory.BIKE, "Rapido", 20, 5, 0.4, dist * 5 + 20),
            ("Uber Auto", CabCategory.AUTO, "Uber", 30, 7, 0.6, dist * 7 + 30),
        ]
        offers = []
        for name, cat, prov, base, per_km, per_min, fare in mock_data:
            offers.append(CabOffer(
                id=f"{prov.lower()}_{cat.value}_{uuid.uuid4().hex[:6]}",
                provider=prov,
                category=cat,
                display_name=name,
                base_fare=base,
                per_km_rate=per_km,
                per_min_rate=per_min,
                surge_multiplier=1.0,
                estimated_fare=round(fare, 2),
                currency="INR",
                estimated_duration_minutes=int(dist * 3),
                estimated_distance_km=round(dist, 2),
                features=["GPS Tracked", "Insured Ride"]
            ))
        return sorted(offers, key=lambda x: x.estimated_fare)


cab_booking_service = CabBookingService()
