"""
Optimized Database Operations
High-performance queries with projections, read replica routing, and caching
"""
from typing import Dict, Any, Optional, List, Callable
from datetime import datetime
import logging
from functools import wraps
import asyncio

from app.database import database, read_replica_database, get_read_replica_database
from app.cache import get_from_cache, set_in_cache, generate_cache_key

logger = logging.getLogger(__name__)


class QueryOptimizer:
    """Database query optimizer with caching and read replica routing"""

    def __init__(self):
        self.read_operations = [
            'find', 'find_one', 'count_documents', 'aggregate',
            'distinct', 'estimated_document_count'
        ]

    async def execute_cached(
        self,
        collection_name: str,
        operation: str,
        query: Dict[str, Any],
        projection: Optional[Dict[str, Any]] = None,
        cache_ttl: int = 300,
        use_read_replica: bool = True,
        database = None
    ) -> Any:
        """Execute query with caching and read replica support"""

        # Generate cache key
        cache_key = generate_cache_key(
            "db",
            collection_name,
            operation,
            str(query),
            str(projection)
        )

        # Check cache first
        cached = await get_from_cache(cache_key)
        if cached:
            return cached

        # Choose database (read replica for read operations)
        db = database
        if use_read_replica and operation in self.read_operations:
            db = await get_read_replica_database()

        collection = db[collection_name]

        # Execute operation
        if operation == "find_one":
            result = await collection.find_one(query, projection)
        elif operation == "find":
            cursor = collection.find(query, projection)
            result = await cursor.to_list(length=1000)
        elif operation == "count_documents":
            result = await collection.count_documents(query)
        elif operation == "aggregate":
            cursor = collection.aggregate(query)
            result = await cursor.to_list(length=1000)
        else:
            raise ValueError(f"Unsupported operation: {operation}")

        # Cache result
        if result is not None:
            await set_in_cache(cache_key, result, ttl=cache_ttl)

        return result


class BatchOperations:
    """High-performance batch database operations"""

    @staticmethod
    async def bulk_insert(
        collection,
        documents: List[Dict[str, Any]],
        batch_size: int = 1000
    ) -> List[str]:
        """Insert documents in batches for optimal performance"""
        inserted_ids = []

        for i in range(0, len(documents), batch_size):
            batch = documents[i:i + batch_size]
            result = await collection.insert_many(batch, ordered=False)
            inserted_ids.extend([str(id) for id in result.inserted_ids])

        return inserted_ids

    @staticmethod
    async def bulk_update(
        collection,
        updates: List[Dict[str, Any]],
        batch_size: int = 1000
    ) -> int:
        """Update documents in bulk using bulk_write"""
        from pymongo import UpdateOne

        modified_count = 0

        for i in range(0, len(updates), batch_size):
            batch = updates[i:i + batch_size]
            operations = [
                UpdateOne(
                    {"_id": update["id"]},
                    {"$set": {k: v for k, v in update.items() if k != "id"}}
                )
                for update in batch
            ]

            result = await collection.bulk_write(operations, ordered=False)
            modified_count += result.modified_count

        return modified_count

    @staticmethod
    async def bulk_delete(
        collection,
        ids: List[str],
        batch_size: int = 1000
    ) -> int:
        """Delete documents in bulk"""
        deleted_count = 0

        for i in range(0, len(ids), batch_size):
            batch = ids[i:i + batch_size]
            result = await collection.delete_many({"_id": {"$in": batch}})
            deleted_count += result.deleted_count

        return deleted_count


class ProjectionHelper:
    """Helper for creating database projections to reduce data transfer"""

    @staticmethod
    def for_list(fields: List[str]) -> Dict[str, Any]:
        """Create projection for list view (minimal fields)"""
        projection = {"_id": 1}
        for field in fields:
            projection[field] = 1
        return projection

    @staticmethod
    def for_detail(include_fields: Optional[List[str]] = None) -> Dict[str, Any]:
        """Create projection for detail view"""
        if include_fields:
            return {field: 1 for field in include_fields}
        return None  # No projection, return all

    @staticmethod
    def exclude(fields: List[str]) -> Dict[str, Any]:
        """Create projection that excludes specific fields"""
        return {field: 0 for field in fields}


