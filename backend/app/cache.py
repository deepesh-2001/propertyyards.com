"""
Redis caching layer
"""
import json
from typing import Any, Optional
import redis.asyncio as redis
from app.config import settings
import logging

logger = logging.getLogger(__name__)

cache: Optional[redis.Redis] = None


async def init_cache():
    """Initialize Redis connection"""
    global cache
    try:
        cache = await redis.from_url(settings.REDIS_URL, encoding="utf8", decode_responses=True)
        await cache.ping()
        logger.info("Redis cache initialized successfully")
    except Exception as e:
        logger.error(f"Failed to connect to Redis: {e}")
        cache = None


async def close_cache():
    """Close Redis connection"""
    global cache
    if cache:
        await cache.close()
        logger.info("Redis cache closed")


async def get_from_cache(key: str) -> Optional[Any]:
    """Get value from cache"""
    if not cache:
        return None
    try:
        value = await cache.get(key)
        if value:
            return json.loads(value)
        return None
    except Exception as e:
        logger.error(f"Cache get error for key {key}: {e}")
        return None


async def set_in_cache(key: str, value: Any, ttl: int = None) -> bool:
    """Set value in cache"""
    if not cache:
        return False
    try:
        ttl = ttl or settings.CACHE_TTL
        await cache.setex(key, ttl, json.dumps(value, default=str))
        return True
    except Exception as e:
        logger.error(f"Cache set error for key {key}: {e}")
        return False


async def delete_from_cache(key: str) -> bool:
    """Delete value from cache"""
    if not cache:
        return False
    try:
        await cache.delete(key)
        return True
    except Exception as e:
        logger.error(f"Cache delete error for key {key}: {e}")
        return False


async def invalidate_cache_pattern(pattern: str) -> int:
    """Invalidate multiple cache keys by pattern"""
    if not cache:
        return 0
    try:
        keys = await cache.keys(pattern)
        if keys:
            return await cache.delete(*keys)
        return 0
    except Exception as e:
        logger.error(f"Cache pattern invalidate error for pattern {pattern}: {e}")
        return 0


def generate_cache_key(*args) -> str:
    """Generate cache key from multiple arguments"""
    return ":".join(str(arg) for arg in args)

