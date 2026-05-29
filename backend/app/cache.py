"""
Redis caching layer with enhanced features
"""
import json
import time
import asyncio
from typing import Any, Optional, Dict, List, Callable
from dataclasses import dataclass
from datetime import datetime, timedelta
import redis.asyncio as redis
from app.config import settings
import logging

logger = logging.getLogger(__name__)

cache: Optional[redis.Redis] = None

@dataclass
class CacheMetrics:
    """Cache performance metrics"""
    hits: int = 0
    misses: int = 0
    sets: int = 0
    deletes: int = 0
    errors: int = 0
    total_response_time: float = 0
    
    @property
    def hit_rate(self) -> float:
        """Calculate cache hit rate"""
        total = self.hits + self.misses
        return (self.hits / total * 100) if total > 0 else 0
    
    @property
    def avg_response_time(self) -> float:
        """Calculate average response time"""
        return self.total_response_time / (self.hits + self.misses + self.sets + self.deletes) if (self.hits + self.misses + self.sets + self.deletes) > 0 else 0

# Global metrics
cache_metrics = CacheMetrics()

class CacheWarmer:
    """Cache warming service for preloading frequently accessed data"""
    
    def __init__(self):
        self.warming_jobs: Dict[str, Dict] = {}
        self.running = False
    
    async def start_warming(self):
        """Start cache warming background task"""
        self.running = True
        asyncio.create_task(self._warming_loop())
        logger.info("Cache warming started")
    
    async def stop_warming(self):
        """Stop cache warming"""
        self.running = False
        logger.info("Cache warming stopped")
    
    def register_warm_job(self, name: str, cache_key: str, data_loader: Callable, ttl: int = 3600):
        """Register a cache warming job"""
        self.warming_jobs[name] = {
            "cache_key": cache_key,
            "data_loader": data_loader,
            "ttl": ttl,
            "last_warmed": None,
            "interval": ttl // 2  # Warm at half the TTL
        }
        logger.info(f"Registered cache warm job: {name}")
    
    async def _warming_loop(self):
        """Background loop for cache warming"""
        while self.running:
            try:
                current_time = time.time()
                
                for name, job in self.warming_jobs.items():
                    # Check if job needs warming
                    if (job["last_warmed"] is None or 
                        current_time - job["last_warmed"] > job["interval"]):
                        
                        try:
                            # Load data and cache it
                            data = await job["data_loader"]()
                            if data is not None:
                                await set_in_cache(job["cache_key"], data, job["ttl"])
                                job["last_warmed"] = current_time
                                logger.debug(f"Warmed cache: {name}")
                        except Exception as e:
                            logger.error(f"Cache warming failed for {name}: {e}")
                
                # Sleep for a minute before next check
                await asyncio.sleep(60)
                
            except Exception as e:
                logger.error(f"Cache warming loop error: {e}")
                await asyncio.sleep(60)

class CacheInvalidator:
    """Intelligent cache invalidation service"""
    
    def __init__(self):
        self.invalidations: Dict[str, List[str]] = {}  # pattern -> list of dependent patterns
    
    def register_dependency(self, pattern: str, dependent_patterns: List[str]):
        """Register cache dependencies"""
        self.invalidations[pattern] = dependent_patterns
        logger.debug(f"Registered cache dependencies: {pattern} -> {dependent_patterns}")
    
    async def invalidate_with_dependencies(self, pattern: str) -> int:
        """Invalidate cache pattern and all dependencies"""
        total_invalidated = 0
        
        # Invalidate the main pattern
        main_invalidated = await invalidate_cache_pattern(pattern)
        total_invalidated += main_invalidated
        
        # Invalidate dependencies
        if pattern in self.invalidations:
            for dep_pattern in self.invalidations[pattern]:
                dep_invalidated = await invalidate_cache_pattern(dep_pattern)
                total_invalidated += dep_invalidated
        
        logger.info(f"Invalidated {total_invalidated} cache keys for pattern: {pattern}")
        return total_invalidated

