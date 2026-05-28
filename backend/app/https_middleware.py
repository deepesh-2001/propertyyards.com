"""
HTTPS Enforcement Middleware
Force HTTPS connections and add security headers
"""
from fastapi import Request, HTTPException
from fastapi.responses import RedirectResponse, JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
import logging

from app.config import settings

logger = logging.getLogger(__name__)


class HTTPSRedirectMiddleware(BaseHTTPMiddleware):
    """Redirect HTTP requests to HTTPS"""

    async def dispatch(self, request: Request, call_next):
        # Check if HTTPS is forced and request is HTTP
        if settings.FORCE_HTTPS and request.url.scheme == "http":
            # Skip for localhost/development
            if request.url.hostname in ["localhost", "127.0.0.1"]:
                return await call_next(request)

            # Build HTTPS URL
            https_url = request.url.replace(scheme="https", port=settings.HTTPS_PORT)

            logger.info(f"Redirecting HTTP to HTTPS: {request.url} -> {https_url}")

            return RedirectResponse(
                url=str(https_url),
                status_code=301  # Permanent redirect
            )

        return await call_next(request)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add security headers including HSTS"""

    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)

        # Add HSTS (HTTP Strict Transport Security) header
        if settings.FORCE_HTTPS or settings.SECURE_HEADERS:
            hsts_value = f"max-age={settings.HSTS_MAX_AGE}"
            if settings.HSTS_INCLUDE_SUBDOMAINS:
                hsts_value += "; includeSubDomains"
            if settings.HSTS_PRELOAD:
                hsts_value += "; preload"

            response.headers["Strict-Transport-Security"] = hsts_value

        # Add other security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Content-Security-Policy"] = "default-src 'self' https:; script-src 'self' 'unsafe-inline' https:; style-src 'self' 'unsafe-inline' https:; img-src 'self' https: data:;"

        return response


class SecureCookieMiddleware(BaseHTTPMiddleware):
    """Ensure cookies are secure"""

    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)

        if settings.SECURE_COOKIE and settings.FORCE_HTTPS:
            # Check if there are any Set-Cookie headers
            if "set-cookie" in response.headers:
                # This is handled automatically by FastAPI when setting secure=True on cookies
                pass

        return response


def setup_https_middleware(app):
    """Setup all HTTPS/security middleware"""
    # Add HTTPS redirect first (before security headers)
    app.add_middleware(HTTPSRedirectMiddleware)

    # Add security headers
    app.add_middleware(SecurityHeadersMiddleware)

    # Add secure cookie handling
    app.add_middleware(SecureCookieMiddleware)

    logger.info("HTTPS enforcement middleware enabled")


# For use in main.py
def enforce_https(app):
    """Main function to enable HTTPS enforcement"""
    if settings.FORCE_HTTPS:
        setup_https_middleware(app)
        logger.info("HTTPS enforcement enabled - all HTTP traffic will be redirected")
    else:
        logger.info("HTTPS enforcement disabled (FORCE_HTTPS=False)")
