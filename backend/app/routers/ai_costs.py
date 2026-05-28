"""
AI Costs Router
API endpoints for AI cost management and optimization
"""
from fastapi import APIRouter, Depends, HTTPException
from typing import Optional

from app.database import get_db
from app.auth import get_current_user

router = APIRouter(prefix="/api/ai", tags=["ai-costs"])


@router.get("/costs/summary")
async def get_cost_summary(
    days: int = 7,
    current_user: dict = Depends(get_current_user)
):
    """Get AI cost summary for period"""
    if current_user.get("role") not in ["admin", "devops"]:
        raise HTTPException(status_code=403, detail="Admin access required")

    try:
        from app.ai_cost_optimizer import ai_cost_optimizer
        summary = ai_cost_optimizer.get_cost_summary(days)
        return summary

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/costs/recommendations")
async def get_optimization_recommendations(
    current_user: dict = Depends(get_current_user)
):
    """Get cost optimization recommendations"""
    if current_user.get("role") not in ["admin", "devops"]:
        raise HTTPException(status_code=403, detail="Admin access required")

    try:
        from app.ai_cost_optimizer import ai_cost_optimizer
        recommendations = ai_cost_optimizer.get_optimization_recommendations()
        return {
            "recommendations": recommendations,
            "generated_at": datetime.utcnow().isoformat()
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/features")
async def get_ai_features(
    current_user: dict = Depends(get_current_user)
):
    """Get status of all AI features"""
    if current_user.get("role") not in ["admin", "devops"]:
        raise HTTPException(status_code=403, detail="Admin access required")

    try:
        from app.ai_cost_optimizer import ai_cost_optimizer
        return {
            "features": ai_cost_optimizer.ai_features,
            "default_tier": ai_cost_optimizer.default_tier.value,
            "daily_budget_usd": ai_cost_optimizer.daily_budget_usd,
            "current_day_spend_usd": round(ai_cost_optimizer.current_day_spend, 4)
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/features/{feature_name}/enable")
async def enable_ai_feature(
    feature_name: str,
    current_user: dict = Depends(get_current_user)
):
    """Enable an AI feature"""
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")

    try:
        from app.ai_cost_optimizer import ai_cost_optimizer

        ai_cost_optimizer.toggle_feature(feature_name, True)

        return {
            "message": f"AI feature '{feature_name}' enabled",
            "feature": feature_name,
            "status": "enabled"
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/features/{feature_name}/disable")
async def disable_ai_feature(
    feature_name: str,
    current_user: dict = Depends(get_current_user)
):
    """Disable an AI feature"""
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")

    try:
        from app.ai_cost_optimizer import ai_cost_optimizer

        ai_cost_optimizer.toggle_feature(feature_name, False)

        return {
            "message": f"AI feature '{feature_name}' disabled",
            "feature": feature_name,
            "status": "disabled"
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/budget/set")
async def set_ai_budget(
    daily_budget_usd: float,
    current_user: dict = Depends(get_current_user)
):
    """Set daily AI budget"""
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")

    try:
        from app.ai_cost_optimizer import ai_cost_optimizer

        ai_cost_optimizer.set_budget(daily_budget_usd)

        return {
            "message": "Daily AI budget updated",
            "daily_budget_usd": daily_budget_usd,
            "effective_immediately": True
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/usage/realtime")
async def get_realtime_usage(
    current_user: dict = Depends(get_current_user)
):
    """Get real-time AI usage metrics"""
    if current_user.get("role") not in ["admin", "devops"]:
        raise HTTPException(status_code=403, detail="Admin access required")

    try:
        from app.ai_cost_optimizer import ai_cost_optimizer

        # Get today's usage
        today_summary = ai_cost_optimizer.get_cost_summary(days=1)

        # Get cache stats
        cache_hits = ai_cost_optimizer.cache_hits
        cache_misses = ai_cost_optimizer.cache_misses
        total = cache_hits + cache_misses
        cache_rate = (cache_hits / total * 100) if total > 0 else 0

        return {
            "today": today_summary,
            "cache": {
                "hits": cache_hits,
                "misses": cache_misses,
                "hit_rate_percent": round(cache_rate, 2),
                "entries": len(ai_cost_optimizer.cache)
            },
            "current_spend_today": round(ai_cost_optimizer.current_day_spend, 4),
            "budget_remaining_percent": round(
                (1 - ai_cost_optimizer.current_day_spend / ai_cost_optimizer.daily_budget_usd) * 100, 2
            ) if ai_cost_optimizer.daily_budget_usd > 0 else 100,
            "timestamp": datetime.utcnow().isoformat()
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/services/pricing")
async def get_ai_service_pricing():
    """Get pricing for all AI services"""
    from app.ai_cost_optimizer import PRICING, AIService

    pricing_info = []
    for service, pricing in PRICING.items():
        info = {
            "service": service.value,
            "type": pricing.get("type", "unknown")
        }

        if pricing.get("type") == "token":
            info["input_per_1k_tokens"] = pricing.get("input_per_1k", 0)
            info["output_per_1k_tokens"] = pricing.get("output_per_1k", 0)
            info["example_1k_input_cost"] = f"${pricing.get('input_per_1k', 0):.6f}"
        elif pricing.get("type") == "image":
            info["per_image"] = pricing.get("per_image", 0)
            info["example_cost"] = f"${pricing.get('per_image', 0):.4f}"

        pricing_info.append(info)

    return {
        "pricing": pricing_info,
        "note": "Prices in USD, subject to change by providers"
    }


from datetime import datetime
