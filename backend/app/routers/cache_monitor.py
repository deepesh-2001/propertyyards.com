"""
Cache Monitoring Router
API endpoints for cache monitoring, metrics, and management
"""
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from typing import Optional, Dict, Any, List
from pydantic import BaseModel

from app.database import get_db
from app.auth import require_admin
from app.cache import (
    cache_metrics, cache_warmer, cache_invalidator, cache_monitor,
    get_cache_info, invalidate_cache_pattern, cache_with_fallback,
    smart_cache_update
)

router = APIRouter(prefix="/api/cache", tags=["cache-monitor"])


# ========== Request Models ==========

class CacheWarmJobRequest(BaseModel):
    name: str
    cache_key: str
    ttl: int = 3600


class CacheInvalidateRequest(BaseModel):
    pattern: str
    with_dependencies: bool = False


class SmartCacheUpdateRequest(BaseModel):
    key: str
    data: Dict[str, Any]
    ttl: Optional[int] = None


# ========== Monitoring Endpoints ==========

@router.get("/metrics")
async def get_cache_metrics(
    current_user: dict = Depends(require_admin())
):
    """Get comprehensive cache metrics"""
    try:
        app_metrics = cache_monitor.get_metrics_summary()
        redis_info = await get_cache_info()
        
        return {
            "application_metrics": app_metrics,
            "redis_info": redis_info,
            "performance_alerts": cache_monitor.check_performance()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def get_cache_health():
    """Get cache health status"""
    try:
        redis_info = await get_cache_info()
        
        if "error" in redis_info:
            return {
                "status": "unhealthy",
                "error": redis_info["error"],
                "timestamp": cache_monitor.get_metrics_summary()["timestamp"]
            }
        
        metrics = cache_monitor.get_metrics_summary()
        alerts = cache_monitor.check_performance()
        
        status = "healthy"
        if alerts:
            status = "degraded"
        
        return {
            "status": status,
            "redis_connected": True,
            "hit_rate": metrics["hit_rate"],
            "avg_response_time_ms": metrics["avg_response_time_ms"],
            "alerts": alerts,
            "timestamp": metrics["timestamp"]
        }
        
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": cache_monitor.get_metrics_summary()["timestamp"]
        }


@router.get("/info")
async def get_cache_info_endpoint(
    current_user: dict = Depends(require_admin())
):
    """Get detailed Redis cache information"""
    return await get_cache_info()


# ========== Management Endpoints ==========

