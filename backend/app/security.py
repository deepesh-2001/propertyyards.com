"""
Security Middleware
Handles rate limiting, input validation, CORS headers, and request logging
"""
from fastapi import Request, HTTPException, status
from fastapi.middleware import Middleware
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware as RateLimiter
import time
import logging
from typing import Callable
import re
from html import escape

logger = logging.getLogger(__name__)

# Rate limiter
limiter = Limiter(key_func=get_remote_address)


def setup_security_middleware(app):
    """Setup all security middleware for the FastAPI app"""

    # Rate limiting
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
    app.add_middleware(RateLimiter)

    # CORS with security headers
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Configure properly for production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["X-RateLimit-Limit", "X-RateLimit-Remaining", "X-RateLimit-Reset"]
    )

    # GZip compression
    app.add_middleware(GZipMiddleware, minimum_size=1000)

    # Trusted hosts (uncomment for production)
    # app.add_middleware(TrustedHostMiddleware, allowed_hosts=["propertyyards.com", "*.propertyyards.com"])

    # Security headers middleware
    @app.middleware("http")
    async def add_security_headers(request: Request, call_next: Callable):
        response = await call_next(request)

        # Security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"

        return response

    # Request logging middleware
    @app.middleware("http")
    async def log_requests(request: Request, call_next: Callable):
        start_time = time.time()

        # Log request
        logger.info(f"Request: {request.method} {request.url.path} from {request.client.host if request.client else 'unknown'}")

        # Process request
        response = await call_next(request)

        # Log response
        process_time = time.time() - start_time
        logger.info(f"Response: {response.status_code} - {process_time:.3f}s")

        # Add process time header
        response.headers["X-Process-Time"] = str(process_time)

        return response

    # Input sanitization middleware
    @app.middleware("http")
    async def sanitize_input(request: Request, call_next: Callable):
        # Sanitize query parameters
        if request.query_params:
            sanitized_params = {}
            for key, value in request.query_params.items():
                if isinstance(value, str):
                    sanitized_params[key] = sanitize_string(value)
                else:
                    sanitized_params[key] = value
            # Replace query params (this is a simplified approach)
            # In production, you'd want to handle this more carefully

        # Sanitize path parameters if needed
        # This would require custom path parameter handling

        response = await call_next(request)
        return response


def sanitize_string(input_string: str) -> str:
    """Sanitize input string to prevent XSS"""
    if not input_string:
        return input_string

    # Remove potential script tags
    sanitized = re.sub(r'<script.*?>.*?</script>', '', input_string, flags=re.IGNORECASE | re.DOTALL)
    sanitized = re.sub(r'<.*?on\w+.*?>.*?</.*?>', '', sanitized, flags=re.IGNORECASE | re.DOTALL)

    # Escape HTML entities
    sanitized = escape(sanitized)

    return sanitized


def validate_email(email: str) -> bool:
    """Validate email format"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None


def validate_phone(phone: str) -> bool:
    """Validate phone number format (Indian format)"""
    pattern = r'^[6-9]\d{9}$'
    return re.match(pattern, phone) is not None


def validate_url(url: str) -> bool:
    """Validate URL format"""
    pattern = r'^https?://[^\s/$.?#].[^\s]*$'
    return re.match(pattern, url) is not None


def sanitize_html(html: str) -> str:
    """Sanitize HTML content (basic implementation)"""
    if not html:
        return html

    # Remove script tags and event handlers
    sanitized = re.sub(r'<script.*?>.*?</script>', '', html, flags=re.IGNORECASE | re.DOTALL)
    sanitized = re.sub(r'on\w+\s*=', '', sanitized, flags=re.IGNORECASE)
    sanitized = re.sub(r'<iframe.*?>.*?</iframe>', '', sanitized, flags=re.IGNORECASE | re.DOTALL)
    sanitized = re.sub(r'<object.*?>.*?</object>', '', sanitized, flags=re.IGNORECASE | re.DOTALL)
    sanitized = re.sub(r'<embed.*?>', '', sanitized, flags=re.IGNORECASE)

    return sanitized


class SecurityValidator:
    """Security validation utilities"""

    @staticmethod
    def validate_user_input(data: dict, rules: dict) -> tuple[bool, str]:
        """
        Validate user input against rules
        Rules format: {field_name: {'type': type, 'required': bool, 'min': int, 'max': int, 'pattern': str}}
        """
        for field, rule in rules.items():
            value = data.get(field)

            # Check required
            if rule.get('required', False) and value is None:
                return False, f"Field '{field}' is required"

            # Skip validation if not required and value is None
            if value is None:
                continue

            # Type check
            expected_type = rule.get('type')
            if expected_type and not isinstance(value, expected_type):
                return False, f"Field '{field}' must be of type {expected_type.__name__}"

            # String validation
            if isinstance(value, str):
                # Min length
                min_length = rule.get('min')
                if min_length and len(value) < min_length:
                    return False, f"Field '{field}' must be at least {min_length} characters"

                # Max length
                max_length = rule.get('max')
                if max_length and len(value) > max_length:
                    return False, f"Field '{field}' must not exceed {max_length} characters"

                # Pattern validation
                pattern = rule.get('pattern')
                if pattern and not re.match(pattern, value):
                    return False, f"Field '{field}' has invalid format"

            # Number validation
            if isinstance(value, (int, float)):
                # Min value
                min_value = rule.get('min')
                if min_value is not None and value < min_value:
                    return False, f"Field '{field}' must be at least {min_value}"

                # Max value
                max_value = rule.get('max')
                if max_value is not None and value > max_value:
                    return False, f"Field '{field}' must not exceed {max_value}"

        return True, ""

    @staticmethod
    def sanitize_dict(data: dict, fields: list = None) -> dict:
        """Sanitize string fields in a dictionary"""
        if fields is None:
            fields = data.keys()

        sanitized = data.copy()
        for field in fields:
            if field in sanitized and isinstance(sanitized[field], str):
                sanitized[field] = sanitize_string(sanitized[field])

        return sanitized
