"""
Property inquiry routes
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.database import get_db
from app.models import Property, Inquiry
from app.schemas import InquiryCreate, InquiryResponse, InquiryUpdate, PaginatedResponse
from app.auth import decode_token
from app.cache import generate_cache_key, get_from_cache, set_in_cache, delete_from_cache
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/inquiries", tags=["Inquiries"])


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


@router.post("", response_model=InquiryResponse)
async def create_inquiry(
    inquiry_data: InquiryCreate,
    authorization: str = None,
    db: Session = Depends(get_db)
):
    """Create a new inquiry for a property"""
    current_user = get_current_user_from_header(authorization)
    if not current_user:
        raise HTTPException(status_code=401, detail="Not authenticated")

    # Check if property exists
    property = db.query(Property).filter(Property.id == inquiry_data.property_id).first()
    if not property:
        raise HTTPException(status_code=404, detail="Property not found")

    # Create inquiry
    new_inquiry = Inquiry(
        user_id=current_user["user_id"],
        property_id=inquiry_data.property_id,
        message=inquiry_data.message
    )

    db.add(new_inquiry)
    db.commit()
    db.refresh(new_inquiry)

    logger.info(f"Inquiry created: {new_inquiry.id}")

    return InquiryResponse.from_orm(new_inquiry)


@router.get("", response_model=PaginatedResponse)
async def get_user_inquiries(
    page: int = 1,
    limit: int = 20,
    authorization: str = None,
    db: Session = Depends(get_db)
):
    """Get current user's inquiries"""
    current_user = get_current_user_from_header(authorization)
    if not current_user:
        raise HTTPException(status_code=401, detail="Not authenticated")

    # Check cache
    cache_key = generate_cache_key("inquiries", current_user["user_id"], page, limit)
    cached_result = await get_from_cache(cache_key)
    if cached_result:
        return PaginatedResponse(**cached_result)

    # Get inquiries
    query = db.query(Inquiry).filter(Inquiry.user_id == current_user["user_id"])
    total = query.count()

    inquiries = query.order_by(Inquiry.created_at.desc()).offset((page - 1) * limit).limit(limit).all()

    result = {
        "items": [InquiryResponse.from_orm(i).dict() for i in inquiries],
        "total": total,
        "page": page,
        "limit": limit,
        "pages": (total + limit - 1) // limit
    }

    # Cache the result
    await set_in_cache(cache_key, result, ttl=300)

    return result


@router.get("/{inquiry_id}", response_model=InquiryResponse)
async def get_inquiry(
    inquiry_id: str,
    authorization: str = None,
    db: Session = Depends(get_db)
):
    """Get inquiry details"""
    current_user = get_current_user_from_header(authorization)
    if not current_user:
        raise HTTPException(status_code=401, detail="Not authenticated")

    # Get inquiry
    inquiry = db.query(Inquiry).filter(Inquiry.id == inquiry_id).first()
    if not inquiry:
        raise HTTPException(status_code=404, detail="Inquiry not found")

    # Check permission
    property = db.query(Property).filter(Property.id == inquiry.property_id).first()
    if inquiry.user_id != current_user["user_id"] and property.user_id != current_user["user_id"] and current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Permission denied")

    return InquiryResponse.from_orm(inquiry)


@router.put("/{inquiry_id}", response_model=InquiryResponse)
async def update_inquiry(
    inquiry_id: str,
    inquiry_update: InquiryUpdate,
    authorization: str = None,
    db: Session = Depends(get_db)
):
    """Update inquiry"""
    current_user = get_current_user_from_header(authorization)
    if not current_user:
        raise HTTPException(status_code=401, detail="Not authenticated")

    # Get inquiry
    inquiry = db.query(Inquiry).filter(Inquiry.id == inquiry_id).first()
    if not inquiry:
        raise HTTPException(status_code=404, detail="Inquiry not found")

    # Check permission
    if inquiry.user_id != current_user["user_id"] and current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Permission denied")

    # Update fields
    update_data = inquiry_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        if value is not None:
            setattr(inquiry, field, value)

    db.commit()
    db.refresh(inquiry)

    # Invalidate cache
    cache_key = generate_cache_key("inquiries", current_user["user_id"], "*", "*")
    await delete_from_cache(cache_key)

    logger.info(f"Inquiry updated: {inquiry_id}")

    return InquiryResponse.from_orm(inquiry)


@router.delete("/{inquiry_id}")
async def delete_inquiry(
    inquiry_id: str,
    authorization: str = None,
    db: Session = Depends(get_db)
):
    """Delete inquiry"""
    current_user = get_current_user_from_header(authorization)
    if not current_user:
        raise HTTPException(status_code=401, detail="Not authenticated")

    # Get inquiry
    inquiry = db.query(Inquiry).filter(Inquiry.id == inquiry_id).first()
    if not inquiry:
        raise HTTPException(status_code=404, detail="Inquiry not found")

    # Check permission
    if inquiry.user_id != current_user["user_id"] and current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Permission denied")

    db.delete(inquiry)
    db.commit()

    logger.info(f"Inquiry deleted: {inquiry_id}")

    return {"message": "Inquiry deleted successfully"}


@router.get("/property/{property_id}/inquiries", response_model=PaginatedResponse)
async def get_property_inquiries(
    property_id: str,
    page: int = 1,
    limit: int = 20,
    authorization: str = None,
    db: Session = Depends(get_db)
):
    """Get all inquiries for a property (property owner only)"""
    current_user = get_current_user_from_header(authorization)
    if not current_user:
        raise HTTPException(status_code=401, detail="Not authenticated")

    # Get property
    property = db.query(Property).filter(Property.id == property_id).first()
    if not property:
        raise HTTPException(status_code=404, detail="Property not found")

    # Check permission
    if property.user_id != current_user["user_id"] and current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Permission denied")

    # Get inquiries
    query = db.query(Inquiry).filter(Inquiry.property_id == property_id)
    total = query.count()

    inquiries = query.order_by(Inquiry.created_at.desc()).offset((page - 1) * limit).limit(limit).all()

    result = {
        "items": [InquiryResponse.from_orm(i).dict() for i in inquiries],
        "total": total,
        "page": page,
        "limit": limit,
        "pages": (total + limit - 1) // limit
    }

    return result

