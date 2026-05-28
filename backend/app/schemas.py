"""
Pydantic schemas for request/response validation
"""
from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum
from typing import Dict, Any


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
    # Access control flags
    is_enabled: Optional[bool] = None
    access_restricted: Optional[bool] = None
    can_post_properties: Optional[bool] = None
    can_contact_agents: Optional[bool] = None
    can_apply_loans: Optional[bool] = None
    can_apply_credit_cards: Optional[bool] = None


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


class ListingType(str, Enum):
    SALE = "sale"
    RENT = "rent"
    BOTH = "both"


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
    listing_type: ListingType = ListingType.SALE
    bedrooms: int = Field(..., ge=0)
    bathrooms: int = Field(..., ge=0)
    area: float = Field(..., gt=0)  # in sq ft
    amenities: Optional[List[str]] = []
    images: Optional[List[str]] = []
    # Rental specific
    rent_period: Optional[str] = None
    deposit_amount: Optional[float] = None
    lease_duration: Optional[str] = None
    furnished: bool = False
    pets_allowed: bool = False
    # Broker information
    broker_id: Optional[str] = None
    broker_name: Optional[str] = None
    broker_phone: Optional[str] = None
    # Enable/Disable flags
    is_enabled: bool = True
    access_restricted: bool = False
    featured: bool = False
    premium_listing: bool = False
    broker_email: Optional[EmailStr] = None
    broker_commission: Optional[float] = None


class PropertyUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    price: Optional[float] = None
    bedrooms: Optional[int] = None
    bathrooms: Optional[int] = None
    area: Optional[float] = None
    amenities: Optional[List[str]] = None
    status: Optional[PropertyStatus] = None
    # Rental specific
    rent_period: Optional[str] = None
    deposit_amount: Optional[float] = None
    lease_duration: Optional[str] = None
    furnished: Optional[bool] = None
    pets_allowed: Optional[bool] = None
    # Broker information
    broker_id: Optional[str] = None
    broker_name: Optional[str] = None
    broker_phone: Optional[str] = None
    broker_email: Optional[EmailStr] = None
    broker_commission: Optional[float] = None
    # Enable/Disable flags
    is_enabled: Optional[bool] = None
    access_restricted: Optional[bool] = None
    featured: Optional[bool] = None
    premium_listing: Optional[bool] = None


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


# ========== CRM Schemas ==========
class LeadStatus(str, Enum):
    NEW = "new"
    CONTACTED = "contacted"
    QUALIFIED = "qualified"
    PROPOSAL = "proposal"
    NEGOTIATION = "negotiation"
    WON = "won"
    LOST = "lost"


class LeadSource(str, Enum):
    WEBSITE = "website"
    REFERRAL = "referral"
    SOCIAL_MEDIA = "social_media"
    EMAIL_CAMPAIGN = "email_campaign"
    PAID_AD = "paid_ad"
    DIRECT = "direct"
    OTHER = "other"


class InteractionType(str, Enum):
    CALL = "call"
    EMAIL = "email"
    MEETING = "meeting"
    PROPERTY_VIEWING = "property_viewing"
    FOLLOW_UP = "follow_up"
    NOTE = "note"


class LeadCreate(BaseModel):
    name: str
    email: EmailStr
    phone: Optional[str] = None
    source: LeadSource = LeadSource.WEBSITE
    status: LeadStatus = LeadStatus.NEW
    property_interest: Optional[str] = None
    budget_range: Optional[str] = None
    preferred_location: Optional[str] = None
    notes: Optional[str] = ""
    assigned_to: Optional[str] = None
    tags: Optional[List[str]] = []


class LeadUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    status: Optional[LeadStatus] = None
    property_interest: Optional[str] = None
    budget_range: Optional[str] = None
    preferred_location: Optional[str] = None
    notes: Optional[str] = None
    assigned_to: Optional[str] = None
    tags: Optional[List[str]] = None


class LeadResponse(BaseModel):
    id: str
    name: str
    email: EmailStr
    phone: Optional[str]
    source: LeadSource
    status: LeadStatus
    property_interest: Optional[str]
    budget_range: Optional[str]
    preferred_location: Optional[str]
    notes: str
    assigned_to: Optional[str]
    created_at: datetime
    updated_at: datetime
    interactions: List
    tags: List[str]


class InteractionCreate(BaseModel):
    interaction_type: InteractionType
    notes: str


class PipelineSummary(BaseModel):
    total_leads: int
    by_status: Dict[str, int]
    conversion_rate: float