class CursorPagination:
    """Efficient cursor-based pagination"""

    @staticmethod
    async def paginate(
        collection,
        query: Dict[str, Any],
        sort_field: str,
        sort_order: int = -1,
        limit: int = 20,
        cursor: Optional[str] = None,
        projection: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Cursor-based pagination for efficient large dataset handling
        """
        # Build query with cursor
        if cursor:
            last_value = cursor
            if sort_order == -1:
                query[sort_field] = {"$lt": last_value}
            else:
                query[sort_field] = {"$gt": last_value}

        # Execute query
        cursor_obj = collection.find(
            query,
            projection
        ).sort(sort_field, sort_order).limit(limit + 1)

        results = await cursor_obj.to_list(length=limit + 1)

        # Check if there are more results
        has_more = len(results) > limit
        if has_more:
            results = results[:-1]

        # Generate next cursor
        next_cursor = None
        if has_more and results:
            next_cursor = str(results[-1].get(sort_field))

        # Format results
        formatted = []
        for doc in results:
            doc["id"] = str(doc["_id"])
            del doc["_id"]
            formatted.append(doc)

        return {
            "data": formatted,
            "next_cursor": next_cursor,
            "has_more": has_more,
            "limit": limit
        }


class RequestDeduplicator:
    """Deduplicate concurrent identical requests"""

    def __init__(self):
        self.pending_requests: Dict[str, asyncio.Future] = {}
        self.lock = asyncio.Lock()

    async def execute(self, key: str, func: Callable, *args, **kwargs) -> Any:
        """Execute function with request deduplication"""
        async with self.lock:
            if key in self.pending_requests:
                # Request already in flight, wait for it
                logger.debug(f"Deduplicating request: {key}")
                return await self.pending_requests[key]

            # Create future for this request
            future = asyncio.Future()
            self.pending_requests[key] = future

        try:
            # Execute the function
            result = await func(*args, **kwargs)

            # Set result and notify waiters
            async with self.lock:
                future.set_result(result)
                del self.pending_requests[key]

            return result

        except Exception as e:
            # Set exception and notify waiters
            async with self.lock:
                future.set_exception(e)
                del self.pending_requests[key]
            raise


class FastAnalytics:
    """Optimized analytics with materialized views"""

    @staticmethod
    async def get_property_stats_fast(database) -> Dict[str, Any]:
        """Get property stats using pre-aggregated data"""
        # Try to get from materialized view
        stats = await database.analytics_materialized.find_one(
            {"type": "property_stats"},
            sort=[("updated_at", -1)]
        )

        if stats and (datetime.utcnow() - stats["updated_at"]).seconds < 3600:
            # Return cached stats if less than 1 hour old
            return stats["data"]

        # Fall back to real-time calculation
        return await FastAnalytics._compute_property_stats(database)

    @staticmethod
    async def _compute_property_stats(database) -> Dict[str, Any]:
        """Compute property statistics efficiently"""
        pipeline = [
            {
                "$group": {
                    "_id": None,
                    "total": {"$sum": 1},
                    "active": {
                        "$sum": {"$cond": [{"$eq": ["$status", "active"]}, 1, 0]}
                    },
                    "sold": {
                        "$sum": {"$cond": [{"$eq": ["$status", "sold"]}, 1, 0]}
                    },
                    "avg_price": {"$avg": "$price"},
                    "max_price": {"$max": "$price"},
                    "min_price": {"$min": "$price"}
                }
            }
        ]

        result = await database.properties.aggregate(pipeline).to_list(length=1)

        if result:
            stats = result[0]
            del stats["_id"]

            # Store in materialized view
            await database.analytics_materialized.update_one(
                {"type": "property_stats"},
                {
                    "$set": {
                        "type": "property_stats",
                        "data": stats,
                        "updated_at": datetime.utcnow()
                    }
                },
                upsert=True
            )

            return stats

        return {}


# Global instances
query_optimizer = QueryOptimizer()
batch_operations = BatchOperations()
projection_helper = ProjectionHelper()
cursor_pagination = CursorPagination()
request_deduplicator = RequestDeduplicator()
fast_analytics = FastAnalytics()
