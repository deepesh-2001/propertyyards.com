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

