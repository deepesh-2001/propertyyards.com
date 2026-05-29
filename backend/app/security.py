"""
Security Middleware
Handles rate limiting, input validation, CORS headers, request logging,
ETag generation and Cache-Control response headers.
Enhanced with IP whitelisting, request size limits, and threat detection.
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
import hashlib
import logging
from typing import Callable, Set, Dict
import re
from html import escape
from collections import defaultdict, deque
import json

logger = logging.getLogger(__name__)

# Rate limiter
limiter = Limiter(key_func=get_remote_address)

# Enhanced security tracking
class ThreatDetector:
    """Advanced threat detection system"""
    
    def __init__(self):
        # Track suspicious IPs
        self.suspicious_ips: Dict[str, Dict] = defaultdict(lambda: {
            "requests": deque(maxlen=1000),
            "failed_attempts": 0,
            "blocked_until": None,
            "threat_score": 0
        })
        
        # Common attack patterns
        self.sql_injection_patterns = [
            r'(\%27)|(\')|(\-\-)|(\%23)|(#)',
            r'((\%3D)|(=))[^\n]*((\%27)|(\')|(\-\-)|(\%3B)|(;))',
            r'\w*((\%27)|(\'))((\%6F)|o|(\%4F))((\%72)|r|(\%52))',
            r'((\%27)|(\'))union',
            r'exec(\s|\+)+(s|x)p\w+',
            r'UNION[^a-zA-Z]', 
            r'SELECT[^a-zA-Z]',
            r'INSERT[^a-zA-Z]',
            r'DELETE[^a-zA-Z]',
            r'UPDATE[^a-zA-Z]',
            r'DROP[^a-zA-Z]'
        ]
        
        self.xss_patterns = [
            r'<script[^>]*>.*?</script>',
            r'javascript:',
            r'on\w+\s*=',
            r'<iframe[^>]*>',
            r'<object[^>]*>',
            r'<embed[^>]*>',
            r'eval\s*\(',
            r'alert\s*\(',
            r'document\.cookie'
        ]
        
        self.path_traversal_patterns = [
            r'\.\./',
            r'\.\.\\',
            r'%2e%2e%2f',
            r'%2e%2e\\',
            r'\.\.%2f',
            r'\.\.%5c'
        ]
        
        # Rate limiting per endpoint
        self.endpoint_limits = {
            "/api/auth/login": {"requests": 5, "window": 300},  # 5 requests per 5 minutes
            "/api/auth/register": {"requests": 3, "window": 300},  # 3 requests per 5 minutes
            "/api/auth/forgot-password": {"requests": 3, "window": 900},  # 3 requests per 15 minutes
            "/api/payments": {"requests": 10, "window": 60},  # 10 requests per minute
            "/api/properties": {"requests": 100, "window": 60},  # 100 requests per minute
            "default": {"requests": 60, "window": 60}  # 60 requests per minute
        }
    
    def analyze_request(self, request: Request) -> Dict[str, any]:
        """Analyze request for threats"""
        threats = []
        threat_score = 0
        
        client_ip = request.client.host if request.client else "unknown"
        user_agent = request.headers.get("user-agent", "")
        path = request.url.path
        query_string = str(request.query_params)
        
        # Check for SQL injection
        for pattern in self.sql_injection_patterns:
            if re.search(pattern, query_string, re.IGNORECASE):
                threats.append("sql_injection")
                threat_score += 30
                break
        
        # Check for XSS
        for pattern in self.xss_patterns:
            if re.search(pattern, query_string, re.IGNORECASE):
                threats.append("xss")
                threat_score += 20
                break
        
        # Check for path traversal
        for pattern in self.path_traversal_patterns:
            if re.search(pattern, path, re.IGNORECASE):
                threats.append("path_traversal")
                threat_score += 25
                break
        
        # Check for suspicious user agents
        suspicious_agents = [
            "sqlmap", "nikto", "dirb", "nmap", "masscan", "zap", "burp",
            "python-requests", "curl", "wget", "powershell"
        ]
        
        for agent in suspicious_agents:
            if agent.lower() in user_agent.lower():
                threats.append("suspicious_user_agent")
                threat_score += 15
                break
        
        # Check request rate
        current_time = time.time()
        ip_data = self.suspicious_ips[client_ip]
        ip_data["requests"].append(current_time)
        
        # Count requests in last minute
        recent_requests = [req for req in ip_data["requests"] if current_time - req < 60]
        
        # Get endpoint-specific limit
        endpoint_limit = self.endpoint_limits.get(path, self.endpoint_limits["default"])
        
        if len(recent_requests) > endpoint_limit["requests"]:
            threats.append("rate_limit_exceeded")
            threat_score += 10
        
        # Update threat score
        ip_data["threat_score"] = max(ip_data["threat_score"], threat_score)
        
        return {
            "threats": threats,
            "threat_score": threat_score,
            "should_block": threat_score >= 50,
            "recent_requests": len(recent_requests)
        }
    
    def is_ip_blocked(self, client_ip: str) -> bool:
        """Check if IP is blocked"""
        ip_data = self.suspicious_ips[client_ip]
        if ip_data["blocked_until"]:
            return time.time() < ip_data["blocked_until"]
        return False
    
    def block_ip(self, client_ip: str, duration: int = 3600):
        """Block IP for specified duration"""
        ip_data = self.suspicious_ips[client_ip]
        ip_data["blocked_until"] = time.time() + duration
        ip_data["threat_score"] = 100
        logger.warning(f"IP {client_ip} blocked for {duration} seconds")

# Global threat detector
threat_detector = ThreatDetector()

# IP whitelist for admin endpoints
ADMIN_IP_WHITELIST: Set[str] = {
    "127.0.0.1", "::1",  # localhost
    # Add production admin IPs here
}

# Request size limits (in bytes)
MAX_REQUEST_SIZE = 10 * 1024 * 1024  # 10MB
MAX_UPLOAD_SIZE = 50 * 1024 * 1024   # 50MB


def setup_security_middleware(app):
    """Setup all security middleware for the FastAPI app"""

    # Rate limiting
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
    app.add_middleware(RateLimiter)

    # GZip compression
    app.add_middleware(GZipMiddleware, minimum_size=1000)

    # Trusted hosts (uncomment for production)
    # app.add_middleware(TrustedHostMiddleware, allowed_hosts=["propertyyards.com", "*.propertyyards.com"])

    # Enhanced threat detection middleware
    @app.middleware("http")
    async def threat_detection_middleware(request: Request, call_next: Callable):
        """Advanced threat detection and IP blocking"""
        client_ip = request.client.host if request.client else "unknown"
        
        # Check if IP is already blocked
        if threat_detector.is_ip_blocked(client_ip):
            logger.warning(f"Blocked IP attempted access: {client_ip}")
            raise HTTPException(
                status_code=403,
                detail="Access denied. Your IP has been temporarily blocked due to suspicious activity."
            )
        
        # Analyze request for threats
        threat_analysis = threat_detector.analyze_request(request)
        
        # Block high-threat requests
        if threat_analysis["should_block"]:
            threat_detector.block_ip(client_ip, duration=3600)  # Block for 1 hour
            logger.warning(f"IP blocked due to threat detection: {client_ip}, threats: {threat_analysis['threats']}")
            raise HTTPException(
                status_code=403,
                detail="Access denied. Suspicious activity detected."
            )
        
        # Log medium-threat requests
        if threat_analysis["threat_score"] >= 25:
            logger.warning(f"Suspicious request from {client_ip}: score={threat_analysis['threat_score']}, threats={threat_analysis['threats']}")
        
        # Add threat info to request state for monitoring
        request.state.threat_analysis = threat_analysis
        
        response = await call_next(request)
        return response

    # Request size limiting middleware
    @app.middleware("http")
    async def request_size_limit_middleware(request: Request, call_next: Callable):
        """Limit request size to prevent DoS attacks"""
        content_length = request.headers.get("content-length")
        if content_length:
            try:
                size = int(content_length)
                # Check if it's a file upload endpoint
                if request.url.path.startswith("/api/upload") or request.url.path.startswith("/api/properties/upload"):
                    max_size = MAX_UPLOAD_SIZE
                else:
                    max_size = MAX_REQUEST_SIZE
                
                if size > max_size:
                    logger.warning(f"Request too large: {size} bytes from {request.client.host}")
                    raise HTTPException(
                        status_code=413,
                        detail=f"Request too large. Maximum size is {max_size // (1024*1024)}MB"
                    )
            except ValueError:
                pass  # Invalid content-length header
        
        response = await call_next(request)
        return response

    # Admin IP whitelist middleware
    @app.middleware("http")
    async def admin_ip_whitelist_middleware(request: Request, call_next: Callable):
        """Restrict admin endpoints to whitelisted IPs"""
        if request.url.path.startswith("/api/admin") or request.url.path.startswith("/admin"):
            client_ip = request.client.host if request.client else "unknown"
            
            # Skip whitelist check in development
            from app.config import settings
            if not settings.DEBUG and client_ip not in ADMIN_IP_WHITELIST:
                logger.warning(f"Admin access denied for IP: {client_ip}")
                raise HTTPException(
                    status_code=403,
                    detail="Admin access restricted to whitelisted IPs only"
                )
        
        response = await call_next(request)
        return response

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

    # ETag + Cache-Control middleware
    @app.middleware("http")
    async def add_cache_headers(request: Request, call_next: Callable):
        response = await call_next(request)

        path = request.url.path

        # ── Cache-Control rules ──────────────────────────────────────
        if request.method == "GET":
            # Public, cacheable API resources (properties, analytics, news)
            if any(path.startswith(p) for p in [
                "/api/properties", "/api/analytics", "/api/news",
                "/api/locality", "/api/brokers",
            ]):
                response.headers.setdefault("Cache-Control", "public, max-age=300, stale-while-revalidate=60")

            # User-specific private data — never share across users
            elif any(path.startswith(p) for p in [
                "/api/users", "/api/payments", "/api/rewards",
                "/api/notifications", "/api/crm", "/api/feedback",
            ]):
                response.headers["Cache-Control"] = "private, no-store"

            # Auth endpoints — never cache
            elif path.startswith("/api/auth"):
                response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate"

            # AI / expensive compute endpoints — short public cache
            elif any(path.startswith(p) for p in ["/api/ai", "/api/architecture", "/api/prediction"]):
                response.headers.setdefault("Cache-Control", "public, max-age=60")

            else:
                response.headers.setdefault("Cache-Control", "no-cache")

        elif request.method in ("POST", "PUT", "PATCH", "DELETE"):
            # Mutations must never be served from cache
            response.headers["Cache-Control"] = "no-store"

        # ── ETag for successful GET responses ─────────────────────────
        if request.method == "GET" and response.status_code == 200:
            try:
                body = b""
                async for chunk in response.body_iterator:
                    body += chunk
                if body:
                    etag = f'"{hashlib.md5(body).hexdigest()}"'
                    response.headers["ETag"] = etag

                    # Check If-None-Match — return 304 if unchanged
                    client_etag = request.headers.get("If-None-Match")
                    if client_etag and client_etag == etag:
                        from fastapi.responses import Response as FResponse
                        not_modified = FResponse(status_code=304)
                        not_modified.headers["ETag"] = etag
                        not_modified.headers["Cache-Control"] = response.headers.get("Cache-Control", "no-cache")
                        return not_modified

                    from fastapi.responses import Response as FResponse
                    return FResponse(
                        content=body,
                        status_code=response.status_code,
                        headers=dict(response.headers),
                        media_type=response.media_type,
                    )
            except Exception:
                pass  # ETag generation is best-effort; never break the response

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