# ========== Referral Schemas ==========
class ReferralStatus(str, Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    REWARDED = "rewarded"
    EXPIRED = "expired"
    CANCELLED = "cancelled"


class RewardType(str, Enum):
    CREDIT = "credit"
    DISCOUNT = "discount"
    CASHBACK = "cashback"
    PREMIUM_FEATURES = "premium_features"


class ReferralCodeCreate(BaseModel):
    user_id: str


class ReferralCodeResponse(BaseModel):
    id: str
    user_id: str
    code: str
    created_at: datetime
    expires_at: datetime
    is_active: bool
    total_referrals: int
    successful_referrals: int
    total_earned: float


class ReferralCreate(BaseModel):
    referrer_id: str
    referred_user_id: str
    referral_code: str


class ReferralResponse(BaseModel):
    id: str
    referrer_id: str
    referred_user_id: str
    referral_code: str
    status: ReferralStatus
    created_at: datetime
    completed_at: Optional[datetime]
    rewarded_at: Optional[datetime]
    reward_amount: float


class RewardCreate(BaseModel):
    referral_id: str
    reward_type: RewardType
    amount: float
    description: str


class RewardResponse(BaseModel):
    id: str
    referral_id: str
    referrer_id: str
    reward_type: RewardType
    amount: float
    description: str
    created_at: datetime
    is_claimed: bool
    claimed_at: Optional[datetime]


class ReferralStats(BaseModel):
    referral_code: Optional[str]
    total_referrals: int
    successful_referrals: int
    completed_referrals: int
    pending_rewards: float
    claimed_rewards: float
    available_rewards: float


class ReferralSettings(BaseModel):
    enabled: bool
    reward_amount: float
    reward_type: RewardType
    min_purchase_amount: float
    referral_bonus_percentage: float
    max_referrals_per_user: int
    referral_expiry_days: int


# ========== Access Control Schemas ==========
class Permission(str, Enum):
    USER_READ = "user:read"
    USER_WRITE = "user:write"
    USER_DELETE = "user:delete"
    PROPERTY_READ = "property:read"
    PROPERTY_WRITE = "property:write"
    PROPERTY_DELETE = "property:delete"
    PROPERTY_APPROVE = "property:approve"
    INQUIRY_READ = "inquiry:read"
    INQUIRY_WRITE = "inquiry:write"
    INQUIRY_DELETE = "inquiry:delete"
    INQUIRY_RESPOND = "inquiry:respond"
    ADMIN_READ = "admin:read"
    ADMIN_WRITE = "admin:write"
    ADMIN_DELETE = "admin:delete"
    ADMIN_MANAGE_USERS = "admin:manage_users"
    ADMIN_MANAGE_ROLES = "admin:manage_roles"
    ADMIN_VIEW_ANALYTICS = "admin:view_analytics"
    CRM_READ = "crm:read"
    CRM_WRITE = "crm:write"
    CRM_DELETE = "crm:delete"
    CRM_MANAGE_LEADS = "crm:manage_leads"
    REFERRAL_READ = "referral:read"
    REFERRAL_WRITE = "referral:write"
    REFERRAL_MANAGE = "referral:manage"
    SYSTEM_CONFIG = "system:config"
    SYSTEM_LOGS = "system:logs"
    SYSTEM_HEALTH = "system:health"


class ResourceType(str, Enum):
    USER = "user"
    PROPERTY = "property"
    INQUIRY = "inquiry"
    LEAD = "lead"
    REWARD = "reward"
    ROLE = "role"
    PERMISSION = "permission"
    SETTINGS = "settings"


class AccessLevel(str, Enum):
    NONE = "none"
    READ = "read"
    WRITE = "write"
    ADMIN = "admin"


class RoleCreate(BaseModel):
    name: str
    permissions: List[str]
    description: str = ""


class RoleResponse(BaseModel):
    id: str
    name: str
    permissions: List[str]
    description: str
    is_system: bool
    created_at: datetime


class RoleUpdate(BaseModel):
    permissions: List[str]
    description: Optional[str] = None


class ACLCreate(BaseModel):
    resource_type: ResourceType
    resource_id: str
    user_id: str
    access_level: AccessLevel


class ACLResponse(BaseModel):
    id: str
    resource_type: ResourceType
    resource_id: str
    user_id: str
    access_level: AccessLevel
    created_at: datetime


class PermissionCheck(BaseModel):
    user_id: str
    permission: Permission


class PermissionCheckResponse(BaseModel):
    has_permission: bool


# ========== Loan Calculator Schemas ==========
class LoanType(str, Enum):
    MORTGAGE = "mortgage"
    PERSONAL = "personal"
    CAR = "car"
    STUDENT = "student"
    BUSINESS = "business"
    HOME_EQUITY = "home_equity"
    CONSTRUCTION = "construction"


class InterestRateType(str, Enum):
    FIXED = "fixed"
    VARIABLE = "variable"
    ADJUSTABLE = "adjustable"


class RepaymentFrequency(str, Enum):
    MONTHLY = "monthly"
    BI_WEEKLY = "bi_weekly"
    WEEKLY = "weekly"
    QUARTERLY = "quarterly"
    ANNUALLY = "annually"


class MortgageLoanRequest(BaseModel):
    principal: float = Field(..., gt=0)
    annual_rate: float = Field(..., ge=0)
    years: int = Field(..., gt=0, le=50)
    down_payment: float = Field(0, ge=0)
    property_tax: float = Field(0, ge=0)
    insurance: float = Field(0, ge=0)


class MortgageLoanResponse(BaseModel):
    loan_amount: float
    down_payment: float
    principal_and_interest: float
    property_tax: float
    insurance: float
    total_monthly_payment: float
    total_payment: float
    total_interest: float
    loan_to_value: float


class AffordabilityRequest(BaseModel):
    monthly_income: float = Field(..., gt=0)
    down_payment: float = Field(..., ge=0)
    annual_rate: float = Field(..., ge=0)
    years: int = Field(..., gt=0, le=50)
    debt_to_income_ratio: float = Field(0.28, ge=0, le=0.5)


class AffordabilityResponse(BaseModel):
    max_monthly_payment: float
    max_loan_amount: float
    max_home_price: float
    down_payment: float
    debt_to_income_ratio: float


class PersonalLoanRequest(BaseModel):
    principal: float = Field(..., gt=0)
    annual_rate: float = Field(..., ge=0)
    years: int = Field(..., gt=0, le=10)
    origination_fee: float = Field(0, ge=0)


class PersonalLoanResponse(BaseModel):
    monthly_payment: float
    total_payment: float
    total_interest: float
    origination_fee: float
    total_cost: float
    apr: float


class CarLoanRequest(BaseModel):
    car_price: float = Field(..., gt=0)
    down_payment: float = Field(0, ge=0)
    annual_rate: float = Field(..., ge=0)
    years: int = Field(..., gt=0, le=10)
    trade_in_value: float = Field(0, ge=0)


class CarLoanResponse(BaseModel):
    car_price: float
    down_payment: float
    trade_in_value: float
    loan_amount: float
    monthly_payment: float
    total_payment: float
    total_interest: float
    message: Optional[str] = None


class StudentLoanRequest(BaseModel):
    principal: float = Field(..., gt=0)
    annual_rate: float = Field(..., ge=0)
    years: int = Field(..., gt=0, le=30)
    grace_period_months: int = Field(6, ge=0)


class StudentLoanResponse(BaseModel):
    principal: float
    monthly_payment: float
    total_payment: float
    total_interest: float
    grace_period_months: int
    grace_period_interest: float


class IncomeDrivenRepaymentRequest(BaseModel):
    annual_income: float = Field(..., gt=0)
    family_size: int = Field(..., gt=0)
    poverty_line: float = Field(14500, gt=0)


class IncomeDrivenRepaymentResponse(BaseModel):
    annual_income: float
    family_size: int
    discretionary_income: float
    monthly_payment: float
    repayment_plan: str


class BusinessLoanRequest(BaseModel):
    principal: float = Field(..., gt=0)
    annual_rate: float = Field(..., ge=0)
    years: int = Field(..., gt=0, le=25)
    collateral_value: float = Field(0, ge=0)


class BusinessLoanResponse(BaseModel):
    principal: float
    monthly_payment: float
    total_payment: float
    total_interest: float
    collateral_value: float
    loan_to_value: float


class HomeEquityLoanRequest(BaseModel):
    home_value: float = Field(..., gt=0)
    current_mortgage: float = Field(..., ge=0)
    annual_rate: float = Field(..., ge=0)
    years: int = Field(..., gt=0, le=30)
    max_ltv_ratio: float = Field(0.85, ge=0.5, le=0.95)


class HomeEquityLoanResponse(BaseModel):
    home_value: float
    current_mortgage: float
    available_equity: float
    max_loan_amount: float
    monthly_payment: float
    total_payment: float
    total_interest: float
    combined_ltv: float


class ConstructionLoanRequest(BaseModel):
    total_cost: float = Field(..., gt=0)
    down_payment: float = Field(..., ge=0)
    annual_rate: float = Field(..., ge=0)
    construction_months: int = Field(..., gt=0, le=36)
    permanent_loan_years: int = Field(..., gt=0, le=50)


class ConstructionLoanResponse(BaseModel):
    total_cost: float
    down_payment: float
    loan_amount: float
    construction_months: int
    monthly_interest_only: float
    total_construction_interest: float
    permanent_loan_years: int
    monthly_payment: float
    total_payment: float
    total_interest: float


class LoanComparisonRequest(BaseModel):
    principal: float = Field(..., gt=0)
    loan_options: List[Dict[str, Any]]


class LoanComparisonResponse(BaseModel):
    option_name: str
    annual_rate: float
    years: int
    monthly_payment: float
    total_payment: float
    total_interest: float
    apr: float


class AmortizationScheduleRequest(BaseModel):
    principal: float = Field(..., gt=0)
    annual_rate: float = Field(..., ge=0)
    years: int = Field(..., gt=0)


class AmortizationScheduleItem(BaseModel):
    month: int
    payment: float
    principal_payment: float
    interest_payment: float
    remaining_balance: float


# ========== Contact Schemas ==========
class ContactInfo(BaseModel):
    company_name: str
    phone: str
    email: EmailStr
    address: str
    city: str
    state: str
    zip_code: str
    country: str
    website: str
    support_hours: str
    emergency_contact: Optional[str] = None


class ContactInquiry(BaseModel):
    name: str
    email: EmailStr
    phone: Optional[str] = None
    subject: str
    message: str
    inquiry_type: str = "general"


# ========== Notification Schemas ==========
class NotificationChannel(str, Enum):
    EMAIL = "email"
    WHATSAPP = "whatsapp"
    SMS = "sms"
    PUSH = "push"
    IN_APP = "in_app"


class NotificationType(str, Enum):
    PROPERTY_INQUIRY = "property_inquiry"
    APPOINTMENT_REMINDER = "appointment_reminder"
    OFFER_RECEIVED = "offer_received"
    PRICE_DROP = "price_drop"
    NEW_LISTING = "new_listing"
    WELCOME = "welcome"
    PASSWORD_RESET = "password_reset"
    EMAIL_VERIFICATION = "email_verification"
    MARKETING = "marketing"
    SYSTEM = "system"


class NotificationStatus(str, Enum):
    PENDING = "pending"
    SENT = "sent"
    DELIVERED = "delivered"
    READ = "read"
    FAILED = "failed"


class WhatsAppMessageRequest(BaseModel):
    to_phone: str
    message: str
    message_type: str = "text"
    preview_url: bool = False


class WhatsAppMessageResponse(BaseModel):
    success: bool
    message_id: Optional[str] = None
    status: str
    error: Optional[str] = None


class WhatsAppTemplateRequest(BaseModel):
    to_phone: str
    template_name: str
    components: List[Dict[str, Any]]
    language_code: str = "en_US"


class EmailMessageRequest(BaseModel):
    to_email: EmailStr
    subject: str
    body: str
    from_email: EmailStr
    from_name: Optional[str] = None
    html: bool = False
    cc: Optional[List[str]] = None
    bcc: Optional[List[str]] = None


class EmailMessageResponse(BaseModel):
    success: bool
    status: str
    to: str
    subject: str
    error: Optional[str] = None


class NotificationRequest(BaseModel):
    user_id: str
    channel: NotificationChannel
    notification_type: NotificationType
    title: str
    message: str
    data: Optional[Dict[str, Any]] = None
    priority: str = "normal"


class NotificationResponse(BaseModel):
    id: str
    user_id: str
    channel: NotificationChannel
    notification_type: NotificationType
    title: str
    message: str
    status: NotificationStatus
    created_at: datetime
    sent_at: Optional[datetime] = None
    data: Optional[Dict[str, Any]] = None


class NotificationPreferences(BaseModel):
    user_id: str
    email_enabled: bool = True
    whatsapp_enabled: bool = False
    sms_enabled: bool = False
    push_enabled: bool = True
    marketing_enabled: bool = False
    property_inquiry_enabled: bool = True
    appointment_reminder_enabled: bool = True
    offer_received_enabled: bool = True
    price_drop_enabled: bool = True
    new_listing_enabled: bool = False


# ========== Broker Schemas ==========
class BrokerCreate(BaseModel):
    user_id: str
    name: str
    phone: str
    email: EmailStr
    license_number: Optional[str] = None
    agency_name: Optional[str] = None
    agency_address: Optional[str] = None
    specialization: Optional[List[str]] = []
    commission_rate: Optional[float] = None
    years_of_experience: Optional[int] = None
    languages_spoken: Optional[List[str]] = []
    bio: Optional[str] = None
    profile_image: Optional[str] = None


class BrokerUpdate(BaseModel):
    name: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[EmailStr] = None
    license_number: Optional[str] = None
    agency_name: Optional[str] = None
    agency_address: Optional[str] = None
    specialization: Optional[List[str]] = None
    commission_rate: Optional[float] = None
    years_of_experience: Optional[int] = None
    languages_spoken: Optional[List[str]] = None
    bio: Optional[str] = None
    profile_image: Optional[str] = None
    is_verified: Optional[bool] = None
    is_active: Optional[bool] = None


class BrokerResponse(BaseModel):
    id: str
    user_id: str
    name: str
    phone: str
    email: EmailStr
    license_number: Optional[str]
    agency_name: Optional[str]
    agency_address: Optional[str]
    specialization: List[str]
    commission_rate: Optional[float]
    years_of_experience: Optional[int]
    languages_spoken: List[str]
    rating: Optional[float]
    total_deals: Optional[int]
    bio: Optional[str]
    profile_image: Optional[str]
    is_verified: bool
    is_active: bool
    created_at: datetime
    updated_at: datetime


# ========== Chat Bot Schemas ==========
class ChatMessage(BaseModel):
    role: str  # user, assistant, system
    content: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None
    context: Optional[Dict[str, Any]] = None


class ChatResponse(BaseModel):
    message: str
    session_id: str
    context: Optional[Dict[str, Any]] = None
    suggestions: Optional[List[str]] = None


class ChatHistoryItem(BaseModel):
    role: str
    content: str
    timestamp: datetime


# ========== Monitoring Schemas ==========
class MetricType(str, Enum):
    REQUEST_COUNT = "request_count"
    RESPONSE_TIME = "response_time"
    ERROR_COUNT = "error_count"
    DATABASE_QUERY_TIME = "database_query_time"
    CACHE_HIT_RATE = "cache_hit_rate"
    MEMORY_USAGE = "memory_usage"
    CPU_USAGE = "cpu_usage"


class AlertSeverity(str, Enum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class MetricRecord(BaseModel):
    metric_type: MetricType
    value: float
    tags: Optional[Dict[str, Any]] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class AlertCreate(BaseModel):
    severity: AlertSeverity
    title: str
    message: str
    source: str = "system"
    tags: Optional[Dict[str, Any]] = None


class AlertResponse(BaseModel):
    id: str
    severity: AlertSeverity
    title: str
    message: str
    source: str
    tags: Dict[str, Any]
    created_at: datetime
    resolved: bool
    resolved_at: Optional[datetime] = None


class SystemLog(BaseModel):
    level: str
    message: str
    source: str = "system"
    extra: Optional[Dict[str, Any]] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class HealthStatus(BaseModel):
    status: str
    health_score: int
    critical_alerts: int
    error_alerts: int
    recent_metrics_count: int
    timestamp: datetime


# ========== Recruitment Schemas ==========
class JobStatus(str, Enum):
    DRAFT = "draft"
    OPEN = "open"
    CLOSED = "closed"
    ON_HOLD = "on_hold"
    FILLED = "filled"


class ApplicationStatus(str, Enum):
    PENDING = "pending"
    REVIEWED = "reviewed"
    SHORTLISTED = "shortlisted"
    INTERVIEW_SCHEDULED = "interview_scheduled"
    INTERVIEW_COMPLETED = "interview_completed"
    OFFER_EXTENDED = "offer_extended"
    OFFER_ACCEPTED = "offer_accepted"
    OFFER_DECLINED = "offer_declined"
    REJECTED = "rejected"
    HIRED = "hired"


class EmploymentType(str, Enum):
    FULL_TIME = "full_time"
    PART_TIME = "part_time"
    CONTRACT = "contract"
    INTERNSHIP = "internship"
    FREELANCE = "freelance"


class ExperienceLevel(str, Enum):
    ENTRY = "entry"
    JUNIOR = "junior"
    MID = "mid"
    SENIOR = "senior"
    LEAD = "lead"
    EXECUTIVE = "executive"


class JobPostingCreate(BaseModel):
    title: str
    description: str
    department: str
    location: str
    employment_type: EmploymentType
    experience_level: ExperienceLevel
    salary_min: float = Field(..., gt=0)
    salary_max: float = Field(..., gt=0)
    requirements: List[str] = []
    responsibilities: List[str] = []
    benefits: List[str] = []
    status: JobStatus = JobStatus.DRAFT


class JobPostingUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    department: Optional[str] = None
    location: Optional[str] = None
    employment_type: Optional[EmploymentType] = None
    experience_level: Optional[ExperienceLevel] = None
    salary_min: Optional[float] = None
    salary_max: Optional[float] = None
    requirements: Optional[List[str]] = None
    responsibilities: Optional[List[str]] = None
    benefits: Optional[List[str]] = None
    status: Optional[JobStatus] = None


class JobPostingResponse(BaseModel):
    id: str
    title: str
    description: str
    department: str
    location: str
    employment_type: EmploymentType
    experience_level: ExperienceLevel
    salary_min: float
    salary_max: float
    requirements: List[str]
    responsibilities: List[str]
    benefits: List[str]
    posted_by: str
    status: JobStatus
    application_count: int
    view_count: int
    created_at: datetime
    updated_at: datetime


class JobApplicationCreate(BaseModel):
    job_id: str
    applicant_name: str
    applicant_email: EmailStr
    applicant_phone: str
    resume_url: str
    cover_letter: str
    skills: List[str] = []
    experience_years: int = Field(..., ge=0)
    expected_salary: float = Field(..., ge=0)
    referral_code: Optional[str] = None


class JobApplicationUpdate(BaseModel):
    status: ApplicationStatus
    notes: Optional[str] = None


class JobApplicationResponse(BaseModel):
    id: str
    job_id: str
    applicant_name: str
    applicant_email: EmailStr
    applicant_phone: str
    resume_url: str
    cover_letter: str
    skills: List[str]
    experience_years: int
    expected_salary: float
    referral_code: Optional[str]
    status: ApplicationStatus
    created_at: datetime
    updated_at: datetime


class SalaryStructureCreate(BaseModel):
    employee_id: str
    base_salary: float = Field(..., gt=0)
    bonus: float = 0
    allowances: Optional[Dict[str, float]] = None
    deductions: Optional[Dict[str, float]] = None
    effective_date: Optional[datetime] = None


class SalaryStructureUpdate(BaseModel):
    base_salary: Optional[float] = None
    bonus: Optional[float] = None
    allowances: Optional[Dict[str, float]] = None
    deductions: Optional[Dict[str, float]] = None


class SalaryStructureResponse(BaseModel):
    employee_id: str
    base_salary: float
    bonus: float
    allowances: Dict[str, float]
    deductions: Dict[str, float]
    effective_date: datetime
    created_at: datetime


class NetSalaryResponse(BaseModel):
    employee_id: str
    base_salary: float
    bonus: float
    total_allowances: float
    total_deductions: float
    gross_salary: float
    net_salary: float


class EmployeeReferralCreate(BaseModel):
    referrer_id: str
    referred_name: str
    referred_email: EmailStr
    referred_phone: str
    job_id: str
    relationship: str


class EmployeeReferralUpdate(BaseModel):
    status: str
    bonus_amount: Optional[float] = None


class EmployeeReferralResponse(BaseModel):
    id: str
    referrer_id: str
    referred_name: str
    referred_email: EmailStr
    referred_phone: str
    job_id: str
    relationship: str
    status: str
    bonus_amount: float
    bonus_paid: bool
    created_at: datetime
    updated_at: datetime


# ========== Self-Healing Property Schemas ==========
class IssueType(str, Enum):
    WATER_LEAK = "water_leak"
    ELECTRICAL = "electrical"
    HVAC = "hvac"
    PLUMBING = "plumbing"
    SECURITY = "security"
    FIRE = "fire"
    STRUCTURAL = "structural"
    PEST = "pest"
    TEMPERATURE = "temperature"
    HUMIDITY = "humidity"
    AIR_QUALITY = "air_quality"


class IssueSeverity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class HealingAction(str, Enum):
    AUTOMATIC_FIX = "automatic_fix"
    SCHEDULED_MAINTENANCE = "scheduled_maintenance"
    ALERT_OWNER = "alert_owner"
    CONTACT_SERVICE = "contact_service"
    EMERGENCY_SHUTDOWN = "emergency_shutdown"


class SensorCreate(BaseModel):
    property_id: str
    sensor_type: str
    location: str
    threshold_min: float
    threshold_max: float
    unit: str


class SensorResponse(BaseModel):
    id: str
    property_id: str
    sensor_type: str
    location: str
    threshold_min: float
    threshold_max: float
    unit: str
    current_value: Optional[float]
    last_reading: Optional[datetime]
    status: str
    created_at: datetime
    updated_at: datetime


class SensorReadingCreate(BaseModel):
    sensor_id: str
    value: float
    timestamp: Optional[datetime] = None


class IssueCreate(BaseModel):
    property_id: str
    sensor_id: str
    issue_type: IssueType
    severity: IssueSeverity
    description: str
    location: str
    auto_healable: bool = True


class IssueResponse(BaseModel):
    id: str
    property_id: str
    sensor_id: str
    issue_type: IssueType
    severity: IssueSeverity
    description: str
    location: str
    status: str
    auto_healable: bool
    healing_action: Optional[HealingAction]
    created_at: datetime
    resolved_at: Optional[datetime]


class PropertyHealthScore(BaseModel):
    property_id: str
    health_score: int
    health_status: str
    active_issues: int
    total_issues: int
    timestamp: datetime


# ========== Payment Schemas ==========
class PaymentMethod(str, Enum):
    CREDIT_CARD = "credit_card"
    DEBIT_CARD = "debit_card"
    BANK_TRANSFER = "bank_transfer"
    CASH = "cash"
    CHECK = "check"
    CRYPTO = "crypto"
    MOBILE_PAYMENT = "mobile_payment"
    INSTALLMENT = "installment"


class PaymentGateway(str, Enum):
    STRIPE = "stripe"
    PAYPAL = "paypal"
    RAZORPAY = "razorpay"
    SQUARE = "square"
    BRAINTREE = "braintree"
    MOLLIE = "mollie"


class PaymentStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    REFUNDED = "refunded"
    CANCELLED = "cancelled"
    PARTIALLY_REFUNDED = "partially_refunded"


class PaymentConditionType(str, Enum):
    DOWN_PAYMENT = "down_payment"
    INSTALLMENT = "installment"
    MILESTONE = "milestone"
    FINAL_PAYMENT = "final_payment"
    DEPOSIT = "deposit"
    BOOKING_AMOUNT = "booking_amount"


class PaymentFrequency(str, Enum):
    ONE_TIME = "one_time"
    WEEKLY = "weekly"
    BI_WEEKLY = "bi_weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    SEMI_ANNUALLY = "semi_annually"
    ANNUALLY = "annually"
    CUSTOM = "custom"


class PaymentConditionCreate(BaseModel):
    property_id: str
    condition_type: PaymentConditionType
    amount: float = Field(..., gt=0)
    due_date: datetime
    description: Optional[str] = None
    is_mandatory: bool = True
    late_fee_percentage: Optional[float] = Field(0, ge=0, le=100)
    early_payment_discount: Optional[float] = Field(0, ge=0, le=100)
    payment_frequency: Optional[PaymentFrequency] = PaymentFrequency.ONE_TIME
    installments_count: Optional[int] = Field(1, ge=1)
    installment_interval_days: Optional[int] = Field(30, ge=1)


class PaymentConditionUpdate(BaseModel):
    amount: Optional[float] = Field(None, gt=0)
    due_date: Optional[datetime] = None
    description: Optional[str] = None
    is_mandatory: Optional[bool] = None
    late_fee_percentage: Optional[float] = Field(None, ge=0, le=100)
    early_payment_discount: Optional[float] = Field(None, ge=0, le=100)
    payment_frequency: Optional[PaymentFrequency] = None
    installments_count: Optional[int] = Field(None, ge=1)
    installment_interval_days: Optional[int] = Field(None, ge=1)


class PaymentConditionResponse(BaseModel):
    id: str
    property_id: str
    condition_type: PaymentConditionType
    amount: float
    due_date: datetime
    description: Optional[str]
    is_mandatory: bool
    late_fee_percentage: float
    early_payment_discount: float
    payment_frequency: PaymentFrequency
    installments_count: int
    installment_interval_days: int
    status: str
    paid_amount: float
    remaining_amount: float
    created_at: datetime
    updated_at: datetime


class PaymentMethodCreate(BaseModel):
    user_id: str
    method_type: PaymentMethod
    gateway: Optional[PaymentGateway] = None
    is_default: bool = False
    card_last_four: Optional[str] = None
    card_brand: Optional[str] = None
    card_expiry_month: Optional[int] = Field(None, ge=1, le=12)
    card_expiry_year: Optional[int] = Field(None, ge=2024)
    bank_account_last_four: Optional[str] = None
    bank_name: Optional[str] = None
    mobile_number: Optional[str] = None
    crypto_address: Optional[str] = None
    crypto_network: Optional[str] = None
    token: Optional[str] = None


class PaymentMethodUpdate(BaseModel):
    is_default: Optional[bool] = None
    card_expiry_month: Optional[int] = Field(None, ge=1, le=12)
    card_expiry_year: Optional[int] = Field(None, ge=2024)


class PaymentMethodResponse(BaseModel):
    id: str
    user_id: str
    method_type: PaymentMethod
    gateway: Optional[PaymentGateway]
    is_default: bool
    card_last_four: Optional[str]
    card_brand: Optional[str]
    card_expiry_month: Optional[int]
    card_expiry_year: Optional[int]
    bank_account_last_four: Optional[str]
    bank_name: Optional[str]
    mobile_number: Optional[str]
    crypto_address: Optional[str]
    crypto_network: Optional[str]
    is_verified: bool
    created_at: datetime
    updated_at: datetime


class PaymentCreate(BaseModel):
    user_id: str
    property_id: str
    payment_condition_id: Optional[str] = None
    amount: float = Field(..., gt=0)
    currency: str = "USD"
    payment_method_id: str
    gateway: PaymentGateway
    description: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class PaymentResponse(BaseModel):
    id: str
    user_id: str
    property_id: str
    payment_condition_id: Optional[str]
    amount: float
    currency: str
    payment_method_id: str
    gateway: PaymentGateway
    status: PaymentStatus
    description: Optional[str]
    transaction_id: Optional[str]
    gateway_response: Optional[Dict[str, Any]]
    metadata: Optional[Dict[str, Any]]
    paid_at: Optional[datetime]
    refunded_at: Optional[datetime]
    refund_amount: float
    created_at: datetime
    updated_at: datetime


class PaymentRefundCreate(BaseModel):
    amount: float = Field(..., gt=0)
    reason: str
    refund_idempotency_key: Optional[str] = None


class PaymentRefundResponse(BaseModel):
    id: str
    payment_id: str
    amount: float
    reason: str
    status: PaymentStatus
    refund_id: Optional[str]
    gateway_response: Optional[Dict[str, Any]]
    processed_at: Optional[datetime]
    created_at: datetime


class InstallmentCreate(BaseModel):
    payment_condition_id: str
    installment_number: int
    amount: float = Field(..., gt=0)
    due_date: datetime


class InstallmentResponse(BaseModel):
    id: str
    payment_condition_id: str
    installment_number: int
    amount: float
    due_date: datetime
    paid_amount: float
    status: str
    paid_at: Optional[datetime]
    late_fee_applied: float
    discount_applied: float
    created_at: datetime
    updated_at: datetime


class InvoiceCreate(BaseModel):
    user_id: str
    property_id: str
    payment_condition_ids: List[str]
    due_date: datetime
    notes: Optional[str] = None
    tax_percentage: float = Field(0, ge=0, le=100)
    discount_percentage: float = Field(0, ge=0, le=100)


class InvoiceResponse(BaseModel):
    id: str
    user_id: str
    property_id: str
    invoice_number: str
    payment_condition_ids: List[str]
    subtotal: float
    tax_amount: float
    discount_amount: float
    total_amount: float
    paid_amount: float
    due_date: datetime
    notes: Optional[str]
    status: str
    paid_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime


class SubscriptionPlan(str, Enum):
    FREE = "free"
    BASIC = "basic"
    PROFESSIONAL = "professional"
    ENTERPRISE = "enterprise"


class SubscriptionStatus(str, Enum):
    ACTIVE = "active"
    TRIAL = "trial"
    PAST_DUE = "past_due"
    CANCELLED = "cancelled"
    EXPIRED = "expired"


class SubscriptionCreate(BaseModel):
    user_id: str
    plan: SubscriptionPlan
    payment_method_id: str
    gateway: PaymentGateway


class SubscriptionResponse(BaseModel):
    id: str
    user_id: str
    plan: SubscriptionPlan
    status: SubscriptionStatus
    payment_method_id: str
    gateway: PaymentGateway
    amount: float
    currency: str
    billing_cycle: str
    trial_end_date: Optional[datetime]
    current_period_start: datetime
    current_period_end: datetime
    cancel_at_period_end: bool
    created_at: datetime
    updated_at: datetime


class PaymentWebhookEvent(BaseModel):
    gateway: PaymentGateway
    event_type: str
    event_id: str
    data: Dict[str, Any]
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class PaymentAnalytics(BaseModel):
    total_payments: float
    successful_payments: float
    failed_payments: float
    refunded_payments: float
    average_payment_amount: float
    payment_method_breakdown: Dict[str, int]
    gateway_breakdown: Dict[str, int]
    daily_payment_trend: List[Dict[str, Any]]
    period_start: datetime
    period_end: datetime


# ========== Salary Processing Schemas ==========
class PayrollFrequency(str, Enum):
    WEEKLY = "weekly"
    BI_WEEKLY = "bi_weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    SEMI_ANNUALLY = "semi_annually"
    ANNUALLY = "annually"


class PayrollStatus(str, Enum):
    DRAFT = "draft"
    PENDING = "pending"
    PROCESSING = "processing"
    PROCESSED = "processed"
    PAID = "paid"
    FAILED = "failed"
    CANCELLED = "cancelled"


class SalaryComponentType(str, Enum):
    BASIC = "basic"
    HRA = "hra"  # House Rent Allowance
    DA = "da"  # Dearness Allowance
    TA = "ta"  # Travel Allowance
    MA = "ma"  # Medical Allowance
    BONUS = "bonus"
    OVERTIME = "overtime"
    COMMISSION = "commission"
    DEDUCTION_TAX = "deduction_tax"
    DEDUCTION_PF = "deduction_pf"  # Provident Fund
    DEDUCTION_ESI = "deduction_esi"  # Employee State Insurance
    DEDUCTION_LOAN = "deduction_loan"
    DEDUCTION_OTHER = "deduction_other"


class SalaryComponentCreate(BaseModel):
    employee_id: str
    component_type: SalaryComponentType
    name: str
    amount: float = Field(..., gt=0)
    is_percentage: bool = False
    percentage_of: Optional[str] = None
    is_taxable: bool = True
    effective_date: datetime
    expiry_date: Optional[datetime] = None


class SalaryComponentResponse(BaseModel):
    id: str
    employee_id: str
    component_type: SalaryComponentType
    name: str
    amount: float
    is_percentage: bool
    percentage_of: Optional[str]
    is_taxable: bool
    effective_date: datetime
    expiry_date: Optional[datetime]
    created_at: datetime
    updated_at: datetime


class PayrollPeriodCreate(BaseModel):
    name: str
    start_date: datetime
    end_date: datetime
    frequency: PayrollFrequency
    payment_date: datetime


class PayrollPeriodResponse(BaseModel):
    id: str
    name: str
    start_date: datetime
    end_date: datetime
    frequency: PayrollFrequency
    payment_date: datetime
    status: PayrollStatus
    total_employees: int
    total_amount: float
    created_at: datetime
    updated_at: datetime


class PayrollEntryCreate(BaseModel):
    payroll_period_id: str
    employee_id: str
    basic_salary: float = Field(..., gt=0)
    working_days: int = Field(..., ge=0)
    paid_days: int = Field(..., ge=0)
    overtime_hours: float = Field(0, ge=0)
    overtime_rate: float = Field(0, ge=0)
    deductions: Optional[Dict[str, float]] = None
    allowances: Optional[Dict[str, float]] = None
    bonuses: Optional[Dict[str, float]] = None
    notes: Optional[str] = None


class PayrollEntryResponse(BaseModel):
    id: str
    payroll_period_id: str
    employee_id: str
    employee_name: str
    employee_designation: str
    basic_salary: float
    working_days: int
    paid_days: int
    overtime_hours: float
    overtime_rate: float
    overtime_amount: float
    gross_salary: float
    total_deductions: float
    total_allowances: float
    total_bonuses: float
    net_salary: float
    tax_deduction: float
    pf_deduction: float
    esi_deduction: float
    other_deductions: float
    deductions: Dict[str, float]
    allowances: Dict[str, float]
    bonuses: Dict[str, float]
    notes: Optional[str]
    status: PayrollStatus
    payment_date: Optional[datetime]
    payment_method: Optional[str]
    transaction_id: Optional[str]
    created_at: datetime
    updated_at: datetime


class SalarySlipCreate(BaseModel):
    payroll_entry_id: str


class SalarySlipResponse(BaseModel):
    id: str
    payroll_entry_id: str
    employee_id: str
    employee_name: str
    employee_email: str
    employee_phone: str
    period_name: str
    period_start: datetime
    period_end: datetime
    payment_date: datetime
    basic_salary: float
    allowances: Dict[str, float]
    deductions: Dict[str, float]
    bonuses: Dict[str, float]
    gross_salary: float
    total_deductions: float
    net_salary: float
    employer_pf_contribution: float
    employer_esi_contribution: float
    generated_at: datetime
    slip_number: str


# ========== Commission Tracking Schemas ==========
class CommissionType(str, Enum):
    PROPERTY_SALE = "property_sale"
    PROPERTY_RENTAL = "property_rental"
    REFERRAL = "referral"
    BROKERAGE = "brokerage"
    PERFORMANCE = "performance"
    TARGET_BONUS = "target_bonus"
    BUILDER_PROPERTY = "builder_property"
    LOAN_COMMISSION = "loan_commission"
    CREDIT_CARD_CASHBACK = "credit_card_cashback"


class CommissionStatus(str, Enum):
    PENDING = "pending"
    CALCULATED = "calculated"
    APPROVED = "approved"
    PAID = "paid"
    REJECTED = "rejected"
    HELD = "held"


class CommissionRuleCreate(BaseModel):
    name: str
    commission_type: CommissionType
    base_rate: float = Field(..., ge=0, le=100)
    tier_rates: Optional[List[Dict[str, Any]]] = None  # [{"min_amount": 100000, "rate": 2.5}, ...]
    conditions: Optional[Dict[str, Any]] = None
    is_active: bool = True
    effective_date: datetime
    expiry_date: Optional[datetime] = None


class CommissionRuleResponse(BaseModel):
    id: str
    name: str
    commission_type: CommissionType
    base_rate: float
    tier_rates: List[Dict[str, Any]]
    conditions: Dict[str, Any]
    is_active: bool
    effective_date: datetime
    expiry_date: Optional[datetime]
    created_at: datetime
    updated_at: datetime


class CommissionCreate(BaseModel):
    recipient_id: str
    recipient_type: str  # employee, broker, agent
    commission_rule_id: str
    deal_id: str
    deal_type: str  # sale, rental
    deal_amount: float = Field(..., gt=0)
    calculated_amount: float = Field(..., ge=0)
    currency: str = "USD"
    due_date: datetime
    notes: Optional[str] = None


class CommissionResponse(BaseModel):
    id: str
    recipient_id: str
    recipient_type: str
    recipient_name: str
    commission_rule_id: str
    rule_name: str
    deal_id: str
    deal_type: str
    deal_amount: float
    calculated_amount: float
    currency: str
    status: CommissionStatus
    due_date: datetime
    paid_date: Optional[datetime]
    payment_method: Optional[str]
    transaction_id: Optional[str]
    notes: Optional[str]
    approved_by: Optional[str]
    approved_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime


class CommissionPayoutCreate(BaseModel):
    commission_ids: List[str]
    payment_method_id: str
    gateway: PaymentGateway
    notes: Optional[str] = None


class CommissionPayoutResponse(BaseModel):
    id: str
    commission_ids: List[str]
    total_amount: float
    currency: str
    payment_method_id: str
    gateway: PaymentGateway
    status: str
    transaction_id: Optional[str]
    notes: Optional[str]
    processed_at: Optional[datetime]
    created_at: datetime


class CommissionAnalytics(BaseModel):
    total_commissions: float
    paid_commissions: float
    pending_commissions: float
    average_commission: float
    top_performers: List[Dict[str, Any]]
    commission_by_type: Dict[str, float]
    monthly_trend: List[Dict[str, Any]]
    period_start: datetime
    period_end: datetime


# ========== Future Prediction Schemas ==========
class PredictionType(str, Enum):
    PROPERTY_VALUE = "property_value"
    MARKET_TREND = "market_trend"
    SALES_FORECAST = "sales_forecast"
    REVENUE_FORECAST = "revenue_forecast"
    DEMAND_PREDICTION = "demand_prediction"
    PRICE_PREDICTION = "price_prediction"
    RENTAL_YIELD = "rental_yield"
    INVESTMENT_RETURN = "investment_return"


class PredictionModel(str, Enum):
    LINEAR_REGRESSION = "linear_regression"
    ARIMA = "arima"
    LSTM = "lstm"
    RANDOM_FOREST = "random_forest"
    XGBOOST = "xgboost"
    PROPHET = "prophet"


class PredictionStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class PredictionRequestCreate(BaseModel):
    prediction_type: PredictionType
    model: PredictionModel = PredictionModel.LINEAR_REGRESSION
    property_id: Optional[str] = None
    location: Optional[str] = None
    historical_data_days: int = Field(365, ge=30, le=3650)
    forecast_days: int = Field(30, ge=1, le=365)
    parameters: Optional[Dict[str, Any]] = None


class PredictionRequestResponse(BaseModel):
    id: str
    prediction_type: PredictionType
    model: PredictionModel
    property_id: Optional[str]
    location: Optional[str]
    historical_data_days: int
    forecast_days: int
    parameters: Dict[str, Any]
    status: PredictionStatus
    created_at: datetime
    completed_at: Optional[datetime]


class PredictionResult(BaseModel):
    id: str
    prediction_request_id: str
    prediction_type: PredictionType
    model: PredictionModel
    property_id: Optional[str]
    location: Optional[str]
    predictions: List[Dict[str, Any]]
    confidence_interval: Optional[Dict[str, Any]]
    accuracy_score: Optional[float]
    feature_importance: Optional[Dict[str, float]]
    metadata: Optional[Dict[str, Any]]
    generated_at: datetime


class PropertyValuePrediction(BaseModel):
    property_id: str
    current_value: float
    predicted_value: float
    predicted_change_percent: float
    predicted_change_amount: float
    confidence: float
    timeframe: str  # 1 month, 3 months, 6 months, 1 year
    factors: List[Dict[str, Any]]
    generated_at: datetime


class MarketTrendPrediction(BaseModel):
    location: str
    current_trend: str  # up, down, stable
    predicted_trend: str
    market_sentiment: str
    price_change_percent: float
    volume_change_percent: float
    key_factors: List[str]
    timeframe: str
    generated_at: datetime


class SalesForecast(BaseModel):
    period: str  # monthly, quarterly, yearly
    forecast_period_start: datetime
    forecast_period_end: datetime
    predicted_sales: int
    predicted_revenue: float
    confidence_level: float
    best_case: Dict[str, float]
    worst_case: Dict[str, float]
    factors: List[Dict[str, Any]]
    generated_at: datetime


# ========== Feedback Schemas ==========
class FeedbackType(str, Enum):
    PROPERTY = "property"
    SERVICE = "service"
    BROKER = "broker"
    PLATFORM = "platform"
    TRANSACTION = "transaction"
    GENERAL = "general"


class FeedbackCategory(str, Enum):
    RATING = "rating"
    REVIEW = "review"
    COMPLAINT = "complaint"
    SUGGESTION = "suggestion"
    BUG_REPORT = "bug_report"
    FEATURE_REQUEST = "feature_request"


class FeedbackStatus(str, Enum):
    PENDING = "pending"
    REVIEWED = "reviewed"
    RESPONDED = "responded"
    RESOLVED = "resolved"
    CLOSED = "closed"


class FeedbackCreate(BaseModel):
    user_id: str
    feedback_type: FeedbackType
    category: FeedbackCategory
    rating: Optional[int] = Field(None, ge=1, le=5)
    subject: str
    message: str
    property_id: Optional[str] = None
    broker_id: Optional[str] = None
    transaction_id: Optional[str] = None
    attachments: Optional[List[str]] = None
    is_anonymous: bool = False


class FeedbackResponse(BaseModel):
    id: str
    user_id: str
    user_name: Optional[str]
    feedback_type: FeedbackType
    category: FeedbackCategory
    rating: Optional[int]
    subject: str
    message: str
    property_id: Optional[str]
    broker_id: Optional[str]
    transaction_id: Optional[str]
    attachments: List[str]
    is_anonymous: bool
    status: FeedbackStatus
    admin_response: Optional[str]
    responded_by: Optional[str]
    responded_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime


class FeedbackReplyCreate(BaseModel):
    message: str
    is_internal: bool = False


class FeedbackReplyResponse(BaseModel):
    id: str
    feedback_id: str
    user_id: str
    user_name: str
    message: str
    is_internal: bool
    created_at: datetime


class FeedbackAnalytics(BaseModel):
    total_feedback: int
    by_type: Dict[str, int]
    by_category: Dict[str, int]
    by_status: Dict[str, int]
    average_rating: float
    rating_distribution: Dict[int, int]
    response_rate: float
    average_response_time_hours: float
    period_start: datetime
    period_end: datetime


class ReviewCreate(BaseModel):
    user_id: str
    property_id: str
    broker_id: Optional[str] = None
    rating: int = Field(..., ge=1, le=5)
    title: str
    review: str
    pros: Optional[List[str]] = []
    cons: Optional[List[str]] = []
    would_recommend: bool
    images: Optional[List[str]] = []
    is_verified: bool = False


class ReviewResponse(BaseModel):
    id: str
    user_id: str
    user_name: str
    property_id: str
    property_title: str
    broker_id: Optional[str]
    broker_name: Optional[str]
    rating: int
    title: str
    review: str
    pros: List[str]
    cons: List[str]
    would_recommend: bool
    images: List[str]
    is_verified: bool
    helpful_count: int
    created_at: datetime
    updated_at: datetime


# ========== Credit Card and Reward Points Schemas ==========
class CreditCardType(str, Enum):
    CASHBACK = "cashback"
    TRAVEL = "travel"
    REWARDS = "rewards"
    AIRLINE = "airline"
    HOTEL = "hotel"
    FUEL = "fuel"
    SHOPPING = "shopping"
    DINING = "dining"
    ENTERTAINMENT = "entertainment"
    BUSINESS = "business"
    STUDENT = "student"


class CreditCardTier(str, Enum):
    BASIC = "basic"
    SILVER = "silver"
    GOLD = "gold"
    PLATINUM = "platinum"
    TITANIUM = "titanium"
    SIGNATURE = "signature"
    INFINITE = "infinite"


class RewardCategory(str, Enum):
    TRAVEL = "travel"
    DINING = "dining"
    SHOPPING = "shopping"
    FUEL = "fuel"
    GROCERY = "grocery"
    ENTERTAINMENT = "entertainment"
    UTILITIES = "utilities"
    INSURANCE = "insurance"
    EDUCATION = "education"
    HEALTHCARE = "healthcare"
    ONLINE = "online"
    INTERNATIONAL = "international"
    RENTAL = "rental"


class CreditCardCreate(BaseModel):
    user_id: str
    card_name: str
    bank_name: str
    card_type: CreditCardType
    tier: CreditCardTier
    card_number_last_4: str = Field(..., min_length=4, max_length=4)
    credit_limit: float = Field(..., gt=0)
    annual_fee: float = Field(0, ge=0)
    interest_rate: float = Field(..., ge=0, le=100)
    reward_rate: float = Field(..., ge=0, le=100)
    reward_categories: List[RewardCategory]
    welcome_bonus_points: Optional[int] = Field(0, ge=0)
    welcome_bonus_spend: Optional[float] = Field(0, ge=0)
    points_expiry_months: Optional[int] = Field(24, ge=1)
    is_active: bool = True
    phone_number: str = Field(..., min_length=10, max_length=15)
    email: str


class CreditCardApplicationCreate(BaseModel):
    user_id: str
    card_name: str
    bank_name: str
    card_type: CreditCardType
    tier: CreditCardTier
    credit_limit_requested: float = Field(..., gt=0)
    annual_income: float = Field(..., gt=0)
    employment_type: str
    employer_name: Optional[str] = None
    employment_duration_months: int = Field(0, ge=0)
    phone_number: str = Field(..., min_length=10, max_length=15)
    email: str
    pan_number: Optional[str] = None
    aadhaar_number: Optional[str] = None
    address: str
    city: str
    state: str
    pincode: str = Field(..., min_length=6, max_length=6)
    terms_accepted: bool = True


class CreditCardApplicationResponse(BaseModel):
    id: str
    user_id: str
    user_name: str
    card_name: str
    bank_name: str
    card_type: CreditCardType
    tier: CreditCardTier
    credit_limit_requested: float
    credit_limit_approved: Optional[float]
    annual_income: float
    employment_type: str
    employer_name: Optional[str]
    employment_duration_months: int
    phone_number: str
    email: str
    pan_number: Optional[str]
    address: str
    city: str
    state: str
    pincode: str
    status: str  # pending, under_review, approved, rejected
    phone_verified: bool
    email_verified: bool
    credit_score: Optional[int]
    rejection_reason: Optional[str]
    approved_by: Optional[str]
    approved_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime


class PhoneVerification(BaseModel):
    phone_number: str
    country_code: str = "+91"
    verification_method: str = "sms"  # sms, voice


class PhoneVerificationResponse(BaseModel):
    verification_id: str
    phone_number: str
    status: str
    otp_sent: bool
    expires_at: datetime
    created_at: datetime


class OTPVerification(BaseModel):
    verification_id: str
    otp: str = Field(..., min_length=6, max_length=6)


class OTPVerificationResponse(BaseModel):
    verified: bool
    phone_number: str
    verified_at: datetime


class CreditCardResponse(BaseModel):
    id: str
    user_id: str
    user_name: str
    card_name: str
    bank_name: str
    card_type: CreditCardType
    tier: CreditCardTier
    card_number_last_4: str
    credit_limit: float
    annual_fee: float
    interest_rate: float
    reward_rate: float
    reward_categories: List[RewardCategory]
    welcome_bonus_points: int
    welcome_bonus_spend: float
    points_expiry_months: int
    current_balance: float
    available_credit: float
    total_points_earned: int
    total_points_redeemed: int
    points_balance: int
    is_active: bool
    issued_date: datetime
    expiry_date: datetime
    created_at: datetime
    updated_at: datetime


class RewardTransactionType(str, Enum):
    EARNED = "earned"
    REDEEMED = "redeemed"
    EXPIRED = "expired"
    BONUS = "bonus"
    ADJUSTMENT = "adjustment"


class RewardTransactionCreate(BaseModel):
    credit_card_id: str
    transaction_type: RewardTransactionType
    points: int
    amount: float = Field(..., gt=0)
    category: Optional[RewardCategory] = None
    description: Optional[str] = None
    merchant: Optional[str] = None


class RewardTransactionResponse(BaseModel):
    id: str
    credit_card_id: str
    card_name: str
    transaction_type: RewardTransactionType
    points: int
    amount: float
    category: Optional[RewardCategory]
    description: Optional[str]
    merchant: Optional[str]
    points_value: float  # Monetary value of points
    transaction_date: datetime
    created_at: datetime


class CashbackCreate(BaseModel):
    credit_card_id: str
    amount: float = Field(..., gt=0)
    category: RewardCategory
    cashback_rate: float = Field(..., ge=0, le=100)
    description: Optional[str] = None


class CashbackResponse(BaseModel):
    id: str
    credit_card_id: str
    card_name: str
    amount: float
    category: RewardCategory
    cashback_rate: float
    points_used: int
    points_value: float
    description: Optional[str]
    status: str
    processed_date: datetime
    created_at: datetime


class CreditCardRecommendation(BaseModel):
    card_name: str
    bank_name: str
    card_type: CreditCardType
    tier: CreditCardTier
    annual_fee: float
    reward_rate: float
    reward_categories: List[RewardCategory]
    welcome_bonus_points: int
    welcome_bonus_spend: float
    match_score: float  # 0-100 based on user preferences
    estimated_annual_rewards: float
    pros: List[str]
    cons: List[str]
    best_for: List[str]


class CreditCardComparison(BaseModel):
    cards: List[CreditCardRecommendation]
    comparison_criteria: List[str]
    recommendation: str
    best_card: CreditCardRecommendation


class BestCreditCardCashback(BaseModel):
    card_name: str
    bank_name: str
    card_type: CreditCardType
    tier: CreditCardTier
    reward_rate: float
    reward_categories: List[RewardCategory]
    estimated_points: int
    estimated_cashback: float
    net_cashback_after_fee: float
    match_score: float


class PointsRedemptionCreate(BaseModel):
    credit_card_id: str
    points: int = Field(..., gt=0)
    redemption_type: str  # cashback, travel, gift_card, merchandise
    redemption_value: float = Field(..., gt=0)
    description: Optional[str] = None


class PointsRedemptionResponse(BaseModel):
    id: str
    credit_card_id: str
    card_name: str
    points_redeemed: int
    redemption_type: str
    redemption_value: float
    points_value: float  # Value per point
    description: Optional[str]
    status: str
    processed_date: datetime
    created_at: datetime


class RewardAnalytics(BaseModel):
    total_points_earned: int
    total_points_redeemed: int
    points_balance: int
    total_cashback_earned: float
    average_points_per_transaction: float
    top_spending_categories: List[Dict[str, Any]]
    monthly_trend: List[Dict[str, Any]]
    best_card_for_rewards: Optional[str]
    period_start: datetime
    period_end: datetime


# ========== Returns Tracking Schemas ==========
class ReturnPeriod(str, Enum):
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    YEARLY = "yearly"
    TOTAL = "total"


class ReturnType(str, Enum):
    COMMISSION = "commission"
    CASHBACK = "cashback"
    INVESTMENT = "investment"
    REWARD_POINTS = "reward_points"


class ReturnRecordCreate(BaseModel):
    user_id: str
    return_type: ReturnType
    period: ReturnPeriod
    period_start: datetime
    period_end: datetime
    amount: float = Field(..., ge=0)
    currency: str = "USD"
    metadata: Optional[Dict[str, Any]] = None


class ReturnRecordResponse(BaseModel):
    id: str
    user_id: str
    user_name: str
    return_type: ReturnType
    period: ReturnPeriod
    period_start: datetime
    period_end: datetime
    amount: float
    currency: str
    growth_rate: Optional[float]
    previous_period_amount: Optional[float]
    metadata: Dict[str, Any]
    created_at: datetime
    updated_at: datetime


class MonthlyReturns(BaseModel):
    month: str  # YYYY-MM
    commission_returns: float
    cashback_returns: float
    total_returns: float
    growth_rate: float
    transaction_count: int
    created_at: datetime


class QuarterlyReturns(BaseModel):
    quarter: str  # YYYY-Q1/Q2/Q3/Q4
    year: int
    quarter_number: int
    commission_returns: float
    cashback_returns: float
    total_returns: float
    growth_rate: float
    transaction_count: int
    created_at: datetime


class YearlyReturns(BaseModel):
    year: int
    commission_returns: float
    cashback_returns: float
    total_returns: float
    growth_rate: float
    transaction_count: int
    average_monthly_returns: float
    created_at: datetime


class TotalReturns(BaseModel):
    user_id: str
    user_name: str
    total_commission_returns: float
    total_cashback_returns: float
    total_investment_returns: float
    total_reward_points: int
    total_returns: float
    first_return_date: datetime
    last_return_date: datetime
    average_monthly_returns: float
    average_quarterly_returns: float
    cagr: Optional[float]  # Compound Annual Growth Rate
    created_at: datetime


class ReturnsComparison(BaseModel):
    current_period: str
    previous_period: str
    current_returns: float
    previous_returns: float
    growth_rate: float
    growth_amount: float
    trend: str  # up, down, stable


# ========== Attendance and Timing Schemas ==========
class AttendanceStatus(str, Enum):
    PRESENT = "present"
    ABSENT = "absent"
    LATE = "late"
    HALF_DAY = "half_day"
    WORK_FROM_HOME = "work_from_home"
    ON_LEAVE = "on_leave"
    HOLIDAY = "holiday"
    WEEKEND = "weekend"


class ShiftType(str, Enum):
    MORNING = "morning"
    AFTERNOON = "afternoon"
    NIGHT = "night"
    FLEXIBLE = "flexible"
    ROTATING = "rotating"


class AttendanceRecordCreate(BaseModel):
    user_id: str
    date: datetime
    check_in_time: Optional[datetime] = None
    check_out_time: Optional[datetime] = None
    status: AttendanceStatus
    shift_type: ShiftType
    work_hours: float = Field(0, ge=0)
    overtime_hours: float = Field(0, ge=0)
    notes: Optional[str] = None
    location: Optional[str] = None
    device_id: Optional[str] = None


class AttendanceRecordResponse(BaseModel):
    id: str
    user_id: str
    user_name: str
    date: datetime
    check_in_time: Optional[datetime]
    check_out_time: Optional[datetime]
    status: AttendanceStatus
    shift_type: ShiftType
    work_hours: float
    overtime_hours: float
    notes: Optional[str]
    location: Optional[str]
    device_id: Optional[str]
    created_at: datetime
    updated_at: datetime


class AttendanceSummary(BaseModel):
    user_id: str
    user_name: str
    period_start: datetime
    period_end: datetime
    total_days: int
    present_days: int
    absent_days: int
    late_days: int
    half_days: int
    work_from_home_days: int
    leave_days: int
    total_work_hours: float
    total_overtime_hours: float
    average_work_hours: float
    attendance_percentage: float


class TimingRecordCreate(BaseModel):
    user_id: str
    date: datetime
    project_id: Optional[str] = None
    task_id: Optional[str] = None
    start_time: datetime
    end_time: Optional[datetime] = None
    duration: float = Field(0, ge=0)  # in hours
    activity: str
    description: Optional[str] = None
    is_billable: bool = True


class TimingRecordResponse(BaseModel):
    id: str
    user_id: str
    user_name: str
    date: datetime
    project_id: Optional[str]
    project_name: Optional[str]
    task_id: Optional[str]
    task_name: Optional[str]
    start_time: datetime
    end_time: Optional[datetime]
    duration: float
    activity: str
    description: Optional[str]
    is_billable: bool
    created_at: datetime
    updated_at: datetime


# ========== Leave Management Schemas ==========
class LeaveType(str, Enum):
    SICK_LEAVE = "sick_leave"
    CASUAL_LEAVE = "casual_leave"
    EARNED_LEAVE = "earned_leave"
    MATERNITY_LEAVE = "maternity_leave"
    PATERNITY_LEAVE = "paternity_leave"
    COMPENSATORY_OFF = "compensatory_off"
    UNPAID_LEAVE = "unpaid_leave"
    EMERGENCY_LEAVE = "emergency_leave"
    STUDY_LEAVE = "study_leave"
    MARRIAGE_LEAVE = "marriage_leave"
    BEREAVEMENT_LEAVE = "bereavement_leave"


class LeaveStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    CANCELLED = "cancelled"
    ON_HOLD = "on_hold"


class LeaveBalance(BaseModel):
    leave_type: LeaveType
    total_allocated: int
    used: int
    balance: int
    carry_forward: int = 0
    expiry_date: Optional[datetime]


class LeaveRequestCreate(BaseModel):
    user_id: str
    leave_type: LeaveType
    start_date: datetime
    end_date: datetime
    total_days: int = Field(..., gt=0)
    reason: str
    attachment_url: Optional[str] = None
    emergency_contact: Optional[str] = None
    work_handover_to: Optional[str] = None


class LeaveRequestResponse(BaseModel):
    id: str
    user_id: str
    user_name: str
    leave_type: LeaveType
    start_date: datetime
    end_date: datetime
    total_days: int
    reason: str
    attachment_url: Optional[str]
    emergency_contact: Optional[str]
    work_handover_to: Optional[str]
    handover_person_name: Optional[str]
    status: LeaveStatus
    approved_by: Optional[str]
    approved_by_name: Optional[str]
    approved_at: Optional[datetime]
    rejection_reason: Optional[str]
    created_at: datetime
    updated_at: datetime


class LeaveApproval(BaseModel):
    leave_request_id: str
    action: str  # approve, reject, on_hold
    rejection_reason: Optional[str] = None
    notes: Optional[str] = None


class LeaveCalendar(BaseModel):
    date: datetime
    user_id: str
    user_name: str
    leave_type: LeaveType
    status: LeaveStatus
    is_half_day: bool = False


# ========== Recruitment Leave Schemas ==========
class RecruitmentLeaveType(str, Enum):
    INTERVIEW_LEAVE = "interview_leave"
    TRAINING_LEAVE = "training_leave"
    ONBOARDING_LEAVE = "onboarding_leave"
    PROBATION_LEAVE = "probation_leave"
    ASSESSMENT_LEAVE = "assessment_leave"


class RecruitmentLeaveCreate(BaseModel):
    candidate_id: str
    candidate_name: str
    leave_type: RecruitmentLeaveType
    start_date: datetime
    end_date: datetime
    total_hours: float = Field(..., gt=0)
    purpose: str
    recruiter_id: str
    interviewer_id: Optional[str] = None
    location: Optional[str] = None
    notes: Optional[str] = None


class RecruitmentLeaveResponse(BaseModel):
    id: str
    candidate_id: str
    candidate_name: str
    leave_type: RecruitmentLeaveType
    start_date: datetime
    end_date: datetime
    total_hours: float
    purpose: str
    recruiter_id: str
    recruiter_name: str
    interviewer_id: Optional[str]
    interviewer_name: Optional[str]
    location: Optional[str]
    notes: Optional[str]
    status: str
    created_at: datetime
    updated_at: datetime


class RecruitmentLeaveSchedule(BaseModel):
    date: datetime
    candidate_id: str
    candidate_name: str
    leave_type: RecruitmentLeaveType
    start_time: datetime
    end_time: datetime
    location: Optional[str]
    recruiter_id: str
    interviewer_id: Optional[str]


# ========== Leave Application Portal Schemas ==========
class LeaveApplication(BaseModel):
    user_id: str
    leave_type: LeaveType
    start_date: datetime
    end_date: datetime
    total_days: int
    reason: str
    attachment_url: Optional[str]
    emergency_contact: Optional[str]
    work_handover_to: Optional[str]
    submission_date: datetime
    portal_status: str  # draft, submitted, under_review, approved, rejected


class LeaveApplicationResponse(BaseModel):
    id: str
    application: LeaveApplication
    leave_request_id: Optional[str]
    current_balance: int
    approval_workflow: List[Dict[str, Any]]
    notifications_sent: List[str]
    created_at: datetime
    updated_at: datetime


class LeavePolicy(BaseModel):
    leave_type: LeaveType
    days_per_year: int
    accrual_rate: str  # monthly, quarterly, yearly
    max_accumulation: int
    carry_forward_allowed: bool
    carry_forward_limit: int
    requires_approval: bool
    approval_levels: List[str]
    documentation_required: bool
    advance_notice_days: int
    description: str


class LeaveAnalytics(BaseModel):
    user_id: str
    user_name: str
    period_start: datetime
    period_end: datetime
    total_leaves_taken: int
    leaves_by_type: Dict[str, int]
    leave_balance: Dict[str, int]
    rejection_rate: float
    average_leave_duration: float
    peak_leave_months: List[str]
    created_at: datetime


# ========== Loan Application Schemas ==========
class LoanApplicationStatus(str, Enum):
    DRAFT = "draft"
    SUBMITTED = "submitted"
    UNDER_REVIEW = "under_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    DISBURSED = "disbursed"
    CLOSED = "closed"


class LoanType(str, Enum):
    HOME_LOAN = "home_loan"
    PERSONAL_LOAN = "personal_loan"
    CAR_LOAN = "car_loan"
    EDUCATION_LOAN = "education_loan"
    BUSINESS_LOAN = "business_loan"
    PROPERTY_LOAN = "property_loan"


class LoanApplicationCreate(BaseModel):
    user_id: str
    loan_type: LoanType
    property_id: Optional[str] = None
    loan_amount: float = Field(..., gt=0)
    loan_term_months: int = Field(..., gt=0)
    interest_rate: float = Field(..., ge=0, le=100)
    purpose: str
    income: float = Field(..., gt=0)
    employment_type: str
    employer_name: Optional[str] = None
    employment_duration_months: int = Field(0, ge=0)
    existing_loans: float = Field(0, ge=0)
    collateral_type: Optional[str] = None
    collateral_value: Optional[float] = Field(None, ge=0)
    documents: List[str] = []
    co_applicant_id: Optional[str] = None


class LoanApplicationResponse(BaseModel):
    id: str
    user_id: str
    user_name: str
    loan_type: LoanType
    property_id: Optional[str]
    property_title: Optional[str]
    loan_amount: float
    loan_term_months: int
    interest_rate: float
    emi: float
    total_payable: float
    purpose: str
    income: float
    employment_type: str
    employer_name: Optional[str]
    employment_duration_months: int
    existing_loans: float
    collateral_type: Optional[str]
    collateral_value: Optional[float]
    documents: List[str]
    co_applicant_id: Optional[str]
    co_applicant_name: Optional[str]
    status: LoanApplicationStatus
    credit_score: Optional[int]
    approval_amount: Optional[float]
    rejection_reason: Optional[str]
    approved_by: Optional[str]
    approved_by_name: Optional[str]
    approved_at: Optional[datetime]
    disbursed_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime


class LoanApproval(BaseModel):
    loan_application_id: str
    action: str  # approve, reject
    approval_amount: Optional[float] = None
    interest_rate: Optional[float] = None
    rejection_reason: Optional[str] = None
    notes: Optional[str] = None


class LoanDisbursement(BaseModel):
    loan_application_id: str
    disbursement_amount: float
    disbursement_method: str  # bank_transfer, check
    bank_account_number: str
    ifsc_code: str
    notes: Optional[str] = None


class LoanEligibility(BaseModel):
    user_id: str
    eligible: bool
    max_loan_amount: float
    max_interest_rate: float
    max_term_months: int
    credit_score: Optional[int]
    debt_to_income_ratio: float
    factors: List[Dict[str, Any]]
    created_at: datetime


# ========== Interview Schemas ==========
class InterviewStatus(str, Enum):
    SCHEDULED = "scheduled"
    INVITED = "invited"
    CONFIRMED = "confirmed"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    RESCHEDULED = "rescheduled"
    NO_SHOW = "no_show"
    SELECTED = "selected"
    REJECTED = "rejected"


class InterviewType(str, Enum):
    SCREENING = "screening"
    TECHNICAL = "technical"
    BEHAVIORAL = "behavioral"
    PANEL = "panel"
    FINAL = "final"
    HR_ROUND = "hr_round"
    MANAGER_ROUND = "manager_round"


class InterviewMode(str, Enum):
    IN_PERSON = "in_person"
    VIDEO_CALL = "video_call"
    PHONE_CALL = "phone_call"
    ONLINE_ASSESSMENT = "online_assessment"


class InterviewRound(str, Enum):
    ROUND_1 = "round_1"
    ROUND_2 = "round_2"
    ROUND_3 = "round_3"
    FINAL_ROUND = "final_round"


class InterviewScheduleCreate(BaseModel):
    job_application_id: str
    job_posting_id: str
    candidate_id: str
    candidate_name: str
    candidate_email: str
    candidate_phone: str
    interviewer_id: str
    interviewer_name: str
    interviewer_email: str
    interview_type: InterviewType
    interview_mode: InterviewMode
    interview_round: InterviewRound
    scheduled_date: datetime
    scheduled_time: str  # HH:MM format
    duration_minutes: int = Field(..., gt=0, le=180)
    location: Optional[str] = None
    meeting_link: Optional[str] = None
    meeting_id: Optional[str] = None
    meeting_password: Optional[str] = None
    notes: Optional[str] = None
    skills_to_assess: List[str] = []
    interview_questions: List[str] = []


class InterviewScheduleResponse(BaseModel):
    id: str
    job_application_id: str
    job_posting_id: str
    job_title: str
    candidate_id: str
    candidate_name: str
    candidate_email: str
    candidate_phone: str
    interviewer_id: str
    interviewer_name: str
    interviewer_email: str
    interview_type: InterviewType
    interview_mode: InterviewMode
    interview_round: InterviewRound
    scheduled_date: datetime
    scheduled_time: str
    duration_minutes: int
    location: Optional[str]
    meeting_link: Optional[str]
    meeting_id: Optional[str]
    meeting_password: Optional[str]
    notes: Optional[str]
    skills_to_assess: List[str]
    interview_questions: List[str]
    status: InterviewStatus
    invitation_sent: bool
    invitation_sent_at: Optional[datetime]
    reminder_sent: bool
    reminder_sent_at: Optional[datetime]
    feedback: Optional[str]
    rating: Optional[int] = Field(None, ge=1, le=5)
    selected: bool = False
    created_at: datetime
    updated_at: datetime


class InterviewInvitationCreate(BaseModel):
    interview_id: str
    candidate_id: str
    candidate_name: str
    candidate_email: str
    candidate_phone: str
    interviewer_name: str
    interviewer_email: str
    job_title: str
    company_name: str
    interview_date: datetime
    interview_time: str
    interview_mode: InterviewMode
    location: Optional[str] = None
    meeting_link: Optional[str] = None
    meeting_id: Optional[str] = None
    meeting_password: Optional[str] = None
    duration_minutes: int
    notes: Optional[str] = None


class InterviewInvitationResponse(BaseModel):
    id: str
    interview_id: str
    candidate_id: str
    candidate_name: str
    candidate_email: str
    candidate_phone: str
    interviewer_name: str
    interviewer_email: str
    job_title: str
    company_name: str
    interview_date: datetime
    interview_time: str
    interview_mode: InterviewMode
    location: Optional[str]
    meeting_link: Optional[str]
    meeting_id: Optional[str]
    meeting_password: Optional[str]
    duration_minutes: int
    notes: Optional[str]
    status: str  # sent, delivered, opened, accepted, declined
    sent_at: datetime
    delivered_at: Optional[datetime]
    opened_at: Optional[datetime]
    responded_at: Optional[datetime]


class InterviewFeedbackCreate(BaseModel):
    interview_id: str
    interviewer_id: str
    interviewer_name: str
    candidate_id: str
    candidate_name: str
    rating: int = Field(..., ge=1, le=5)
    technical_score: Optional[int] = Field(None, ge=0, le=100)
    communication_score: Optional[int] = Field(None, ge=0, le=100)
    problem_solving_score: Optional[int] = Field(None, ge=0, le=100)
    cultural_fit_score: Optional[int] = Field(None, ge=0, le=100)
    strengths: List[str] = []
    weaknesses: List[str] = []
    comments: str
    recommendation: str  # hire, reject, on_hold, next_round
    next_round_recommended: bool = False
    salary_expectation: Optional[float] = None
    availability: Optional[str] = None


class InterviewFeedbackResponse(BaseModel):
    id: str
    interview_id: str
    interviewer_id: str
    interviewer_name: str
    candidate_id: str
    candidate_name: str
    rating: int
    technical_score: Optional[int]
    communication_score: Optional[int]
    problem_solving_score: Optional[int]
    cultural_fit_score: Optional[int]
    strengths: List[str]
    weaknesses: List[str]
    comments: str
    recommendation: str
    next_round_recommended: bool
    salary_expectation: Optional[float]
    availability: Optional[str]
    created_at: datetime
    updated_at: datetime


class InterviewProcessStep(BaseModel):
    step_id: str
    step_name: str
    step_type: str  # screening, technical, behavioral, final
    order: int
    duration_minutes: int
    required: bool = True
    auto_advance: bool = False
    pass_threshold: Optional[int] = None


class InterviewWorkflowCreate(BaseModel):
    job_posting_id: str
    workflow_name: str
    steps: List[InterviewProcessStep]
    is_active: bool = True


class InterviewWorkflowResponse(BaseModel):
    id: str
    job_posting_id: str
    workflow_name: str
    steps: List[InterviewProcessStep]
    is_active: bool
    created_at: datetime
    updated_at: datetime


class InterviewTimingLogic(BaseModel):
    interview_id: str
    buffer_time_minutes: int = 15
    max_interviews_per_day: int = 6
    working_hours_start: str = "09:00"
    working_hours_end: str = "18:00"
    break_hours: List[Dict[str, str]] = []  # [{"start": "12:00", "end": "13:00"}]
    timezone: str = "Asia/Kolkata"
    weekend_days: List[int] = [6, 7]  # Saturday, Sunday


# ========== Investment Notification Schemas ==========
class NotificationChannel(str, Enum):
    EMAIL = "email"
    WHATSAPP = "whatsapp"
    SMS = "sms"
    PUSH = "push"


class NotificationStatus(str, Enum):
    PENDING = "pending"
    SENT = "sent"
    FAILED = "failed"
    DELIVERED = "delivered"
    READ = "read"


class InvestmentNotificationCreate(BaseModel):
    user_id: str
    investment_id: str
    investment_type: str
    amount: float
    property_name: str
    property_image: Optional[str] = None
    property_size: Optional[float] = None
    property_location: Optional[str] = None
    investor_name: str
    investor_email: str
    investor_phone: str
    channels: List[NotificationChannel] = [NotificationChannel.EMAIL, NotificationChannel.WHATSAPP]
    additional_details: Optional[Dict[str, Any]] = None


class InvestmentNotificationResponse(BaseModel):
    id: str
    user_id: str
    investment_id: str
    investment_type: str
    amount: float
    property_name: str
    property_image: Optional[str]
    property_size: Optional[float]
    property_location: Optional[str]
    investor_name: str
    investor_email: str
    investor_phone: str
    channels: List[NotificationChannel]
    email_status: NotificationStatus
    whatsapp_status: NotificationStatus
    sms_status: Optional[NotificationStatus] = None
    push_status: Optional[NotificationStatus] = None
    email_sent_at: Optional[datetime]
    whatsapp_sent_at: Optional[datetime]
    sms_sent_at: Optional[datetime]
    push_sent_at: Optional[datetime]
    error_message: Optional[str]
    created_at: datetime
    updated_at: datetime


class EmailTemplate(BaseModel):
    template_name: str
    subject: str
    body: str
    variables: Dict[str, Any]


class WhatsAppMessage(BaseModel):
    phone_number: str
    message: str
    media_url: Optional[str] = None
    template_name: Optional[str] = None


class WhatsAppMessageResponse(BaseModel):
    message_id: str
    phone_number: str
    status: str
    sent_at: datetime
    error_message: Optional[str]


# ========== RBI Compliance and Fraud Detection Schemas ==========
class FraudRiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class TransactionStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    BLOCKED = "blocked"
    FLAGGED = "flagged"
    UNDER_REVIEW = "under_review"


class KYCStatus(str, Enum):
    NOT_STARTED = "not_started"
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    VERIFIED = "verified"
    REJECTED = "rejected"
    EXPIRED = "expired"


class FraudDetectionRule(BaseModel):
    rule_id: str
    rule_name: str
    rule_type: str  # amount_threshold, velocity_check, geo_anomaly, device_anomaly
    threshold_value: Optional[float] = None
    time_window_minutes: Optional[int] = None
    is_active: bool = True
    severity: FraudRiskLevel


class FraudAlertCreate(BaseModel):
    transaction_id: str
    user_id: str
    risk_level: FraudRiskLevel
    rule_triggered: str
    risk_factors: List[str]
    transaction_amount: float
    transaction_currency: str
    ip_address: Optional[str] = None
    device_id: Optional[str] = None
    location: Optional[str] = None
    additional_details: Optional[Dict[str, Any]] = None


class FraudAlertResponse(BaseModel):
    id: str
    transaction_id: str
    user_id: str
    user_name: str
    risk_level: FraudRiskLevel
    rule_triggered: str
    risk_factors: List[str]
    transaction_amount: float
    transaction_currency: str
    ip_address: Optional[str]
    device_id: Optional[str]
    location: Optional[str]
    status: str  # open, investigating, resolved, false_positive
    action_taken: Optional[str] = None
    resolved_by: Optional[str] = None
    resolved_at: Optional[datetime]
    additional_details: Optional[Dict[str, Any]]
    created_at: datetime
    updated_at: datetime


class TransactionMonitoringLog(BaseModel):
    transaction_id: str
    user_id: str
    transaction_amount: float
    transaction_type: str
    payment_method: str
    merchant_id: Optional[str] = None
    ip_address: Optional[str] = None
    device_fingerprint: Optional[str] = None
    geolocation: Optional[Dict[str, Any]] = None
    risk_score: float = 0.0
    risk_level: FraudRiskLevel = FraudRiskLevel.LOW
    status: TransactionStatus
    blocked: bool = False
    block_reason: Optional[str] = None
    additional_checks_performed: List[str] = []
    created_at: datetime


class KYCDocumentType(str, Enum):
    PAN_CARD = "pan_card"
    AADHAAR_CARD = "aadhaar_card"
    PASSPORT = "passport"
    DRIVING_LICENSE = "driving_license"
    VOTER_ID = "voter_id"
    BANK_STATEMENT = "bank_statement"


class KYCVerificationCreate(BaseModel):
    user_id: str
    document_type: KYCDocumentType
    document_number: str
    document_image_url: str
    selfie_image_url: Optional[str] = None
    date_of_birth: Optional[datetime] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    pincode: Optional[str] = None


class KYCVerificationResponse(BaseModel):
    id: str
    user_id: str
    user_name: str
    document_type: KYCDocumentType
    document_number: str
    document_image_url: str
    selfie_image_url: Optional[str]
    status: KYCStatus
    verification_score: Optional[float] = None
    verified_by: Optional[str] = None
    verified_at: Optional[datetime]
    rejection_reason: Optional[str] = None
    expiry_date: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime


class TransactionLimitCheck(BaseModel):
    user_id: str
    transaction_amount: float
    transaction_type: str
    daily_total: float
    monthly_total: float
    within_limits: bool
    limit_type: Optional[str] = None  # transaction, daily, monthly
    remaining_limit: Optional[float] = None
    kyc_required: bool
    pan_required: bool
    two_factor_required: bool


class SecurePaymentRequest(BaseModel):
    user_id: str
    amount: float
    currency: str = "INR"
    payment_method: str
    merchant_id: Optional[str] = None
    description: str
    ip_address: Optional[str] = None
    device_fingerprint: Optional[str] = None
    geolocation: Optional[Dict[str, Any]] = None
    pan_number: Optional[str] = None
    aadhaar_number: Optional[str] = None
    two_factor_otp: Optional[str] = None


class SecurePaymentResponse(BaseModel):
    transaction_id: str
    status: TransactionStatus
    amount: float
    currency: str
    risk_score: float


# ========== Image Upload Schemas ==========
class ImageCategory(str, Enum):
    PROPERTY = "property"
    PROFILE = "profile"
    DOCUMENT = "document"
    BROKER = "broker"
    GENERAL = "general"


class ImageUploadResponse(BaseModel):
    id: str
    url: str
    thumbnail_url: Optional[str] = None
    medium_url: Optional[str] = None
    original_filename: str
    file_size: int
    width: int
    height: int
    format: str
    category: ImageCategory
    uploaded_by: str
    created_at: datetime


class ImageUploadRequest(BaseModel):
    category: ImageCategory = ImageCategory.PROPERTY
    property_id: Optional[str] = None
    user_id: Optional[str] = None
    alt_text: Optional[str] = None


class BatchImageUploadResponse(BaseModel):
    successful: List[ImageUploadResponse]
    failed: List[Dict[str, Any]]
    total_uploaded: int
    total_failed: int


class ImageDeleteResponse(BaseModel):
    success: bool
    message: str
    image_id: str


class ImageRenderRequest(BaseModel):
    image_id: str
    width: Optional[int] = None
    height: Optional[int] = None
    quality: int = Field(85, ge=1, le=100)
    format: str = "webp"


class ImageOptimizationSettings(BaseModel):
    max_width: int = 1920
    max_height: int = 1080
    thumbnail_width: int = 150
    thumbnail_height: int = 150
    medium_width: int = 800
    medium_height: int = 600
    quality: int = 85
    thumbnail_quality: int = 70
    medium_quality: int = 80
    enable_webp: bool = True
    enable_avif: bool = False
    max_file_size_mb: float = 10.0
    allowed_formats: List[str] = ["jpg", "jpeg", "png", "webp", "gif"]


class ImageStats(BaseModel):
    total_images: int
    total_size_bytes: int
    by_category: Dict[str, int]
    recent_uploads: List[ImageUploadResponse]


# ========== Reimbursement Schemas ==========

class ReimbursementCategory(str, Enum):
    TRAVEL = "travel"
    ACCOMMODATION = "accommodation"
    MEALS = "meals"
    EQUIPMENT = "equipment"
    MEDICAL = "medical"
    TRAINING = "training"
    COMMUNICATION = "communication"
    OTHER = "other"


class ReimbursementStatus(str, Enum):
    DRAFT = "draft"
    SUBMITTED = "submitted"
    UNDER_REVIEW = "under_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    PAID = "paid"


class ReimbursementCreate(BaseModel):
    employee_id: str
    category: ReimbursementCategory
    title: str
    description: Optional[str] = None
    amount: float = Field(..., gt=0)
    expense_date: datetime
    receipt_urls: Optional[List[str]] = []
    notes: Optional[str] = None


class ReimbursementResponse(BaseModel):
    id: str
    employee_id: str
    employee_name: str
    category: ReimbursementCategory
    title: str
    description: Optional[str]
    amount: float
    approved_amount: Optional[float]
    expense_date: datetime
    receipt_urls: List[str]
    status: ReimbursementStatus
    submitted_at: Optional[datetime]
    reviewed_by: Optional[str]
    reviewed_at: Optional[datetime]
    rejection_reason: Optional[str]
    paid_at: Optional[datetime]
    payroll_period_id: Optional[str]
    notes: Optional[str]
    created_at: datetime
    updated_at: datetime


class ReimbursementReview(BaseModel):
    approved_amount: Optional[float] = None
    rejection_reason: Optional[str] = None


class ReimbursementAnalytics(BaseModel):
    total_submitted: float
    total_approved: float
    total_paid: float
    total_pending: float
    by_category: Dict[str, float]
    by_status: Dict[str, int]
    average_processing_days: float


# ========== Claims Schemas ==========

class ClaimType(str, Enum):
    MEDICAL = "medical"
    ACCIDENT = "accident"
    LIFE_INSURANCE = "life_insurance"
    PROPERTY_DAMAGE = "property_damage"
    TRAVEL_INSURANCE = "travel_insurance"
    COMMISSION_DISPUTE = "commission_dispute"
    SALARY_DISPUTE = "salary_dispute"
    OTHER = "other"


class ClaimStatus(str, Enum):
    OPEN = "open"
    UNDER_INVESTIGATION = "under_investigation"
    APPROVED = "approved"
    PARTIALLY_APPROVED = "partially_approved"
    REJECTED = "rejected"
    CLOSED = "closed"


class ClaimPriority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class ClaimCreate(BaseModel):
    employee_id: str
    claim_type: ClaimType
    title: str
    description: str
    claimed_amount: float = Field(..., gt=0)
    incident_date: datetime
    priority: ClaimPriority = ClaimPriority.MEDIUM
    supporting_docs: Optional[List[str]] = []
    related_commission_id: Optional[str] = None
    related_payroll_id: Optional[str] = None


class ClaimResponse(BaseModel):
    id: str
    employee_id: str
    employee_name: str
    claim_type: ClaimType
    title: str
    description: str
    claimed_amount: float
    approved_amount: Optional[float]
    incident_date: datetime
    priority: ClaimPriority
    status: ClaimStatus
    supporting_docs: List[str]
    related_commission_id: Optional[str]
    related_payroll_id: Optional[str]
    assigned_to: Optional[str]
    resolution_notes: Optional[str]
    resolved_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime


class ClaimResolution(BaseModel):
    approved_amount: Optional[float] = None
    resolution_notes: str
    status: ClaimStatus


class ClaimAnalytics(BaseModel):
    total_claims: int
    open_claims: int
    approved_claims: int
    rejected_claims: int
    total_claimed_amount: float
    total_approved_amount: float
    by_type: Dict[str, int]
    by_priority: Dict[str, int]
    average_resolution_days: float


# ========== Tax Schemas ==========

class TaxRegime(str, Enum):
    OLD = "old"
    NEW = "new"


class TaxSlabCreate(BaseModel):
    regime: TaxRegime
    min_income: float = Field(..., ge=0)
    max_income: Optional[float] = None
    rate: float = Field(..., ge=0, le=100)
    surcharge_rate: float = Field(0, ge=0, le=100)
    cess_rate: float = Field(4.0, ge=0, le=100)
    financial_year: str


class TaxSlabResponse(BaseModel):
    id: str
    regime: TaxRegime
    min_income: float
    max_income: Optional[float]
    rate: float
    surcharge_rate: float
    cess_rate: float
    financial_year: str
    created_at: datetime


class TaxComputationRequest(BaseModel):
    employee_id: str
    financial_year: str
    regime: TaxRegime = TaxRegime.NEW
    gross_annual_income: float = Field(..., gt=0)
    hra_exemption: float = Field(0, ge=0)
    section_80c: float = Field(0, ge=0)
    section_80d: float = Field(0, ge=0)
    section_80ccd: float = Field(0, ge=0)
    other_deductions: float = Field(0, ge=0)
    tds_already_deducted: float = Field(0, ge=0)


class TaxComputationResponse(BaseModel):
    employee_id: str
    financial_year: str
    regime: TaxRegime
    gross_annual_income: float
    total_exemptions: float
    taxable_income: float
    basic_tax: float
    surcharge: float
    cess: float
    total_tax_liability: float
    tds_already_deducted: float
    balance_tax_payable: float
    monthly_tds: float
    effective_tax_rate: float
    computed_at: datetime


class Form16Summary(BaseModel):
    employee_id: str
    employee_name: str
    employee_pan: Optional[str]
    financial_year: str
    employer_name: str
    gross_salary: float
    exempt_allowances: float
    net_salary: float
    deductions_80c: float
    deductions_80d: float
    other_deductions: float
    taxable_income: float
    total_tax: float
    tds_deducted: float
    balance_payable: float
    generated_at: datetime


# ========== Onboarding & Offboarding Schemas ==========

class OnboardingStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    DOCUMENTS_SUBMITTED = "documents_submitted"
    VERIFICATION_PENDING = "verification_pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class OffboardingStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    ASSETS_RETURNED = "assets_returned"
    CLEARANCE_PENDING = "clearance_pending"
    APPROVED = "approved"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class EPFOStatus(str, Enum):
    NOT_REGISTERED = "not_registered"
    REGISTERED = "registered"
    ACTIVE = "active"
    INACTIVE = "inactive"
    WITHDRAWN = "withdrawn"
    TRANSFERRED = "transferred"


class EPFODetails(BaseModel):
    uan_number: Optional[str] = None
    pf_account_number: Optional[str] = None
    establishment_id: Optional[str] = None
    epfo_office: Optional[str] = None
    date_of_joining: Optional[datetime] = None
    date_of_exit: Optional[datetime] = None
    pf_contribution_rate: float = 12.0
    pension_contribution_rate: float = 8.33
    status: EPFOStatus = EPFOStatus.NOT_REGISTERED
    nomination_details: Optional[Dict[str, Any]] = None


class ESIDetails(BaseModel):
    esi_number: Optional[str] = None
    establishment_id: Optional[str] = None
    esi_office: Optional[str] = None
    date_of_joining: Optional[datetime] = None
    date_of_exit: Optional[datetime] = None
    esi_contribution_rate: float = 1.0
    status: EPFOStatus = EPFOStatus.NOT_REGISTERED
    ip_number: Optional[str] = None


class BankAccountDetails(BaseModel):
    account_number: str
    bank_name: str
    branch_name: str
    ifsc_code: str
    account_type: str = "savings"
    is_primary: bool = True


class DocumentType(str, Enum):
    AADHAR_CARD = "aadhar_card"
    PAN_CARD = "pan_card"
    PASSPORT = "passport"
    DRIVING_LICENSE = "driving_license"
    VOTER_ID = "voter_id"
    EDUCATION_CERTIFICATE = "education_certificate"
    EXPERIENCE_CERTIFICATE = "experience_certificate"
    RELIEVING_LETTER = "relieving_letter"
    SALARY_SLIP = "salary_slip"
    PHOTOGRAPH = "photograph"
    ADDRESS_PROOF = "address_proof"
    OTHER = "other"


class DocumentSubmission(BaseModel):
    document_type: DocumentType
    document_url: str
    submitted_at: datetime = Field(default_factory=datetime.utcnow)
    verified: bool = False
    verified_by: Optional[str] = None
    verified_at: Optional[datetime] = None
    rejection_reason: Optional[str] = None


class OnboardingChecklist(BaseModel):
    task_name: str
    description: Optional[str] = None
    completed: bool = False
    completed_at: Optional[datetime] = None
    completed_by: Optional[str] = None
    due_date: Optional[datetime] = None


class EmployeeOnboardingCreate(BaseModel):
    employee_id: str
    employee_name: str
    email: str
    phone_number: str
    designation: str
    department: str
    reporting_manager_id: Optional[str] = None
    date_of_joining: datetime
    employment_type: str = "full_time"
    work_location: str
    salary_offered: float
    epfo_details: Optional[EPFODetails] = None
    esi_details: Optional[ESIDetails] = None
    bank_account: BankAccountDetails
    documents: List[DocumentSubmission] = []
    checklist: List[OnboardingChecklist] = []
    notes: Optional[str] = None


class EmployeeOnboardingUpdate(BaseModel):
    status: Optional[OnboardingStatus] = None
    reporting_manager_id: Optional[str] = None
    epfo_details: Optional[EPFODetails] = None
    esi_details: Optional[ESIDetails] = None
    bank_account: Optional[BankAccountDetails] = None
    documents: Optional[List[DocumentSubmission]] = None
    checklist: Optional[List[OnboardingChecklist]] = None
    notes: Optional[str] = None
    rejection_reason: Optional[str] = None


class EmployeeOnboardingResponse(BaseModel):
    id: str
    employee_id: str
    employee_name: str
    email: str
    phone_number: str
    designation: str
    department: str
    reporting_manager_id: Optional[str] = None
    reporting_manager_name: Optional[str] = None
    date_of_joining: datetime
    employment_type: str
    work_location: str
    salary_offered: float
    epfo_details: Optional[EPFODetails] = None
    esi_details: Optional[ESIDetails] = None
    bank_account: BankAccountDetails
    documents: List[DocumentSubmission] = []
    checklist: List[OnboardingChecklist] = []
    status: OnboardingStatus
    notes: Optional[str] = None
    rejection_reason: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime] = None


class EmployeeOffboardingCreate(BaseModel):
    employee_id: str
    employee_name: str
    email: str
    phone_number: str
    designation: str
    department: str
    date_of_resignation: datetime
    last_working_day: datetime
    reason_for_leaving: str
    exit_type: str = "resignation"
    is_eligible_rehire: bool = True
    handover_to: Optional[str] = None
    settlement_amount: Optional[float] = None
    pending_leaves: int = 0
    encashable_leaves: int = 0
    assets_to_return: List[str] = []
    clearance_checklist: List[OnboardingChecklist] = []
    notes: Optional[str] = None


class EmployeeOffboardingUpdate(BaseModel):
    status: Optional[OffboardingStatus] = None
    last_working_day: Optional[datetime] = None
    reason_for_leaving: Optional[str] = None
    is_eligible_rehire: Optional[bool] = None
    handover_to: Optional[str] = None
    settlement_amount: Optional[float] = None
    assets_to_return: Optional[List[str]] = None
    clearance_checklist: Optional[List[OnboardingChecklist]] = None
    notes: Optional[str] = None
    rejection_reason: Optional[str] = None


class EmployeeOffboardingResponse(BaseModel):
    id: str
    employee_id: str
    employee_name: str
    email: str
    phone_number: str
    designation: str
    department: str
    date_of_resignation: datetime
    last_working_day: datetime
    reason_for_leaving: str
    exit_type: str
    is_eligible_rehire: bool
    handover_to: Optional[str] = None
    handover_to_name: Optional[str] = None
    settlement_amount: Optional[float] = None
    pending_leaves: int
    encashable_leaves: int
    assets_to_return: List[str] = []
    clearance_checklist: List[OnboardingChecklist] = []
    status: OffboardingStatus
    notes: Optional[str] = None
    rejection_reason: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime] = None


