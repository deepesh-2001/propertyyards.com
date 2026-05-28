"""
Admin Portal Router
Comprehensive admin dashboard and management interface
"""
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks, UploadFile, File
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from pydantic import BaseModel

from app.database import get_db
from app.auth import get_current_user
from app.realtime_analytics import realtime_collector, alert_manager
from app.predictive_analytics import predictive_analytics
from app.ai_image_service import ai_image_generator, image_cache_manager, GeneratedImage
from app.cache_pipeline import cache_warmer

router = APIRouter(prefix="/api/admin/portal", tags=["admin-portal"])


# ========== Dashboard Data Models ==========

class DashboardStats(BaseModel):
    """Dashboard statistics"""
    total_users: int
    total_properties: int
    active_properties: int
    total_inquiries: int
    revenue_today: float
    revenue_this_month: float


class SystemHealth(BaseModel):
    """System health status"""
    database_status: str
    cache_status: str
    ai_service_status: str
    websocket_connections: int
    active_background_tasks: int


class RecentActivity(BaseModel):
    """Recent activity item"""
    type: str
    description: str
    user: str
    timestamp: datetime
    metadata: Optional[Dict[str, Any]] = None


# ========== Dashboard Endpoints ==========

@router.get("/dashboard")
async def get_admin_dashboard(
    database=Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get comprehensive admin dashboard data"""
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")

    try:
        # Get real-time stats
        now = datetime.utcnow()
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        month_start = today_start.replace(day=1)

        # Count statistics
        total_users = await database.users.count_documents({})
        total_properties = await database.properties.count_documents({})
        active_properties = await database.properties.count_documents({"status": "active"})
        total_inquiries = await database.inquiries.count_documents({})

        # Get revenue
        revenue_pipeline = [
            {"$match": {"status": "paid", "created_at": {"$gte": today_start}}},
            {"$group": {"_id": None, "total": {"$sum": "$calculated_amount"}}}
        ]
        today_revenue_result = await database.commissions.aggregate(revenue_pipeline).to_list(length=1)
        revenue_today = today_revenue_result[0]["total"] if today_revenue_result else 0

        month_pipeline = [
            {"$match": {"status": "paid", "created_at": {"$gte": month_start}}},
            {"$group": {"_id": None, "total": {"$sum": "$calculated_amount"}}}
        ]
        month_revenue_result = await database.commissions.aggregate(month_pipeline).to_list(length=1)
        revenue_this_month = month_revenue_result[0]["total"] if month_revenue_result else 0

        # Get real-time data
        realtime_data = realtime_collector.get_live_dashboard_data()
        recent_alerts = alert_manager.get_recent_alerts(5)

        # Get predictions
        forecasts = await predictive_analytics.generate_dashboard_forecasts(database)

        # System health
        system_health = {
            "database_status": "healthy",
            "cache_status": "healthy",
            "ai_service_status": "ready" if ai_image_generator.api_key else "not_configured",
            "websocket_connections": 0,  # Would need websocket manager
            "active_background_tasks": 0
        }

        # Recent activity (mock - would fetch from audit log)
        recent_activity = [
            {
                "type": "new_property",
                "description": "New property listed in Mumbai",
                "user": "Agent Johnson",
                "timestamp": (now - timedelta(minutes=5)).isoformat()
            },
            {
                "type": "user_registration",
                "description": "New user registered",
                "user": "john@example.com",
                "timestamp": (now - timedelta(minutes=15)).isoformat()
            },
            {
                "type": "inquiry",
                "description": "New inquiry for Villa in Bangalore",
                "user": "Potential Buyer",
                "timestamp": (now - timedelta(minutes=30)).isoformat()
            }
        ]

        return {
            "stats": {
                "total_users": total_users,
                "total_properties": total_properties,
                "active_properties": active_properties,
                "total_inquiries": total_inquiries,
                "revenue_today": round(revenue_today, 2),
                "revenue_this_month": round(revenue_this_month, 2)
            },
            "realtime": realtime_data,
            "alerts": recent_alerts,
            "forecasts": forecasts,
            "system_health": system_health,
            "recent_activity": recent_activity,
            "timestamp": now.isoformat()
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/users/management")
async def get_user_management(
    page: int = 1,
    limit: int = 50,
    search: Optional[str] = None,
    role: Optional[str] = None,
    database=Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get users for management"""
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")

    try:
        query = {}
        if search:
            query["$or"] = [
                {"email": {"$regex": search, "$options": "i"}},
                {"full_name": {"$regex": search, "$options": "i"}}
            ]
        if role:
            query["role"] = role

        skip = (page - 1) * limit

        users = await database.users.find(query).skip(skip).limit(limit).to_list(length=limit)
        total = await database.users.count_documents(query)

        # Format users
        formatted_users = []
        for user in users:
            formatted_users.append({
                "id": str(user["_id"]),
                "email": user.get("email"),
                "full_name": user.get("full_name"),
                "role": user.get("role"),
                "status": user.get("status", "active"),
                "created_at": user.get("created_at"),
                "last_login": user.get("last_login"),
                "properties_count": await database.properties.count_documents({"user_id": str(user["_id"])})
            })

        return {
            "users": formatted_users,
            "pagination": {
                "page": page,
                "limit": limit,
                "total": total,
                "pages": (total + limit - 1) // limit
            }
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/properties/management")
async def get_property_management(
    page: int = 1,
    limit: int = 50,
    status: Optional[str] = None,
    city: Optional[str] = None,
    database=Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get properties for management"""
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")

    try:
        query = {}
        if status:
            query["status"] = status
        if city:
            query["city"] = city

        skip = (page - 1) * limit

        properties = await database.properties.find(query).skip(skip).limit(limit).to_list(length=limit)
        total = await database.properties.count_documents(query)

        formatted_properties = []
        for prop in properties:
            formatted_properties.append({
                "id": str(prop["_id"]),
                "title": prop.get("title"),
                "city": prop.get("city"),
                "price": prop.get("price"),
                "status": prop.get("status"),
                "property_type": prop.get("property_type"),
                "created_at": prop.get("created_at"),
                "views": prop.get("view_count", 0),
                "inquiries": await database.inquiries.count_documents({"property_id": str(prop["_id"])})
            })

        return {
            "properties": formatted_properties,
            "pagination": {
                "page": page,
                "limit": limit,
                "total": total,
                "pages": (total + limit - 1) // limit
            }
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/inquiries/management")
async def get_inquiry_management(
    page: int = 1,
    limit: int = 50,
    status: Optional[str] = None,
    database=Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get inquiries for management"""
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")

    try:
        query = {}
        if status:
            query["status"] = status

        skip = (page - 1) * limit

        inquiries = await database.inquiries.find(query).sort("created_at", -1).skip(skip).limit(limit).to_list(length=limit)
        total = await database.inquiries.count_documents(query)

        formatted_inquiries = []
        for inquiry in inquiries:
            # Get property info
            property_info = await database.properties.find_one({"_id": inquiry.get("property_id")})

            # Get user info
            user_info = await database.users.find_one({"_id": inquiry.get("user_id")})

            formatted_inquiries.append({
                "id": str(inquiry["_id"]),
                "property_title": property_info.get("title") if property_info else "Unknown",
                "user_email": user_info.get("email") if user_info else "Unknown",
                "message": inquiry.get("message", "")[:100] + "..." if len(inquiry.get("message", "")) > 100 else inquiry.get("message", ""),
                "status": inquiry.get("status"),
                "created_at": inquiry.get("created_at"),
                "response_count": inquiry.get("response_count", 0)
            })

        return {
            "inquiries": formatted_inquiries,
            "pagination": {
                "page": page,
                "limit": limit,
                "total": total,
                "pages": (total + limit - 1) // limit
            }
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ========== AI Image Generation Management ==========

@router.post("/ai/generate-property-image")
async def generate_property_image(
    property_id: str,
    style: str = "modern",
    background_tasks: BackgroundTasks = None,
    database=Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Generate AI image for property"""
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")

    try:
        # Get property data
        property_data = await database.properties.find_one({"_id": property_id})
        if not property_data:
            raise HTTPException(status_code=404, detail="Property not found")

        # Queue for generation
        await ai_image_generator.queue_generation({
            "type": "property",
            "data": property_data,
            "style": style
        })

        return {
            "message": "Property image generation queued",
            "property_id": property_id,
            "style": style,
            "status": "queued"
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/ai/generate-market-visual")
async def generate_market_visual(
    city: str,
    chart_type: str = "trend",
    background_tasks: BackgroundTasks = None,
    database=Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Generate market visualization"""
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")

    try:
        # Get market data
        pipeline = [
            {"$match": {"city": city, "created_at": {"$gte": datetime.utcnow() - timedelta(days=30)}}},
            {"$group": {"_id": {"$dateToString": {"format": "%Y-%m-%d", "date": "$created_at"}}, "avg_price": {"$avg": "$price"}}},
            {"$sort": {"_id": 1}}
        ]
        market_data = await database.properties.aggregate(pipeline).to_list(length=30)

        # Queue for generation
        await ai_image_generator.queue_generation({
            "type": "market",
            "data": {"city": city, "trend": "upward", "market_data": market_data},
            "chart_type": chart_type
        })

        return {
            "message": "Market visualization generation queued",
            "city": city,
            "chart_type": chart_type
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/ai/generated-images")
async def get_generated_images(
    image_type: Optional[str] = None,
    limit: int = 20,
    database=Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get list of AI generated images"""
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")

    try:
        query = {}
        if image_type:
            query["image_type"] = image_type

        images = await database.ai_images.find(query).sort("created_at", -1).limit(limit).to_list(length=limit)

        return {
            "images": [
                {
                    "id": img["id"],
                    "prompt": img["prompt"][:100] + "..." if len(img["prompt"]) > 100 else img["prompt"],
                    "image_type": img["image_type"],
                    "created_at": img["created_at"],
                    "metadata": img.get("metadata", {})
                }
                for img in images
            ],
            "total": await database.ai_images.count_documents(query)
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ========== System Management ==========

@router.post("/system/clear-cache")
async def admin_clear_cache(
    pattern: str = "*",
    database=Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Clear cache (admin only)"""
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")

    try:
        from app.cache import invalidate_cache_pattern
        from app.cache_pipeline import local_cache

        await invalidate_cache_pattern(pattern)
        local_cache.clear()

        return {"message": f"Cache cleared for pattern: {pattern}"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/system/warm-cache")
async def admin_warm_cache(
    cache_types: List[str],
    database=Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Warm cache (admin only)"""
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")

    try:
        warmed = []

        if "analytics" in cache_types:
            from app.analytics import analytics_manager
            await analytics_manager.get_dashboard_analytics(database)
            warmed.append("analytics")

        if "properties" in cache_types:
            await cache_warmer.warm_property_cache(database, limit=100)
            warmed.append("properties")

        return {"message": "Cache warmed", "warmed_types": warmed}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/system/logs")
async def get_system_logs(
    lines: int = 100,
    level: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """Get system logs (admin only)"""
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")

    try:
        # Read last N lines from log file
        logs = []
        try:
            with open('app.log', 'r') as f:
                all_lines = f.readlines()
                logs = all_lines[-lines:]
        except FileNotFoundError:
            logs = ["Log file not found"]

        if level:
            logs = [line for line in logs if level.upper() in line.upper()]

        return {
            "logs": logs,
            "total_lines": len(logs),
            "level_filter": level
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
