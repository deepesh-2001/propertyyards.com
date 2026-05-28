"""
Performance Optimization Module
Handles query caching, rate limiting, and async query optimization for high throughput (10,000 QPM)
"""
from typing import Dict, Any, Optional, List, Callable
from datetime import datetime, timedelta
import logging
import asyncio
import json
from functools import wraps

from app.config import settings
from app.cache import get_cache

logger = logging.getLogger(__name__)


class QueryCacheLayer:
    """Multi-layer caching system for high throughput"""
    
    def __init__(self):
        self.cache = get_cache()
        self.default_ttl = 300  # 5 minutes
        self.cache_stats = {
            "hits": 0,
            "misses": 0,
            "total": 0
        }
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        try:
            value = await self.cache.get(key)
            if value:
                self.cache_stats["hits"] += 1
                return json.loads(value)
            self.cache_stats["misses"] += 1
            return None
        except Exception as e:
            logger.error(f"Cache get error: {e}")
            return None
    
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set value in cache"""
        try:
            ttl = ttl or self.default_ttl
            serialized = json.dumps(value)
            await self.cache.set(key, serialized, ex=ttl)
            return True
        except Exception as e:
            logger.error(f"Cache set error: {e}")
            return False
    
    async def delete(self, key: str) -> bool:
        """Delete value from cache"""
        try:
            await self.cache.delete(key)
            return True
        except Exception as e:
            logger.error(f"Cache delete error: {e}")
            return False
    
    async def invalidate_pattern(self, pattern: str) -> bool:
        """Invalidate cache by pattern"""
        try:
            await self.cache.delete(pattern)
            return True
        except Exception as e:
            logger.error(f"Cache pattern invalidation error: {e}")
            return False
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        self.cache_stats["total"] = self.cache_stats["hits"] + self.cache_stats["misses"]
        hit_rate = (self.cache_stats["hits"] / self.cache_stats["total"] * 100) if self.cache_stats["total"] > 0 else 0
        return {
            **self.cache_stats,
            "hit_rate": f"{hit_rate:.2f}%"
        }


class RateLimiter:
    """Rate limiter for high throughput protection"""
    
    def __init__(self):
        self.cache = get_cache()
        self.requests_per_minute = settings.RATE_LIMIT_REQUESTS
        self.requests_per_user = settings.RATE_LIMIT_PER_USER
        self.burst_size = settings.RATE_LIMIT_BURST
    
    async def check_rate_limit(self, identifier: str, user_id: Optional[str] = None) -> Dict[str, Any]:
        """Check if request is within rate limits"""
        try:
            current_time = datetime.utcnow()
            minute_key = f"rate_limit:{identifier}:{current_time.strftime('%Y%m%d%H%M')}"
            
            # Get current count
            current_count = await self.cache.get(minute_key)
            current_count = int(current_count) if current_count else 0
            
            # Check global rate limit
            if current_count >= self.requests_per_minute:
                return {
                    "allowed": False,
                    "limit": self.requests_per_minute,
                    "remaining": 0,
                    "reset_at": current_time + timedelta(minutes=1),
                    "reason": "global_rate_limit"
                }
            
            # Check user-specific rate limit
            if user_id:
                user_key = f"user_rate_limit:{user_id}:{current_time.strftime('%Y%m%d%H%M')}"
                user_count = await self.cache.get(user_key)
                user_count = int(user_count) if user_count else 0
                
                if user_count >= self.requests_per_user:
                    return {
                        "allowed": False,
                        "limit": self.requests_per_user,
                        "remaining": 0,
                        "reset_at": current_time + timedelta(minutes=1),
                        "reason": "user_rate_limit"
                    }
                
                # Increment user counter
                await self.cache.set(user_key, str(user_count + 1), ex=60)
            
            # Increment global counter
            await self.cache.set(minute_key, str(current_count + 1), ex=60)
            
            return {
                "allowed": True,
                "limit": self.requests_per_minute,
                "remaining": self.requests_per_minute - current_count - 1,
                "reset_at": current_time + timedelta(minutes=1),
                "reason": None
            }
        except Exception as e:
            logger.error(f"Rate limit check error: {e}")
            # Allow request if rate limiting fails
            return {
                "allowed": True,
                "limit": self.requests_per_minute,
                "remaining": self.requests_per_minute,
                "reset_at": datetime.utcnow() + timedelta(minutes=1),
                "reason": None
            }


class AsyncQueryOptimizer:
    """Async query optimization for high throughput"""
    
    def __init__(self):
        self.batch_size = 100
        self.max_concurrent_queries = 50
    
    async def execute_batch_queries(
        self,
        queries: List[Callable],
        database
    ) -> List[Any]:
        """Execute multiple queries concurrently with batching"""
        try:
            semaphore = asyncio.Semaphore(self.max_concurrent_queries)
            
            async def execute_with_limit(query):
                async with semaphore:
                    return await query(database)
            
            results = await asyncio.gather(
                *[execute_with_limit(q) for q in queries],
                return_exceptions=True
            )
            
            # Filter out exceptions
            successful_results = []
            for result in results:
                if not isinstance(result, Exception):
                    successful_results.append(result)
                else:
                    logger.error(f"Query execution error: {result}")
            
            return successful_results
        except Exception as e:
            logger.error(f"Batch query execution error: {e}")
            raise
    
    async def paginate_large_query(
        self,
        collection_name: str,
        query: Dict[str, Any],
        database,
        batch_size: Optional[int] = None
    ) -> List[Any]:
        """Paginate large queries for better performance"""
        try:
            batch_size = batch_size or self.batch_size
            all_results = []
            skip = 0
            
            while True:
                cursor = database[collection_name].find(query).skip(skip).limit(batch_size)
                batch = await cursor.to_list(length=batch_size)
                
                if not batch:
                    break
                
                all_results.extend(batch)
                skip += batch_size
                
                # Stop if we've retrieved all results
                if len(batch) < batch_size:
                    break
            
            return all_results
        except Exception as e:
            logger.error(f"Paginated query error: {e}")
            raise
    
    async def parallel_aggregate(
        self,
        collection_name: str,
        pipelines: List[Dict[str, Any]],
        database
    ) -> List[Dict[str, Any]]:
        """Execute multiple aggregation pipelines in parallel"""
        try:
            async def execute_pipeline(pipeline):
                result = await database[collection_name].aggregate(pipeline).to_list(length=1000)
                return result
            
            results = await self.execute_batch_queries(
                [lambda db, p=pipeline: execute_pipeline(p) for pipeline in pipelines],
                database
            )
            
            return results
        except Exception as e:
            logger.error(f"Parallel aggregation error: {e}")
            raise


def cached(ttl: int = 300):
    """Decorator for caching function results"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            cache_layer = QueryCacheLayer()
            
            # Generate cache key
            cache_key = f"cached:{func.__name__}:{str(args)}:{str(kwargs)}"
            
            # Try to get from cache
            cached_result = await cache_layer.get(cache_key)
            if cached_result is not None:
                return cached_result
            
            # Execute function
            result = await func(*args, **kwargs)
            
            # Cache result
            await cache_layer.set(cache_key, result, ttl)
            
            return result
        return wrapper
    return decorator


