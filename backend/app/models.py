"""
Pydantic models for MongoDB
"""
from pydantic import BaseModel, Field, EmailStr
from datetime import datetime
from typing import Optional, List
from enum import Enum
import uuid


class UserRole(str, Enum):
    ADMIN = "admin"
    SELLER = "seller"
    BUYER = "buyer"
    AGENT = "agent"


class PropertyStatus(str, Enum):
    LISTED = "listed"
    SOLD = "sold"
    RENTED = "rented"
    PENDING = "pending"


class InquiryStatus(str, Enum):
    PENDING = "pending"
    RESPONDED = "responded"
    CLOSED = "closed"


class PropertyType(str, Enum):
    APARTMENT = "apartment"
    HOUSE = "house"
    CONDO = "condo"
    TOWNHOUSE = "townhouse"
    LAND = "land"
    COMMERCIAL = "commercial"


class ListingType(str, Enum):
    SALE = "sale"
    RENT = "rent"
    BOTH = "both"


class Property(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    title: str
    description: Optional[str] = None
    location: str
    city: str
    state: str
    country: str
    price: float
    property_type: PropertyType
    listing_type: ListingType = ListingType.SALE
    bedrooms: int
    bathrooms: int
    area: float
    amenities: List[str] = []
    images: List[str] = []
    status: PropertyStatus = PropertyStatus.LISTED
    # Rental specific fields
    rent_period: Optional[str] = None  # monthly, yearly, weekly
    deposit_amount: Optional[float] = None
    lease_duration: Optional[str] = None  # 6 months, 1 year, etc.
    furnished: bool = False
    pets_allowed: bool = False
    # Broker information
    broker_id: Optional[str] = None
    broker_name: Optional[str] = None
    broker_phone: Optional[str] = None
    broker_email: Optional[EmailStr] = None
    broker_commission: Optional[float] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        collection_name = "properties"


class Inquiry(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    property_id: str
    message: str
    status: InquiryStatus = InquiryStatus.PENDING
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        collection_name = "inquiries"


class Wishlist(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    property_id: str
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        collection_name = "wishlists"


class AuditLog(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: Optional[str] = None
    action: str
    resource_type: str
    resource_id: Optional[str] = None
    details: Optional[dict] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        collection_name = "audit_logs"


class Broker(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    name: str
    phone: str
    email: EmailStr
    license_number: Optional[str] = None
    agency_name: Optional[str] = None
    agency_address: Optional[str] = None
    specialization: List[str] = []  # residential, commercial, rental, etc.
    commission_rate: Optional[float] = None
    years_of_experience: Optional[int] = None
    languages_spoken: List[str] = []
    rating: Optional[float] = None
    total_deals: Optional[int] = None
    bio: Optional[str] = None
    profile_image: Optional[str] = None
    is_verified: bool = False
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        collection_name = "brokers"


class ChatConversation(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    session_id: str
    messages: List[dict] = []
    context: Optional[dict] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        collection_name = "chat_conversations"

