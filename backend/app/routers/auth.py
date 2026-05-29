"""
Authentication routes
"""
from fastapi import APIRouter, Depends, HTTPException, status, Header
from bson import ObjectId
from datetime import datetime, timezone
from app.database import get_database
from app.schemas import UserCreate, TokenResponse, TokenRequest, RefreshTokenRequest, UserResponse
from app.auth import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    decode_token,
    invalidate_all_user_sessions
)
from app.feature_flags import require_feature_flag
import logging
from typing import Optional

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/auth", tags=["Authentication"])


@router.post("/register", response_model=UserResponse)
@require_feature_flag("user_registration")
async def register(user_data: UserCreate, db = Depends(get_database)):
    """Register a new user"""
    # Check if user already exists
    existing_user = await db.users.find_one({"email": user_data.email})
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    # Create new user
    now = datetime.now(timezone.utc)
    new_user_doc = {
        "email": user_data.email,
        "first_name": user_data.first_name,
        "last_name": user_data.last_name,
        "phone_number": user_data.phone_number,
        "password_hash": hash_password(user_data.password),
        "role": user_data.role,
        "is_active": True,
        "created_at": now,
        "updated_at": now,
    }

    result = await db.users.insert_one(new_user_doc)
    new_user_doc["id"] = str(result.inserted_id)

    logger.info(f"New user registered: {new_user_doc['email']}")
    return UserResponse(**new_user_doc)


@router.post("/login", response_model=TokenResponse)
@require_feature_flag("user_management")
async def login(credentials: TokenRequest, db = Depends(get_database)):
    """Login user and get tokens"""
    # Find user
    user = await db.users.find_one({"email": credentials.email})
    if not user or not verify_password(credentials.password, user["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )

    if not user.get("is_active", True):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive"
        )

    # Create tokens
    access_token = create_access_token(str(user["_id"]), user["email"], user["role"])
    refresh_token = create_refresh_token(str(user["_id"]), user["email"], user["role"])

    logger.info(f"User logged in: {user['email']}")

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=30 * 60  # 30 minutes in seconds
    )


@router.post("/refresh", response_model=TokenResponse)
@require_feature_flag("user_management")
async def refresh_token(token_request: RefreshTokenRequest, db = Depends(get_database)):
    """Refresh access token using refresh token"""
    token_data = decode_token(token_request.refresh_token)
    if not token_data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )

    # Verify user still exists and is active
    user = await db.users.find_one({"_id": ObjectId(token_data.user_id)})
    if not user or not user.get("is_active", True):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User not found or inactive"
        )

    # Create new tokens
    access_token = create_access_token(str(user["_id"]), user["email"], user["role"])
    refresh_token = create_refresh_token(str(user["_id"]), user["email"], user["role"])

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=30 * 60
    )


@router.post("/logout")
async def logout(authorization: Optional[str] = Header(None)):
    """Logout user — invalidates all server-side sessions"""
    if authorization:
        try:
            token = authorization.split(" ", 1)[1]
            token_data = decode_token(token)
            if token_data:
                await invalidate_all_user_sessions(token_data.user_id)
        except Exception:
            pass
    return {"message": "Logged out successfully"}

