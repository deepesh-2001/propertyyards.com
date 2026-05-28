"""
User profile routes
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.database import get_db
from app.models import User, Property, Inquiry, Wishlist
from app.schemas import UserResponse, UserUpdate, UserProfileResponse, PaginatedResponse
from app.auth import decode_token
from app.cache import get_from_cache, set_in_cache, delete_from_cache, generate_cache_key, invalidate_cache_pattern
import logging
from typing import Optional

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/users", tags=["Users"])


def get_current_user(token: str = None) -> dict:
    """Get current user from token"""
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")

    token_data = decode_token(token)
    if not token_data:
        raise HTTPException(status_code=401, detail="Invalid token")

    return {"user_id": token_data.user_id, "email": token_data.email, "role": token_data.role}


@router.get("/me", response_model=UserProfileResponse)
async def get_current_user_profile(
    authorization: str = None,
    db: Session = Depends(get_db)
):
    """Get current user profile"""
    if not authorization:
        raise HTTPException(status_code=401, detail="Not authenticated")

    # Extract token from "Bearer <token>"
    try:
        token = authorization.split(" ")[1]
    except IndexError:
        raise HTTPException(status_code=401, detail="Invalid token format")

    current_user = get_current_user(token)
    user_id = current_user["user_id"]

    # Check cache
    cache_key = generate_cache_key("user", user_id)
    cached_user = await get_from_cache(cache_key)
    if cached_user:
        return UserProfileResponse(**cached_user)

    # Get from database
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Get counts
    properties_count = db.query(func.count(Property.id)).filter(Property.user_id == user_id).scalar()
    inquiries_count = db.query(func.count(Inquiry.id)).filter(Inquiry.user_id == user_id).scalar()

    user_data = {
        "id": str(user.id),
        "email": user.email,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "phone_number": user.phone_number,
        "role": user.role,
        "is_active": user.is_active,
        "created_at": user.created_at,
        "updated_at": user.updated_at,
        "properties_count": properties_count,
        "inquiries_count": inquiries_count
    }

    # Cache the result
    await set_in_cache(cache_key, user_data, ttl=1800)  # 30 minutes

    return UserProfileResponse(**user_data)


@router.put("/me", response_model=UserResponse)
async def update_current_user_profile(
    user_update: UserUpdate,
    authorization: str = None,
    db: Session = Depends(get_db)
):
    """Update current user profile"""
    if not authorization:
        raise HTTPException(status_code=401, detail="Not authenticated")

    try:
        token = authorization.split(" ")[1]
    except IndexError:
        raise HTTPException(status_code=401, detail="Invalid token format")

    current_user = get_current_user(token)
    user_id = current_user["user_id"]

    # Get user
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Update fields
    update_data = user_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(user, field, value)

    db.commit()
    db.refresh(user)

    # Invalidate cache
    cache_key = generate_cache_key("user", user_id)
    await delete_from_cache(cache_key)

    logger.info(f"User profile updated: {user.email}")

    return UserResponse.from_orm(user)


@router.get("/{user_id}", response_model=UserProfileResponse)
async def get_user_by_id(
    user_id: str,
    db: Session = Depends(get_db)
):
    """Get user profile by ID (public profile)"""
    # Check cache
    cache_key = generate_cache_key("user", user_id)
    cached_user = await get_from_cache(cache_key)
    if cached_user:
        return UserProfileResponse(**cached_user)

    # Get from database
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Get counts
    properties_count = db.query(func.count(Property.id)).filter(Property.user_id == user_id).scalar()
    inquiries_count = db.query(func.count(Inquiry.id)).filter(Inquiry.user_id == user_id).scalar()

    user_data = {
        "id": str(user.id),
        "email": user.email,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "phone_number": user.phone_number,
        "role": user.role,
        "is_active": user.is_active,
        "created_at": user.created_at,
        "updated_at": user.updated_at,
        "properties_count": properties_count,
        "inquiries_count": inquiries_count
    }

    # Cache the result
    await set_in_cache(cache_key, user_data, ttl=1800)

    return UserProfileResponse(**user_data)


@router.get("/{user_id}/properties", response_model=PaginatedResponse)
async def get_user_properties(
    user_id: str,
    page: int = 1,
    limit: int = 20,
    db: Session = Depends(get_db)
):
    """Get all properties by a user"""
    # Check if user exists
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Get properties with pagination
    query = db.query(Property).filter(Property.user_id == user_id)
    total = query.count()

    properties = query.offset((page - 1) * limit).limit(limit).all()

    return {
        "items": properties,
        "total": total,
        "page": page,
        "limit": limit,
        "pages": (total + limit - 1) // limit
    }

