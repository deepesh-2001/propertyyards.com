"""
Health check endpoints and system monitoring
"""
from fastapi import APIRouter, HTTPException
from datetime import datetime
import psutil
import platform
import socket
import os
from app.database import client
from app.cache import cache, get_from_cache
from app.config import settings
from app import cron
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/health", tags=["Health"])


async def check_database():
    """Check MongoDB connection"""
    try:
        if client:
            await client.admin.command('ping')
            return {"status": "healthy", "type": "mongodb"}
        return {"status": "unhealthy", "type": "mongodb", "message": "No client"}
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return {"status": "unhealthy", "type": "mongodb", "message": str(e)}


async def check_cache():
    """Check Redis connection"""
    try:
        if cache:
            await cache.ping()
            return {"status": "healthy", "type": "redis"}
        return {"status": "unhealthy", "type": "redis", "message": "No cache"}
    except Exception as e:
        logger.error(f"Cache health check failed: {e}")
        return {"status": "unhealthy", "type": "redis", "message": str(e)}


def get_system_info():
    """Get system information"""
    return {
        "hostname": socket.gethostname(),
        "platform": platform.system(),
        "platform_release": platform.release(),
        "platform_version": platform.version(),
        "architecture": platform.machine(),
        "processor": platform.processor(),
        "python_version": platform.python_version()
    }


def get_pod_info():
    """Get pod/container information"""
    pod_info = {
        "pod_name": os.environ.get("POD_NAME", "unknown"),
        "pod_namespace": os.environ.get("POD_NAMESPACE", "unknown"),
        "pod_ip": os.environ.get("POD_IP", "unknown"),
        "node_name": os.environ.get("NODE_NAME", "unknown"),
        "container_id": os.environ.get("HOSTNAME", "unknown")[:12],
        "environment": settings.ENVIRONMENT
    }
    return pod_info


def get_system_metrics():
    """Get system metrics"""
    try:
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        return {
            "cpu": {
                "percent": cpu_percent,
                "core_count": psutil.cpu_count()
            },
            "memory": {
                "total": memory.total,
                "available": memory.available,
                "percent": memory.percent,
                "used": memory.used
            },
            "disk": {
                "total": disk.total,
                "used": disk.used,
                "free": disk.free,
                "percent": disk.percent
            },
            "load_average": os.getloadavg() if hasattr(os, 'getloadavg') else None
        }
    except Exception as e:
        logger.error(f"Failed to get system metrics: {e}")
        return {"error": str(e)}


@router.get("/")
async def health_check():
    """Basic health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "environment": settings.ENVIRONMENT,
        "version": settings.API_VERSION
    }


@router.get("/detailed")
async def detailed_health_check():
    """Detailed health check with all services"""
    db_status = await check_database()
    cache_status = await check_cache()
    
    overall_status = "healthy" if all(
        s["status"] == "healthy" for s in [db_status, cache_status]
    ) else "degraded"
    
    return {
        "status": overall_status,
        "timestamp": datetime.utcnow().isoformat(),
        "environment": settings.ENVIRONMENT,
        "services": {
            "database": db_status,
            "cache": cache_status
        },
        "system": get_system_info(),
        "pod": get_pod_info()
    }


@router.get("/ready")
async def readiness_check():
    """Readiness check - indicates if the pod is ready to serve traffic"""
    db_status = await check_database()
    cache_status = await check_cache()
    
    if db_status["status"] != "healthy":
        raise HTTPException(status_code=503, detail="Database not ready")
    
    if cache_status["status"] != "healthy":
        raise HTTPException(status_code=503, detail="Cache not ready")
    
    return {
        "status": "ready",
        "timestamp": datetime.utcnow().isoformat()
    }


@router.get("/live")
async def liveness_check():
    """Liveness check - indicates if the pod is still running"""
    return {
        "status": "alive",
        "timestamp": datetime.utcnow().isoformat()
    }


@router.get("/metrics")
async def metrics():
    """System metrics endpoint"""
    return {
        "timestamp": datetime.utcnow().isoformat(),
        "system": get_system_metrics(),
        "pod": get_pod_info()
    }


@router.get("/pod")
async def pod_status():
    """Pod/container status information"""
    return {
        "timestamp": datetime.utcnow().isoformat(),
        "pod": get_pod_info(),
        "system": get_system_info()
    }


@router.get("/cron")
async def cron_status():
    """Cron job scheduler status"""
    return {
        "timestamp": datetime.utcnow().isoformat(),
        "scheduler": cron.get_scheduler_status(),
        "cache_health": await get_from_cache("cache:health:status"),
        "cache_last_check": await get_from_cache("cache:health:last_check"),
        "cache_last_sync": await get_from_cache("cache:last_sync")
    }