class OnboardingAnalytics(BaseModel):
    total_onboardings: int
    pending_onboardings: int
    in_progress_onboardings: int
    completed_onboardings: int
    rejected_onboardings: int
    average_onboarding_days: float
    by_department: Dict[str, int]
    by_status: Dict[str, int]
    monthly_trend: List[Dict[str, Any]]


class OffboardingAnalytics(BaseModel):
    total_offboardings: int
    pending_offboardings: int
    in_progress_offboardings: int
    completed_offboardings: int
    average_tenure_days: float
    attrition_rate: float
    by_department: Dict[str, int]
    by_reason: Dict[str, int]
    by_exit_type: Dict[str, int]
    monthly_trend: List[Dict[str, Any]]


# ========== Easy Property Onboarding Schemas ==========

class PropertyOnboardingSource(str, Enum):
    MANUAL = "manual"
    URL_IMPORT = "url_import"
    TEXT_IMPORT = "text_import"
    BULK_UPLOAD = "bulk_upload"


class PropertyOnboardingStatus(str, Enum):
    DRAFT = "draft"
    PENDING_REVIEW = "pending_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    PUBLISHED = "published"
    ARCHIVED = "archived"


class QuickPropertyCreate(BaseModel):
    """Simplified property creation for easy onboarding"""
    title: str
    property_type: PropertyType
    city: str
    state: str
    price: float
    area: float
    area_unit: str = "sq_ft"
    bedrooms: Optional[int] = None
    bathrooms: Optional[int] = None
    description: Optional[str] = None
    source_url: Optional[str] = None
    source_site: Optional[str] = None
    images: List[str] = []
    contact_name: str
    contact_phone: str
    contact_email: EmailStr
    is_builder_property: bool = False
    builder_name: Optional[str] = None
    amenities: List[str] = []
    notes: Optional[str] = None