class CacheMonitor:
    """Cache performance monitoring"""
    
    def __init__(self):
        self.alerts_enabled = True
        self.hit_rate_threshold = 70  # Alert if hit rate below 70%
        self.error_rate_threshold = 5   # Alert if error rate above 5%
    
    def check_performance(self):
        """Check cache performance and generate alerts"""
        total_ops = cache_metrics.hits + cache_metrics.misses + cache_metrics.sets + cache_metrics.deletes
        
        if total_ops == 0:
            return
        
        hit_rate = cache_metrics.hit_rate
        error_rate = (cache_metrics.errors / total_ops) * 100
        
        alerts = []
        
        if hit_rate < self.hit_rate_threshold:
            alerts.append(f"Low cache hit rate: {hit_rate:.1f}% (threshold: {self.hit_rate_threshold}%)")
        
        if error_rate > self.error_rate_threshold:
            alerts.append(f"High cache error rate: {error_rate:.1f}% (threshold: {self.error_rate_threshold}%)")
        
        if alerts:
            for alert in alerts:
                logger.warning(f"Cache performance alert: {alert}")
        
        return alerts
    
    def get_metrics_summary(self) -> Dict[str, Any]:
        """Get comprehensive cache metrics"""
        total_ops = cache_metrics.hits + cache_metrics.misses + cache_metrics.sets + cache_metrics.deletes
        
        return {
            "hits": cache_metrics.hits,
            "misses": cache_metrics.misses,
            "sets": cache_metrics.sets,
            "deletes": cache_metrics.deletes,
            "errors": cache_metrics.errors,
            "total_operations": total_ops,
            "hit_rate": cache_metrics.hit_rate,
            "avg_response_time_ms": cache_metrics.avg_response_time * 1000,
            "timestamp": datetime.utcnow().isoformat()
        }

# Global instances
cache_warmer = CacheWarmer()
cache_invalidator = CacheInvalidator()
cache_monitor = CacheMonitor()


async def init_cache():
    """Initialize Redis connection"""
    global cache
    try:
        cache = await redis.from_url(settings.REDIS_URL, encoding="utf8", decode_responses=True)
        await cache.ping()
        logger.info("Redis cache initialized successfully")
        
        # Start cache warming
        await cache_warmer.start_warming()
        
        # Register common cache dependencies
        register_common_dependencies()
        
    except Exception as e:
        logger.error(f"Failed to connect to Redis: {e}")
        cache = None


async def close_cache():
    """Close Redis connection"""
    global cache
    try:
        # Stop cache warming
        await cache_warmer.stop_warming()
        
        if cache:
            await cache.close()
            logger.info("Redis cache closed")
    except Exception as e:
        logger.error(f"Error closing cache: {e}")


async def get_from_cache(key: str) -> Optional[Any]:
    """Get value from cache with metrics tracking"""
    start_time = time.time()
    
    if not cache:
        cache_metrics.misses += 1
        return None
    
    try:
        value = await cache.get(key)
        response_time = time.time() - start_time
        cache_metrics.total_response_time += response_time
        
        if value:
            cache_metrics.hits += 1
            return json.loads(value)
        
        cache_metrics.misses += 1
        return None
        
    except Exception as e:
        cache_metrics.errors += 1
        logger.error(f"Cache get error for key {key}: {e}")
        return None


async def set_in_cache(key: str, value: Any, ttl: int = None) -> bool:
    """Set value in cache with metrics tracking"""
    start_time = time.time()
    
    if not cache:
        cache_metrics.errors += 1
        return False
    
    try:
        ttl = ttl or settings.CACHE_TTL
        await cache.setex(key, ttl, json.dumps(value, default=str))
        
        response_time = time.time() - start_time
        cache_metrics.total_response_time += response_time
        cache_metrics.sets += 1
        
        return True
        
    except Exception as e:
        cache_metrics.errors += 1
        logger.error(f"Cache set error for key {key}: {e}")
        return False


