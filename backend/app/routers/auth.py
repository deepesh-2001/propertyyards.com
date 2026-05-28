"""
Authentication routes
"""
from fastapi import APIRouter, Depends, HTTPException, status
from app.database import get_database
from app.models import User
from app.schemas import UserCreate, TokenResponse, TokenRequest, RefreshTokenRequest, UserResponse
from app.auth import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    decode_token
)
from app.feature_flags import require_feature_flag
import logging

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
    new_user = User(
        email=user_data.email,
        first_name=user_data.first_name,
        last_name=user_data.last_name,
        phone_number=user_data.phone_number,
        password_hash=hash_password(user_data.password),
        role=user_data.role
    )

    result = await db.users.insert_one(new_user.dict())
    new_user.id = str(result.inserted_id)

    logger.info(f"New user registered: {new_user.email}")
    return new_user


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
    user = await db.users.find_one({"_id": token_data.user_id})
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
async def logout():
    """Logout user (client should delete tokens)"""
    return {"message": "Logged out successfully"}