class URLPropertyImport(BaseModel):
    """Import property from external URL"""
    url: str
    site: str = "magicbricks"
    contact_name: str
    contact_phone: str
    contact_email: EmailStr
    override_data: Optional[Dict[str, Any]] = None


class TextPropertyImport(BaseModel):
    """Extract property from text description"""
    text: str
    city: str = "Mumbai"
    contact_name: str
    contact_phone: str
    contact_email: EmailStr
    override_data: Optional[Dict[str, Any]] = None


class BulkPropertyImport(BaseModel):
    """Bulk import properties from CSV/JSON data"""
    properties: List[Dict[str, Any]]
    source: PropertyOnboardingSource = PropertyOnboardingSource.BULK_UPLOAD


class PropertyOnboardingUpdate(BaseModel):
    """Update onboarding property"""
    status: Optional[PropertyOnboardingStatus] = None
    rejection_reason: Optional[str] = None
    review_notes: Optional[str] = None
    published_at: Optional[datetime] = None


class PropertyOnboardingResponse(BaseModel):
    """Response for property onboarding"""
    id: str
    original_property_id: Optional[str] = None
    source: PropertyOnboardingSource
    status: PropertyOnboardingStatus
    property_data: Dict[str, Any]
    scraped_data: Optional[Dict[str, Any]] = None
    extracted_data: Optional[Dict[str, Any]] = None
    price_comparison: Optional[Dict[str, Any]] = None
    contact_name: str
    contact_phone: str
    contact_email: str
    submitted_by: str
    reviewed_by: Optional[str] = None
    rejection_reason: Optional[str] = None
    review_notes: Optional[str] = None
    published_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime


