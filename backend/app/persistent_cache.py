"""
Persistent Cache System
Stores historical analytics and computed data for efficiency
"""
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import logging
import hashlib
import json
from app.cache import get_from_cache, set_in_cache, delete_from_cache, generate_cache_key
from app.database import get_db

logger = logging.getLogger(__name__)


class PersistentCacheManager:
    """Manager for persistent caching with database backup"""

    def __init__(self):
        self.short_ttl = 300      # 5 minutes
        self.medium_ttl = 1800    # 30 minutes
        self.long_ttl = 86400     # 24 hours
        self.very_long_ttl = 604800  # 7 days

    async def get_or_compute(
        self,
        key: str,
        compute_func,
        database=None,
        ttl: int = 300,
        persist: bool = True
    ) -> Any:
        """
        Get from cache or compute and store
        First checks Redis, then database, then computes
        """
        try:
            # 1. Check Redis cache
            cached = await get_from_cache(key)
            if cached:
                logger.debug(f"Cache hit (Redis): {key}")
                return cached

            # 2. Check persistent database cache (if persist=True)
            if persist and database:
                db_cached = await self._get_from_db_cache(key, database)
                if db_cached:
                    # Restore to Redis
                    await set_in_cache(key, db_cached, ttl=ttl)
                    logger.debug(f"Cache hit (DB): {key}")
                    return db_cached

            # 3. Compute
            result = await compute_func()

            # 4. Store in both caches
            await set_in_cache(key, result, ttl=ttl)
            if persist and database:
                await self._store_in_db_cache(key, result, ttl, database)

            logger.debug(f"Cache miss, computed: {key}")
            return result

        except Exception as e:
            logger.error(f"Cache error for {key}: {e}")
            # Fallback to direct computation
            return await compute_func()

    async def _get_from_db_cache(
        self,
        key: str,
        database
    ) -> Optional[Any]:
        """Get from persistent database cache"""
        try:
            cache_entry = await database.cache.find_one({
                "key": key,
                "expires_at": {"$gt": datetime.utcnow()}
            })

            if cache_entry:
                return cache_entry["value"]
            return None

        except Exception as e:
            logger.error(f"DB cache get error: {e}")
            return None

    async def _store_in_db_cache(
        self,
        key: str,
        value: Any,
        ttl: int,
        database
    ):
        """Store in persistent database cache"""
        try:
            expires_at = datetime.utcnow() + timedelta(seconds=ttl)

            await database.cache.update_one(
                {"key": key},
                {
                    "$set": {
                        "key": key,
                        "value": value,
                        "created_at": datetime.utcnow(),
                        "expires_at": expires_at,
                        "access_count": 0
                    }
                },
                upsert=True
            )

        except Exception as e:
            logger.error(f"DB cache store error: {e}")

    async def increment_access_count(self, key: str, database):
        """Track cache access for analytics"""
        try:
            await database.cache.update_one(
                {"key": key},
                {"$inc": {"access_count": 1}}
            )
        except Exception as e:
            logger.error(f"Cache access tracking error: {e}")

    async def invalidate_pattern(
        self,
        pattern: str,
        database=None
    ):
        """Invalidate cache by pattern from both Redis and DB"""
        try:
            # Invalidate Redis
            from app.cache import invalidate_cache_pattern
            await invalidate_cache_pattern(pattern)

            # Invalidate DB cache
            if database:
                await database.cache.delete_many({
                    "key": {"$regex": pattern.replace("*", ".*")}
                })

            logger.info(f"Cache invalidated: {pattern}")

        except Exception as e:
            logger.error(f"Cache invalidation error: {e}")

    async def warm_cache(
        self,
        keys_compute_map: Dict[str, callable],
        database=None,
        ttl: int = 3600
    ):
        """Pre-compute and warm cache for frequently accessed data"""
        results = {}
        for key, compute_func in keys_compute_map.items():
            try:
                result = await self.get_or_compute(
                    key,
                    compute_func,
                    database=database,
                    ttl=ttl
                )
                results[key] = result
                logger.info(f"Cache warmed: {key}")
            except Exception as e:
                logger.error(f"Cache warm failed for {key}: {e}")

        return results

    async def cleanup_expired(self, database):
        """Clean up expired cache entries from database"""
        try:
            result = await database.cache.delete_many({
                "expires_at": {"$lt": datetime.utcnow()}
            })
            logger.info(f"Cleaned up {result.deleted_count} expired cache entries")
            return result.deleted_count
        except Exception as e:
            logger.error(f"Cache cleanup error: {e}")
            return 0

    async def get_cache_stats(self, database) -> Dict[str, Any]:
        """Get cache statistics"""
        try:
            total_entries = await database.cache.count_documents({})
            expired_entries = await database.cache.count_documents({
                "expires_at": {"$lt": datetime.utcnow()}
            })
            active_entries = total_entries - expired_entries

            # Get most accessed entries
            pipeline = [
                {"$match": {"access_count": {"$gt": 0}}},
                {"$sort": {"access_count": -1}},
                {"$limit": 10},
                {"$project": {"key": 1, "access_count": 1, "created_at": 1}}
            ]
            popular_entries = await database.cache.aggregate(pipeline).to_list(length=10)

            return {
                "total_entries": total_entries,
                "active_entries": active_entries,
                "expired_entries": expired_entries,
                "popular_entries": popular_entries
            }

        except Exception as e:
            logger.error(f"Cache stats error: {e}")
            return {}


# Global instance
persistent_cache = PersistentCacheManager()
