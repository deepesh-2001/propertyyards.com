"""
Cache Decorators for FastAPI Endpoints
Easy-to-use decorators for caching endpoint responses
"""
from functools import wraps
from typing import Callable, Optional, Any
import logging
from fastapi import Request

from app.cache import get_from_cache, set_in_cache, generate_cache_key, delete_from_cache, invalidate_cache_pattern
from app.cache_pipeline import local_cache, redis_pipeline
from app.persistent_cache import persistent_cache

logger = logging.getLogger(__name__)


def cached(
    ttl: int = 300,
    key_prefix: str = "",
    use_local_cache: bool = True,
    use_persistent: bool = False,
    vary_on_user: bool = False,
    vary_on_query: bool = True,
    invalidate_on: Optional[list] = None
):
    """
    Cache decorator for FastAPI endpoints

    Args:
        ttl: Time to live in seconds
        key_prefix: Prefix for cache key
        use_local_cache: Use in-memory local cache
        use_persistent: Store in persistent MongoDB cache
        vary_on_user: Include user ID in cache key
        vary_on_query: Include query params in cache key
        invalidate_on: List of cache patterns to invalidate on POST/PUT/DELETE
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Build cache key
            request = kwargs.get('request')
            current_user = kwargs.get('current_user')

            key_parts = [key_prefix or func.__name__]

            if vary_on_user and current_user:
                user_id = str(current_user.get('_id', current_user.get('user_id', 'anon')))
                key_parts.append(user_id)

            if vary_on_query and request:
                # Include relevant query params
                query_params = str(sorted(request.query_params.items()))
                key_parts.append(query_params)

            # Add function arguments (except request/db)
            for k, v in kwargs.items():
                if k not in ['request', 'database', 'db', 'current_user'] and v is not None:
                    key_parts.append(f"{k}:{v}")

            cache_key = generate_cache_key(*key_parts)

            # Try local cache first (fastest)
            if use_local_cache:
                local_result = local_cache.get(cache_key)
                if local_result is not None:
                    logger.debug(f"Local cache hit: {cache_key}")
                    return local_result

            # Try Redis cache
            cached = await get_from_cache(cache_key)
            if cached is not None:
                logger.debug(f"Redis cache hit: {cache_key}")
                # Store in local cache for next time
                if use_local_cache:
                    local_cache.set(cache_key, cached, ttl=min(ttl, 60))
                return cached

            # Try persistent cache
            if use_persistent:
                db = kwargs.get('database') or kwargs.get('db')
                if db:
                    persistent = await persistent_cache._get_from_db_cache(cache_key, db)
                    if persistent is not None:
                        logger.debug(f"Persistent cache hit: {cache_key}")
                        # Restore to Redis and local
                        await set_in_cache(cache_key, persistent, ttl=ttl)
                        if use_local_cache:
                            local_cache.set(cache_key, persistent, ttl=min(ttl, 60))
                        return persistent

            # Execute function
            result = await func(*args, **kwargs)

            # Cache result
            if result is not None:
                # Store in Redis
                await set_in_cache(cache_key, result, ttl=ttl)

                # Store in local cache
                if use_local_cache:
                    local_cache.set(cache_key, result, ttl=min(ttl, 60))

                # Store in persistent cache
                if use_persistent:
                    db = kwargs.get('database') or kwargs.get('db')
                    if db:
                        await persistent_cache._store_in_db_cache(cache_key, result, ttl, db)

            return result

        return wrapper
    return decorator


def cache_invalidate(pattern: str):
    """
    Decorator to invalidate cache after successful operation
    Useful for POST/PUT/DELETE operations
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Execute function
            result = await func(*args, **kwargs)

            # Invalidate cache
            try:
                await invalidate_cache_pattern(pattern)
                logger.info(f"Cache invalidated: {pattern}")
            except Exception as e:
                logger.error(f"Cache invalidation error: {e}")

            return result

        return wrapper
    return decorator


