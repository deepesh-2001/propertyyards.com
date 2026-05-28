"""
Ticket Booking Service
Book flight tickets via external APIs (Amadeus, Skyscanner, etc.)
"""
import asyncio
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
import aiohttp
import json
import uuid

logger = logging.getLogger(__name__)


class TicketStatus(Enum):
    """Ticket booking status"""
    PENDING = "pending"
    RESERVED = "reserved"  # Held but not paid
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"
    EXPIRED = "expired"


class PaymentStatus(Enum):
    """Payment status"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    REFUNDED = "refunded"


@dataclass
class Passenger:
    """Passenger details"""
    first_name: str
    last_name: str
    email: str
    phone: str
    date_of_birth: Optional[str] = None
    passport_number: Optional[str] = None
    nationality: Optional[str] = None
    gender: Optional[str] = None  # M/F/O


@dataclass
class FlightSegment:
    """Flight segment for booking"""
    airline: str
    flight_number: str
    departure_airport: str
    arrival_airport: str
    departure_time: datetime
    arrival_time: datetime
    aircraft_type: Optional[str] = None
    cabin_class: str = "economy"


@dataclass
class TicketBooking:
    """Ticket booking record"""
    booking_id: str
    user_id: str
    pnr: str  # Passenger Name Record
    status: TicketStatus
    payment_status: PaymentStatus
    
    # Flight details
    segments: List[FlightSegment]
    passengers: List[Passenger]
    
    # Pricing
    base_fare: float
    taxes: float
    total_amount: float
    currency: str = "INR"
    
    # Provider info
    provider: str  # amadeus, skyscanner, etc.
    provider_booking_id: Optional[str] = None
    
    # Timestamps
    created_at: datetime = None
    expires_at: Optional[datetime] = None  # Reservation expiry
    confirmed_at: Optional[datetime] = None
    
    # E-ticket
    eticket_number: Optional[str] = None
    eticket_url: Optional[str] = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.utcnow()
        if self.expires_at is None and self.status == TicketStatus.RESERVED:
            # Hold reservation for 20 minutes
            self.expires_at = self.created_at + timedelta(minutes=20)


class TicketBookingService:
    """Service for booking tickets via external APIs"""

    def __init__(self):
        self.enabled = True
        self.providers = {
            "amadeus": {
                "api_key": None,
                "api_secret": None,
                "base_url": "https://api.amadeus.com/v2",
                "enabled": False
            },
            "skyscanner": {
                "api_key": None,
                "base_url": "https://partners.api.skyscanner.net/apiservices",
                "enabled": False
            },
            "cleartrip": {
                "api_key": None,
                "base_url": "https://api.cleartrip.com",
                "enabled": False
            },
            "make_my_trip": {
                "api_key": None,
                "base_url": "https://api.makemytrip.com",
                "enabled": False
            }
        }
        self.bookings: Dict[str, TicketBooking] = {}
        self.payment_gateway = None

    async def initialize(self, provider_keys: Optional[Dict[str, str]] = None):
        """Initialize with API keys"""
        if provider_keys:
            for provider, key in provider_keys.items():
                if provider in self.providers:
                    self.providers[provider]["api_key"] = key
                    self.providers[provider]["enabled"] = True
        
        logger.info("Ticket Booking Service initialized")
        active_providers = [p for p, c in self.providers.items() if c["enabled"]]
        logger.info(f"Active providers: {active_providers if active_providers else 'None (mock mode)'}")

    async def search_bookable_flights(
        self,
        origin: str,
        destination: str,
        departure_date: datetime,
        passengers: int = 1,
        cabin_class: str = "economy"
    ) -> List[Dict[str, Any]]:
        """Search flights that can be booked"""
        try:
            results = []
            
            # Search all enabled providers
            for provider_name, config in self.providers.items():
                if config["enabled"]:
                    provider_results = await self._search_provider(
                        provider_name, origin, destination, 
                        departure_date, passengers, cabin_class
                    )
                    results.extend(provider_results)
            
            # If no APIs configured, return mock data
            if not results:
                results = self._generate_mock_bookable_flights(
                    origin, destination, departure_date, passengers, cabin_class
                )
            
            # Sort by price
            results.sort(key=lambda x: x["price"])
            return results
            
        except Exception as e:
            logger.error(f"Flight search error: {e}")
            return self._generate_mock_bookable_flights(
                origin, destination, departure_date, passengers, cabin_class
            )

    async def _search_provider(
        self,
        provider: str,
        origin: str,
        destination: str,
        departure_date: datetime,
        passengers: int,
        cabin_class: str
    ) -> List[Dict]:
        """Search specific provider"""
        try:
            if provider == "amadeus":
                return await self._search_amadeus(origin, destination, departure_date, passengers, cabin_class)
            elif provider == "skyscanner":
                return await self._search_skyscanner_bookable(origin, destination, departure_date, passengers, cabin_class)
            return []
        except Exception as e:
            logger.error(f"Provider {provider} search failed: {e}")
            return []

    async def _search_amadeus(
        self,
        origin: str,
        destination: str,
        departure_date: datetime,
        passengers: int,
        cabin_class: str
    ) -> List[Dict]:
        """Search Amadeus API for bookable flights"""
        config = self.providers["amadeus"]
        if not config["api_key"]:
            return []
        
        try:
            async with aiohttp.ClientSession() as session:
                # Get access token
                auth_url = "https://api.amadeus.com/v1/security/oauth2/token"
                auth_data = {
                    "grant_type": "client_credentials",
                    "client_id": config["api_key"],
                    "client_secret": config["api_secret"]
                }
                
                async with session.post(auth_url, data=auth_data) as auth_response:
                    if auth_response.status != 200:
                        return []
                    auth_json = await auth_response.json()
                    access_token = auth_json.get("access_token")
                
                # Search flights
                search_url = "https://api.amadeus.com/v2/shopping/flight-offers"
                headers = {"Authorization": f"Bearer {access_token}"}
                params = {
                    "originLocationCode": origin,
                    "destinationLocationCode": destination,
                    "departureDate": departure_date.strftime("%Y-%m-%d"),
                    "adults": passengers,
                    "travelClass": cabin_class.upper(),
                    "max": 10
                }
                
                async with session.get(search_url, headers=headers, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        return self._parse_amadeus_offers(data)
                    return []
                    
        except Exception as e:
            logger.error(f"Amadeus search error: {e}")
            return []

    def _parse_amadeus_offers(self, data: Dict) -> List[Dict]:
        """Parse Amadeus flight offers"""
        offers = []
        for offer in data.get("data", []):
            offer_data = {
                "id": offer.get("id"),
                "provider": "amadeus",
                "price": float(offer.get("price", {}).get("total", 0)),
                "currency": offer.get("price", {}).get("currency", "INR"),
                "seats_available": offer.get("numberOfBookableSeats", 0),
                "segments": []
            }
            
            for itinerary in offer.get("itineraries", []):
                for segment in itinerary.get("segments", []):
                    offer_data["segments"].append({
                        "flight_number": segment.get("number"),
                        "airline": segment.get("carrierCode"),
                        "departure": segment.get("departure", {}),
                        "arrival": segment.get("arrival", {})
                    })
            
            offers.append(offer_data)
        return offers

    async def _search_skyscanner_bookable(
        self,
        origin: str,
        destination: str,
        departure_date: datetime,
        passengers: int,
        cabin_class: str
    ) -> List[Dict]:
        """Search Skyscanner for bookable flights"""
        # Placeholder for Skyscanner booking API
        return []

    def _generate_mock_bookable_flights(
        self,
        origin: str,
        destination: str,
        departure_date: datetime,
        passengers: int,
        cabin_class: str
    ) -> List[Dict]:
        """Generate mock bookable flights"""
        airlines = ["IndiGo", "Air India", "Vistara"]
        base_price = 3500 if cabin_class == "economy" else 8000
        
        results = []
        for i, airline in enumerate(airlines):
            flight_number = f"{airline[:2].upper()}{100 + i}"
            duration = 150 + (i * 15)
            
            results.append({
                "id": f"mock_{airline}_{i}",
                "provider": "mock",
                "airline": airline,
                "flight_number": flight_number,
                "origin": origin,
                "destination": destination,
                "departure_time": (departure_date + timedelta(hours=8+i)).isoformat(),
                "arrival_time": (departure_date + timedelta(hours=8+i, minutes=duration)).isoformat(),
                "duration_minutes": duration,
                "cabin_class": cabin_class,
                "price": base_price + (i * 200),
                "currency": "INR",
                "seats_available": 25 - i * 5,
                "refundable": i == 0,
                "baggage_included": i < 2,
                "bookable": True
            })
        
        return results

    async def hold_reservation(
        self,
        user_id: str,
        flight_id: str,
        provider: str,
        passengers: List[Passenger],
        contact_email: str,
        contact_phone: str
    ) -> TicketBooking:
        """Hold flight reservation (without payment)"""
        try:
            booking_id = str(uuid.uuid4())
            pnr = self._generate_pnr()
            
            # Calculate pricing
            base_fare = 3500 * len(passengers)
            taxes = base_fare * 0.12
            
            # Create segments
            segments = [
                FlightSegment(
                    airline="IndiGo",
                    flight_number="6E123",
                    departure_airport="DEL",
                    arrival_airport="BOM",
                    departure_time=datetime.utcnow() + timedelta(days=1),
                    arrival_time=datetime.utcnow() + timedelta(days=1, hours=2),
                    cabin_class="economy"
                )
            ]
            
            booking = TicketBooking(
                booking_id=booking_id,
                user_id=user_id,
                pnr=pnr,
                status=TicketStatus.RESERVED,
                payment_status=PaymentStatus.PENDING,
                segments=segments,
                passengers=passengers,
                base_fare=base_fare,
                taxes=taxes,
                total_amount=base_fare + taxes,
                provider=provider,
                provider_booking_id=None
            )
            
            # Store booking
            self.bookings[booking_id] = booking
            
            logger.info(f"Reservation held: {booking_id}, PNR: {pnr}")
            return booking
            
        except Exception as e:
            logger.error(f"Hold reservation failed: {e}")
            raise

    async def confirm_booking(
        self,
        booking_id: str,
        payment_details: Dict[str, Any]
    ) -> TicketBooking:
        """Confirm booking after payment"""
        try:
            booking = self.bookings.get(booking_id)
            if not booking:
                raise ValueError("Booking not found")
            
            if booking.status != TicketStatus.RESERVED:
                raise ValueError("Booking not in reserved state")
            
            if booking.expires_at and datetime.utcnow() > booking.expires_at:
                booking.status = TicketStatus.EXPIRED
                raise ValueError("Reservation expired")
            
            # Process payment
            payment_success = await self._process_payment(booking, payment_details)
            
            if not payment_success:
                booking.payment_status = PaymentStatus.FAILED
                raise ValueError("Payment failed")
            
            # Confirm with provider
            provider_confirmed = await self._confirm_with_provider(booking)
            
            if provider_confirmed:
                booking.status = TicketStatus.CONFIRMED
                booking.payment_status = PaymentStatus.COMPLETED
                booking.confirmed_at = datetime.utcnow()
                booking.eticket_number = self._generate_eticket_number()
                
                logger.info(f"Booking confirmed: {booking_id}")
            else:
                # Refund payment
                await self._refund_payment(booking)
                raise ValueError("Provider confirmation failed")
            
            return booking
            
        except Exception as e:
            logger.error(f"Confirm booking failed: {e}")
            raise

    async def _process_payment(
        self,
        booking: TicketBooking,
        payment_details: Dict
    ) -> bool:
        """Process payment"""
        try:
            # Integrate with payment gateway (Razorpay, Stripe, etc.)
            payment_method = payment_details.get("method", "card")
            
            if payment_method == "cash":
                # For cash payments, mark as completed immediately
                # (Payment collected at counter)
                return True
            
            # For online payments, integrate with gateway
            # This is a mock implementation
            logger.info(f"Processing payment of ₹{booking.total_amount}")
            return True
            
        except Exception as e:
            logger.error(f"Payment processing failed: {e}")
            return False

    async def _confirm_with_provider(self, booking: TicketBooking) -> bool:
        """Confirm booking with external provider"""
        try:
            if booking.provider == "amadeus" and self.providers["amadeus"]["enabled"]:
                # Call Amadeus booking API
                return await self._confirm_amadeus(booking)
            
            # Mock confirmation for testing
            logger.info(f"Mock confirmation for {booking.provider}")
            return True
            
        except Exception as e:
            logger.error(f"Provider confirmation failed: {e}")
            return False

    async def _confirm_amadeus(self, booking: TicketBooking) -> bool:
        """Confirm booking via Amadeus"""
        # Placeholder for Amadeus booking API
        return True

    async def _refund_payment(self, booking: TicketBooking):
        """Refund payment"""
        try:
            booking.payment_status = PaymentStatus.REFUNDED
            logger.info(f"Refunded payment for booking {booking.booking_id}")
        except Exception as e:
            logger.error(f"Refund failed: {e}")

    async def cancel_booking(
        self,
        booking_id: str,
        reason: Optional[str] = None
    ) -> bool:
        """Cancel booking and process refund if applicable"""
        try:
            booking = self.bookings.get(booking_id)
            if not booking:
                return False
            
            if booking.status == TicketStatus.CANCELLED:
                return True
            
            # Check cancellation policy
            hours_before_departure = (booking.segments[0].departure_time - datetime.utcnow()).total_seconds() / 3600
            
            if hours_before_departure < 2:
                raise ValueError("Cannot cancel within 2 hours of departure")
            
            # Cancel with provider
            if booking.provider != "mock":
                await self._cancel_with_provider(booking)
            
            # Process refund
            if booking.payment_status == PaymentStatus.COMPLETED:
                if hours_before_departure > 24:
                    # Full refund
                    await self._refund_payment(booking)
                else:
                    # Partial refund (deduct cancellation fee)
                    booking.total_amount *= 0.7  # 30% cancellation fee
                    await self._refund_payment(booking)
            
            booking.status = TicketStatus.CANCELLED
            logger.info(f"Booking cancelled: {booking_id}")
            return True
            
        except Exception as e:
            logger.error(f"Cancel booking failed: {e}")
            return False

    async def _cancel_with_provider(self, booking: TicketBooking):
        """Cancel with external provider"""
        logger.info(f"Cancelling with provider {booking.provider}")

    async def get_booking(self, booking_id: str) -> Optional[TicketBooking]:
        """Get booking details"""
        return self.bookings.get(booking_id)

    async def get_user_bookings(self, user_id: str) -> List[TicketBooking]:
        """Get all bookings for user"""
        return [b for b in self.bookings.values() if b.user_id == user_id]

    async def generate_eticket(self, booking_id: str) -> Dict[str, Any]:
        """Generate e-ticket"""
        booking = self.bookings.get(booking_id)
        if not booking:
            raise ValueError("Booking not found")
        
        if booking.status != TicketStatus.CONFIRMED:
            raise ValueError("Booking not confirmed")
        
        eticket = {
            "eticket_number": booking.eticket_number,
            "pnr": booking.pnr,
            "booking_id": booking.booking_id,
            "passengers": [
                {
                    "name": f"{p.first_name} {p.last_name}",
                    "email": p.email
                }
                for p in booking.passengers
            ],
            "flight_details": [
                {
                    "airline": s.airline,
                    "flight_number": s.flight_number,
                    "departure": {
                        "airport": s.departure_airport,
                        "time": s.departure_time.isoformat()
                    },
                    "arrival": {
                        "airport": s.arrival_airport,
                        "time": s.arrival_time.isoformat()
                    },
                    "cabin_class": s.cabin_class
                }
                for s in booking.segments
            ],
            "total_amount": booking.total_amount,
            "currency": booking.currency,
            "issued_at": datetime.utcnow().isoformat()
        }
        
        return eticket

    def _generate_pnr(self) -> str:
        """Generate 6-character PNR"""
        import random
        import string
        return ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))

    def _generate_eticket_number(self) -> str:
        """Generate e-ticket number"""
        import random
        return f"{random.randint(100, 999)}-{random.randint(1000000000, 9999999999)}"

    async def check_booking_status(self, pnr: str) -> Optional[Dict]:
        """Check booking status by PNR"""
        for booking in self.bookings.values():
            if booking.pnr == pnr:
                return {
                    "pnr": booking.pnr,
                    "status": booking.status.value,
                    "flight_number": booking.segments[0].flight_number if booking.segments else None,
                    "departure_time": booking.segments[0].departure_time.isoformat() if booking.segments else None,
                    "passengers": len(booking.passengers)
                }
        return None


# Global instance
ticket_booking = TicketBookingService()
