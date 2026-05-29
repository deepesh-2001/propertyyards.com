"""
Authentication and authorization
"""
from datetime import datetime, timedelta, timezone
from typing import Optional
from fastapi import Header
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel
from app.config import settings
from app.session import session_manager
import logging

logger = logging.getLogger(__name__)

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """Hash password using bcrypt"""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password against hash"""
    try:
        return pwd_context.verify(plain_password, hashed_password)
    except Exception as e:
        logger.error(f"Password verification error: {e}")
        return False


# JWT Token models
class TokenData(BaseModel):
    """JWT token payload"""
    user_id: str
    email: str
    role: str
    exp: int


def create_access_token(user_id: str, email: str, role: str) -> str:
    """Create JWT access token"""
    expires = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode = {
        "user_id": user_id,
        "email": email,
        "role": role,
        "exp": int(expires.timestamp())
    }

    try:
        encoded_jwt = jwt.encode(
            to_encode,
            settings.JWT_SECRET_KEY,
            algorithm=settings.JWT_ALGORITHM
        )
        return encoded_jwt
    except Exception as e:
        logger.error(f"Token creation error: {e}")
        raise


def create_refresh_token(user_id: str, email: str, role: str) -> str:
    """Create JWT refresh token"""
    expires = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)

    to_encode = {
        "user_id": user_id,
        "email": email,
        "role": role,
        "type": "refresh",
        "exp": int(expires.timestamp())
    }

    try:
        encoded_jwt = jwt.encode(
            to_encode,
            settings.JWT_SECRET_KEY,
            algorithm=settings.JWT_ALGORITHM
        )
        return encoded_jwt
    except Exception as e:
        logger.error(f"Refresh token creation error: {e}")
        raise


def decode_token(token: str) -> Optional[TokenData]:
    """Decode and validate JWT token"""
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM]
        )

        user_id = payload.get("user_id")
        email = payload.get("email")
        role = payload.get("role")

        if not all([user_id, email, role]):
            return None

        return TokenData(
            user_id=user_id,
            email=email,
            role=role,
            exp=payload.get("exp", 0)
        )
    except JWTError as e:
        logger.error(f"Token decode error: {e}")
        return None


# Roles
class Role:
    """User roles"""
    ADMIN = "admin"
    SELLER = "seller"
    BUYER = "buyer"
    AGENT = "agent"

    ALL = [ADMIN, SELLER, BUYER, AGENT]


async def create_user_session(
    user_id: str,
    email: str,
    role: str,
    user_agent: Optional[str] = None,
    ip_address: Optional[str] = None,
    metadata: Optional[dict] = None
) -> dict:
    """Create a new user session"""
    return await session_manager.create_session(
        user_id=user_id,
        email=email,
        role=role,
        user_agent=user_agent,
        ip_address=ip_address,
        metadata=metadata
    )


async def invalidate_session(session_id: str) -> bool:
    """Invalidate a specific session"""
    return await session_manager.delete_session(session_id)


async def invalidate_all_user_sessions(user_id: str) -> int:
    """Invalidate all sessions for a user (logout from all devices)"""
    return await session_manager.delete_user_sessions(user_id)


async def get_active_sessions(user_id: str) -> list:
    """Get all active sessions for a user"""
    return await session_manager.get_user_sessions(user_id)


def get_current_user(authorization: Optional[str] = Header(None)) -> dict:
    """Extract and validate current user from the Authorization header (Bearer token).

    Declared with fastapi.Header so that when used via Depends() the value is read
    from the HTTP `Authorization` header rather than a query parameter.
    """
    from fastapi import HTTPException
    if not authorization:
        raise HTTPException(status_code=401, detail="Not authenticated")
    try:
        token = authorization.split(" ")[1]
        token_data = decode_token(token)
        if token_data:
            return {
                "user_id": token_data.user_id,
                "email": token_data.email,
                "role": token_data.role
            }
    except Exception:
        pass
    raise HTTPException(status_code=401, detail="Invalid token")