def cached_list(
    ttl: int = 300,
    key_prefix: str = "",
    page_size: int = 20
):
    """
    Specialized cache decorator for list endpoints
    Caches paginated results with proper cache key generation
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            request = kwargs.get('request')

            # Build cache key from query params
            key_parts = [key_prefix or func.__name__]

            if request:
                # Include pagination and filter params
                params = dict(request.query_params)
                relevant_params = {k: v for k, v in params.items()
                                 if k in ['page', 'limit', 'sort', 'order', 'search', 'filter']}
                if relevant_params:
                    key_parts.append(str(sorted(relevant_params.items())))

            cache_key = generate_cache_key(*key_parts)

            # Try cache
            cached = await get_from_cache(cache_key)
            if cached is not None:
                return cached

            # Execute and cache
            result = await func(*args, **kwargs)

            if result is not None:
                await set_in_cache(cache_key, result, ttl=ttl)
                local_cache.set(cache_key, result, ttl=min(ttl, 60))

            return result

        return wrapper
    return decorator


def cached_detail(
    ttl: int = 600,
    key_prefix: str = "",
    id_param: str = "id"
):
    """
    Specialized cache decorator for detail endpoints
    Caches individual resource details
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Get ID from kwargs
            resource_id = kwargs.get(id_param) or kwargs.get(f"{id_param}_id")

            if not resource_id:
                return await func(*args, **kwargs)

            # Build cache key
            cache_key = generate_cache_key(key_prefix or func.__name__, str(resource_id))

            # Try local cache first
            local_result = local_cache.get(cache_key)
            if local_result is not None:
                return local_result

            # Try Redis
            cached = await get_from_cache(cache_key)
            if cached is not None:
                local_cache.set(cache_key, cached, ttl=min(ttl, 60))
                return cached

            # Execute and cache
            result = await func(*args, **kwargs)

            if result is not None:
                await set_in_cache(cache_key, result, ttl=ttl)
                local_cache.set(cache_key, result, ttl=min(ttl, 60))

            return result

        return wrapper
    return decorator


class CacheStats:
    """Track cache hit/miss statistics"""

    def __init__(self):
        self.hits = 0
        self.misses = 0
        self.local_hits = 0
        self.redis_hits = 0
        self.persistent_hits = 0

    def record_hit(self, source: str = "redis"):
        self.hits += 1
        if source == "local":
            self.local_hits += 1
        elif source == "redis":
            self.redis_hits += 1
        elif source == "persistent":
            self.persistent_hits += 1

    def record_miss(self):
        self.misses += 1

    def get_stats(self) -> dict:
        total = self.hits + self.misses
        hit_rate = (self.hits / total * 100) if total > 0 else 0

        return {
            "total_requests": total,
            "hits": self.hits,
            "misses": self.misses,
            "hit_rate": f"{hit_rate:.2f}%",
            "local_hits": self.local_hits,
            "redis_hits": self.redis_hits,
            "persistent_hits": self.persistent_hits
        }


# Global cache stats instance
cache_stats = CacheStats()


def cached_with_stats(
    ttl: int = 300,
    key_prefix: str = "",
    use_local: bool = True
):
    """Cache decorator with statistics tracking"""
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            cache_key = generate_cache_key(key_prefix or func.__name__, str(kwargs))

            # Try local cache
            if use_local:
                local_result = local_cache.get(cache_key)
                if local_result is not None:
                    cache_stats.record_hit("local")
                    return local_result

            # Try Redis
            cached = await get_from_cache(cache_key)
            if cached is not None:
                cache_stats.record_hit("redis")
                if use_local:
                    local_cache.set(cache_key, cached, ttl=min(ttl, 60))
                return cached

            # Miss - execute function
            cache_stats.record_miss()
            result = await func(*args, **kwargs)

            if result is not None:
                await set_in_cache(cache_key, result, ttl=ttl)
                if use_local:
                    local_cache.set(cache_key, result, ttl=min(ttl, 60))

            return result

        return wrapper
    return decorator
