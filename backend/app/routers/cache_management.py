"""
Cache Management Router
Handles cache warming, statistics, and manual cache operations
"""
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from typing import Dict, Any, List, Optional
from pydantic import BaseModel
from datetime import datetime

from app.database import get_db
from app.auth import get_current_user
from app.cache import get_from_cache, set_in_cache, delete_from_cache, invalidate_cache_pattern
from app.persistent_cache import persistent_cache
from app.cache_pipeline import redis_pipeline, cache_warmer, local_cache
from app.background_tasks import background_processor, analytics_processor

router = APIRouter(prefix="/api/cache", tags=["cache-management"])


class CacheWarmRequest(BaseModel):
    """Request to warm specific caches"""
    cache_types: List[str] = ["analytics", "properties", "users"]
    force_refresh: bool = False


class CacheInvalidateRequest(BaseModel):
    """Request to invalidate caches"""
    pattern: str
    include_persistent: bool = True


class CacheEntryRequest(BaseModel):
    """Request to get/set cache entry"""
    key: str
    value: Optional[Any] = None
    ttl: int = 3600


# ========== Cache Statistics ==========

@router.get("/stats")
async def get_cache_stats(
    database=Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get comprehensive cache statistics"""
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")

    try:
        # Get persistent cache stats
        persistent_stats = await persistent_cache.get_cache_stats(database)

        # Get local cache stats
        local_stats = {
            "size": len(local_cache._cache),
            "max_size": local_cache.max_size,
            "ttl_entries": len(local_cache._ttl)
        }

        return {
            "persistent_cache": persistent_stats,
            "local_cache": local_stats,
            "generated_at": datetime.utcnow()
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ========== Cache Warming ==========

@router.post("/warm")
async def warm_cache(
    request: CacheWarmRequest,
    background_tasks: BackgroundTasks,
    database=Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Warm caches in the background"""
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")

    try:
        warmed_caches = []

        if "analytics" in request.cache_types:
            background_tasks.add_task(
                analytics_processor.precompute_daily_analytics,
                database
            )
            warmed_caches.append("analytics")

        if "properties" in request.cache_types:
            background_tasks.add_task(
                cache_warmer.warm_property_cache,
                database,
                100
            )
            warmed_caches.append("properties")

        if "users" in request.cache_types:
            # Warm user caches
            background_tasks.add_task(
                _warm_user_cache,
                database
            )
            warmed_caches.append("users")

        return {
            "message": "Cache warming started",
            "warmed_caches": warmed_caches,
            "force_refresh": request.force_refresh
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


async def _warm_user_cache(database):
    """Warm user cache"""
    try:
        users = await database.users.find().limit(100).to_list(length=100)
        cache_data = {
            f"user:{str(user['_id'])}": {
                "id": str(user["_id"]),
                "email": user.get("email"),
                "role": user.get("role"),
                "full_name": user.get("full_name")
            }
            for user in users
        }
        await redis_pipeline.set_many(cache_data, ttl=1800)
    except Exception as e:
        print(f"User cache warming error: {e}")


# ========== Cache Invalidation ==========

@router.post("/invalidate")
async def invalidate_cache(
    request: CacheInvalidateRequest,
    database=Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Invalidate caches by pattern"""
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")

    try:
        # Invalidate Redis cache
        await invalidate_cache_pattern(request.pattern)

        # Clear local cache if pattern matches all
        if request.pattern == "*" or request.pattern == "**":
            local_cache.clear()

        # Invalidate persistent cache
        if request.include_persistent:
            await persistent_cache.invalidate_pattern(request.pattern, database)

        return {
            "message": "Cache invalidation completed",
            "pattern": request.pattern,
            "include_persistent": request.include_persistent
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/key/{key}")
async def delete_cache_key(
    key: str,
    database=Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Delete a specific cache key"""
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")

    try:
        # Delete from Redis
        await delete_from_cache(key)

        # Delete from local cache
        local_cache.delete(key)

        # Delete from persistent cache
        await database.cache.delete_one({"key": key})

        return {"message": f"Cache key '{key}' deleted"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ========== Cache Inspection ==========

@router.get("/key/{key}")
async def get_cache_entry(
    key: str,
    database=Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get a specific cache entry"""
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")

    try:
        # Try local cache first
        local_value = local_cache.get(key)
        if local_value:
            return {
                "key": key,
                "value": local_value,
                "source": "local_cache",
                "ttl_remaining": local_cache._ttl.get(key, 0) - datetime.utcnow().timestamp()
            }

        # Try Redis
        redis_value = await get_from_cache(key)
        if redis_value:
            return {
                "key": key,
                "value": redis_value,
                "source": "redis",
                "ttl_remaining": "unknown"
            }

        # Try persistent cache
        persistent_entry = await database.cache.find_one({"key": key})
        if persistent_entry:
            return {
                "key": key,
                "value": persistent_entry["value"],
                "source": "persistent_db",
                "created_at": persistent_entry["created_at"],
                "expires_at": persistent_entry["expires_at"],
                "access_count": persistent_entry.get("access_count", 0)
            }

        raise HTTPException(status_code=404, detail="Cache key not found")

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/key")
async def set_cache_entry(
    request: CacheEntryRequest,
    database=Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Set a cache entry manually"""
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")

    try:
        # Set in Redis
        await set_in_cache(request.key, request.value, ttl=request.ttl)

        # Set in local cache
        local_cache.set(request.key, request.value, ttl=min(request.ttl, 300))

        # Set in persistent cache
        await persistent_cache._store_in_db_cache(
            request.key,
            request.value,
            request.ttl,
            database
        )

        return {
            "message": "Cache entry set",
            "key": request.key,
            "ttl": request.ttl
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ========== Bulk Cache Operations ==========

@router.post("/bulk-get")
async def bulk_get_cache(
    keys: List[str],
    current_user: dict = Depends(get_current_user)
):
    """Get multiple cache entries at once"""
    try:
        results = {}

        # Check local cache first
        for key in keys:
            local_value = local_cache.get(key)
            if local_value:
                results[key] = {"value": local_value, "source": "local"}

        # Get remaining from Redis
        remaining_keys = [k for k in keys if k not in results]
        if remaining_keys:
            redis_results = await redis_pipeline.get_many(remaining_keys)
            for key, value in redis_results.items():
                if value:
                    results[key] = {"value": value, "source": "redis"}
                    # Update local cache
                    local_cache.set(key, value, ttl=60)

        return {
            "found": len(results),
            "total": len(keys),
            "results": results
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/bulk-set")
async def bulk_set_cache(
    entries: Dict[str, Any],
    ttl: int = 3600,
    current_user: dict = Depends(get_current_user)
):
    """Set multiple cache entries at once"""
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")

    try:
        # Set in Redis using pipeline
        await redis_pipeline.set_many(entries, ttl=ttl)

        # Set in local cache
        for key, value in entries.items():
            local_cache.set(key, value, ttl=min(ttl, 300))

        return {
            "message": "Bulk cache set completed",
            "count": len(entries),
            "ttl": ttl
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ========== Cache Cleanup ==========

@router.post("/cleanup")
async def cleanup_cache(
    database=Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Clean up expired cache entries"""
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")

    try:
        # Clean up persistent cache
        cleaned_count = await persistent_cache.cleanup_expired(database)

        # Clean up local cache (expired items are auto-removed on access)
        local_cache.clear()

        return {
            "message": "Cache cleanup completed",
            "persistent_cleaned": cleaned_count,
            "local_cleared": True
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ========== Preload Popular Data ==========

@router.post("/preload")
async def preload_popular_data(
    background_tasks: BackgroundTasks,
    database=Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Preload popular data into cache"""
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")

    try:
        # Preload in background
        background_tasks.add_task(_preload_all_popular_data, database)

        return {
            "message": "Preloading started",
            "preloaded_items": [
                "popular_properties",
                "analytics_dashboard",
                "featured_listings",
                "top_cities",
                "recent_inquiries"
            ]
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


async def _preload_all_popular_data(database):
    """Preload all popular data"""
    try:
        # Preload popular properties
        popular_props = await database.properties.find(
            {"view_count": {"$gt": 100}}
        ).sort("view_count", -1).limit(50).to_list(length=50)

        prop_cache = {
            f"property:popular:{str(p['_id'])}": {
                "id": str(p["_id"]),
                "title": p.get("title"),
                "price": p.get("price"),
                "city": p.get("city"),
                "view_count": p.get("view_count", 0)
            }
            for p in popular_props
        }
        await redis_pipeline.set_many(prop_cache, ttl=7200)  # 2 hours

        # Preload top cities
        pipeline = [
            {"$group": {"_id": "$city", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}},
            {"$limit": 20}
        ]
        cities = await database.properties.aggregate(pipeline).to_list(length=20)
        await set_in_cache("top_cities", cities, ttl=86400)  # 24 hours

        print("Popular data preloaded successfully")

    except Exception as e:
        print(f"Preload error: {e}")
