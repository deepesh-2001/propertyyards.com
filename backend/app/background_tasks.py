"""
Background Task Processor
Handles heavy analytics and caching operations in the background
"""
from typing import Callable, Dict, Any, List
from datetime import datetime, timedelta
import asyncio
import logging
from concurrent.futures import ThreadPoolExecutor

logger = logging.getLogger(__name__)


class BackgroundTaskProcessor:
    """Processor for background tasks"""

    def __init__(self):
        self.tasks: Dict[str, asyncio.Task] = {}
        self.results: Dict[str, Any] = {}
        self.executor = ThreadPoolExecutor(max_workers=4)
        self.running = False

    async def start(self):
        """Start the background task processor"""
        self.running = True
        logger.info("Background task processor started")

    async def stop(self):
        """Stop the background task processor"""
        self.running = False

        # Cancel all running tasks
        for task_id, task in self.tasks.items():
            if not task.done():
                task.cancel()
                logger.info(f"Cancelled task: {task_id}")

        self.executor.shutdown(wait=True)
        logger.info("Background task processor stopped")

    async def submit_task(
        self,
        task_id: str,
        func: Callable,
        *args,
        **kwargs
    ) -> str:
        """Submit a task for background execution"""
        if task_id in self.tasks and not self.tasks[task_id].done():
            logger.warning(f"Task {task_id} already running, skipping")
            return task_id

        async def _wrapper():
            try:
                logger.info(f"Starting background task: {task_id}")
                start_time = datetime.utcnow()

                if asyncio.iscoroutinefunction(func):
                    result = await func(*args, **kwargs)
                else:
                    # Run sync function in executor
                    loop = asyncio.get_event_loop()
                    result = await loop.run_in_executor(
                        self.executor,
                        func,
                        *args,
                        **kwargs
                    )

                duration = (datetime.utcnow() - start_time).total_seconds()
                self.results[task_id] = {
                    "result": result,
                    "completed_at": datetime.utcnow(),
                    "duration": duration,
                    "status": "completed"
                }

                logger.info(f"Background task completed: {task_id} ({duration:.2f}s)")

            except Exception as e:
                self.results[task_id] = {
                    "error": str(e),
                    "completed_at": datetime.utcnow(),
                    "status": "failed"
                }
                logger.error(f"Background task failed: {task_id} - {e}")

        self.tasks[task_id] = asyncio.create_task(_wrapper())
        return task_id

    async def get_task_status(self, task_id: str) -> Dict[str, Any]:
        """Get status of a background task"""
        if task_id not in self.tasks:
            return {"status": "not_found"}

        task = self.tasks[task_id]

        if task.done():
            if task_id in self.results:
                return self.results[task_id]
            return {"status": "completed"}

        return {"status": "running"}

    async def schedule_periodic_task(
        self,
        task_id: str,
        func: Callable,
        interval_seconds: int,
        *args,
        **kwargs
    ):
        """Schedule a task to run periodically"""
        async def _periodic_runner():
            while self.running:
                try:
                    await self.submit_task(f"{task_id}_{datetime.utcnow().isoformat()}", func, *args, **kwargs)
                    await asyncio.sleep(interval_seconds)
                except asyncio.CancelledError:
                    break
                except Exception as e:
                    logger.error(f"Periodic task error: {e}")
                    await asyncio.sleep(interval_seconds)

        asyncio.create_task(_periodic_runner())
        logger.info(f"Scheduled periodic task: {task_id} (every {interval_seconds}s)")


class AnalyticsBackgroundProcessor:
    """Background processor specifically for analytics"""

    def __init__(self, task_processor: BackgroundTaskProcessor):
        self.task_processor = task_processor
        self.analytics_manager = None  # Will be set when needed

    async def precompute_daily_analytics(self, database):
        """Pre-compute daily analytics and store in cache"""
        from app.analytics import analytics_manager
        from app.persistent_cache import persistent_cache

        try:
            # Compute all analytics
            dashboard_analytics = await analytics_manager.get_dashboard_analytics(
                database=database
            )

            # Store in persistent cache
            cache_key = f"analytics:daily:{datetime.utcnow().strftime('%Y-%m-%d')}"
            await persistent_cache._store_in_db_cache(
                cache_key,
                dashboard_analytics,
                86400 * 2,  # 2 days TTL
                database
            )

            logger.info("Daily analytics pre-computed and cached")
            return dashboard_analytics

        except Exception as e:
            logger.error(f"Daily analytics pre-computation failed: {e}")
            raise

    async def update_timeseries_metrics(self, database):
        """Update time-series metrics for trending"""
        from app.timeseries import timeseries_manager, TimeSeriesGranularity

        try:
            # Get current counts
            property_count = await database.properties.count_documents({})
            user_count = await database.users.count_documents({})
            inquiry_count = await database.inquiries.count_documents({})

            # Store in time-series
            await timeseries_manager.store_metric(
                "property_count",
                float(property_count),
                {},
                TimeSeriesGranularity.HOUR,
                database
            )

            await timeseries_manager.store_metric(
                "user_count",
                float(user_count),
                {},
                TimeSeriesGranularity.HOUR,
                database
            )

            await timeseries_manager.store_metric(
                "inquiry_count",
                float(inquiry_count),
                {},
                TimeSeriesGranularity.HOUR,
                database
            )

            logger.info("Time-series metrics updated")

        except Exception as e:
            logger.error(f"Time-series update failed: {e}")
            raise

    async def warm_frequently_used_caches(self, database):
        """Warm caches for frequently accessed data"""
        from app.persistent_cache import persistent_cache

        try:
            # Define frequently accessed data
            cache_warmers = {
                "analytics:dashboard": lambda: self.analytics_manager.get_dashboard_analytics(database),
                "analytics:property": lambda: self.analytics_manager.get_property_analytics(database),
                "analytics:user": lambda: self.analytics_manager.get_user_analytics(database),
            }

            # Warm all caches
            await persistent_cache.warm_cache(
                cache_warmers,
                database=database,
                ttl=3600
            )

            logger.info("Frequently used caches warmed")

        except Exception as e:
            logger.error(f"Cache warming failed: {e}")
            raise

    async def cleanup_old_data(self, database):
        """Cleanup old data from cache and time-series"""
        from app.persistent_cache import persistent_cache
        from app.timeseries import timeseries_manager

        try:
            # Cleanup persistent cache
            cache_cleaned = await persistent_cache.cleanup_expired(database)

            # Cleanup time-series
            timeseries_cleaned = await timeseries_manager.cleanup_old_data(database)

            logger.info(f"Cleanup completed: {cache_cleaned} cache, {timeseries_cleaned} timeseries entries")

        except Exception as e:
            logger.error(f"Cleanup failed: {e}")
            raise


# Global instances
background_processor = BackgroundTaskProcessor()
analytics_processor = AnalyticsBackgroundProcessor(background_processor)