class PropertyOnboardingAnalytics(BaseModel):
    """Analytics for property onboarding"""
    total_onboardings: int
    by_source: Dict[str, int]
    by_status: Dict[str, int]
    by_property_type: Dict[str, int]
    by_city: Dict[str, int]
    average_processing_time_hours: float
    auto_published_count: int
    manual_review_count: int
    monthly_trend: List[Dict[str, Any]]


# ========== Whiteboard Schemas ==========

class WhiteboardItemType(str, Enum):
    """Types of whiteboard items"""
    TEXT = "text"
    SHAPE = "shape"
    IMAGE = "image"
    DRAWING = "drawing"
    NOTE = "note"
    STICKER = "sticker"
    ARROW = "arrow"
    LINE = "line"


class WhiteboardPermission(str, Enum):
    """Whiteboard sharing permissions"""
    VIEW = "view"
    EDIT = "edit"
    ADMIN = "admin"


class WhiteboardItemCreate(BaseModel):
    """Schema for creating a whiteboard item"""
    item_type: WhiteboardItemType
    x: float
    y: float
    width: Optional[float] = None
    height: Optional[float] = None
    content: Optional[str] = None
    color: Optional[str] = "#000000"
    background_color: Optional[str] = "#ffffff"
    font_size: Optional[int] = 14
    rotation: Optional[float] = 0
    z_index: Optional[int] = 0
    metadata: Optional[Dict[str, Any]] = None


