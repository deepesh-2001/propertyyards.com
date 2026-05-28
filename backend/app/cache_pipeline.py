"""
Redis Pipeline Operations
High-performance batch Redis operations using pipelining
"""
from typing import Dict, Any, Optional, List, Union
import asyncio
import logging
import json
import pickle

from app.cache import cache

logger = logging.getLogger(__name__)


class RedisPipeline:
    """Redis pipeline for batch operations"""

    def __init__(self):
        self.commands = []
        self.max_pipeline_size = 1000

    async def get_many(self, keys: List[str]) -> Dict[str, Any]:
        """Get multiple keys in one pipeline operation"""
        if not keys:
            return {}

        try:
            # Use mget for efficient multi-key retrieval
            values = await cache.mget(keys)

            # Parse results
            results = {}
            for key, value in zip(keys, values):
                if value:
                    try:
                        results[key] = json.loads(value)
                    except (json.JSONDecodeError, TypeError):
                        results[key] = value

            return results

        except Exception as e:
            logger.error(f"Pipeline get_many error: {e}")
            return {}

    async def set_many(
        self,
        mapping: Dict[str, Any],
        ttl: int = 3600
    ) -> bool:
        """Set multiple keys in one pipeline operation"""
        if not mapping:
            return True

        try:
            # Serialize values
            serialized = {
                key: json.dumps(value) if not isinstance(value, (str, bytes)) else value
                for key, value in mapping.items()
            }

            # Use mset for efficient multi-key set
            await cache.mset(serialized)

            # Set TTL for all keys using pipeline
            pipe = cache.pipeline()
            for key in mapping.keys():
                pipe.expire(key, ttl)
            await pipe.execute()

            return True

        except Exception as e:
            logger.error(f"Pipeline set_many error: {e}")
            return False

    async def delete_many(self, keys: List[str]) -> int:
        """Delete multiple keys in one operation"""
        if not keys:
            return 0

        try:
            return await cache.delete(*keys)
        except Exception as e:
            logger.error(f"Pipeline delete_many error: {e}")
            return 0

    async def get_or_set_many(
        self,
        keys_compute_map: Dict[str, Callable],
        ttl: int = 3600
    ) -> Dict[str, Any]:
        """
        Get multiple values from cache or compute and store them
        Highly efficient for batch operations
        """
        results = {}
        keys_to_compute = []

        # Try to get all from cache first
        cached_values = await self.get_many(list(keys_compute_map.keys()))

        for key, compute_func in keys_compute_map.items():
            if key in cached_values:
                results[key] = cached_values[key]
            else:
                keys_to_compute.append((key, compute_func))

        # Compute missing values concurrently
        if keys_to_compute:
            compute_tasks = [
                self._safe_compute(key, func)
                for key, func in keys_to_compute
            ]
            computed_results = await asyncio.gather(*compute_tasks, return_exceptions=True)

            # Store computed values
            values_to_cache = {}
            for (key, _), result in zip(keys_to_compute, computed_results):
                if not isinstance(result, Exception):
                    results[key] = result
                    values_to_cache[key] = result

            # Batch store in cache
            if values_to_cache:
                await self.set_many(values_to_cache, ttl)

        return results

    async def _safe_compute(self, key: str, func: Callable) -> Any:
        """Safely execute compute function"""
        try:
            if asyncio.iscoroutinefunction(func):
                return await func()
            return func()
        except Exception as e:
            logger.error(f"Compute error for key {key}: {e}")
            raise

    async def increment_counters(
        self,
        counters: Dict[str, int]
    ) -> Dict[str, int]:
        """Increment multiple counters atomically"""
        try:
            pipe = cache.pipeline()
            for key, amount in counters.items():
                pipe.incrby(key, amount)

            results = await pipe.execute()
            return dict(zip(counters.keys(), results))

        except Exception as e:
            logger.error(f"Pipeline increment error: {e}")
            return {}

    async def set_with_tags(
        self,
        key: str,
        value: Any,
        tags: List[str],
        ttl: int = 3600
    ):
        """Set value with tags for tag-based invalidation"""
        try:
            # Store value
            await cache.setex(key, ttl, json.dumps(value))

            # Add to tag sets
            pipe = cache.pipeline()
            for tag in tags:
                tag_key = f"tag:{tag}"
                pipe.sadd(tag_key, key)
                pipe.expire(tag_key, ttl * 2)  # Tag expiration longer than value

            await pipe.execute()

        except Exception as e:
            logger.error(f"Set with tags error: {e}")

    async def invalidate_by_tag(self, tag: str) -> int:
        """Invalidate all keys with a specific tag"""
        try:
            tag_key = f"tag:{tag}"

            # Get all keys with this tag
            keys = await cache.smembers(tag_key)

            if keys:
                # Delete all keys
                await cache.delete(*keys)
                # Delete tag set
                await cache.delete(tag_key)

            return len(keys)

        except Exception as e:
            logger.error(f"Tag invalidation error: {e}")
            return 0


