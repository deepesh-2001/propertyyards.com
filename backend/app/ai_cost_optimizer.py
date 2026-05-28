"""
AI Cost Optimizer
Tracks AI usage, costs, and implements intelligent optimization strategies
"""
import asyncio
import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict
import hashlib
import json

logger = logging.getLogger(__name__)


class AIService(Enum):
    """AI services we use"""
    GEMINI_TEXT = "gemini_text"  # Gemini Pro for text
    GEMINI_VISION = "gemini_vision"  # Gemini Pro Vision
    IMAGEN = "imagen"  # Google Imagen 3
    OPENAI_GPT4 = "openai_gpt4"  # GPT-4 (fallback)
    OPENAI_DALLE = "openai_dalle"  # DALL-E 3 (fallback)


class CostTier(Enum):
    """Cost optimization tiers"""
    ECONOMY = "economy"  # Cheapest options
    BALANCED = "balanced"  # Good balance
    PREMIUM = "premium"  # Best quality
    AUTO = "auto"  # Smart routing


@dataclass
class AIUsageRecord:
    """AI usage record"""
    timestamp: datetime
    service: AIService
    operation: str
    input_tokens: int
    output_tokens: int
    cost_usd: float
    cached: bool = False
    user_id: Optional[str] = None
    request_hash: Optional[str] = None
    latency_ms: float = 0.0
    success: bool = True
    error_message: Optional[str] = None


@dataclass
class CostBreakdown:
    """Cost breakdown by service"""
    service: AIService
    total_calls: int
    total_cost_usd: float
    avg_cost_per_call: float
    cached_calls: int
    cache_hit_rate: float
    cost_saved_by_cache: float


# Pricing models (per 1000 tokens or per image)
PRICING = {
    AIService.GEMINI_TEXT: {
        "input_per_1k": 0.000125,  # $0.125 per 1M tokens
        "output_per_1k": 0.000375,  # $0.375 per 1M tokens
        "type": "token"
    },
    AIService.GEMINI_VISION: {
        "input_per_1k": 0.00025,  # Vision slightly more expensive
        "output_per_1k": 0.000375,
        "type": "token"
    },
    AIService.IMAGEN: {
        "per_image": 0.04,  # $0.04 per image (standard quality)
        "type": "image"
    },
    AIService.OPENAI_GPT4: {
        "input_per_1k": 0.03,  # $30 per 1M tokens
        "output_per_1k": 0.06,  # $60 per 1M tokens
        "type": "token"
    },
    AIService.OPENAI_DALLE: {
        "per_image": 0.04,  # $0.04 per image
        "type": "image"
    }
}