class WhiteboardItemUpdate(BaseModel):
    """Schema for updating a whiteboard item"""
    x: Optional[float] = None
    y: Optional[float] = None
    width: Optional[float] = None
    height: Optional[float] = None
    content: Optional[str] = None
    color: Optional[str] = None
    background_color: Optional[str] = None
    font_size: Optional[int] = None
    rotation: Optional[float] = None
    z_index: Optional[int] = None
    metadata: Optional[Dict[str, Any]] = None


class WhiteboardItemResponse(BaseModel):
    """Schema for whiteboard item response"""
    id: str
    item_type: WhiteboardItemType
    x: float
    y: float
    width: Optional[float] = None
    height: Optional[float] = None
    content: Optional[str] = None
    color: Optional[str] = None
    background_color: Optional[str] = None
    font_size: Optional[int] = None
    rotation: Optional[float] = None
    z_index: Optional[int] = None
    metadata: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: datetime


class WhiteboardCreate(BaseModel):
    """Schema for creating a whiteboard"""
    title: str
    description: Optional[str] = None
    background_color: Optional[str] = "#ffffff"
    grid_enabled: Optional[bool] = True
    is_public: Optional[bool] = False
    tags: Optional[List[str]] = []


class WhiteboardUpdate(BaseModel):
    """Schema for updating a whiteboard"""
    title: Optional[str] = None
    description: Optional[str] = None
    background_color: Optional[str] = None
    grid_enabled: Optional[bool] = None
    is_public: Optional[bool] = None
    tags: Optional[List[str]] = None


