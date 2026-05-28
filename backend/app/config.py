 the"""
Environment configuration
"""
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "mongodb://localhost:27017/housing_db"
    DATABASE_ECHO: bool = False

    # Redis
    REDIS_URL: str = "redis://localhost:6379"
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

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()

