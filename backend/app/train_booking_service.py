"""
Train Booking Service
Integrates with RailYatri, IRCTC (via RapidAPI), and ConfirmTkt APIs
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


class TrainClass(Enum):
    SLEEPER = "SL"
    AC3_TIER = "3A"
    AC2_TIER = "2A"
    AC1_TIER = "1A"
    AC_CHAIR_CAR = "CC"
    SECOND_SITTING = "2S"
    GENERAL = "GN"


class BookingStatus(Enum):
    CNF = "Confirmed"
    RAC = "Reservation Against Cancellation"
    WL = "Waitlist"
    CANCELLED = "Cancelled"
    COMPLETED = "Completed"


@dataclass
class TrainSchedule:
    station_code: str
    station_name: str
    arrival: Optional[str]
    departure: Optional[str]
    day: int
    distance_km: int
    platform: Optional[str] = None


@dataclass
class TrainOffer:
    train_number: str
    train_name: str
    origin_code: str
    destination_code: str
    departure_time: str
    arrival_time: str
    duration: str
    travel_date: str
    available_classes: List[Dict]
    days_of_operation: List[str]
    train_type: str
    distance_km: int
    provider: str = "irctc"


@dataclass
class TrainBooking:
    booking_id: str
    user_id: str
    pnr: str
    train_number: str
    train_name: str
    travel_date: str
    from_station: str
    to_station: str
    travel_class: TrainClass
    passengers: List[Dict]
    base_fare: float
    service_charge: float
    total_fare: float
    currency: str
    status: BookingStatus
    provider_booking_id: Optional[str] = None
    seat_numbers: Optional[List[str]] = None
    coach: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    cancelled_at: Optional[datetime] = None


class TrainBookingService:
    """Train search and booking via IRCTC/RailYatri/ConfirmTkt APIs"""

    def __init__(self):
        self.providers = {
            "railyatri": {
                "api_key": None,
                "base_url": "https://www.railyatri.in/api",
                "rapidapi_host": "railyatri.p.rapidapi.com",
                "enabled": False
            },
            "irctc_rapidapi": {
                "api_key": None,
                "base_url": "https://irctc1.p.rapidapi.com",
                "rapidapi_host": "irctc1.p.rapidapi.com",
                "enabled": False
            },
            "confirmtkt": {
                "api_key": None,
                "base_url": "https://confirmtkt.com/api",
                "enabled": False
            }
        }
        self.bookings: Dict[str, TrainBooking] = {}

    async def initialize(
        self,
        railyatri_key: Optional[str] = None,
        irctc_rapidapi_key: Optional[str] = None,
        confirmtkt_key: Optional[str] = None
    ):
        if railyatri_key:
            self.providers["railyatri"]["api_key"] = railyatri_key
            self.providers["railyatri"]["enabled"] = True

        if irctc_rapidapi_key:
            self.providers["irctc_rapidapi"]["api_key"] = irctc_rapidapi_key
            self.providers["irctc_rapidapi"]["enabled"] = True

        if confirmtkt_key:
            self.providers["confirmtkt"]["api_key"] = confirmtkt_key
            self.providers["confirmtkt"]["enabled"] = True

        active = [p for p, c in self.providers.items() if c["enabled"]]
        logger.info(f"Train Booking Service initialized. Active: {active or ['mock mode']}")

    async def search_trains(
        self,
        from_station: str,
        to_station: str,
        travel_date: str,
        travel_class: Optional[str] = None
    ) -> List[TrainOffer]:
        """Search trains between stations"""
        for provider, config in self.providers.items():
            if config["enabled"]:
                try:
                    results = await self._search_provider(
                        provider, from_station, to_station, travel_date
                    )
                    if results:
                        return results
                except Exception as e:
                    logger.error(f"{provider} search error: {e}")

        return self._mock_trains(from_station, to_station, travel_date)

    async def _search_provider(
        self,
        provider: str,
        from_station: str,
        to_station: str,
        travel_date: str
    ) -> List[TrainOffer]:
        if provider == "irctc_rapidapi":
            return await self._irctc_search(from_station, to_station, travel_date)
        elif provider == "railyatri":
            return await self._railyatri_search(from_station, to_station, travel_date)
        return []

    async def _irctc_search(
        self, from_station: str, to_station: str, travel_date: str
    ) -> List[TrainOffer]:
        """IRCTC via RapidAPI"""
        config = self.providers["irctc_rapidapi"]
        try:
            async with aiohttp.ClientSession() as session:
                url = f"{config['base_url']}/api/v3/trainBetweenStations"
                headers = {
                    "X-RapidAPI-Key": config["api_key"],
                    "X-RapidAPI-Host": config["rapidapi_host"]
                }
                params = {
                    "fromStationCode": from_station.upper(),
                    "toStationCode": to_station.upper(),
                    "dateOfJourney": travel_date
                }
                async with session.get(url, headers=headers, params=params) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        return self._parse_irctc_response(data, travel_date)
                    logger.warning(f"IRCTC API status {resp.status}")
                    return []
        except Exception as e:
            logger.error(f"IRCTC API error: {e}")
            return []

    def _parse_irctc_response(self, data: Dict, travel_date: str) -> List[TrainOffer]:
        offers = []
        for train in data.get("data", []):
            classes = []
            for cls in train.get("classType", []):
                classes.append({
                    "class_code": cls,
                    "available_seats": train.get("avlDayList", [{}])[0].get("availablityStatus", "AVAILABLE"),
                    "fare": self._estimate_fare(cls, train.get("distance", 500))
                })
            offers.append(TrainOffer(
                train_number=train.get("trainNumber", ""),
                train_name=train.get("trainName", ""),
                origin_code=train.get("fromStnCode", ""),
                destination_code=train.get("toStnCode", ""),
                departure_time=train.get("departureTime", ""),
                arrival_time=train.get("arrivalTime", ""),
                duration=train.get("duration", ""),
                travel_date=travel_date,
                available_classes=classes,
                days_of_operation=train.get("runningDays", []),
                train_type=train.get("trainType", "EXPRESS"),
                distance_km=train.get("distance", 0),
                provider="IRCTC"
            ))
        return offers

    async def _railyatri_search(
        self, from_station: str, to_station: str, travel_date: str
    ) -> List[TrainOffer]:
        """RailYatri API via RapidAPI"""
        config = self.providers["railyatri"]
        try:
            async with aiohttp.ClientSession() as session:
                url = f"https://{config['rapidapi_host']}/get-trains-between-stations/"
                headers = {
                    "X-RapidAPI-Key": config["api_key"],
                    "X-RapidAPI-Host": config["rapidapi_host"]
                }
                params = {
                    "from_station_code": from_station.upper(),
                    "to_station_code": to_station.upper(),
                    "date": travel_date
                }
                async with session.get(url, headers=headers, params=params) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        return self._parse_railyatri_response(data, travel_date)
                    return []
        except Exception as e:
            logger.error(f"RailYatri API error: {e}")
            return []

    def _parse_railyatri_response(self, data: Dict, travel_date: str) -> List[TrainOffer]:
        offers = []
        for train in data.get("data", {}).get("trainBetweenStation", []):
            offers.append(TrainOffer(
                train_number=train.get("train_number", ""),
                train_name=train.get("train_name", ""),
                origin_code=train.get("from_station_code", ""),
                destination_code=train.get("to_station_code", ""),
                departure_time=train.get("departure_time", ""),
                arrival_time=train.get("arrival_time", ""),
                duration=train.get("duration", ""),
                travel_date=travel_date,
                available_classes=self._build_classes(train),
                days_of_operation=train.get("train_base", {}).get("running_days", []),
                train_type=train.get("train_base", {}).get("train_type", "EXPRESS"),
                distance_km=int(train.get("distance", 0)),
                provider="RailYatri"
            ))
        return offers

    def _build_classes(self, train: Dict) -> List[Dict]:
        classes = []
        for cls_code in ["SL", "3A", "2A", "1A", "CC", "2S"]:
            if train.get(f"has_{cls_code.lower()}", True):
                classes.append({
                    "class_code": cls_code,
                    "available_seats": "AVAILABLE",
                    "fare": self._estimate_fare(cls_code, int(train.get("distance", 500)))
                })
        return classes

    def _estimate_fare(self, cls: str, distance_km: int) -> float:
        base_rates = {
            "SL": 0.45, "3A": 1.20, "2A": 1.80,
            "1A": 3.00, "CC": 0.80, "2S": 0.30, "GN": 0.25
        }
        rate = base_rates.get(cls, 0.45)
        return round(max(60, distance_km * rate + 40), 2)

    async def check_availability(
        self, train_number: str, from_station: str,
        to_station: str, travel_date: str, travel_class: str
    ) -> Dict:
        """Check seat availability"""
        for provider, config in self.providers.items():
            if config["enabled"] and provider == "irctc_rapidapi":
                try:
                    async with aiohttp.ClientSession() as session:
                        url = f"{config['base_url']}/api/v1/checkSeatAvailability"
                        headers = {
                            "X-RapidAPI-Key": config["api_key"],
                            "X-RapidAPI-Host": config["rapidapi_host"]
                        }
                        params = {
                            "classType": travel_class,
                            "fromStationCode": from_station.upper(),
                            "quota": "GN",
                            "toStationCode": to_station.upper(),
                            "trainNumber": train_number,
                            "date": travel_date
                        }
                        async with session.get(url, headers=headers, params=params) as resp:
                            if resp.status == 200:
                                return await resp.json()
                except Exception as e:
                    logger.error(f"Availability check error: {e}")

        return {"available": True, "seats": 42, "status": "AVAILABLE", "source": "mock"}

    async def book_train(
        self,
        user_id: str,
        train_number: str,
        train_name: str,
        travel_date: str,
        from_station: str,
        to_station: str,
        travel_class: str,
        passengers: List[Dict],
        total_fare: float
    ) -> TrainBooking:
        """Create a train booking record"""
        booking_id = str(uuid.uuid4())
        pnr = str(uuid.uuid4().int)[:10]
        booking = TrainBooking(
            booking_id=booking_id,
            user_id=user_id,
            pnr=pnr,
            train_number=train_number,
            train_name=train_name,
            travel_date=travel_date,
            from_station=from_station,
            to_station=to_station,
            travel_class=TrainClass(travel_class),
            passengers=passengers,
            base_fare=total_fare * 0.95,
            service_charge=total_fare * 0.05,
            total_fare=total_fare,
            currency="INR",
            status=BookingStatus.CNF
        )
        self.bookings[booking_id] = booking
        logger.info(f"Train booked: {booking_id}, PNR: {pnr}")
        return booking

    async def cancel_booking(self, booking_id: str) -> Dict:
        booking = self.bookings.get(booking_id)
        if not booking:
            return {"success": False, "message": "Booking not found"}
        booking.status = BookingStatus.CANCELLED
        booking.cancelled_at = datetime.utcnow()
        refund = booking.total_fare * 0.75
        return {"success": True, "refund_amount": refund, "currency": "INR"}

    def _mock_trains(
        self, from_station: str, to_station: str, travel_date: str
    ) -> List[TrainOffer]:
        trains = [
            ("12951", "MUMBAI RAJDHANI", "16:35", "08:15+1", "15h 40m", "Express", 1385),
            ("12301", "HOWRAH RAJDHANI", "17:05", "09:55+1", "16h 50m", "Rajdhani", 1450),
            ("12259", "SEALDAH DURONTO", "20:10", "11:50+1", "15h 40m", "Duronto", 1400),
            ("12019", "SHATABDI EXP", "06:00", "14:30", "8h 30m", "Shatabdi", 700),
            ("19027", "VIVEK EXPRESS", "23:00", "19:30+1", "20h 30m", "Express", 1600),
        ]
        offers = []
        for num, name, dep, arr, dur, typ, dist in trains:
            offers.append(TrainOffer(
                train_number=num,
                train_name=name,
                origin_code=from_station.upper(),
                destination_code=to_station.upper(),
                departure_time=dep,
                arrival_time=arr,
                duration=dur,
                travel_date=travel_date,
                available_classes=[
                    {"class_code": "SL", "available_seats": 120, "fare": self._estimate_fare("SL", dist)},
                    {"class_code": "3A", "available_seats": 64, "fare": self._estimate_fare("3A", dist)},
                    {"class_code": "2A", "available_seats": 46, "fare": self._estimate_fare("2A", dist)},
                    {"class_code": "1A", "available_seats": 18, "fare": self._estimate_fare("1A", dist)},
                ],
                days_of_operation=["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"],
                train_type=typ,
                distance_km=dist,
                provider="Mock"
            ))
        return offers


train_booking_service = TrainBookingService()