class WhiteboardResponse(BaseModel):
    """Schema for whiteboard response"""
    id: str
    title: str
    description: Optional[str] = None
    background_color: str
    grid_enabled: bool
    is_public: bool
    tags: List[str]
    owner_id: str
    items: List[WhiteboardItemResponse] = []
    created_at: datetime
    updated_at: datetime


class WhiteboardShareCreate(BaseModel):
    """Schema for sharing a whiteboard"""
    user_id: str
    permission: WhiteboardPermission = WhiteboardPermission.VIEW


class WhiteboardShareResponse(BaseModel):
    """Schema for whiteboard share response"""
    id: str
    whiteboard_id: str
    user_id: str
    permission: WhiteboardPermission
    shared_by: str
    created_at: datetime


class WhiteboardListResponse(BaseModel):
    """Schema for whiteboard list response"""
    id: str
    title: str
    description: Optional[str] = None
    is_public: bool
    owner_id: str
    owner_name: Optional[str] = None
    item_count: int
    created_at: datetime
    updated_at: datetime


# ========== Enhanced Analytics Schemas ==========

class PropertyAnalytics(BaseModel):
    """Property analytics schema"""
    total_properties: int
    active_properties: int
    sold_properties: int
    pending_properties: int
    by_type: Dict[str, int]
    by_city: Dict[str, int]
    by_price_range: Dict[str, int]
    average_price: float
    median_price: float
    price_trend: List[Dict[str, Any]]
    monthly_listings: List[Dict[str, Any]]
    top_cities: List[Dict[str, Any]]
    conversion_rate: float
    average_days_to_sell: float