async def delete_from_cache(key: str) -> bool:
    """Delete value from cache with metrics tracking"""
    start_time = time.time()
    
    if not cache:
        cache_metrics.errors += 1
        return False
    
    try:
        result = await cache.delete(key)
        
        response_time = time.time() - start_time
        cache_metrics.total_response_time += response_time
        cache_metrics.deletes += 1
        
        return result > 0
        
    except Exception as e:
        cache_metrics.errors += 1
        logger.error(f"Cache delete error for key {key}: {e}")
        return False


async def invalidate_cache_pattern(pattern: str) -> int:
    """Invalidate multiple cache keys by pattern"""
    if not cache:
        return 0
    try:
        keys = await cache.keys(pattern)
        if keys:
            deleted = await cache.delete(*keys)
            cache_metrics.deletes += deleted
            return deleted
        return 0
    except Exception as e:
        cache_metrics.errors += 1
        logger.error(f"Cache pattern invalidate error for pattern {pattern}: {e}")
        return 0


async def get_cache_info() -> Dict[str, Any]:
    """Get Redis cache information"""
    if not cache:
        return {"error": "Cache not available"}
    
    try:
        info = await cache.info()
        return {
            "redis_version": info.get("redis_version"),
            "used_memory": info.get("used_memory_human"),
            "connected_clients": info.get("connected_clients"),
            "total_commands_processed": info.get("total_commands_processed"),
            "keyspace_hits": info.get("keyspace_hits"),
            "keyspace_misses": info.get("keyspace_misses"),
            "uptime_in_seconds": info.get("uptime_in_seconds")
        }
    except Exception as e:
        logger.error(f"Error getting cache info: {e}")
        return {"error": str(e)}


async def cache_with_fallback(
    key: str, 
    data_loader: Callable, 
    ttl: int = None, 
    fallback_ttl: int = 60
) -> Any:
    """Get from cache with fallback to data loader and error handling"""
    try:
        # Try to get from cache first
        cached_data = await get_from_cache(key)
        if cached_data is not None:
            return cached_data
        
        # Load fresh data
        data = await data_loader()
        if data is not None:
            # Cache the fresh data
            await set_in_cache(key, data, ttl or settings.CACHE_TTL)
        
        return data
        
    except Exception as e:
        logger.error(f"Cache with fallback error for key {key}: {e}")
        
        # Try to get stale data as fallback
        try:
            stale_data = await get_from_cache(f"{key}:stale")
            if stale_data is not None:
                return stale_data
        except:
            pass
        
        # Final fallback - try data loader directly
        try:
            return await data_loader()
        except Exception as fallback_error:
            logger.error(f"Final fallback failed for key {key}: {fallback_error}")
            raise


async def smart_cache_update(
    key: str, 
    data: Any, 
    ttl: int = None,
    condition: Callable = None
) -> bool:
    """Smart cache update with conditional logic"""
    try:
        # Check condition if provided
        if condition and not condition(data):
            return False
        
        # Update main cache
        success = await set_in_cache(key, data, ttl)
        
        if success:
            # Also store as stale data for emergency fallback
            stale_ttl = max(ttl or settings.CACHE_TTL, 3600)  # Keep stale data for at least 1 hour
            await set_in_cache(f"{key}:stale", data, stale_ttl)
        
        return success
        
    except Exception as e:
        logger.error(f"Smart cache update error for key {key}: {e}")
        return False


def generate_cache_key(*args) -> str:
    """Generate cache key from multiple arguments"""
    return ":".join(str(arg) for arg in args)


def register_common_dependencies():
    """Register common cache dependencies"""
    # Property dependencies
    cache_invalidator.register_dependency(
        "property:*",
        ["properties:*", "search:*", "analytics:*"]
    )
    
    # User dependencies
    cache_invalidator.register_dependency(
        "user:*",
        ["users:*", "profiles:*"]
    )
    
    # Payment dependencies
    cache_invalidator.register_dependency(
        "payment:*",
        ["payments:*", "transactions:*", "wallets:*"]
    )


# Aliases for backward compatibility
get_cache = get_from_cache
set_cache = set_in_cache

