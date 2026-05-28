"""
Enhanced Property Routes with Aggressive Caching
Additional cached endpoints for property management
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List, Optional, Dict, Any
from datetime import datetime

from app.database import get_db
from app.auth import get_current_user
from app.cache import get_from_cache, set_in_cache, generate_cache_key, invalidate_cache_pattern
from app.cache_decorators import cached, cache_invalidate, cached_list, cached_detail
from app.cache_pipeline import redis_pipeline, local_cache, cache_warmer
from app.feature_flags import require_feature_flag
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/properties-cached", tags=["Properties Cached"])


# ========== Cached Property List Endpoints ==========

@router.get("/popular")
@cached_list(ttl=1800, key_prefix="properties:popular")  # 30 minutes
async def get_popular_properties(
    limit: int = Query(20, ge=1, le=100),
    database=Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get most popular properties (cached for 30 minutes)"""
    try:
        pipeline = [
            {"$sort": {"view_count": -1}},
            {"$limit": limit},
            {"$project": {
                "_id": 1,
                "title": 1,
                "price": 1,
                "city": 1,
                "property_type": 1,
                "bedrooms": 1,
                "bathrooms": 1,
                "area_sqft": 1,
                "image_url": 1,
                "view_count": 1
            }}
        ]

        properties = await database.properties.aggregate(pipeline).to_list(length=limit)

        for prop in properties:
            prop["id"] = str(prop["_id"])
            del prop["_id"]

        return properties

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/featured")
@cached(ttl=3600, key_prefix="properties:featured")  # 1 hour
async def get_featured_properties(
    limit: int = Query(10, ge=1, le=50),
    database=Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get featured/premium properties (cached for 1 hour)"""
    try:
        properties = await database.properties.find(
            {"featured": True, "status": "active"}
        ).sort("created_at", -1).limit(limit).to_list(length=limit)

        for prop in properties:
            prop["id"] = str(prop["_id"])
            del prop["_id"]

        return properties

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/recent")
@cached_list(ttl=600, key_prefix="properties:recent")  # 10 minutes
async def get_recent_properties(
    limit: int = Query(20, ge=1, le=100),
    database=Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get recently added properties (cached for 10 minutes)"""
    try:
        properties = await database.properties.find(
            {"status": "active"}
        ).sort("created_at", -1).limit(limit).to_list(length=limit)

        for prop in properties:
            prop["id"] = str(prop["_id"])
            del prop["_id"]

        return properties

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/by-city/{city}")
@cached(ttl=900, key_prefix="properties:city")  # 15 minutes
async def get_properties_by_city(
    city: str,
    limit: int = Query(50, ge=1, le=200),
    database=Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get properties by city (cached for 15 minutes)"""
    try:
        properties = await database.properties.find(
            {"city": city, "status": "active"}
        ).sort("created_at", -1).limit(limit).to_list(length=limit)

        for prop in properties:
            prop["id"] = str(prop["_id"])
            del prop["_id"]

        return {
            "city": city,
            "count": len(properties),
            "properties": properties
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ========== Cached Property Statistics ==========

@router.get("/stats/overview")
@cached(ttl=600, key_prefix="properties:stats:overview")  # 10 minutes
async def get_property_stats_overview(
    database=Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get property statistics overview (cached for 10 minutes)"""
    try:
        # Use aggregation for efficient counting
        pipeline = [
            {"$group": {
                "_id": None,
                "total": {"$sum": 1},
                "active": {"$sum": {"$cond": [{"$eq": ["$status", "active"]}, 1, 0]}},
                "sold": {"$sum": {"$cond": [{"$eq": ["$status", "sold"]}, 1, 0]}},
                "avg_price": {"$avg": "$price"},
                "max_price": {"$max": "$price"},
                "min_price": {"$min": "$price"}
            }}
        ]

        result = await database.properties.aggregate(pipeline).to_list(length=1)

        if result:
            stats = result[0]
            del stats["_id"]

            # Get city distribution
            city_pipeline = [
                {"$group": {"_id": "$city", "count": {"$sum": 1}}},
                {"$sort": {"count": -1}},
                {"$limit": 10}
            ]
            cities = await database.properties.aggregate(city_pipeline).to_list(length=10)

            stats["top_cities"] = [{"city": c["_id"], "count": c["count"]} for c in cities]

            return stats

        return {"total": 0, "active": 0, "sold": 0}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats/by-type")
@cached(ttl=1800, key_prefix="properties:stats:by_type")  # 30 minutes
async def get_property_stats_by_type(
    database=Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get property statistics by type (cached for 30 minutes)"""
    try:
        pipeline = [
            {"$group": {
                "_id": "$property_type",
                "count": {"$sum": 1},
                "avg_price": {"$avg": "$price"},
                "avg_area": {"$avg": "$area_sqft"}
            }},
            {"$sort": {"count": -1}}
        ]

        results = await database.properties.aggregate(pipeline).to_list(length=20)

        return [
            {
                "property_type": r["_id"],
                "count": r["count"],
                "average_price": r["avg_price"],
                "average_area": r["avg_area"]
            }
            for r in results
        ]

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ========== Cached Search & Filter ==========

@router.post("/search-cached")
@cached(ttl=300, key_prefix="properties:search", vary_on_query=True)  # 5 minutes
async def search_properties_cached(
    search_query: Dict[str, Any],
    database=Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Cached property search (5 minutes)"""
    try:
        # Build query from search parameters
        query = {"status": "active"}

        if "city" in search_query:
            query["city"] = search_query["city"]

        if "property_type" in search_query:
            query["property_type"] = search_query["property_type"]

        if "min_price" in search_query or "max_price" in search_query:
            query["price"] = {}
            if "min_price" in search_query:
                query["price"]["$gte"] = search_query["min_price"]
            if "max_price" in search_query:
                query["price"]["$lte"] = search_query["max_price"]

        if "bedrooms" in search_query:
            query["bedrooms"] = {"$gte": search_query["bedrooms"]}

        # Execute search
        limit = search_query.get("limit", 50)
        properties = await database.properties.find(query).limit(limit).to_list(length=limit)

        for prop in properties:
            prop["id"] = str(prop["_id"])
            del prop["_id"]

        return {
            "count": len(properties),
            "query": query,
            "results": properties
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ========== Cache Warming Endpoints ==========

@router.post("/warm-cache")
async def warm_property_cache(
    database=Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Manually warm property cache"""
    if current_user.get("role") not in ["admin", "agent"]:
        raise HTTPException(status_code=403, detail="Admin or agent access required")

    try:
        await cache_warmer.warm_property_cache(database, limit=100)

        return {
            "message": "Property cache warmed successfully",
            "timestamp": datetime.utcnow()
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ========== Bulk Operations with Cache ==========

@router.get("/bulk/details")
async def get_properties_bulk_details(
    property_ids: str,  # Comma-separated IDs
    database=Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get multiple property details in one request (with caching)"""
    try:
        ids = [id.strip() for id in property_ids.split(",") if id.strip()]

        if len(ids) > 100:
            raise HTTPException(status_code=400, detail="Maximum 100 IDs allowed")

        # Generate cache keys
        cache_keys = [f"property:{id}" for id in ids]

        # Try to get from cache in bulk
        cached_results = await redis_pipeline.get_many(cache_keys)

        # Find missing IDs
        found_ids = set()
        for key, value in cached_results.items():
            if value:
                prop_id = key.replace("property:", "")
                found_ids.add(prop_id)

        missing_ids = [id for id in ids if id not in found_ids]

        # Fetch missing from database
        if missing_ids:
            properties = await database.properties.find(
                {"_id": {"$in": missing_ids}}
            ).to_list(length=len(missing_ids))

            # Cache the newly fetched properties
            new_cache_entries = {}
            for prop in properties:
                prop["id"] = str(prop["_id"])
                del prop["_id"]
                new_cache_entries[f"property:{prop['id']}"] = prop

            if new_cache_entries:
                await redis_pipeline.set_many(new_cache_entries, ttl=3600)

            # Merge results
            cached_results.update(new_cache_entries)

        # Format response
        results = []
        for id in ids:
            key = f"property:{id}"
            if key in cached_results:
                results.append(cached_results[key])

        return {
            "requested": len(ids),
            "found": len(results),
            "properties": results
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