def rate_limited(user_id_param: str = "user_id"):
    """Decorator for rate limiting endpoints"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            rate_limiter = RateLimiter()
            
            # Get user_id from kwargs or args
            user_id = kwargs.get(user_id_param)
            identifier = f"{func.__name__}:{user_id or 'anonymous'}"
            
            # Check rate limit
            rate_check = await rate_limiter.check_rate_limit(identifier, user_id)
            
            if not rate_check["allowed"]:
                from fastapi import HTTPException
                raise HTTPException(
                    status_code=429,
                    detail={
                        "error": "Rate limit exceeded",
                        "limit": rate_check["limit"],
                        "reset_at": rate_check["reset_at"].isoformat()
                    }
                )
            
            # Execute function
            return await func(*args, **kwargs)
        return wrapper
    return decorator


class PerformanceMonitor:
    """Performance monitoring for high throughput"""
    
    def __init__(self):
        self.metrics = {
            "query_times": [],
            "cache_hits": 0,
            "cache_misses": 0,
            "total_requests": 0,
            "errors": 0
        }
    
    def record_query_time(self, duration_ms: float):
        """Record query execution time"""
        self.metrics["query_times"].append(duration_ms)
        # Keep only last 1000 measurements
        if len(self.metrics["query_times"]) > 1000:
            self.metrics["query_times"] = self.metrics["query_times"][-1000:]
    
    def record_cache_hit(self):
        """Record cache hit"""
        self.metrics["cache_hits"] += 1
    
    def record_cache_miss(self):
        """Record cache miss"""
        self.metrics["cache_misses"] += 1
    
    def record_request(self):
        """Record request"""
        self.metrics["total_requests"] += 1
    
    def record_error(self):
        """Record error"""
        self.metrics["errors"] += 1
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get performance metrics"""
        avg_query_time = (
            sum(self.metrics["query_times"]) / len(self.metrics["query_times"])
            if self.metrics["query_times"]
            else 0
        )
        
        cache_hit_rate = (
            self.metrics["cache_hits"] / (self.metrics["cache_hits"] + self.metrics["cache_misses"]) * 100
            if (self.metrics["cache_hits"] + self.metrics["cache_misses"]) > 0
            else 0
        )
        
        error_rate = (
            self.metrics["errors"] / self.metrics["total_requests"] * 100
            if self.metrics["total_requests"] > 0
            else 0
        )
        
        return {
            "average_query_time_ms": round(avg_query_time, 2),
            "cache_hit_rate": round(cache_hit_rate, 2),
            "total_requests": self.metrics["total_requests"],
            "error_rate": round(error_rate, 2),
            "queries_per_minute": self._calculate_qpm()
        }
    
    def _calculate_qpm(self) -> float:
        """Calculate queries per minute"""
        if not self.metrics["query_times"]:
            return 0
        
        # Simplified QPM calculation based on recent query times
        recent_queries = len(self.metrics["query_times"])
        return recent_queries  # This would be more sophisticated in production


# Global instances
query_cache = QueryCacheLayer()
rate_limiter = RateLimiter()
query_optimizer = AsyncQueryOptimizer()
performance_monitor = PerformanceMonitor()
