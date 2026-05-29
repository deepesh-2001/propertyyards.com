"""
Admin routes
"""
from fastapi import APIRouter, Depends, HTTPException, status, Header
from app.database import get_database
from app.models import AuditLog
from app.schemas import AdminStats, UserStats, PropertyStats, UserResponse, PropertyResponse
from app.auth import decode_token
from app.cache import invalidate_cache_pattern, generate_cache_key, get_from_cache, set_in_cache
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/admin", tags=["Admin"])


def get_current_admin(authorization: str = Header(None)) -> dict:
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
    authorization: str = Header(None),
    db = Depends(get_database)
):
    """Get platform analytics"""
    admin_user = get_current_admin(authorization)

    # Check cache
    cache_key = "admin:analytics"
    cached_stats = await get_from_cache(cache_key)
    if cached_stats:
        return AdminStats(**cached_stats)

    # Calculate statistics
    total_users = await db.users.count_documents({})
    active_users = await db.users.count_documents({"is_active": True})
    total_sellers = await db.users.count_documents({"role": "seller"})
    total_buyers = await db.users.count_documents({"role": "buyer"})
    total_agents = await db.users.count_documents({"role": "agent"})

    total_properties = await db.properties.count_documents({})
    active_listings = await db.properties.count_documents({"status": "listed"})
    sold_properties = await db.properties.count_documents({"status": "sold"})
    rented_properties = await db.properties.count_documents({"status": "rented"})
    
    # Calculate total value
    properties_cursor = db.properties.find({}, {"price": 1})
    properties = await properties_cursor.to_list(length=None)
    total_value = sum(p.get("price", 0) for p in properties)

    total_inquiries = await db.inquiries.count_documents({})
    total_wishlist = await db.wishlists.count_documents({})

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
    authorization: str = Header(None),
    db = Depends(get_database)
):
    """Get all users (admin only)"""
    admin_user = get_current_admin(authorization)

    # Build query
    query_filter = {}
    if role:
        query_filter["role"] = role

    skip = (page - 1) * limit
    users_cursor = db.users.find(query_filter).skip(skip).limit(limit)
    users = await users_cursor.to_list(length=limit)

    # Convert to response format
    user_responses = []
    for user in users:
        user_dict = {
            "id": str(user["_id"]),
            **{k: v for k, v in user.items() if k != "_id"}
        }
        user_responses.append(UserResponse(**user_dict))

    return user_responses


@router.get("/properties", response_model=list[PropertyResponse])
async def get_all_properties(
    page: int = 1,
    limit: int = 50,
    status: str = None,
    authorization: str = Header(None),
    db = Depends(get_database)
):
    """Get all properties (admin only)"""
    admin_user = get_current_admin(authorization)

    # Build query
    query_filter = {}
    if status:
        query_filter["status"] = status

    skip = (page - 1) * limit
    properties_cursor = db.properties.find(query_filter).skip(skip).limit(limit)
    properties = await properties_cursor.to_list(length=limit)

    # Convert to response format
    property_responses = []
    for prop in properties:
        prop_dict = {
            "id": str(prop["_id"]),
            **{k: v for k, v in prop.items() if k != "_id"}
        }
        property_responses.append(PropertyResponse(**prop_dict))

    return property_responses


@router.post("/properties/{property_id}/approve")
async def approve_property(
    property_id: str,
    authorization: str = Header(None),
    db = Depends(get_database)
):
    """Approve a property listing"""
    admin_user = get_current_admin(authorization)

    # Get property
    property = await db.properties.find_one({"_id": property_id})
    if not property:
        raise HTTPException(status_code=404, detail="Property not found")

    # Update status
    await db.properties.update_one({"_id": property_id}, {"$set": {"status": "listed"}})

    # Log audit
    audit_log = AuditLog(
        user_id=admin_user["user_id"],
        action="approve_property",
        resource_type="property",
        resource_id=property_id,
        details={"status": "listed"}
    )
    await db.audit_logs.insert_one(audit_log.dict())

    # Invalidate cache
    await invalidate_cache_pattern("properties:*")

    logger.info(f"Property approved: {property_id}")

    return {"message": "Property approved"}


@router.post("/properties/{property_id}/reject")
async def reject_property(
    property_id: str,
    reason: str = None,
    authorization: str = Header(None),
    db = Depends(get_database)
):
    """Reject a property listing"""
    admin_user = get_current_admin(authorization)

    # Get property
    property = await db.properties.find_one({"_id": property_id})
    if not property:
        raise HTTPException(status_code=404, detail="Property not found")

    # Delete property
    await db.properties.delete_one({"_id": property_id})

    # Log audit
    audit_log = AuditLog(
        user_id=admin_user["user_id"],
        action="reject_property",
        resource_type="property",
        resource_id=property_id,
        details={"reason": reason}
    )
    await db.audit_logs.insert_one(audit_log.dict())

    # Invalidate cache
    await invalidate_cache_pattern("properties:*")

    logger.info(f"Property rejected: {property_id}")

    return {"message": "Property rejected"}


@router.delete("/users/{user_id}")
async def delete_user(
    user_id: str,
    authorization: str = Header(None),
    db = Depends(get_database)
):
    """Delete a user (admin only)"""
    admin_user = get_current_admin(authorization)

    # Get user
    user = await db.users.find_one({"_id": user_id})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Prevent deleting admin
    if user["role"] == "admin":
        raise HTTPException(status_code=400, detail="Cannot delete admin users")

    # Delete user
    await db.users.delete_one({"_id": user_id})

    # Log audit
    audit_log = AuditLog(
        user_id=admin_user["user_id"],
        action="delete_user",
        resource_type="user",
        resource_id=user_id,
        details={"email": user["email"]}
    )
    await db.audit_logs.insert_one(audit_log.dict())

    logger.info(f"User deleted: {user_id}")

    return {"message": "User deleted successfully"}


@router.post("/users/{user_id}/deactivate")
async def deactivate_user(
    user_id: str,
    authorization: str = Header(None),
    db = Depends(get_database)
):
    """Deactivate a user"""
    admin_user = get_current_admin(authorization)

    # Get user
    user = await db.users.find_one({"_id": user_id})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Deactivate user
    await db.users.update_one({"_id": user_id}, {"$set": {"is_active": False}})

    # Log audit
    audit_log = AuditLog(
        user_id=admin_user["user_id"],
        action="deactivate_user",
        resource_type="user",
        resource_id=user_id
    )
    await db.audit_logs.insert_one(audit_log.dict())

    logger.info(f"User deactivated: {user_id}")

    return {"message": "User deactivated"}


@router.get("/audit-logs", response_model=list)
async def get_audit_logs(
    page: int = 1,
    limit: int = 50,
    action: str = None,
    authorization: str = Header(None),
    db = Depends(get_database)
):
    """Get audit logs"""
    admin_user = get_current_admin(authorization)

    # Build query
    query_filter = {}
    if action:
        query_filter["action"] = action

    skip = (page - 1) * limit
    logs_cursor = db.audit_logs.find(query_filter).sort("created_at", -1).skip(skip).limit(limit)
    logs = await logs_cursor.to_list(length=limit)

    # Convert to list format
    return logs

