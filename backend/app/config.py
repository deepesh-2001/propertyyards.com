"""
Environment configuration with validation
"""
from pydantic_settings import BaseSettings
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "mongodb://localhost:27017/housing_db"
    READ_REPLICA_URL: Optional[str] = None
    DATABASE_ECHO: bool = False
    MAX_DB_CONNECTIONS: int = 100
    MIN_DB_CONNECTIONS: int = 10
    CONNECTION_POOL_RECYCLE: int = 3600
    CONNECTION_POOL_TIMEOUT: int = 30

    # Redis
    REDIS_URL: str = "redis://localhost:6379"
    REDIS_PASSWORD: Optional[str] = None
    CACHE_TTL: int = 3600  # 1 hour

    # Firecrawl
    FIRECRAWL_API_KEY: str = ""

    # JWT
    JWT_SECRET_KEY: str = "your-secret-key-change-in-production"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # API
    API_TITLE: str = "Housing Platform API"
    API_VERSION: str = "1.0.0"
    API_DESCRIPTION: str = "Real estate management system"
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000

    # CORS
    CORS_ORIGINS: list = ["https://propertyyards.com", "http://localhost:5173", "http://localhost:3000"]
    CORS_CREDENTIALS: bool = True
    CORS_METHODS: list = ["*"]
    CORS_HEADERS: list = ["*"]

    # App
    DEBUG: bool = False
    ENVIRONMENT: str = "development"

    # Pagination
    DEFAULT_PAGE_SIZE: int = 20
    MAX_PAGE_SIZE: int = 100

    # Contact Information
    COMPANY_NAME: str = "PropertyYards"
    CONTACT_PHONE: str = "+1-800-PROPERTY"
    CONTACT_EMAIL: str = "contact@propertyyards.com"
    CONTACT_ADDRESS: str = "123 Real Estate Ave"
    CONTACT_CITY: str = "New York"
    CONTACT_STATE: str = "NY"
    CONTACT_ZIP: str = "10001"
    CONTACT_COUNTRY: str = "USA"
    CONTACT_WEBSITE: str = "https://propertyyards.com"
    SUPPORT_HOURS: str = "Mon-Fri 9:00 AM - 6:00 PM EST"
    EMERGENCY_CONTACT: str = "+1-800-EMERGENCY"

    # WhatsApp Configuration
    WHATSAPP_API_KEY: str = ""
    WHATSAPP_PHONE_NUMBER_ID: str = ""
    WHATSAPP_API_VERSION: str = "v18.0"
    WHATSAPP_WEBHOOK_VERIFY_TOKEN: str = "propertyyards_webhook_token"

    # Email Configuration
    SMTP_SERVER: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USERNAME: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_USE_TLS: bool = True
    EMAIL_FROM: str = "noreply@propertyyards.com"
    EMAIL_FROM_NAME: str = "PropertyYards"

    # SendGrid Configuration (optional)
    SENDGRID_API_KEY: str = ""

    # Mailgun Configuration (optional)
    MAILGUN_API_KEY: str = ""
    MAILGUN_DOMAIN: str = ""

    # Stripe Configuration
    STRIPE_SECRET_KEY: str = ""
    STRIPE_PUBLISHABLE_KEY: str = ""
    STRIPE_WEBHOOK_SECRET: str = ""
    STRIPE_API_VERSION: str = "2023-10-16"

    # PayPal Configuration
    PAYPAL_CLIENT_ID: str = ""
    PAYPAL_CLIENT_SECRET: str = ""
    PAYPAL_WEBHOOK_ID: str = ""
    PAYPAL_MODE: str = "sandbox"  # sandbox or live

    # Razorpay Configuration
    RAZORPAY_KEY_ID: str = ""
    RAZORPAY_KEY_SECRET: str = ""
    RAZORPAY_WEBHOOK_SECRET: str = ""

    # PayU Configuration
    PAYU_MERCHANT_KEY: str = ""
    PAYU_MERCHANT_SALT: str = ""
    PAYU_TEST_MODE: bool = True

    # Square Configuration
    SQUARE_ACCESS_TOKEN: str = ""
    SQUARE_APPLICATION_ID: str = ""
    SQUARE_LOCATION_ID: str = ""
    SQUARE_WEBHOOK_SIGNATURE_KEY: str = ""

    # Braintree Configuration
    BRAINTREE_MERCHANT_ID: str = ""
    BRAINTREE_PUBLIC_KEY: str = ""
    BRAINTREE_PRIVATE_KEY: str = ""

    # Mollie Configuration
    MOLLIE_API_KEY: str = ""
    MOLLIE_WEBHOOK_SECRET: str = ""

    # Payment Settings
    DEFAULT_CURRENCY: str = "USD"
    DEFAULT_PAYMENT_GATEWAY: str = "stripe"
    PAYMENT_TIMEOUT_MINUTES: int = 30
    REFUND_WINDOW_DAYS: int = 30
    AUTO_CAPTURE_PAYMENT: bool = True

    # Auto-scaling Configuration
    ENABLE_AUTO_SCALING: bool = True
    MIN_WORKERS: int = 4
    MAX_WORKERS: int = 50
    SCALE_UP_THRESHOLD: float = 0.6
    SCALE_DOWN_THRESHOLD: float = 0.2
    SCALE_UP_COOLDOWN: int = 60
    SCALE_DOWN_COOLDOWN: int = 300
    TARGET_CPU_PERCENTAGE: float = 70.0
    TARGET_MEMORY_PERCENTAGE: float = 80.0
    REQUEST_QUEUE_THRESHOLD: int = 500

    # Performance Optimization for High Throughput (10,000 QPM)
    ENABLE_QUERY_OPTIMIZATION: bool = True
    ENABLE_INDEX_OPTIMIZATION: bool = True
    ENABLE_CONNECTION_POOLING: bool = True
    MAX_DB_CONNECTIONS: int = 500
    MIN_DB_CONNECTIONS: int = 50
    CONNECTION_POOL_TIMEOUT: int = 30
    CONNECTION_POOL_MAX_OVERFLOW: int = 100
    CONNECTION_POOL_RECYCLE: int = 3600
    CONNECTION_POOL_PRE_PING: bool = True

    # Rate Limiting for High Throughput
    ENABLE_RATE_LIMITING: bool = True
    RATE_LIMIT_REQUESTS: int = 1000
    RATE_LIMIT_PERIOD: int = 60
    RATE_LIMIT_BURST: int = 100
    RATE_LIMIT_PER_USER: int = 100
    RATE_LIMIT_PER_USER_PERIOD: int = 60

    # RBI Compliance Configuration
    RBI_COMPLIANCE_ENABLED: bool = True
    MAX_TRANSACTION_AMOUNT: float = 200000.0  # INR 2 lakhs per transaction
    MAX_DAILY_TRANSACTION_AMOUNT: float = 1000000.0  # INR 10 lakhs per day
    MAX_MONTHLY_TRANSACTION_AMOUNT: float = 5000000.0  # INR 50 lakhs per month
    TRANSACTION_MONITORING_ENABLED: bool = True
    FRAUD_DETECTION_ENABLED: bool = True
    TWO_FACTOR_AUTHENTICATION_REQUIRED: bool = True
    TRANSACTION_LIMIT_FOR_KYC: float = 50000.0  # KYC required above INR 50k
    PAN_REQUIRED_ABOVE_AMOUNT: float = 50000.0  # PAN required above INR 50k
    AADHAAR_VERIFICATION_ENABLED: bool = True
    TRANSACTION_LOG_RETENTION_DAYS: int = 365
    ALERT_SUSPICIOUS_TRANSACTIONS: bool = True
    AUTO_BLOCK_SUSPICIOUS_ACCOUNTS: bool = True
    MERCHANT_CATEGORY_CODE_RESTRICTIONS: bool = True
    GEOLOCATION_VERIFICATION: bool = True
    DEVICE_FINGERPRINTING: bool = True
    IP_WHITELIST_ENABLED: bool = False

    # Image Upload Configuration
    IMAGE_STORAGE_TYPE: str = "local"  # local, s3, cloudinary
    IMAGE_UPLOAD_DIR: str = "uploads/images"
    IMAGE_MAX_FILE_SIZE_MB: float = 10.0
    IMAGE_ALLOWED_FORMATS: list = ["jpg", "jpeg", "png", "webp", "gif"]
    IMAGE_MAX_WIDTH: int = 1920
    IMAGE_MAX_HEIGHT: int = 1080
    IMAGE_THUMBNAIL_WIDTH: int = 150
    IMAGE_THUMBNAIL_HEIGHT: int = 150
    IMAGE_MEDIUM_WIDTH: int = 800
    IMAGE_MEDIUM_HEIGHT: int = 600
    IMAGE_QUALITY: int = 85
    IMAGE_THUMBNAIL_QUALITY: int = 70
    IMAGE_MEDIUM_QUALITY: int = 80
    IMAGE_ENABLE_WEBP: bool = True
    IMAGE_ENABLE_AVIF: bool = False
    IMAGE_CACHE_TTL: int = 86400  # 24 hours
    IMAGE_CDN_URL: str = ""
    
    # AWS S3 Configuration
    AWS_ACCESS_KEY_ID: str = ""
    AWS_SECRET_ACCESS_KEY: str = ""
    AWS_REGION: str = "us-east-1"
    AWS_S3_BUCKET: str = ""
    AWS_S3_BUCKET_PREFIX: str = "images/"
    
    # Cloudinary Configuration
    CLOUDINARY_CLOUD_NAME: str = ""
    CLOUDINARY_API_KEY: str = ""
    CLOUDINARY_API_SECRET: str = ""
    CLOUDINARY_UPLOAD_FOLDER: str = "housing_platform"

    # OpenAI Configuration (AI Image Generation)
    OPENAI_API_KEY: str = ""
    OPENAI_IMAGE_MODEL: str = "dall-e-3"

    # Telegram Bot Configuration
    TELEGRAM_BOT_TOKEN: str = ""
    TELEGRAM_WEBHOOK_URL: str = ""

    # Social Media API Keys
    FACEBOOK_ACCESS_TOKEN: str = ""
    FACEBOOK_PAGE_ID: str = ""
    INSTAGRAM_ACCESS_TOKEN: str = ""
    TWITTER_API_KEY: str = ""
    TWITTER_API_SECRET: str = ""
    LINKEDIN_ACCESS_TOKEN: str = ""

    # News Service Configuration
    NEWS_AUTHOR_NAME: str = "PropertyYards Editorial Team"
    AUTO_PUBLISH_NEWS: bool = False
    NEWS_FETCH_INTERVAL_HOURS: int = 6

    class Config:
        env_file = ".env"
        case_sensitive = True

    def validate_settings(self):
        """Validate critical settings"""
        errors = []

        # Validate JWT secret
        if self.JWT_SECRET_KEY == "your-secret-key-change-in-production" and self.ENVIRONMENT == "production":
            errors.append("JWT_SECRET_KEY must be changed in production")

        # Validate database URL
        if not self.DATABASE_URL:
            errors.append("DATABASE_URL is required")

        # Validate Redis URL
        if not self.REDIS_URL:
            errors.append("REDIS_URL is required")

        # Validate environment
        if self.ENVIRONMENT not in ["development", "staging", "production"]:
            errors.append("ENVIRONMENT must be one of: development, staging, production")

        # Validate connection pool settings
        if self.MIN_DB_CONNECTIONS >= self.MAX_DB_CONNECTIONS:
            errors.append("MIN_DB_CONNECTIONS must be less than MAX_DB_CONNECTIONS")

        if errors:
            for error in errors:
                logger.error(f"Configuration error: {error}")
            raise ValueError(f"Configuration validation failed: {'; '.join(errors)}")

        logger.info("Configuration validation passed")


settings = Settings()

# Validate settings on import
try:
    settings.validate_settings()
except Exception as e:
    logger.warning(f"Settings validation warning: {e}")