class CacheWarmer:
    """Intelligent cache warming system"""

    def __init__(self, pipeline: RedisPipeline):
        self.pipeline = pipeline
        self.warming_in_progress = False

    async def warm_analytics_cache(self, database):
        """Warm analytics caches in bulk"""
        if self.warming_in_progress:
            return

        self.warming_in_progress = True
        try:
            from app.analytics import analytics_manager

            # Define cache entries to warm
            cache_entries = {
                "analytics:dashboard": lambda: analytics_manager.get_dashboard_analytics(database),
                "analytics:property": lambda: analytics_manager.get_property_analytics(database),
                "analytics:user": lambda: analytics_manager.get_user_analytics(database),
                "analytics:revenue": lambda: analytics_manager.get_revenue_analytics(database),
            }

            # Use pipeline for efficient warming
            await self.pipeline.get_or_set_many(cache_entries, ttl=3600)

            logger.info("Analytics cache warmed successfully")

        except Exception as e:
            logger.error(f"Cache warming error: {e}")
        finally:
            self.warming_in_progress = False

    async def warm_property_cache(self, database, limit: int = 100):
        """Warm popular property caches"""
        try:
            # Get most viewed properties
            pipeline = [
                {"$sort": {"view_count": -1}},
                {"$limit": limit},
                {"$project": {"_id": 1, "title": 1, "price": 1, "city": 1}}
            ]

            properties = await database.properties.aggregate(pipeline).to_list(length=limit)

            # Batch cache properties
            cache_data = {
                f"property:{str(prop['_id'])}": prop
                for prop in properties
            }

            await self.pipeline.set_many(cache_data, ttl=1800)

            logger.info(f"Property cache warmed with {len(properties)} items")

        except Exception as e:
            logger.error(f"Property cache warming error: {e}")


class LocalCache:
    """In-memory local cache for ultra-fast access"""

    def __init__(self, max_size: int = 1000):
        self._cache: Dict[str, Any] = {}
        self._ttl: Dict[str, float] = {}
        self.max_size = max_size
        self._access_count: Dict[str, int] = {}

    def get(self, key: str) -> Optional[Any]:
        """Get from local cache"""
        if key in self._cache:
            # Check TTL
            if self._ttl.get(key, 0) > asyncio.get_event_loop().time():
                self._access_count[key] = self._access_count.get(key, 0) + 1
                return self._cache[key]
            else:
                # Expired
                self.delete(key)
        return None

    def set(self, key: str, value: Any, ttl: int = 60):
        """Set in local cache with LRU eviction"""
        # Evict if at capacity
        if len(self._cache) >= self.max_size and key not in self._cache:
            self._evict_lru()

        self._cache[key] = value
        self._ttl[key] = asyncio.get_event_loop().time() + ttl
        self._access_count[key] = 0

    def delete(self, key: str):
        """Delete from local cache"""
        self._cache.pop(key, None)
        self._ttl.pop(key, None)
        self._access_count.pop(key, None)

    def _evict_lru(self):
        """Evict least recently used item"""
        if not self._access_count:
            return

        # Find least accessed
        lru_key = min(self._access_count, key=self._access_count.get)
        self.delete(lru_key)

    def clear(self):
        """Clear all local cache"""
        self._cache.clear()
        self._ttl.clear()
        self._access_count.clear()


# Global instances
redis_pipeline = RedisPipeline()
cache_warmer = CacheWarmer(redis_pipeline)
local_cache = LocalCache(max_size=1000)
