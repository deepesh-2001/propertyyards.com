"""
Admin routes
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from app.database import get_db
from app.models import User, Property, Inquiry, Wishlist, AuditLog
from app.schemas import AdminStats, UserStats, PropertyStats, UserResponse, PropertyResponse
from app.auth import decode_token
from app.cache import invalidate_cache_pattern, generate_cache_key, get_from_cache, set_in_cache
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/admin", tags=["Admin"])


def get_current_admin(authorization: str = None) -> dict:
    """Get current admin user"""
    if not authorization:
        raise HTTPException(status_code=401, detail="Not authenticated")

    try:
        token = authorization.split(" ")[1]
        token_data = decode_token(token)
        if not token_data or token_data.role != "admin":
            raise HTTPException(status_code=403, detail="Admin access required")
        return {"user_id": token_data.user_id, "role": token_data.role}
    except Exception as e:
        raise HTTPException(status_code=401, detail="Invalid token")


@router.get("/analytics", response_model=AdminStats)
async def get_analytics(
    authorization: str = None,
    db: Session = Depends(get_db)
):
    """Get platform analytics"""
    admin_user = get_current_admin(authorization)

    # Check cache
    cache_key = "admin:analytics"
    cached_stats = await get_from_cache(cache_key)
    if cached_stats:
        return AdminStats(**cached_stats)

    # Calculate statistics
    total_users = db.query(func.count(User.id)).scalar()
    active_users = db.query(func.count(User.id)).filter(User.is_active == True).scalar()
    total_sellers = db.query(func.count(User.id)).filter(User.role == "seller").scalar()
    total_buyers = db.query(func.count(User.id)).filter(User.role == "buyer").scalar()
    total_agents = db.query(func.count(User.id)).filter(User.role == "agent").scalar()

    total_properties = db.query(func.count(Property.id)).scalar()
    active_listings = db.query(func.count(Property.id)).filter(Property.status == "listed").scalar()
    sold_properties = db.query(func.count(Property.id)).filter(Property.status == "sold").scalar()
    rented_properties = db.query(func.count(Property.id)).filter(Property.status == "rented").scalar()
    total_value = db.query(func.sum(Property.price)).scalar() or 0

    total_inquiries = db.query(func.count(Inquiry.id)).scalar()
    total_wishlist = db.query(func.count(Wishlist.id)).scalar()

    stats = AdminStats(
        users=UserStats(
            total_users=total_users,
            active_users=active_users,
            total_sellers=total_sellers,
            total_buyers=total_buyers,
            total_agents=total_agents
        ),
        properties=PropertyStats(
            total_properties=total_properties,
            active_listings=active_listings,
            sold_properties=sold_properties,
            rented_properties=rented_properties,
            total_value=total_value
        ),
        total_inquiries=total_inquiries,
        total_wishlist_items=total_wishlist
    )

    # Cache the result
    await set_in_cache(cache_key, stats.dict(), ttl=900)  # 15 minutes

    return stats


@router.get("/users", response_model=list[UserResponse])
async def get_all_users(
    page: int = 1,
    limit: int = 50,
    role: str = None,
    authorization: str = None,
    db: Session = Depends(get_db)
):
    """Get all users (admin only)"""
    admin_user = get_current_admin(authorization)

    # Build query
    query = db.query(User)
    if role:
        query = query.filter(User.role == role)

    total = query.count()
    users = query.offset((page - 1) * limit).limit(limit).all()

    return users


@router.get("/properties", response_model=list[PropertyResponse])
async def get_all_properties(
    page: int = 1,
    limit: int = 50,
    status: str = None,
    authorization: str = None,
    db: Session = Depends(get_db)
):
    """Get all properties (admin only)"""
    admin_user = get_current_admin(authorization)

    # Build query
    query = db.query(Property)
    if status:
        query = query.filter(Property.status == status)

    total = query.count()
    properties = query.offset((page - 1) * limit).limit(limit).all()

    return properties


@router.post("/properties/{property_id}/approve")
async def approve_property(
    property_id: str,
    authorization: str = None,
    db: Session = Depends(get_db)
):
    """Approve a property listing"""
    admin_user = get_current_admin(authorization)

    # Get property
    property = db.query(Property).filter(Property.id == property_id).first()
    if not property:
        raise HTTPException(status_code=404, detail="Property not found")

    # Update status
    property.status = "listed"
    db.commit()

    # Log audit
    audit_log = AuditLog(
        user_id=admin_user["user_id"],
        action="approve_property",
        resource_type="property",
        resource_id=property_id,
        details={"status": "listed"}
    )
    db.add(audit_log)
    db.commit()

    # Invalidate cache
    await invalidate_cache_pattern("properties:*")

    logger.info(f"Property approved: {property_id}")

    return {"message": "Property approved"}


@router.post("/properties/{property_id}/reject")
async def reject_property(
    property_id: str,
    reason: str = None,
    authorization: str = None,
    db: Session = Depends(get_db)
):
    """Reject a property listing"""
    admin_user = get_current_admin(authorization)

    # Get property
    property = db.query(Property).filter(Property.id == property_id).first()
    if not property:
        raise HTTPException(status_code=404, detail="Property not found")

    # Delete property
    db.delete(property)

    # Log audit
    audit_log = AuditLog(
        user_id=admin_user["user_id"],
        action="reject_property",
        resource_type="property",
        resource_id=property_id,
        details={"reason": reason}
    )
    db.add(audit_log)
    db.commit()

    # Invalidate cache
    await invalidate_cache_pattern("properties:*")

    logger.info(f"Property rejected: {property_id}")

    return {"message": "Property rejected"}


@router.delete("/users/{user_id}")
async def delete_user(
    user_id: str,
    authorization: str = None,
    db: Session = Depends(get_db)
):
    """Delete a user (admin only)"""
    admin_user = get_current_admin(authorization)

    # Get user
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Prevent deleting admin
    if user.role == "admin":
        raise HTTPException(status_code=400, detail="Cannot delete admin users")

    # Delete user
    db.delete(user)

    # Log audit
    audit_log = AuditLog(
        user_id=admin_user["user_id"],
        action="delete_user",
        resource_type="user",
        resource_id=user_id,
        details={"email": user.email}
    )
    db.add(audit_log)
    db.commit()

    logger.info(f"User deleted: {user_id}")

    return {"message": "User deleted successfully"}


@router.post("/users/{user_id}/deactivate")
async def deactivate_user(
    user_id: str,
    authorization: str = None,
    db: Session = Depends(get_db)
):
    """Deactivate a user"""
    admin_user = get_current_admin(authorization)

    # Get user
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Deactivate user
    user.is_active = False
    db.commit()

    # Log audit
    audit_log = AuditLog(
        user_id=admin_user["user_id"],
        action="deactivate_user",
        resource_type="user",
        resource_id=user_id
    )
    db.add(audit_log)
    db.commit()

    logger.info(f"User deactivated: {user_id}")

    return {"message": "User deactivated"}


@router.get("/audit-logs", response_model=list)
async def get_audit_logs(
    page: int = 1,
    limit: int = 50,
    action: str = None,
    authorization: str = None,
    db: Session = Depends(get_db)
):
    """Get audit logs"""
    admin_user = get_current_admin(authorization)

    # Build query
    query = db.query(AuditLog)
    if action:
        query = query.filter(AuditLog.action == action)

    logs = query.order_by(AuditLog.created_at.desc()).offset((page - 1) * limit).limit(limit).all()

    return logs