class UserAnalytics(BaseModel):
    """User analytics schema"""
    total_users: int
    active_users: int
    new_users_this_month: int
    by_role: Dict[str, int]
    by_city: Dict[str, Any]
    user_growth_trend: List[Dict[str, Any]]
    active_sessions: int
    average_session_duration: float


class RevenueAnalytics(BaseModel):
    """Revenue analytics schema"""
    total_revenue: float
    revenue_this_month: float
    revenue_this_quarter: float
    revenue_this_year: float
    by_source: Dict[str, float]
    by_payment_method: Dict[str, float]
    monthly_revenue_trend: List[Dict[str, Any]]
    average_transaction_value: float
    growth_rate: float


class CommissionAnalytics(BaseModel):
    """Commission analytics schema"""
    total_commissions: float
    pending_commissions: float
    paid_commissions: float
    by_recipient: List[Dict[str, Any]]
    by_type: Dict[str, float]
    monthly_commission_trend: List[Dict[str, Any]]
    top_performers: List[Dict[str, Any]]
    average_commission: float


class InquiryAnalytics(BaseModel):
    """Inquiry analytics schema"""
    total_inquiries: int
    inquiries_this_month: int
    response_rate: float
    average_response_time_hours: float
    by_status: Dict[str, int]
    by_property: List[Dict[str, Any]]
    conversion_to_sale: float
    monthly_inquiry_trend: List[Dict[str, Any]]


class DashboardAnalytics(BaseModel):
    """Combined dashboard analytics"""
    property_analytics: PropertyAnalytics
    user_analytics: UserAnalytics
    revenue_analytics: RevenueAnalytics
    commission_analytics: CommissionAnalytics
    inquiry_analytics: InquiryAnalytics
    generated_at: datetime


# ========== Sales & Investment Schemas ==========

class SaleType(str, Enum):
    PROPERTY_SALE = "property_sale"
    RENTAL = "rental"
    COMMERCIAL = "commercial"
    LAND = "land"


class SalesRecordCreate(BaseModel):
    property_id: str
    seller_id: str
    buyer_id: Optional[str] = None
    sale_type: SaleType = SaleType.PROPERTY_SALE
    sale_price: float = Field(..., gt=0)
    original_listing_price: float = Field(..., gt=0)
    commission_amount: float = 0
    broker_id: Optional[str] = None
    broker_commission: float = 0
    sale_date: Optional[datetime] = None
    closing_date: Optional[datetime] = None
    payment_method: Optional[str] = None
    financing_details: Optional[Dict[str, Any]] = None
    notes: Optional[str] = None


class SalesRecordUpdate(BaseModel):
    sale_price: Optional[float] = None
    status: Optional[str] = None
    closing_date: Optional[datetime] = None
    notes: Optional[str] = None


class SalesRecordResponse(BaseModel):
    id: str
    property_id: str
    seller_id: str
    buyer_id: Optional[str]
    sale_type: SaleType
    sale_price: float
    original_listing_price: float
    commission_amount: float
    broker_id: Optional[str]
    broker_commission: float
    sale_date: datetime
    closing_date: Optional[datetime]
    payment_method: Optional[str]
    financing_details: Optional[Dict[str, Any]]
    status: str
    notes: Optional[str]
    created_at: datetime
    updated_at: datetime


class SalesSummary(BaseModel):
    total_sales: int
    total_sales_value: float
    total_commission: float
    average_sale_price: float
    sales_by_type: Dict[str, int]
    sales_by_month: List[Dict[str, Any]]
    top_performing_brokers: List[Dict[str, Any]]
    conversion_rate: float


class ProjectionType(str, Enum):
    SALES = "sales"
    REVENUE = "revenue"
    GROWTH = "growth"
    MARKET_TREND = "market_trend"
    AI_FORECAST = "ai_forecast"


class ProjectionCreate(BaseModel):
    projection_type: ProjectionType
    title: str
    description: Optional[str] = None
    period_start: datetime
    period_end: datetime
    location_filter: Optional[str] = None
    property_type_filter: Optional[str] = None
    projected_value: float
    confidence_level: float = Field(0.8, ge=0.0, le=1.0)
    methodology: str
    data_points_used: int
    historical_data_range: Optional[str] = None
    breakdown_by_month: Optional[List[Dict[str, Any]]] = None
    assumptions: Optional[Dict[str, Any]] = None


class ProjectionResponse(BaseModel):
    id: str
    projection_type: ProjectionType
    title: str
    description: Optional[str]
    period_start: datetime
    period_end: datetime
    location_filter: Optional[str]
    property_type_filter: Optional[str]
    projected_value: float
    confidence_level: float
    methodology: str
    data_points_used: int
    historical_data_range: Optional[str]
    breakdown_by_month: List[Dict[str, Any]]
    assumptions: Optional[Dict[str, Any]]
    created_by: str
    created_at: datetime
    updated_at: datetime


class FutureGrowthCreate(BaseModel):
    title: str
    location: str
    growth_rate_projected: float
    time_horizon_years: int = Field(..., ge=1, le=50)
    property_value_change: float
    rental_yield_change: float
    demand_index: float = Field(..., ge=0, le=100)
    supply_index: float = Field(..., ge=0, le=100)
    infrastructure_developments: Optional[List[str]] = None
    economic_indicators: Optional[Dict[str, Any]] = None
    population_growth: float
    ai_confidence_score: float = 0.0
    risk_factors: Optional[List[str]] = None
    opportunities: Optional[List[str]] = None


class FutureGrowthResponse(BaseModel):
    id: str
    title: str
    location: str
    growth_rate_projected: float
    time_horizon_years: int
    property_value_change: float
    rental_yield_change: float
    demand_index: float
    supply_index: float
    infrastructure_developments: List[str]
    economic_indicators: Optional[Dict[str, Any]]
    population_growth: float
    ai_confidence_score: float
    risk_factors: List[str]
    opportunities: List[str]
    created_at: datetime
    updated_at: datetime


class FutureProjectCreate(BaseModel):
    project_name: str
    developer_name: str
    location: str
    city: str
    state: str
    project_type: PropertyType
    total_units: int = Field(..., gt=0)
    unit_types: Optional[List[str]] = None
    price_range_min: float = Field(..., gt=0)
    price_range_max: float = Field(..., gt=0)
    launch_date: Optional[datetime] = None
    completion_date: Optional[datetime] = None
    construction_status: str = "pre_launch"
    amenities: Optional[List[str]] = None
    description: Optional[str] = None
    contact_info: Optional[Dict[str, Any]] = None
    expected_roi: Optional[float] = None


class FutureProjectUpdate(BaseModel):
    project_name: Optional[str] = None
    construction_status: Optional[str] = None
    price_range_min: Optional[float] = None
    price_range_max: Optional[float] = None
    launch_date: Optional[datetime] = None
    completion_date: Optional[datetime] = None
    expected_roi: Optional[float] = None
    is_featured: Optional[bool] = None
    is_verified: Optional[bool] = None


class FutureProjectResponse(BaseModel):
    id: str
    project_name: str
    developer_name: str
    location: str
    city: str
    state: str
    project_type: PropertyType
    total_units: int
    unit_types: List[str]
    price_range_min: float
    price_range_max: float
    launch_date: Optional[datetime]
    completion_date: Optional[datetime]
    construction_status: str
    amenities: List[str]
    description: Optional[str]
    contact_info: Optional[Dict[str, Any]]
    expected_roi: Optional[float]
    is_verified: bool
    is_featured: bool
    created_by: Optional[str]
    created_at: datetime
    updated_at: datetime


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


class InvestmentOpportunityCreate(BaseModel):
    title: str
    description: str
    investment_type: InvestmentType
    location: str
    city: str
    state: str
    minimum_investment: float = Field(..., gt=0)
    expected_roi_annual: float = Field(..., gt=0)
    investment_term_months: int = Field(..., gt=0)
    risk_level: RiskLevel = RiskLevel.MODERATE
    property_id: Optional[str] = None
    project_id: Optional[str] = None
    total_funding_needed: Optional[float] = None
    documents: Optional[List[str]] = None
    highlights: Optional[List[str]] = None
    market_analysis: Optional[Dict[str, Any]] = None
    financial_projections: Optional[Dict[str, Any]] = None
    closing_date: Optional[datetime] = None


class InvestmentOpportunityUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    minimum_investment: Optional[float] = None
    expected_roi_annual: Optional[float] = None
    status: Optional[str] = None
    funding_raised: Optional[float] = None
    investors_count: Optional[int] = None
    closing_date: Optional[datetime] = None


class InvestmentOpportunityResponse(BaseModel):
    id: str
    title: str
    description: str
    investment_type: InvestmentType
    location: str
    city: str
    state: str
    minimum_investment: float
    expected_roi_annual: float
    investment_term_months: int
    risk_level: RiskLevel
    property_id: Optional[str]
    project_id: Optional[str]
    total_funding_needed: Optional[float]
    funding_raised: float
    investors_count: int
    documents: List[str]
    highlights: List[str]
    market_analysis: Optional[Dict[str, Any]]
    financial_projections: Optional[Dict[str, Any]]
    status: str
    closing_date: Optional[datetime]
    created_by: str
    created_at: datetime
    updated_at: datetime


class AIProjectionRequest(BaseModel):
    location: str
    property_type: Optional[str] = None
    time_horizon_months: int = Field(12, ge=1, le=60)
    include_market_factors: bool = True
    include_economic_indicators: bool = True


class AIProjectionResponse(BaseModel):
    location: str
    projected_price_change: float
    projected_rental_yield: float
    confidence_score: float
    market_trend: str
    growth_drivers: List[str]
    risk_factors: List[str]
    monthly_projections: List[Dict[str, Any]]
    generated_at: datetime


class InvestmentSummary(BaseModel):
    total_opportunities: int
    total_funding_needed: float
    total_funding_raised: float
    by_investment_type: Dict[str, int]
    by_risk_level: Dict[str, int]
    top_opportunities: List[Dict[str, Any]]
    average_roi: float

