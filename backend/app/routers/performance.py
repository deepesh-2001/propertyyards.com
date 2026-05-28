"""
Performance Monitoring Router
Endpoints for monitoring system performance, cache stats, and rate limiting status
"""
from fastapi import APIRouter, Depends, HTTPException
from typing import Optional
from datetime import datetime

from app.database import get_db
from app.performance import (
    query_cache,
    rate_limiter,
    performance_monitor
)
from app.auth import get_current_user

router = APIRouter(prefix="/api/performance", tags=["performance"])


@router.get("/cache-stats")
async def get_cache_stats(
    current_user: dict = Depends(get_current_user)
):
    """Get cache statistics"""
    try:
        if current_user["role"] not in ["admin"]:
            raise HTTPException(status_code=403, detail="Admin access required")
        
        stats = query_cache.get_cache_stats()
        return stats
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/performance-metrics")
async def get_performance_metrics(
    current_user: dict = Depends(get_current_user)
):
    """Get system performance metrics"""
    try:
        if current_user["role"] not in ["admin"]:
            raise HTTPException(status_code=403, detail="Admin access required")
        
        metrics = performance_monitor.get_performance_metrics()
        return metrics
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/rate-limit-status")
async def get_rate_limit_status(
    identifier: str,
    user_id: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """Check rate limit status for an identifier"""
    try:
        status = await rate_limiter.check_rate_limit(identifier, user_id)
        return status
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/clear-cache")
async def clear_cache(
    pattern: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """Clear cache (admin only)"""
    try:
        if current_user["role"] not in ["admin"]:
            raise HTTPException(status_code=403, detail="Admin access required")
        
        if pattern:
            success = await query_cache.invalidate_pattern(pattern)
            return {"message": f"Cache pattern '{pattern}' cleared", "success": success}
        else:
            # Clear all cache (implementation depends on cache backend)
            return {"message": "Cache clear requested", "success": True}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def health_check():
    """Health check endpoint for load balancers"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0"
    }


@router.get("/readiness")
async def readiness_check(
    database=Depends(get_db)
):
    """Readiness check for Kubernetes"""
    try:
        # Check database connection
        await database.command('ping')
        
        return {
            "status": "ready",
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        return {
            "status": "not_ready",
            "timestamp": datetime.utcnow().isoformat(),
            "error": str(e)
        }