class AICostOptimizer:
    """Optimizes AI usage and tracks costs"""

    def __init__(self):
        self.enabled = True
        self.default_tier = CostTier.AUTO
        self.usage_history: List[AIUsageRecord] = []
        self.cache: Dict[str, Any] = {}  # Simple hash-based cache
        self.cache_ttl_seconds = 3600  # 1 hour
        self.cache_hits = 0
        self.cache_misses = 0

        # Daily budget
        self.daily_budget_usd = 50.0
        self.current_day_spend = 0.0
        self.last_budget_reset = datetime.utcnow()

        # Service routing preferences
        self.service_priority = [
            AIService.GEMINI_TEXT,  # Cheapest
            AIService.GEMINI_VISION,
            AIService.IMAGEN,
            AIService.OPENAI_GPT4,  # Most expensive (fallback)
            AIService.OPENAI_DALLE
        ]

        # Feature flags for AI features
        self.ai_features = {
            "property_image_gen": True,
            "article_gen": True,
            "market_analysis": True,
            "price_prediction": True,
            "chatbot": True,
            "architecture_3d": True,
            "social_content": True
        }

    async def start(self):
        """Start cost optimizer"""
        asyncio.create_task(self._budget_monitoring_loop())
        asyncio.create_task(self._cache_cleanup_loop())
        logger.info("AI Cost Optimizer started")

    async def _budget_monitoring_loop(self):
        """Monitor daily budget"""
        while self.enabled:
            try:
                # Reset budget at midnight UTC
                now = datetime.utcnow()
                if now.date() != self.last_budget_reset.date():
                    self.current_day_spend = 0.0
                    self.last_budget_reset = now
                    logger.info("Daily AI budget reset")

                # Check if approaching limit
                if self.current_day_spend >= self.daily_budget_usd * 0.8:
                    logger.warning(f"AI budget 80% consumed: ${self.current_day_spend:.2f}")
                    self._enable_cost_saving_mode()

                await asyncio.sleep(300)  # Check every 5 minutes

            except Exception as e:
                logger.error(f"Budget monitoring error: {e}")
                await asyncio.sleep(300)

    def _enable_cost_saving_mode(self):
        """Enable cost-saving mode when budget is tight"""
        # Disable non-essential features
        self.ai_features["social_content"] = False
        self.ai_features["architecture_3d"] = False
        self.cache_ttl_seconds = 7200  # Increase cache time
        logger.info("Cost-saving mode enabled")

    async def _cache_cleanup_loop(self):
        """Clean expired cache entries"""
        while self.enabled:
            try:
                now = datetime.utcnow()
                expired_keys = [
                    k for k, v in self.cache.items()
                    if (now - v.get("timestamp", now)).total_seconds() > self.cache_ttl_seconds
                ]
                for k in expired_keys:
                    del self.cache[k]

                await asyncio.sleep(600)  # Clean every 10 minutes

            except Exception as e:
                logger.error(f"Cache cleanup error: {e}")
                await asyncio.sleep(600)

    def generate_cache_key(self, service: AIService, prompt: str, params: Dict) -> str:
        """Generate cache key for request"""
        key_data = f"{service.value}:{prompt}:{json.dumps(params, sort_keys=True)}"
        return hashlib.md5(key_data.encode()).hexdigest()

    def get_cached_result(self, cache_key: str) -> Optional[Any]:
        """Get cached result if available"""
        if cache_key in self.cache:
            entry = self.cache[cache_key]
            age = (datetime.utcnow() - entry["timestamp"]).total_seconds()

            if age < self.cache_ttl_seconds:
                self.cache_hits += 1
                logger.debug(f"Cache hit: {cache_key[:8]}...")
                return entry["data"]
            else:
                # Expired
                del self.cache[cache_key]

        self.cache_misses += 1
        return None

    def cache_result(self, cache_key: str, result: Any):
        """Cache a result"""
        self.cache[cache_key] = {
            "data": result,
            "timestamp": datetime.utcnow()
        }

    def select_service(self, operation: str, tier: CostTier = CostTier.AUTO) -> AIService:
        """Select best AI service based on operation and tier"""
        if tier == CostTier.ECONOMY:
            # Always use cheapest
            if "image" in operation:
                return AIService.IMAGEN
            return AIService.GEMINI_TEXT

        elif tier == CostTier.PREMIUM:
            # Use best quality (OpenAI)
            if "image" in operation:
                return AIService.OPENAI_DALLE
            return AIService.OPENAI_GPT4

        elif tier == CostTier.BALANCED:
            # Use Gemini (good quality, low cost)
            if "image" in operation:
                return AIService.IMAGEN
            return AIService.GEMINI_TEXT

        else:  # AUTO
            # Smart routing based on budget and requirements
            if self.current_day_spend > self.daily_budget_usd * 0.7:
                # Budget getting tight, use cheapest
                if "image" in operation:
                    return AIService.IMAGEN
                return AIService.GEMINI_TEXT

            # Check operation type
            if operation in ["architecture_3d", "property_visualization"]:
                return AIService.IMAGEN  # High quality images
            elif operation in ["article_gen", "market_analysis"]:
                return AIService.GEMINI_TEXT  # Good for long text
            elif operation in ["chatbot", "price_prediction"]:
                return AIService.GEMINI_TEXT  # Fast and cheap

            # Default to Gemini
            return AIService.GEMINI_TEXT

    def calculate_cost(
        self,
        service: AIService,
        input_tokens: int = 0,
        output_tokens: int = 0,
        image_count: int = 0
    ) -> float:
        """Calculate cost for an operation"""
        pricing = PRICING.get(service, {})

        if pricing.get("type") == "token":
            input_cost = (input_tokens / 1000) * pricing.get("input_per_1k", 0)
            output_cost = (output_tokens / 1000) * pricing.get("output_per_1k", 0)
            return input_cost + output_cost

        elif pricing.get("type") == "image":
            return image_count * pricing.get("per_image", 0)

        return 0.0

    def record_usage(
        self,
        service: AIService,
        operation: str,
        input_tokens: int = 0,
        output_tokens: int = 0,
        image_count: int = 0,
        cached: bool = False,
        user_id: Optional[str] = None,
        latency_ms: float = 0.0,
        success: bool = True
    ) -> AIUsageRecord:
        """Record AI usage"""
        cost = 0.0 if cached else self.calculate_cost(service, input_tokens, output_tokens, image_count)

        record = AIUsageRecord(
            timestamp=datetime.utcnow(),
            service=service,
            operation=operation,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cost_usd=cost,
            cached=cached,
            user_id=user_id,
            latency_ms=latency_ms,
            success=success
        )

        self.usage_history.append(record)
        self.current_day_spend += cost

        # Keep only recent history
        cutoff = datetime.utcnow() - timedelta(days=30)
        self.usage_history = [r for r in self.usage_history if r.timestamp > cutoff]

        logger.debug(f"AI usage recorded: {operation} - ${cost:.4f}")
        return record

    def get_cost_summary(self, days: int = 7) -> Dict[str, Any]:
        """Get cost summary for period"""
        cutoff = datetime.utcnow() - timedelta(days=days)
        recent_usage = [r for r in self.usage_history if r.timestamp > cutoff]

        # Breakdown by service
        service_stats: Dict[AIService, Dict] = defaultdict(lambda: {
            "calls": 0,
            "cost": 0.0,
            "cached": 0,
            "failed": 0,
            "latency_total": 0.0
        })

        for record in recent_usage:
            stats = service_stats[record.service]
            stats["calls"] += 1
            stats["cost"] += record.cost_usd
            if record.cached:
                stats["cached"] += 1
            if not record.success:
                stats["failed"] += 1
            stats["latency_total"] += record.latency_ms

        # Format breakdown
        breakdown = []
        total_cost = 0.0
        total_calls = 0

        for service, stats in service_stats.items():
            calls = stats["calls"]
            cost = stats["cost"]
            cached = stats["cached"]
            failed = stats["failed"]

            total_cost += cost
            total_calls += calls

            breakdown.append({
                "service": service.value,
                "total_calls": calls,
                "total_cost_usd": round(cost, 4),
                "avg_cost_per_call": round(cost / calls, 6) if calls > 0 else 0,
                "cached_calls": cached,
                "cache_hit_rate": round(cached / calls * 100, 2) if calls > 0 else 0,
                "failed_calls": failed,
                "avg_latency_ms": round(stats["latency_total"] / calls, 2) if calls > 0 else 0
            })

        # Cache stats
        total_cache_hits = self.cache_hits
        total_cache_misses = self.cache_misses
        cache_total = total_cache_hits + total_cache_misses
        cache_hit_rate = total_cache_hits / cache_total * 100 if cache_total > 0 else 0

        # Estimate savings from cache
        # Assume average cost per cached request would be $0.01
        estimated_savings = total_cache_hits * 0.01

        return {
            "period_days": days,
            "total_cost_usd": round(total_cost, 4),
            "total_api_calls": total_calls,
            "avg_daily_cost": round(total_cost / days, 4),
            "breakdown_by_service": breakdown,
            "cache_stats": {
                "hits": total_cache_hits,
                "misses": total_cache_misses,
                "hit_rate_percent": round(cache_hit_rate, 2),
                "estimated_savings_usd": round(estimated_savings, 4)
            },
            "daily_budget_usd": self.daily_budget_usd,
            "current_day_spend_usd": round(self.current_day_spend, 4),
            "budget_remaining_percent": round(
                (1 - self.current_day_spend / self.daily_budget_usd) * 100, 2
            ) if self.daily_budget_usd > 0 else 100
        }

    def get_optimization_recommendations(self) -> List[Dict[str, Any]]:
        """Get cost optimization recommendations"""
        recommendations = []

        summary = self.get_cost_summary(days=7)
        cache_hit_rate = summary["cache_stats"]["hit_rate_percent"]
        daily_spend = summary["avg_daily_cost"]
        budget = summary["daily_budget_usd"]

        # Check cache hit rate
        if cache_hit_rate < 50:
            recommendations.append({
                "priority": "high",
                "type": "cache_optimization",
                "message": f"Cache hit rate is low ({cache_hit_rate}%)",
                "action": "Increase cache TTL or improve cache key generation",
                "potential_savings": "20-40%"
            })

        # Check budget utilization
        if daily_spend > budget * 0.8:
            recommendations.append({
                "priority": "high",
                "type": "budget_alert",
                "message": f"Daily spend (${daily_spend}) approaching budget (${budget})",
                "action": "Enable cost-saving mode or increase budget",
                "potential_savings": "N/A - budget management"
            })

        # Check service mix
        breakdown = summary["breakdown_by_service"]
        expensive_services = [b for b in breakdown if b["service"] in [
            "openai_gpt4", "openai_dalle"
        ]]

        if expensive_services:
            expensive_cost = sum(s["total_cost_usd"] for s in expensive_services)
            if expensive_cost > summary["total_cost_usd"] * 0.5:
                recommendations.append({
                    "priority": "medium",
                    "type": "service_optimization",
                    "message": f"Using expensive OpenAI services ({expensive_cost:.2f} USD)",
                    "action": "Switch to Gemini for non-critical operations",
                    "potential_savings": "40-60%"
                })

        # Check for failed requests
        failed_calls = sum(b["failed_calls"] for b in breakdown)
        if failed_calls > summary["total_api_calls"] * 0.05:
            recommendations.append({
                "priority": "high",
                "type": "reliability",
                "message": f"High failure rate: {failed_calls} failed calls",
                "action": "Review error logs and implement retry logic",
                "potential_savings": "Avoid wasted costs on failed requests"
            })

        if not recommendations:
            recommendations.append({
                "priority": "low",
                "type": "healthy",
                "message": "AI usage is optimized",
                "action": "No action needed",
                "potential_savings": "0%"
            })

        return recommendations

    def set_budget(self, daily_budget_usd: float):
        """Set daily budget"""
        self.daily_budget_usd = daily_budget_usd
        logger.info(f"Daily AI budget set to ${daily_budget_usd}")

    def toggle_feature(self, feature: str, enabled: bool):
        """Toggle AI feature on/off"""
        if feature in self.ai_features:
            self.ai_features[feature] = enabled
            logger.info(f"AI feature '{feature}' {'enabled' if enabled else 'disabled'}")

    async def generate_with_optimization(
        self,
        operation: str,
        prompt: str,
        params: Dict[str, Any],
        tier: CostTier = CostTier.AUTO,
        use_cache: bool = True
    ) -> Tuple[Any, AIUsageRecord]:
        """Generate content with full cost optimization"""
        start_time = datetime.utcnow()

        # Check if feature is enabled
        feature_key = operation.split("_")[0]
        if not self.ai_features.get(operation, True):
            raise Exception(f"AI feature '{operation}' is disabled")

        # Select service
        service = self.select_service(operation, tier)

        # Check cache
        cache_key = self.generate_cache_key(service, prompt, params)
        if use_cache:
            cached_result = self.get_cached_result(cache_key)
            if cached_result:
                record = self.record_usage(
                    service=service,
                    operation=operation,
                    cached=True,
                    latency_ms=(datetime.utcnow() - start_time).total_seconds() * 1000
                )
                return cached_result, record

        # Generate (this would call the actual AI service)
        # Placeholder - actual implementation would call AI API
        result = None  # Would be actual AI response

        # Record usage (actual token counts would come from API response)
        latency_ms = (datetime.utcnow() - start_time).total_seconds() * 1000
        record = self.record_usage(
            service=service,
            operation=operation,
            input_tokens=len(prompt.split()) * 1.3,  # Approximate
            output_tokens=500,  # Placeholder
            cached=False,
            latency_ms=latency_ms
        )

        # Cache result
        if use_cache and result:
            self.cache_result(cache_key, result)

        return result, record


# Global instance
ai_cost_optimizer = AICostOptimizer()
