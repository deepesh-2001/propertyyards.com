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


class SaleType(str, Enum):
    PROPERTY_SALE = "property_sale"
    RENTAL = "rental"
    COMMERCIAL = "commercial"
    LAND = "land"


class SalesRecord(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    property_id: str
    seller_id: str
    buyer_id: Optional[str] = None
    sale_type: SaleType = SaleType.PROPERTY_SALE
    sale_price: float
    original_listing_price: float
    commission_amount: float = 0
    broker_id: Optional[str] = None
    broker_commission: float = 0
    sale_date: datetime = Field(default_factory=datetime.utcnow)
    closing_date: Optional[datetime] = None
    payment_method: Optional[str] = None  # cash, mortgage, loan
    financing_details: Optional[dict] = None
    status: str = "completed"  # pending, completed, cancelled
    notes: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        collection_name = "sales_records"


class ProjectionType(str, Enum):
    SALES = "sales"
    REVENUE = "revenue"
    GROWTH = "growth"
    MARKET_TREND = "market_trend"
    AI_FORECAST = "ai_forecast"


class Projection(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    projection_type: ProjectionType
    title: str
    description: Optional[str] = None
    period_start: datetime
    period_end: datetime
    location_filter: Optional[str] = None  # city, state, or all
    property_type_filter: Optional[str] = None
    projected_value: float
    confidence_level: float = 0.8  # 0.0 to 1.0
    methodology: str  # linear_regression, moving_average, ai_model, etc.
    data_points_used: int
    historical_data_range: Optional[str] = None  # e.g., "12 months"
    breakdown_by_month: List[dict] = []  # monthly projections
    assumptions: Optional[dict] = None
    created_by: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        collection_name = "projections"


class FutureGrowth(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    location: str  # city or region
    growth_rate_projected: float  # percentage
    time_horizon_years: int  # 1, 3, 5, 10 years
    property_value_change: float  # projected percentage change
    rental_yield_change: float  # projected percentage change
    demand_index: float  # 0 to 100
    supply_index: float  # 0 to 100
    infrastructure_developments: List[str] = []  # upcoming projects
    economic_indicators: Optional[dict] = None  # employment, gdp growth, etc.
    population_growth: float  # projected percentage
    ai_confidence_score: float = 0.0  # AI model confidence
    risk_factors: List[str] = []
    opportunities: List[str] = []
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        collection_name = "future_growth"


class FutureProject(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    project_name: str
    developer_name: str
    location: str
    city: str
    state: str
    project_type: PropertyType
    total_units: int
    unit_types: List[str] = []  # 1BHK, 2BHK, 3BHK, etc.
    price_range_min: float
    price_range_max: float
    launch_date: Optional[datetime] = None
    completion_date: Optional[datetime] = None
    construction_status: str = "pre_launch"  # pre_launch, under_construction, ready
    amenities: List[str] = []
    description: Optional[str] = None
    contact_info: Optional[dict] = None
    expected_roi: Optional[float] = None  # expected return on investment
    is_verified: bool = False
    is_featured: bool = False
    created_by: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        collection_name = "future_projects"


class InvestmentType(str, Enum):
    RESIDENTIAL = "residential"
    COMMERCIAL = "commercial"
    RENTAL = "rental"
    LAND = "land"
    MIXED_USE = "mixed_use"
    REIT = "reit"


class RiskLevel(str, Enum):
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    SPECULATIVE = "speculative"


class InvestmentOpportunity(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    description: str
    investment_type: InvestmentType
    location: str
    city: str
    state: str
    minimum_investment: float
    expected_roi_annual: float  # percentage
    investment_term_months: int
    risk_level: RiskLevel = RiskLevel.MODERATE
    property_id: Optional[str] = None  # if linked to existing property
    project_id: Optional[str] = None  # if linked to future project
    total_funding_needed: Optional[float] = None
    funding_raised: float = 0
    investors_count: int = 0
    documents: List[str] = []  # URLs to investment documents
    highlights: List[str] = []
    market_analysis: Optional[dict] = None
    financial_projections: Optional[dict] = None
    status: str = "open"  # open, funded, closed, cancelled
    closing_date: Optional[datetime] = None
    created_by: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        collection_name = "investment_opportunities"

