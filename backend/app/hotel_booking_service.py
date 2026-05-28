"""
Hotel Booking Service
Integrates with Booking.com, Agoda, and MakeMyTrip APIs via RapidAPI
"""
import asyncio
import logging
import uuid
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import aiohttp
import json

logger = logging.getLogger(__name__)


class RoomType(Enum):
    STANDARD = "standard"
    DELUXE = "deluxe"
    SUITE = "suite"
    EXECUTIVE = "executive"
    FAMILY = "family"
    TWIN = "twin"


class HotelBookingStatus(Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    CHECKED_IN = "checked_in"
    CHECKED_OUT = "checked_out"
    CANCELLED = "cancelled"
    NO_SHOW = "no_show"


@dataclass
class RoomOffer:
    room_id: str
    room_type: RoomType
    room_name: str
    price_per_night: float
    total_price: float
    currency: str
    max_guests: int
    bed_type: str
    amenities: List[str]
    free_cancellation: bool
    free_cancellation_until: Optional[str]
    breakfast_included: bool
    images: List[str] = field(default_factory=list)


@dataclass
class HotelOffer:
    hotel_id: str
    provider: str
    name: str
    address: str
    city: str
    country: str
    star_rating: float
    review_score: float
    review_count: int
    latitude: float
    longitude: float
    check_in: str
    check_out: str
    nights: int
    rooms: List[RoomOffer]
    amenities: List[str]
    images: List[str] = field(default_factory=list)
    distance_from_center_km: Optional[float] = None
    provider_hotel_id: Optional[str] = None
    booking_url: Optional[str] = None


@dataclass
class HotelBooking:
    booking_id: str
    user_id: str
    confirmation_number: str
    hotel_name: str
    hotel_address: str
    room_type: RoomType
    room_name: str
    check_in: str
    check_out: str
    nights: int
    guests: int
    price_per_night: float
    total_price: float
    taxes: float
    final_price: float
    currency: str
    status: HotelBookingStatus
    provider: str
    guest_name: str
    guest_email: str
    guest_phone: str
    special_requests: Optional[str] = None
    provider_booking_id: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    cancelled_at: Optional[datetime] = None


class HotelBookingService:
    """Hotel search and booking via Booking.com/Agoda/MakeMyTrip APIs"""

    def __init__(self):
        self.providers = {
            "booking_com": {
                "api_key": None,
                "rapidapi_host": "booking-com.p.rapidapi.com",
                "base_url": "https://booking-com.p.rapidapi.com/v1",
                "enabled": False
            },
            "agoda": {
                "api_key": None,
                "rapidapi_host": "agoda-com.p.rapidapi.com",
                "base_url": "https://agoda-com.p.rapidapi.com",
                "enabled": False
            },
            "tripadvisor": {
                "api_key": None,
                "rapidapi_host": "tripadvisor16.p.rapidapi.com",
                "base_url": "https://tripadvisor16.p.rapidapi.com/api/v1/hotels",
                "enabled": False
            }
        }
        self.bookings: Dict[str, HotelBooking] = {}

    async def initialize(
        self,
        booking_com_key: Optional[str] = None,
        agoda_key: Optional[str] = None,
        tripadvisor_key: Optional[str] = None
    ):
        if booking_com_key:
            self.providers["booking_com"]["api_key"] = booking_com_key
            self.providers["booking_com"]["enabled"] = True

        if agoda_key:
            self.providers["agoda"]["api_key"] = agoda_key
            self.providers["agoda"]["enabled"] = True

        if tripadvisor_key:
            self.providers["tripadvisor"]["api_key"] = tripadvisor_key
            self.providers["tripadvisor"]["enabled"] = True

        active = [p for p, c in self.providers.items() if c["enabled"]]
        logger.info(f"Hotel Booking Service initialized. Active: {active or ['mock mode']}")

    async def search_hotels(
        self,
        city: str,
        check_in: str,
        check_out: str,
        adults: int = 2,
        rooms: int = 1,
        min_stars: Optional[int] = None,
        max_price: Optional[float] = None
    ) -> List[HotelOffer]:
        """Search hotels across all providers"""
        nights = self._calc_nights(check_in, check_out)

        tasks = []
        for provider, config in self.providers.items():
            if config["enabled"]:
                tasks.append(self._search_provider(
                    provider, city, check_in, check_out, adults, rooms, nights
                ))

        if not tasks:
            return self._mock_hotels(city, check_in, check_out, nights, adults)

        results = await asyncio.gather(*tasks, return_exceptions=True)
        offers = []
        for r in results:
            if isinstance(r, list):
                offers.extend(r)

        if min_stars:
            offers = [h for h in offers if h.star_rating >= min_stars]
        if max_price:
            offers = [h for h in offers if any(r.total_price <= max_price for r in h.rooms)]

        return sorted(offers, key=lambda h: h.rooms[0].total_price if h.rooms else 0) \
            if offers else self._mock_hotels(city, check_in, check_out, nights, adults)

    async def _search_provider(
        self, provider: str, city: str, check_in: str,
        check_out: str, adults: int, rooms: int, nights: int
    ) -> List[HotelOffer]:
        try:
            if provider == "booking_com":
                return await self._booking_com_search(city, check_in, check_out, adults, rooms, nights)
            elif provider == "tripadvisor":
                return await self._tripadvisor_search(city, check_in, check_out, adults, nights)
            return []
        except Exception as e:
            logger.error(f"{provider} search error: {e}")
            return []

    async def _booking_com_search(
        self, city: str, check_in: str, check_out: str,
        adults: int, rooms: int, nights: int
    ) -> List[HotelOffer]:
        config = self.providers["booking_com"]
        try:
            async with aiohttp.ClientSession() as session:
                # Step 1: Get destination ID
                dest_url = f"{config['base_url']}/hotels/locations"
                headers = {
                    "X-RapidAPI-Key": config["api_key"],
                    "X-RapidAPI-Host": config["rapidapi_host"]
                }
                async with session.get(
                    dest_url, headers=headers,
                    params={"name": city, "locale": "en-gb"}
                ) as resp:
                    if resp.status != 200:
                        return []
                    locations = await resp.json()
                    if not locations:
                        return []
                    dest_id = locations[0].get("dest_id")
                    dest_type = locations[0].get("dest_type", "city")

                # Step 2: Search hotels
                search_url = f"{config['base_url']}/hotels/search"
                params = {
                    "dest_id": dest_id,
                    "dest_type": dest_type,
                    "checkin_date": check_in,
                    "checkout_date": check_out,
                    "adults_number": adults,
                    "room_number": rooms,
                    "units": "metric",
                    "order_by": "popularity",
                    "locale": "en-gb",
                    "currency": "INR",
                    "filter_by_currency": "INR",
                    "page_number": 0
                }
                async with session.get(search_url, headers=headers, params=params) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        return self._parse_booking_com(data, check_in, check_out, nights)
                    return []
        except Exception as e:
            logger.error(f"Booking.com error: {e}")
            return []

    def _parse_booking_com(
        self, data: Dict, check_in: str, check_out: str, nights: int
    ) -> List[HotelOffer]:
        offers = []
        for hotel in data.get("result", [])[:15]:
            price_night = hotel.get("min_total_price", 0) / max(nights, 1)
            room = RoomOffer(
                room_id=f"bc_{hotel.get('hotel_id')}",
                room_type=RoomType.STANDARD,
                room_name="Standard Room",
                price_per_night=round(price_night, 2),
                total_price=hotel.get("min_total_price", 0),
                currency="INR",
                max_guests=2,
                bed_type="Double",
                amenities=["Free WiFi", "AC"],
                free_cancellation=hotel.get("is_free_cancellable", False),
                free_cancellation_until=None,
                breakfast_included=hotel.get("has_free_breakfast", False)
            )
            offers.append(HotelOffer(
                hotel_id=str(hotel.get("hotel_id", "")),
                provider="Booking.com",
                name=hotel.get("hotel_name", ""),
                address=hotel.get("address", ""),
                city=hotel.get("city", ""),
                country=hotel.get("country_trans", "India"),
                star_rating=float(hotel.get("class", 3)),
                review_score=float(hotel.get("review_score", 7.5)),
                review_count=hotel.get("review_nr", 0),
                latitude=float(hotel.get("latitude", 0)),
                longitude=float(hotel.get("longitude", 0)),
                check_in=check_in,
                check_out=check_out,
                nights=nights,
                rooms=[room],
                amenities=hotel.get("hotel_facilities_filtered", []),
                images=[hotel.get("main_photo_url", "")],
                distance_from_center_km=float(hotel.get("distance", 0)),
                provider_hotel_id=str(hotel.get("hotel_id")),
                booking_url=hotel.get("url")
            ))
        return offers

    async def _tripadvisor_search(
        self, city: str, check_in: str, check_out: str, adults: int, nights: int
    ) -> List[HotelOffer]:
        config = self.providers["tripadvisor"]
        try:
            async with aiohttp.ClientSession() as session:
                url = f"{config['base_url']}/searchHotels"
                headers = {
                    "X-RapidAPI-Key": config["api_key"],
                    "X-RapidAPI-Host": config["rapidapi_host"]
                }
                params = {
                    "geoId": city,
                    "checkIn": check_in,
                    "checkOut": check_out,
                    "adults": adults,
                    "currencyCode": "INR"
                }
                async with session.get(url, headers=headers, params=params) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        return self._parse_tripadvisor(data, check_in, check_out, nights)
                    return []
        except Exception as e:
            logger.error(f"TripAdvisor error: {e}")
            return []

    def _parse_tripadvisor(
        self, data: Dict, check_in: str, check_out: str, nights: int
    ) -> List[HotelOffer]:
        offers = []
        for hotel in data.get("data", {}).get("data", [])[:15]:
            price = hotel.get("priceDetails", {}).get("price", 3000)
            room = RoomOffer(
                room_id=f"ta_{hotel.get('id')}",
                room_type=RoomType.STANDARD,
                room_name="Standard Room",
                price_per_night=price,
                total_price=price * nights,
                currency="INR",
                max_guests=2,
                bed_type="Double",
                amenities=["Free WiFi"],
                free_cancellation=True,
                free_cancellation_until=None,
                breakfast_included=False
            )
            offers.append(HotelOffer(
                hotel_id=str(hotel.get("id", "")),
                provider="TripAdvisor",
                name=hotel.get("title", ""),
                address=hotel.get("secondaryInfo", ""),
                city=city,
                country="India",
                star_rating=float(hotel.get("bubbleRating", {}).get("rating", 3.5)),
                review_score=float(hotel.get("bubbleRating", {}).get("rating", 7.0)),
                review_count=hotel.get("bubbleRating", {}).get("count", 0),
                latitude=0,
                longitude=0,
                check_in=check_in,
                check_out=check_out,
                nights=nights,
                rooms=[room],
                amenities=["Free WiFi", "Restaurant"],
                images=[hotel.get("cardPhotos", [{}])[0].get("sizes", {}).get("urlTemplate", "") if hotel.get("cardPhotos") else ""]
            ))
        return offers

    async def book_hotel(
        self,
        user_id: str,
        hotel_id: str,
        hotel_name: str,
        hotel_address: str,
        room_type: str,
        room_name: str,
        check_in: str,
        check_out: str,
        guests: int,
        price_per_night: float,
        total_price: float,
        provider: str,
        guest_name: str,
        guest_email: str,
        guest_phone: str,
        special_requests: Optional[str] = None
    ) -> HotelBooking:
        nights = self._calc_nights(check_in, check_out)
        taxes = total_price * 0.12
        booking_id = str(uuid.uuid4())
        confirmation = f"HB{str(uuid.uuid4().int)[:8].upper()}"

        booking = HotelBooking(
            booking_id=booking_id,
            user_id=user_id,
            confirmation_number=confirmation,
            hotel_name=hotel_name,
            hotel_address=hotel_address,
            room_type=RoomType(room_type),
            room_name=room_name,
            check_in=check_in,
            check_out=check_out,
            nights=nights,
            guests=guests,
            price_per_night=price_per_night,
            total_price=total_price,
            taxes=taxes,
            final_price=total_price + taxes,
            currency="INR",
            status=HotelBookingStatus.CONFIRMED,
            provider=provider,
            guest_name=guest_name,
            guest_email=guest_email,
            guest_phone=guest_phone,
            special_requests=special_requests
        )
        self.bookings[booking_id] = booking
        logger.info(f"Hotel booked: {booking_id}, Confirmation: {confirmation}")
        return booking

    async def cancel_booking(self, booking_id: str) -> Dict:
        booking = self.bookings.get(booking_id)
        if not booking:
            return {"success": False, "message": "Booking not found"}
        booking.status = HotelBookingStatus.CANCELLED
        booking.cancelled_at = datetime.utcnow()
        refund = booking.total_price * 0.80
        return {"success": True, "refund_amount": round(refund, 2), "currency": "INR"}

    def _calc_nights(self, check_in: str, check_out: str) -> int:
        try:
            ci = datetime.strptime(check_in, "%Y-%m-%d")
            co = datetime.strptime(check_out, "%Y-%m-%d")
            return max(1, (co - ci).days)
        except Exception:
            return 1

    def _mock_hotels(
        self, city: str, check_in: str, check_out: str, nights: int, adults: int
    ) -> List[HotelOffer]:
        hotels_data = [
            ("Taj Hotel & Convention Centre", 4.5, 8.9, 2840, "Luxury", ["Pool", "Spa", "Gym", "Restaurant", "Free WiFi"]),
            ("OYO Townhouse 123", 3.0, 7.2, 1200, "Budget", ["Free WiFi", "AC", "TV"]),
            ("Marriott Executive Apartments", 5.0, 9.1, 6500, "Luxury", ["Pool", "Spa", "Gym", "Concierge", "Free WiFi"]),
            ("ibis Styles Hotel", 3.5, 8.0, 2100, "Business", ["Free WiFi", "Restaurant", "Gym", "Business Center"]),
            ("Lemon Tree Premier", 4.0, 8.4, 3200, "Superior", ["Pool", "Gym", "Restaurant", "Free WiFi", "Bar"]),
            ("FabHotel Prime", 2.5, 6.8, 800, "Economy", ["Free WiFi", "AC"]),
            ("Hyatt Regency", 5.0, 9.3, 8500, "Luxury", ["Pool", "Spa", "Multiple Restaurants", "Free WiFi"]),
        ]
        offers = []
        for i, (name, stars, score, price_night, cat, amenities) in enumerate(hotels_data):
            total = price_night * nights
            room = RoomOffer(
                room_id=f"mock_{i}_std",
                room_type=RoomType.STANDARD if stars < 4 else RoomType.DELUXE,
                room_name=f"{'Deluxe' if stars >= 4 else 'Standard'} Room",
                price_per_night=price_night,
                total_price=total,
                currency="INR",
                max_guests=adults,
                bed_type="King" if stars >= 4 else "Double",
                amenities=amenities[:3],
                free_cancellation=stars >= 3,
                free_cancellation_until=check_in,
                breakfast_included=stars >= 4
            )
            offers.append(HotelOffer(
                hotel_id=f"mock_{i}",
                provider="PropertyYards Travel",
                name=name,
                address=f"Plot {i+1}, Main Road, {city}",
                city=city,
                country="India",
                star_rating=stars,
                review_score=score,
                review_count=100 + i * 50,
                latitude=28.6 + i * 0.01,
                longitude=77.2 + i * 0.01,
                check_in=check_in,
                check_out=check_out,
                nights=nights,
                rooms=[room],
                amenities=amenities,
                distance_from_center_km=round(0.5 + i * 0.8, 1)
            ))
        return sorted(offers, key=lambda h: h.rooms[0].price_per_night)


hotel_booking_service = HotelBookingService()
