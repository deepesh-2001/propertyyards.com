"""
Property listing routes
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_
from app.database import get_db
from app.models import Property, Wishlist, Inquiry
from app.schemas import (
    PropertyCreate,
    PropertyUpdate,
    PropertyResponse,
    PropertyListResponse,
    PropertySearchFilters,
    PaginatedResponse
)
from app.auth import decode_token
from app.cache import get_from_cache, set_in_cache, delete_from_cache, generate_cache_key, invalidate_cache_pattern
from app.feature_flags import require_feature_flag
import logging
from typing import Optional
import json

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/properties", tags=["Properties"])


def get_current_user_from_header(authorization: str = None) -> dict:
    """Extract current user from authorization header"""
    if not authorization:
        return None

    try:
        token = authorization.split(" ")[1]
        token_data = decode_token(token)
        if token_data:
            return {"user_id": token_data.user_id, "role": token_data.role}
    except Exception:
        pass

    return None


@router.post("", response_model=PropertyResponse)
@require_feature_flag("property_management")
async def create_property(
    property_data: PropertyCreate,
    authorization: str = None,
    db: Session = Depends(get_db)
):
    """Create a new property listing"""
    current_user = get_current_user_from_header(authorization)
    if not current_user:
        raise HTTPException(status_code=401, detail="Not authenticated")

    # Verify user has permission (seller or agent)
    if current_user["role"] not in ["seller", "agent"]:
        raise HTTPException(status_code=403, detail="Only sellers and agents can create listings")

    # Create property
    new_property = Property(
        user_id=current_user["user_id"],
        title=property_data.title,
        description=property_data.description,
        location=property_data.location,
        city=property_data.city,
        state=property_data.state,
        country=property_data.country,
        price=property_data.price,
        property_type=property_data.property_type,
        bedrooms=property_data.bedrooms,
        bathrooms=property_data.bathrooms,
        area=property_data.area,
        amenities=property_data.amenities or [],
        images=property_data.images or []
    )

    db.add(new_property)
    db.commit()
    db.refresh(new_property)

    # Invalidate listing cache
    await invalidate_cache_pattern("properties:*")

    logger.info(f"Property created: {new_property.id}")

    return PropertyResponse.from_orm(new_property)


@router.get("", response_model=PaginatedResponse)
@require_feature_flag("property_search")
async def list_properties(
    page: int = 1,
    limit: int = 20,
    status: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """List all properties with pagination"""
    # Check cache
    cache_key = generate_cache_key("properties", page, limit, status or "all")
    cached_result = await get_from_cache(cache_key)
    if cached_result:
        return PaginatedResponse(**cached_result)

    # Build query
    query = db.query(Property)
    if status:
        query = query.filter(Property.status == status)

    total = query.count()
    properties = query.order_by(Property.created_at.desc()).offset((page - 1) * limit).limit(limit).all()

    # Convert to response schema
    items = [PropertyListResponse.from_orm(p) for p in properties]

    result = {
        "items": [item.dict() for item in items],
        "total": total,
        "page": page,
        "limit": limit,
        "pages": (total + limit - 1) // limit
    }

    # Cache the result
    await set_in_cache(cache_key, result, ttl=300)  # 5 minutes

    return result


@router.get("/search", response_model=PaginatedResponse)
@require_feature_flag("property_search")
async def search_properties(
    filters: PropertySearchFilters = Depends(),
    db: Session = Depends(get_db)
):
    """Search properties with advanced filters"""
    # Build cache key
    cache_key = generate_cache_key(
        "search",
        filters.query or "",
        filters.city or "",
        filters.min_price or "",
        filters.max_price or "",
        filters.property_type or "",
        filters.page,
        filters.limit
    )

    cached_result = await get_from_cache(cache_key)
    if cached_result:
        return PaginatedResponse(**cached_result)

    # Build query
    query = db.query(Property)

    # Apply filters
    if filters.query:
        query = query.filter(
            or_(
                Property.title.ilike(f"%{filters.query}%"),
                Property.description.ilike(f"%{filters.query}%"),
                Property.location.ilike(f"%{filters.query}%")
            )
        )

    if filters.city:
        query = query.filter(Property.city.ilike(f"%{filters.city}%"))

    if filters.state:
        query = query.filter(Property.state.ilike(f"%{filters.state}%"))

    if filters.min_price:
        query = query.filter(Property.price >= filters.min_price)

    if filters.max_price:
        query = query.filter(Property.price <= filters.max_price)

    if filters.property_type:
        query = query.filter(Property.property_type == filters.property_type)

    if filters.min_bedrooms:
        query = query.filter(Property.bedrooms >= filters.min_bedrooms)

    if filters.max_bedrooms:
        query = query.filter(Property.bedrooms <= filters.max_bedrooms)

    if filters.min_bathrooms:
        query = query.filter(Property.bathrooms >= filters.min_bathrooms)

    if filters.max_bathrooms:
        query = query.filter(Property.bathrooms <= filters.max_bathrooms)

    total = query.count()
    properties = query.order_by(Property.created_at.desc()).offset((filters.page - 1) * filters.limit).limit(filters.limit).all()

    items = [PropertyListResponse.from_orm(p) for p in properties]

    result = {
        "items": [item.dict() for item in items],
        "total": total,
        "page": filters.page,
        "limit": filters.limit,
        "pages": (total + filters.limit - 1) // filters.limit
    }

    # Cache the result
    await set_in_cache(cache_key, result, ttl=300)

    return result


@router.get("/{property_id}", response_model=PropertyResponse)
@require_feature_flag("property_search")
async def get_property(property_id: str, db: Session = Depends(get_db)):
    """Get property details"""
    # Check cache
    cache_key = generate_cache_key("property", property_id)
    cached_property = await get_from_cache(cache_key)
    if cached_property:
        return PropertyResponse(**cached_property)

    # Get from database
    property = db.query(Property).filter(Property.id == property_id).first()
    if not property:
        raise HTTPException(status_code=404, detail="Property not found")

    # Get wishlist count
    wishlist_count = db.query(func.count(Wishlist.id)).filter(Wishlist.property_id == property_id).scalar()

    result = PropertyResponse.from_orm(property)
    result.wishlist_count = wishlist_count

    # Cache the result
    await set_in_cache(cache_key, result.dict(), ttl=600)  # 10 minutes

    return result


@router.put("/{property_id}", response_model=PropertyResponse)
@require_feature_flag("property_management")
async def update_property(
    property_id: str,
    property_update: PropertyUpdate,
    authorization: str = None,
    db: Session = Depends(get_db)
):
    """Update property listing"""
    current_user = get_current_user_from_header(authorization)
    if not current_user:
        raise HTTPException(status_code=401, detail="Not authenticated")

    # Get property
    property = db.query(Property).filter(Property.id == property_id).first()
    if not property:
        raise HTTPException(status_code=404, detail="Property not found")

    # Check ownership
    if property.user_id != current_user["user_id"] and current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Permission denied")

    # Update fields
    update_data = property_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        if value is not None:
            setattr(property, field, value)

    db.commit()
    db.refresh(property)

    # Invalidate cache
    cache_key = generate_cache_key("property", property_id)
    await delete_from_cache(cache_key)
    await invalidate_cache_pattern("properties:*")

    logger.info(f"Property updated: {property_id}")

    return PropertyResponse.from_orm(property)


@router.delete("/{property_id}")
@require_feature_flag("property_management")
async def delete_property(
    property_id: str,
    authorization: str = None,
    db: Session = Depends(get_db)
):
    """Delete property listing"""
    current_user = get_current_user_from_header(authorization)
    if not current_user:
        raise HTTPException(status_code=401, detail="Not authenticated")

    # Get property
    property = db.query(Property).filter(Property.id == property_id).first()
    if not property:
        raise HTTPException(status_code=404, detail="Property not found")

    # Check ownership
    if property.user_id != current_user["user_id"] and current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Permission denied")

    db.delete(property)
    db.commit()

    # Invalidate cache
    cache_key = generate_cache_key("property", property_id)
    await delete_from_cache(cache_key)
    await invalidate_cache_pattern("properties:*")

    logger.info(f"Property deleted: {property_id}")

    return {"message": "Property deleted successfully"}


@router.post("/{property_id}/wishlist")
@require_feature_flag("property_wishlist")
async def add_to_wishlist(
    property_id: str,
    authorization: str = None,
    db: Session = Depends(get_db)
):
    """Add property to wishlist"""
    current_user = get_current_user_from_header(authorization)
    if not current_user:
        raise HTTPException(status_code=401, detail="Not authenticated")

    # Check if property exists
    property = db.query(Property).filter(Property.id == property_id).first()
    if not property:
        raise HTTPException(status_code=404, detail="Property not found")

    # Check if already in wishlist
    existing = db.query(Wishlist).filter(
        and_(
            Wishlist.user_id == current_user["user_id"],
            Wishlist.property_id == property_id
        )
    ).first()

    if existing:
        raise HTTPException(status_code=400, detail="Already in wishlist")

    # Add to wishlist
    wishlist_item = Wishlist(
        user_id=current_user["user_id"],
        property_id=property_id
    )

    db.add(wishlist_item)
    db.commit()

    logger.info(f"Added to wishlist: {property_id}")

    return {"message": "Added to wishlist"}


@router.delete("/{property_id}/wishlist")
@require_feature_flag("property_wishlist")
async def remove_from_wishlist(
    property_id: str,
    authorization: str = None,
    db: Session = Depends(get_db)
):
    """Remove property from wishlist"""
    current_user = get_current_user_from_header(authorization)
    if not current_user:
        raise HTTPException(status_code=401, detail="Not authenticated")

    # Remove from wishlist
    wishlist_item = db.query(Wishlist).filter(
        and_(
            Wishlist.user_id == current_user["user_id"],
            Wishlist.property_id == property_id
        )
    ).first()

    if not wishlist_item:
        raise HTTPException(status_code=404, detail="Not in wishlist")

    db.delete(wishlist_item)
    db.commit()

    logger.info(f"Removed from wishlist: {property_id}")

    return {"message": "Removed from wishlist"}