@router.post("/invalidate")
async def invalidate_cache(
    request: CacheInvalidateRequest,
    current_user: dict = Depends(require_admin())
):
    """Invalidate cache keys by pattern"""
    try:
        if request.with_dependencies:
            invalidated_count = await cache_invalidator.invalidate_with_dependencies(request.pattern)
        else:
            invalidated_count = await invalidate_cache_pattern(request.pattern)
        
        return {
            "success": True,
            "pattern": request.pattern,
            "keys_invalidated": invalidated_count,
            "with_dependencies": request.with_dependencies
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/warm/register")
async def register_warm_job(
    request: CacheWarmJobRequest,
    current_user: dict = Depends(require_admin())
):
    """Register a cache warming job"""
    try:
        # This is a simplified version - in production, you'd need a proper data loader
        async def sample_data_loader():
            return {"sample": "data", "timestamp": "now"}
        
        cache_warmer.register_warm_job(
            name=request.name,
            cache_key=request.cache_key,
            data_loader=sample_data_loader,
            ttl=request.ttl
        )
        
        return {
            "success": True,
            "message": f"Cache warm job registered: {request.name}",
            "job": {
                "name": request.name,
                "cache_key": request.cache_key,
                "ttl": request.ttl
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/warm/jobs")
async def get_warm_jobs(
    current_user: dict = Depends(require_admin())
):
    """Get registered cache warming jobs"""
    return {
        "jobs": [
            {
                "name": name,
                "cache_key": job["cache_key"],
                "ttl": job["ttl"],
                "interval": job["interval"],
                "last_warmed": job["last_warmed"]
            }
            for name, job in cache_warmer.warming_jobs.items()
        ],
        "total_jobs": len(cache_warmer.warming_jobs),
        "warming_active": cache_warmer.running
    }


@router.post("/warm/start")
async def start_cache_warming(
    current_user: dict = Depends(require_admin())
):
    """Start cache warming service"""
    try:
        await cache_warmer.start_warming()
        return {
            "success": True,
            "message": "Cache warming started"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/warm/stop")
async def stop_cache_warming(
    current_user: dict = Depends(require_admin())
):
    """Stop cache warming service"""
    try:
        await cache_warmer.stop_warming()
        return {
            "success": True,
            "message": "Cache warming stopped"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/smart-update")
async def smart_update_cache(
    request: SmartCacheUpdateRequest,
    current_user: dict = Depends(require_admin())
):
    """Smart cache update with conditional logic"""
    try:
        success = await smart_cache_update(
            key=request.key,
            data=request.data,
            ttl=request.ttl
        )
        
        return {
            "success": success,
            "key": request.key,
            "message": "Cache updated successfully" if success else "Cache update failed"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/dependencies")
async def get_cache_dependencies(
    current_user: dict = Depends(require_admin())
):
    """Get registered cache dependencies"""
    return {
        "dependencies": cache_invalidator.invalidations
    }


@router.post("/dependencies/register")
async def register_cache_dependency(
    pattern: str,
    dependent_patterns: List[str],
    current_user: dict = Depends(require_admin())
):
    """Register cache dependency"""
    try:
        cache_invalidator.register_dependency(pattern, dependent_patterns)
        
        return {
            "success": True,
            "pattern": pattern,
            "dependent_patterns": dependent_patterns,
            "message": f"Dependency registered: {pattern} -> {dependent_patterns}"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ========== Performance Analysis ==========

@router.get("/performance")
async def get_performance_analysis(
    current_user: dict = Depends(require_admin())
):
    """Get detailed performance analysis"""
    try:
        metrics = cache_monitor.get_metrics_summary()
        redis_info = await get_cache_info()
        
        analysis = {
            "hit_rate_analysis": {
                "current": metrics["hit_rate"],
                "status": "good" if metrics["hit_rate"] >= 70 else "needs_improvement",
                "recommendation": "Hit rate is healthy" if metrics["hit_rate"] >= 70 else "Consider adjusting cache TTL or warming strategies"
            },
            "response_time_analysis": {
                "current_ms": metrics["avg_response_time_ms"],
                "status": "good" if metrics["avg_response_time_ms"] <= 10 else "slow",
                "recommendation": "Response time is optimal" if metrics["avg_response_time_ms"] <= 10 else "Check Redis performance and network latency"
            },
            "error_rate_analysis": {
                "error_count": metrics["errors"],
                "total_operations": metrics["total_operations"],
                "error_rate": (metrics["errors"] / metrics["total_operations"] * 100) if metrics["total_operations"] > 0 else 0,
                "status": "good" if metrics["errors"] == 0 else "investigate"
            },
            "memory_analysis": {
                "redis_memory": redis_info.get("used_memory", "N/A"),
                "connected_clients": redis_info.get("connected_clients", "N/A"),
                "uptime_seconds": redis_info.get("uptime_in_seconds", "N/A")
            }
        }
        
        return {
            "metrics": metrics,
            "redis_info": redis_info,
            "analysis": analysis,
            "alerts": cache_monitor.check_performance()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ========== Utility Endpoints ==========

@router.post("/test")
async def test_cache_performance(
    iterations: int = 100,
    current_user: dict = Depends(require_admin())
):
    """Test cache performance with sample operations"""
    try:
        import time
        import random
        
        test_key = f"test_cache_{random.randint(1000, 9999)}"
        test_data = {"test": "data", "timestamp": time.time()}
        
        # Test write performance
        write_times = []
        for i in range(iterations):
            start = time.time()
            await smart_cache_update(f"{test_key}_{i}", test_data, 60)
            write_times.append(time.time() - start)
        
        # Test read performance
        read_times = []
        for i in range(iterations):
            start = time.time()
            await cache_with_fallback(f"{test_key}_{i}", lambda: test_data, 60)
            read_times.append(time.time() - start)
        
        # Cleanup
        await invalidate_cache_pattern(f"{test_key}_*")
        
        avg_write_time = sum(write_times) / len(write_times) * 1000  # ms
        avg_read_time = sum(read_times) / len(read_times) * 1000  # ms
        
        return {
            "test_iterations": iterations,
            "write_performance": {
                "avg_time_ms": avg_write_time,
                "total_time_ms": sum(write_times) * 1000,
                "ops_per_second": iterations / (sum(write_times))
            },
            "read_performance": {
                "avg_time_ms": avg_read_time,
                "total_time_ms": sum(read_times) * 1000,
                "ops_per_second": iterations / (sum(read_times))
            },
            "message": "Cache performance test completed"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
