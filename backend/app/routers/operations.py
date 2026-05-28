"""
Operations Router
Dashboard and controls for usage tracking, auto-scaling, and auto-healing
"""
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from typing import Optional
from datetime import datetime, timedelta

from app.database import get_db
from app.auth import get_current_user

router = APIRouter(prefix="/api/operations", tags=["operations"])


# ========== Usage & Analytics ==========

@router.get("/usage/dashboard")
async def get_usage_dashboard(
    current_user: dict = Depends(get_current_user),
    database=Depends(get_db)
):
    """Get usage analytics dashboard"""
    if current_user.get("role") not in ["admin", "devops"]:
        raise HTTPException(status_code=403, detail="Admin or DevOps access required")

    try:
        from app.usage_tracker import usage_tracker

        # Get current load
        current_load = usage_tracker.get_current_load()

        # Get load history
        load_history = usage_tracker.get_load_history(minutes=60)

        # Get endpoint stats
        endpoint_stats = usage_tracker.get_endpoint_stats()

        # Get today's summary
        today_summary = await usage_tracker.get_daily_summary(database=database)

        # Get rate limiter status
        from app.usage_tracker import rate_limiter

        return {
            "current_load": current_load,
            "load_history": load_history,
            "endpoint_stats": endpoint_stats,
            "today_summary": today_summary,
            "buffer_size": len(usage_tracker.buffer),
            "is_tracking": usage_tracker.is_tracking
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/usage/daily")
async def get_daily_usage(
    date: Optional[str] = None,
    current_user: dict = Depends(get_current_user),
    database=Depends(get_db)
):
    """Get daily usage summary"""
    if current_user.get("role") not in ["admin", "devops"]:
        raise HTTPException(status_code=403, detail="Admin or DevOps access required")

    try:
        from app.usage_tracker import usage_tracker
        summary = await usage_tracker.get_daily_summary(date, database)
        return summary

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/usage/endpoints")
async def get_endpoint_usage(
    filter: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """Get endpoint usage statistics"""
    if current_user.get("role") not in ["admin", "devops"]:
        raise HTTPException(status_code=403, detail="Admin or DevOps access required")

    try:
        from app.usage_tracker import usage_tracker
        stats = usage_tracker.get_endpoint_stats(filter)
        return {"endpoints": stats}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/usage/user/{user_id}")
async def get_user_usage(
    user_id: str,
    date: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """Get usage for specific user"""
    if current_user.get("role") != "admin" and current_user.get("_id") != user_id:
        raise HTTPException(status_code=403, detail="Admin access required")

    try:
        from app.usage_tracker import usage_tracker
        stats = usage_tracker.get_user_stats(user_id, date)

        if stats:
            return {
                "user_id": stats.user_id,
                "date": stats.date,
                "api_calls": stats.api_calls,
                "endpoints_accessed": list(stats.endpoints_accessed),
                "avg_response_time_ms": round(stats.total_response_time_ms / stats.api_calls, 2) if stats.api_calls > 0 else 0,
                "errors": stats.errors,
                "bytes_transferred": stats.bytes_transferred
            }

        return {"message": "No usage data found"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ========== Auto-Scaling ==========

@router.get("/scaling/status")
async def get_scaling_status(
    current_user: dict = Depends(get_current_user)
):
    """Get auto-scaling status"""
    if current_user.get("role") not in ["admin", "devops"]:
        raise HTTPException(status_code=403, detail="Admin or DevOps access required")

    try:
        from app.auto_scaler import auto_scaler
        return auto_scaler.get_status()

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/scaling/manual")
async def manual_scale(
    target_instances: int,
    current_user: dict = Depends(get_current_user)
):
    """Manually scale instances"""
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")

    try:
        from app.auto_scaler import auto_scaler

        success = auto_scaler.manual_scale(target_instances)

        if success:
            return {
                "message": "Scaling initiated",
                "target_instances": target_instances,
                "previous_instances": auto_scaler.current_instances
            }
        else:
            raise HTTPException(status_code=400, detail="Invalid target instance count")

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/scaling/enable")
async def enable_auto_scaling(
    current_user: dict = Depends(get_current_user)
):
    """Enable auto-scaling"""
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")

    try:
        from app.auto_scaler import auto_scaler
        auto_scaler.enabled = True
        return {"message": "Auto-scaling enabled"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/scaling/disable")
async def disable_auto_scaling(
    current_user: dict = Depends(get_current_user)
):
    """Disable auto-scaling"""
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")

    try:
        from app.auto_scaler import auto_scaler
        auto_scaler.enabled = False
        return {"message": "Auto-scaling disabled"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/scaling/configure")
async def configure_scaling(
    min_instances: int,
    max_instances: int,
    current_user: dict = Depends(get_current_user)
):
    """Configure auto-scaling limits"""
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")

    try:
        from app.auto_scaler import auto_scaler

        auto_scaler.min_instances = min_instances
        auto_scaler.max_instances = max_instances

        return {
            "message": "Scaling configuration updated",
            "min_instances": min_instances,
            "max_instances": max_instances
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ========== Auto-Healing ==========

@router.get("/healing/status")
async def get_healing_status(
    current_user: dict = Depends(get_current_user)
):
    """Get auto-healing status"""
    if current_user.get("role") not in ["admin", "devops"]:
        raise HTTPException(status_code=403, detail="Admin or DevOps access required")

    try:
        from app.auto_healing import auto_healing
        return auto_healing.get_health_summary()

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/healing/enable")
async def enable_auto_healing(
    current_user: dict = Depends(get_current_user)
):
    """Enable auto-healing"""
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")

    try:
        from app.auto_healing import auto_healing
        auto_healing.enabled = True
        return {"message": "Auto-healing enabled"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/healing/disable")
async def disable_auto_healing(
    current_user: dict = Depends(get_current_user)
):
    """Disable auto-healing"""
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")

    try:
        from app.auto_healing import auto_healing
        auto_healing.enabled = False
        return {"message": "Auto-healing disabled"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/healing/rules/{rule_name}/enable")
async def enable_healing_rule(
    rule_name: str,
    current_user: dict = Depends(get_current_user)
):
    """Enable a healing rule"""
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")

    try:
        from app.auto_healing import auto_healing

        success = auto_healing.enable_rule(rule_name)

        if success:
            return {"message": f"Rule {rule_name} enabled"}
        else:
            raise HTTPException(status_code=404, detail="Rule not found")

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/healing/rules/{rule_name}/disable")
async def disable_healing_rule(
    rule_name: str,
    current_user: dict = Depends(get_current_user)
):
    """Disable a healing rule"""
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")

    try:
        from app.auto_healing import auto_healing

        success = auto_healing.disable_rule(rule_name)

        if success:
            return {"message": f"Rule {rule_name} disabled"}
        else:
            raise HTTPException(status_code=404, detail="Rule not found")

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/healing/trigger-recovery")
async def trigger_recovery(
    service: str,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user)
):
    """Manually trigger recovery for a service"""
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")

    try:
        from app.auto_healing import auto_healing
        from app.auto_healing import FailureType

        # Trigger in background
        background_tasks.add_task(
            auto_healing._handle_failure,
            FailureType.SERVICE_DOWN,
            service,
            "high",
            f"Manually triggered recovery by {current_user.get('_id')}"
        )

        return {"message": f"Recovery triggered for {service}"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ========== Overall System Health ==========

@router.get("/health/full")
async def get_full_system_health(
    current_user: dict = Depends(get_current_user)
):
    """Get complete system health including all services"""
    if current_user.get("role") not in ["admin", "devops"]:
        raise HTTPException(status_code=403, detail="Admin or DevOps access required")

    try:
        from app.service_manager import service_manager
        from app.auto_scaler import auto_scaler
        from app.auto_healing import auto_healing
        from app.usage_tracker import usage_tracker

        # Get all service statuses
        service_status = service_manager.get_all_status()

        # Get health check
        health = await service_manager.health_check()

        # Get operational metrics
        scaling_status = auto_scaler.get_status()
        healing_status = auto_healing.get_health_summary()
        current_load = usage_tracker.get_current_load()

        return {
            "timestamp": datetime.utcnow().isoformat(),
            "overall_health": health,
            "services": service_status,
            "scaling": {
                "enabled": scaling_status["enabled"],
                "current_instances": scaling_status["current_instances"],
                "target_instances": scaling_status["target_instances"]
            },
            "healing": {
                "enabled": healing_status["enabled"],
                "auto_recovery_rate": healing_status["auto_recovery_rate"],
                "services_health": healing_status["services_health"]
            },
            "load": current_load,
            "recommendations": _generate_recommendations(
                health, scaling_status, healing_status, current_load
            )
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def _generate_recommendations(health, scaling, healing, load):
    """Generate operational recommendations"""
    recommendations = []

    # Check failed services
    if health.get("failed_services"):
        recommendations.append({
            "priority": "high",
            "type": "service_failure",
            "message": f"Failed services detected: {health['failed_services']}",
            "action": "Check service logs and restart if needed"
        })

    # Check scaling
    if scaling["current_instances"] >= scaling.get("max_instances", 10):
        recommendations.append({
            "priority": "medium",
            "type": "scaling_limit",
            "message": "Running at maximum instance capacity",
            "action": "Consider increasing max_instances or investigating load source"
        })

    # Check healing rate
    if healing.get("auto_recovery_rate", 100) < 80:
        recommendations.append({
            "priority": "high",
            "type": "recovery_rate",
            "message": "Auto-recovery rate below 80%",
            "action": "Review failure patterns and improve recovery rules"
        })

    # Check CPU
    if load.get("cpu_percent", 0) > 80:
        recommendations.append({
            "priority": "medium",
            "type": "high_cpu",
            "message": f"High CPU usage: {load['cpu_percent']:.1f}%",
            "action": "Consider scaling up or optimizing resource usage"
        })

    if not recommendations:
        recommendations.append({
            "priority": "low",
            "type": "healthy",
            "message": "System operating normally",
            "action": "No action required"
        })

    return recommendations
