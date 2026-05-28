"""
Travel Lead Service
Auto-generates CRM leads from user travel activity (cab/train/hotel bookings).
Infers intent: a cab pickup near a property area → property inquiry lead.
"""
import logging
import uuid
from datetime import datetime
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


class LeadSource(Enum):
    CAB_BOOKING = "cab_booking"
    TRAIN_BOOKING = "train_booking"
    HOTEL_BOOKING = "hotel_booking"
    FLIGHT_BOOKING = "flight_booking"
    CAB_ESTIMATE = "cab_estimate"
    HOTEL_SEARCH = "hotel_search"


class LeadPriority(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    HOT = "hot"


class LeadStatus(Enum):
    NEW = "new"
    CONTACTED = "contacted"
    QUALIFIED = "qualified"
    CONVERTED = "converted"
    LOST = "lost"


@dataclass
class TravelLead:
    lead_id: str
    user_id: str
    user_email: Optional[str]
    user_phone: Optional[str]
    source: LeadSource
    priority: LeadPriority
    status: LeadStatus

    # Location context
    pickup_address: Optional[str] = None
    pickup_lat: Optional[float] = None
    pickup_lng: Optional[float] = None
    drop_address: Optional[str] = None
    drop_lat: Optional[float] = None
    drop_lng: Optional[float] = None
    city: Optional[str] = None

    # Travel context
    travel_date: Optional[str] = None
    travel_type: str = "cab"
    booking_value: float = 0.0
    currency: str = "INR"

    # Inferred intent
    intent_tags: List[str] = field(default_factory=list)
    notes: str = ""

    created_at: datetime = field(default_factory=datetime.utcnow)
    booking_reference: Optional[str] = None


# Known property-related area keywords for intent detection
PROPERTY_AREA_KEYWORDS = [
    "sector", "plot", "phase", "colony", "nagar", "vihar", "enclave",
    "apartments", "society", "township", "layout", "extension",
    "housing board", "dlf", "unitech", "godrej", "prestige", "sobha",
    "brigade", "puravankara", "lodha", "oberoi", "hiranandani"
]

HOTEL_INTENT_KEYWORDS = [
    "hotel", "inn", "resort", "suites", "stay", "guest house",
    "service apartment", "oyo", "fab hotel", "lemon tree"
]

AIRPORT_KEYWORDS = [
    "airport", "terminal", "departure", "arrival", "domestic", "international",
    "t1", "t2", "t3", "igi", "csia", "kia", "hia", "cjb"
]


def _detect_intent(
    pickup_address: Optional[str],
    drop_address: Optional[str],
    travel_type: str
) -> tuple[List[str], LeadPriority]:
    """Detect user intent and priority from addresses."""
    tags = []
    text = f"{pickup_address or ''} {drop_address or ''}".lower()

    if any(kw in text for kw in PROPERTY_AREA_KEYWORDS):
        tags.append("property_area_visit")
        tags.append("potential_property_buyer")

    if any(kw in text for kw in AIRPORT_KEYWORDS):
        tags.append("airport_transfer")
        tags.append("out_of_town_visitor")

    if any(kw in text for kw in HOTEL_INTENT_KEYWORDS):
        tags.append("hotel_area")
        tags.append("temporary_resident")

    if travel_type == "hotel_booking":
        tags.append("needs_accommodation")
        tags.append("relocation_potential")

    if travel_type == "train_booking":
        tags.append("intercity_traveller")
        tags.append("destination_city_visitor")

    if travel_type == "flight_booking":
        tags.append("high_value_traveller")
        tags.append("potential_nri_buyer")

    if "property_area_visit" in tags:
        priority = LeadPriority.HOT
    elif "out_of_town_visitor" in tags or "relocation_potential" in tags:
        priority = LeadPriority.HIGH
    elif tags:
        priority = LeadPriority.MEDIUM
    else:
        priority = LeadPriority.LOW

    return tags, priority


class TravelLeadService:
    """Auto-generates and stores leads from travel activity."""

    def __init__(self):
        self.leads: Dict[str, TravelLead] = {}

    async def create_lead_from_cab_estimate(
        self,
        user_id: str,
        user_email: Optional[str],
        user_phone: Optional[str],
        pickup_lat: float,
        pickup_lng: float,
        drop_lat: float,
        drop_lng: float,
        pickup_address: Optional[str] = None,
        drop_address: Optional[str] = None
    ) -> Optional[TravelLead]:
        """Create a soft lead when user requests a cab estimate."""
        try:
            tags, priority = _detect_intent(pickup_address, drop_address, "cab_estimate")
            if priority == LeadPriority.LOW:
                return None

            lead = TravelLead(
                lead_id=str(uuid.uuid4()),
                user_id=user_id,
                user_email=user_email,
                user_phone=user_phone,
                source=LeadSource.CAB_ESTIMATE,
                priority=priority,
                status=LeadStatus.NEW,
                pickup_address=pickup_address,
                pickup_lat=pickup_lat,
                pickup_lng=pickup_lng,
                drop_address=drop_address,
                drop_lat=drop_lat,
                drop_lng=drop_lng,
                travel_type="cab_estimate",
                intent_tags=tags,
                notes=f"User estimated cab fare. Pickup: {pickup_address}, Drop: {drop_address}"
            )
            self.leads[lead.lead_id] = lead
            await self._persist_lead(lead)
            logger.info(f"Auto-lead created from cab estimate: {lead.lead_id} priority={priority.value}")
            return lead
        except Exception as e:
            logger.warning(f"Auto-lead creation failed (cab estimate): {e}")
            return None

    async def create_lead_from_cab_booking(
        self,
        user_id: str,
        user_email: Optional[str],
        user_phone: Optional[str],
        booking_id: str,
        pickup_address: str,
        pickup_lat: float,
        pickup_lng: float,
        drop_address: str,
        drop_lat: float,
        drop_lng: float,
        estimated_fare: float,
        provider: str,
        category: str
    ) -> TravelLead:
        """Create a lead when a cab is booked — higher intent than estimate."""
        tags, priority = _detect_intent(pickup_address, drop_address, "cab_booking")
        tags.append("cab_booked")

        if priority == LeadPriority.LOW:
            priority = LeadPriority.MEDIUM

        lead = TravelLead(
            lead_id=str(uuid.uuid4()),
            user_id=user_id,
            user_email=user_email,
            user_phone=user_phone,
            source=LeadSource.CAB_BOOKING,
            priority=priority,
            status=LeadStatus.NEW,
            pickup_address=pickup_address,
            pickup_lat=pickup_lat,
            pickup_lng=pickup_lng,
            drop_address=drop_address,
            drop_lat=drop_lat,
            drop_lng=drop_lng,
            travel_type="cab_booking",
            booking_value=estimated_fare,
            currency="INR",
            intent_tags=tags,
            notes=f"Cab booked via {provider} ({category}). Fare: ₹{estimated_fare}. "
                  f"Pickup: {pickup_address} → Drop: {drop_address}",
            booking_reference=booking_id
        )
        self.leads[lead.lead_id] = lead
        await self._persist_lead(lead)
        logger.info(f"Auto-lead created from cab booking: {lead.lead_id} priority={priority.value}")
        return lead

    async def create_lead_from_train_booking(
        self,
        user_id: str,
        user_email: Optional[str],
        user_phone: Optional[str],
        booking_id: str,
        from_station: str,
        to_station: str,
        travel_date: str,
        train_name: str,
        total_fare: float
    ) -> TravelLead:
        """Create a lead from train booking — visitor to destination city."""
        tags = [
            "train_booked",
            "intercity_traveller",
            f"destination:{to_station.upper()}",
            "potential_property_inquiry"
        ]
        priority = LeadPriority.HIGH

        lead = TravelLead(
            lead_id=str(uuid.uuid4()),
            user_id=user_id,
            user_email=user_email,
            user_phone=user_phone,
            source=LeadSource.TRAIN_BOOKING,
            priority=priority,
            status=LeadStatus.NEW,
            pickup_address=f"Station: {from_station}",
            drop_address=f"Station: {to_station}",
            city=to_station,
            travel_date=travel_date,
            travel_type="train_booking",
            booking_value=total_fare,
            currency="INR",
            intent_tags=tags,
            notes=f"Train booked: {train_name} from {from_station} → {to_station} on {travel_date}. "
                  f"Fare: ₹{total_fare}. High intent visitor to destination city.",
            booking_reference=booking_id
        )
        self.leads[lead.lead_id] = lead
        await self._persist_lead(lead)
        logger.info(f"Auto-lead created from train booking: {lead.lead_id} city={to_station}")
        return lead

    async def create_lead_from_hotel_search(
        self,
        user_id: str,
        user_email: Optional[str],
        user_phone: Optional[str],
        city: str,
        check_in: str,
        check_out: str,
        adults: int
    ) -> Optional[TravelLead]:
        """Soft lead from hotel search — person looking to stay in a city."""
        try:
            tags = [
                "hotel_search",
                f"destination:{city.upper()}",
                "accommodation_seeker",
                "potential_relocation"
            ]
            priority = LeadPriority.MEDIUM

            lead = TravelLead(
                lead_id=str(uuid.uuid4()),
                user_id=user_id,
                user_email=user_email,
                user_phone=user_phone,
                source=LeadSource.HOTEL_BOOKING,
                priority=priority,
                status=LeadStatus.NEW,
                city=city,
                travel_date=check_in,
                travel_type="hotel_search",
                intent_tags=tags,
                notes=f"User searched hotels in {city} for {check_in} to {check_out} "
                      f"({adults} adults). Potential relocation or long-stay customer."
            )
            self.leads[lead.lead_id] = lead
            await self._persist_lead(lead)
            logger.info(f"Auto-lead created from hotel search: {lead.lead_id} city={city}")
            return lead
        except Exception as e:
            logger.warning(f"Auto-lead creation failed (hotel search): {e}")
            return None

    async def create_lead_from_hotel_booking(
        self,
        user_id: str,
        user_email: Optional[str],
        user_phone: Optional[str],
        booking_id: str,
        hotel_name: str,
        hotel_address: str,
        city: str,
        check_in: str,
        check_out: str,
        nights: int,
        guests: int,
        final_price: float,
        guest_name: str,
        guest_phone: str
    ) -> TravelLead:
        """Create a high-priority lead from hotel booking."""
        tags = [
            "hotel_booked",
            f"destination:{city.upper()}",
            "confirmed_visitor",
            "accommodation_confirmed",
            "potential_property_buyer"
        ]
        if nights >= 7:
            tags.append("long_stay")
            tags.append("relocation_strong_signal")
        if nights >= 30:
            tags.append("temporary_resident")

        priority = LeadPriority.HOT if nights >= 7 else LeadPriority.HIGH

        lead = TravelLead(
            lead_id=str(uuid.uuid4()),
            user_id=user_id,
            user_email=user_email,
            user_phone=guest_phone or user_phone,
            source=LeadSource.HOTEL_BOOKING,
            priority=priority,
            status=LeadStatus.NEW,
            drop_address=hotel_address,
            city=city,
            travel_date=check_in,
            travel_type="hotel_booking",
            booking_value=final_price,
            currency="INR",
            intent_tags=tags,
            notes=f"Hotel booked: {hotel_name} in {city}. "
                  f"Check-in: {check_in}, Check-out: {check_out} ({nights} nights, {guests} guests). "
                  f"Total: ₹{final_price}. Guest: {guest_name}.",
            booking_reference=booking_id
        )
        self.leads[lead.lead_id] = lead
        await self._persist_lead(lead)
        logger.info(f"Auto-lead created from hotel booking: {lead.lead_id} priority={priority.value}")
        return lead

    async def _persist_lead(self, lead: TravelLead):
        """Persist lead to DB, then fire HOT-lead outreach notification."""
        try:
            from app.database import database as db
            if db is None:
                return

            lead_doc = {
                "lead_id": lead.lead_id,
                "user_id": lead.user_id,
                "user_email": lead.user_email,
                "user_phone": lead.user_phone,
                "source": lead.source.value,
                "priority": lead.priority.value,
                "status": lead.status.value,
                "pickup_address": lead.pickup_address,
                "pickup_lat": lead.pickup_lat,
                "pickup_lng": lead.pickup_lng,
                "drop_address": lead.drop_address,
                "drop_lat": lead.drop_lat,
                "drop_lng": lead.drop_lng,
                "city": lead.city,
                "travel_date": lead.travel_date,
                "travel_type": lead.travel_type,
                "booking_value": lead.booking_value,
                "currency": lead.currency,
                "intent_tags": lead.intent_tags,
                "notes": lead.notes,
                "booking_reference": lead.booking_reference,
                "created_at": lead.created_at
            }
            await db["travel_leads"].update_one(
                {"lead_id": lead.lead_id},
                {"$set": lead_doc},
                upsert=True
            )
        except Exception as e:
            logger.warning(f"Lead persist error: {e}")

        # Fire property-interest outreach for HIGH / HOT leads
        if lead.priority in (LeadPriority.HIGH, LeadPriority.HOT):
            try:
                from app.travel_notification_service import travel_notification_service
                # Resolve a display name from email or phone
                display_name = (
                    lead.user_email.split("@")[0].replace(".", " ").title()
                    if lead.user_email else "Valued Guest"
                )
                await travel_notification_service.notify_hot_lead(
                    name=display_name,
                    email=lead.user_email,
                    phone=lead.user_phone,
                    city=lead.city,
                    intent_tags=lead.intent_tags,
                    source=lead.source.value
                )
            except Exception as e:
                logger.warning(f"Hot-lead notification failed: {e}")

    def get_leads_for_user(self, user_id: str) -> List[TravelLead]:
        return [l for l in self.leads.values() if l.user_id == user_id]

    def get_hot_leads(self) -> List[TravelLead]:
        return [l for l in self.leads.values() if l.priority == LeadPriority.HOT]

    def get_leads_by_city(self, city: str) -> List[TravelLead]:
        city = city.upper()
        return [l for l in self.leads.values() if l.city and l.city.upper() == city]

    def get_all_leads(self, status: Optional[str] = None) -> List[TravelLead]:
        leads = list(self.leads.values())
        if status:
            leads = [l for l in leads if l.status.value == status]
        return sorted(leads, key=lambda l: (
            ["hot", "high", "medium", "low"].index(l.priority.value)
        ))


travel_lead_service = TravelLeadService()
