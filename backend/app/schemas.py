"""
Pydantic schemas for request/response validation
"""
from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum


# ========== User Schemas ==========
class UserType(str, Enum):
    ADMIN = "admin"
    SELLER = "seller"
    BUYER = "buyer"
    AGENT = "agent"


class UserBase(BaseModel):
    email: EmailStr
    first_name: str
    last_name: str
    phone_number: Optional[str] = None


class UserCreate(UserBase):
    password: str = Field(..., min_length=8)
    role: UserType = UserType.BUYER


class UserUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone_number: Optional[str] = None


class UserResponse(UserBase):
    id: str
    role: UserType
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class UserProfileResponse(UserResponse):
    """Detailed user profile"""
    properties_count: int = 0
    inquiries_count: int = 0


# ========== Property Schemas ==========
class PropertyType(str, Enum):
    APARTMENT = "apartment"
    HOUSE = "house"
    CONDO = "condo"
    TOWNHOUSE = "townhouse"
    COMMERCIAL = "commercial"
    LAND = "land"


class PropertyStatus(str, Enum):
    LISTED = "listed"
    SOLD = "sold"
    RENTED = "rented"
    PENDING = "pending"


class PropertyCreate(BaseModel):
    title: str
    description: str
    location: str
    city: str
    state: str
    country: str
    price: float = Field(..., gt=0)
    property_type: PropertyType
    bedrooms: int = Field(..., ge=0)
    bathrooms: int = Field(..., ge=0)
    area: float = Field(..., gt=0)  # in sq ft
    amenities: Optional[List[str]] = []
    images: Optional[List[str]] = []


class PropertyUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    price: Optional[float] = None
    bedrooms: Optional[int] = None
    bathrooms: Optional[int] = None
    area: Optional[float] = None
    amenities: Optional[List[str]] = None
    status: Optional[PropertyStatus] = None


class PropertyResponse(PropertyCreate):
    id: str
    user_id: str
    status: PropertyStatus
    created_at: datetime
    updated_at: datetime
    wishlist_count: int = 0

    class Config:
        from_attributes = True


class PropertyListResponse(BaseModel):
    """Simplified property response for list endpoints"""
    id: str
    title: str
    location: str
    city: str
    price: float
    property_type: PropertyType
    bedrooms: int
    bathrooms: int
    area: float
    status: PropertyStatus
    images: Optional[List[str]] = []
    created_at: datetime


# ========== Inquiry Schemas ==========
class InquiryStatus(str, Enum):
    PENDING = "pending"
    RESPONDED = "responded"
    CLOSED = "closed"


class InquiryCreate(BaseModel):
    property_id: str
    message: str = Field(..., min_length=10)


class InquiryUpdate(BaseModel):
    message: Optional[str] = None
    status: Optional[InquiryStatus] = None


class InquiryResponse(BaseModel):
    id: str
    user_id: str
    property_id: str
    message: str
    status: InquiryStatus
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ========== Wishlist Schemas ==========
class WishlistItem(BaseModel):
    property_id: str


class WishlistResponse(BaseModel):
    id: str
    user_id: str
    property_id: str
    property: PropertyListResponse
    created_at: datetime


# ========== Authentication Schemas ==========
class TokenRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class RefreshTokenRequest(BaseModel):
    refresh_token: str


# ========== Search Schemas ==========
class PropertySearchFilters(BaseModel):
    query: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    min_price: Optional[float] = None
    max_price: Optional[float] = None
    property_type: Optional[PropertyType] = None
    min_bedrooms: Optional[int] = None
    max_bedrooms: Optional[int] = None
    min_bathrooms: Optional[int] = None
    max_bathrooms: Optional[int] = None
    amenities: Optional[List[str]] = []
    page: int = Field(1, ge=1)
    limit: int = Field(20, ge=1, le=100)


# ========== Admin Schemas ==========
class UserStats(BaseModel):
    total_users: int
    active_users: int
    total_sellers: int
    total_buyers: int
    total_agents: int


class PropertyStats(BaseModel):
    total_properties: int
    active_listings: int
    sold_properties: int
    rented_properties: int
    total_value: float


class AdminStats(BaseModel):
    users: UserStats
    properties: PropertyStats
    total_inquiries: int
    total_wishlist_items: int


# ========== Pagination ==========
class PaginationParams(BaseModel):
    page: int = Field(1, ge=1)
    limit: int = Field(20, ge=1, le=100)


class PaginatedResponse(BaseModel):
    items: List
    total: int
    page: int
    limit: int
    pages: int

