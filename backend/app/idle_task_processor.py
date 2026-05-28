"""
Idle Task Processor
Handles background processing during low-traffic periods
Includes AI image generation, cache warming, and maintenance tasks
"""
import asyncio
import logging
from typing import List, Dict, Any, Optional, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import time

from app.realtime_analytics import realtime_collector
from app.ai_image_service import ai_image_generator, image_cache_manager, GeneratedImage
from app.social_media_manager import social_media_manager
from app.cache_pipeline import cache_warmer
from app.background_tasks import background_processor

logger = logging.getLogger(__name__)


class TaskPriority(Enum):
    LOW = 1
    MEDIUM = 2
    HIGH = 3


@dataclass
class IdleTask:
    """Idle task definition"""
    id: str
    name: str
    task_func: Callable
    priority: TaskPriority
    estimated_duration: int  # seconds
    last_run: Optional[datetime] = None
    run_count: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)


class IdleTaskProcessor:
    """Processes tasks during system idle time"""

    def __init__(self):
        self.tasks: Dict[str, IdleTask] = {}
        self.is_running = False
        self.processor_task = None
        self.min_idle_threshold = 10  # Minimum idle time before processing (seconds)
        self.idle_check_interval = 30  # Check every 30 seconds
        self.current_load = 0.0
        self.load_history: List[float] = []
        self.max_history = 10

    def register_task(
        self,
        task_id: str,
        name: str,
        task_func: Callable,
        priority: TaskPriority = TaskPriority.MEDIUM,
        estimated_duration: int = 60
    ):
        """Register a task for idle processing"""
        self.tasks[task_id] = IdleTask(
            id=task_id,
            name=name,
            task_func=task_func,
            priority=priority,
            estimated_duration=estimated_duration
        )
        logger.info(f"Registered idle task: {name} (priority: {priority.name})")

    async def start(self):
        """Start the idle task processor"""
        if self.is_running:
            return

        self.is_running = True
        self.processor_task = asyncio.create_task(self._processor_loop())
        logger.info("Idle task processor started")

    async def stop(self):
        """Stop the idle task processor"""
        self.is_running = False
        if self.processor_task:
            self.processor_task.cancel()
        logger.info("Idle task processor stopped")

    async def _processor_loop(self):
        """Main processor loop"""
        while self.is_running:
            try:
                # Update current load
                await self._update_load_metrics()

                # Check if system is idle
                if await self._is_system_idle():
                    logger.info("System idle - processing tasks")
                    await self._process_idle_tasks()

                await asyncio.sleep(self.idle_check_interval)

            except Exception as e:
                logger.error(f"Idle processor error: {e}")
                await asyncio.sleep(self.idle_check_interval)

    async def _update_load_metrics(self):
        """Update system load metrics"""
        # Get real-time metrics
        current_minute = realtime_collector.get_current_minute()

        # Calculate load based on API calls and active sessions
        api_calls = current_minute.api_calls
        active_sessions = current_minute.active_sessions

        # Simple load calculation (0.0 to 1.0)
        load = min(1.0, (api_calls / 100 + active_sessions / 50) / 2)

        self.current_load = load
        self.load_history.append(load)

        # Keep only recent history
        if len(self.load_history) > self.max_history:
            self.load_history.pop(0)

    async def _is_system_idle(self) -> bool:
        """Check if system is in idle state"""
        if len(self.load_history) < 3:
            return False

        # Check if load has been low for the last few checks
        recent_loads = self.load_history[-3:]
        avg_load = sum(recent_loads) / len(recent_loads)

        return avg_load < 0.3  # Consider idle if load < 30%

    async def _process_idle_tasks(self):
        """Process tasks during idle time"""
        # Sort tasks by priority
        sorted_tasks = sorted(
            self.tasks.values(),
            key=lambda t: (t.priority.value, t.last_run or datetime.min)
        )

        for task in sorted_tasks:
            if not self.is_running:
                break

            # Check if enough time has passed since last run
            if task.last_run:
                time_since_last = (datetime.utcnow() - task.last_run).total_seconds()
                min_interval = self._get_min_interval(task.priority)

                if time_since_last < min_interval:
                    continue

            try:
                logger.info(f"Processing idle task: {task.name}")
                start_time = time.time()

                # Execute task
                if asyncio.iscoroutinefunction(task.task_func):
                    await task.task_func()
                else:
                    task.task_func()

                # Update task stats
                task.last_run = datetime.utcnow()
                task.run_count += 1

                duration = time.time() - start_time
                logger.info(f"Task {task.name} completed in {duration:.2f}s")

                # Small delay between tasks
                await asyncio.sleep(1)

                # Check if still idle after each task
                await self._update_load_metrics()
                if not await self._is_system_idle():
                    logger.info("System no longer idle - pausing task processing")
                    break

            except Exception as e:
                logger.error(f"Task {task.name} failed: {e}")

    def _get_min_interval(self, priority: TaskPriority) -> int:
        """Get minimum interval between runs based on priority"""
        intervals = {
            TaskPriority.HIGH: 300,    # 5 minutes
            TaskPriority.MEDIUM: 600,  # 10 minutes
            TaskPriority.LOW: 1800     # 30 minutes
        }
        return intervals.get(priority, 600)

    def get_task_status(self) -> Dict[str, Any]:
        """Get status of all registered tasks"""
        return {
            "is_running": self.is_running,
            "current_load": round(self.current_load, 2),
            "is_idle": self._calculate_is_idle(),
            "tasks": [
                {
                    "id": task.id,
                    "name": task.name,
                    "priority": task.priority.name,
                    "last_run": task.last_run.isoformat() if task.last_run else None,
                    "run_count": task.run_count,
                    "estimated_duration": task.estimated_duration
                }
                for task in self.tasks.values()
            ]
        }

    def _calculate_is_idle(self) -> bool:
        """Calculate if system is idle based on history"""
        if len(self.load_history) < 3:
            return False
        return sum(self.load_history[-3:]) / 3 < 0.3


class AIImageGenerationTask:
    """Background task for AI image generation"""

    def __init__(self, database):
        self.database = database
        self.pending_generations = []

    async def execute(self):
        """Execute AI image generation for pending items"""
        try:
            # Process image generation queue
            await ai_image_generator.process_queue_during_idle(max_concurrent=2)

            # Generate future prediction visuals
            await self._generate_future_visuals()

            # Generate market trend images
            await self._generate_market_visuals()

        except Exception as e:
            logger.error(f"AI image generation task error: {e}")

    async def _generate_future_visuals(self):
        """Generate future prediction visualizations"""
        try:
            # Get top cities
            pipeline = [
                {"$match": {"status": "active"}},
                {"$group": {"_id": "$city", "count": {"$sum": 1}}},
                {"$sort": {"count": -1}},
                {"$limit": 5}
            ]
            top_cities = await self.database.properties.aggregate(pipeline).to_list(length=5)

            for city_data in top_cities:
                city = city_data["_id"]

                # Queue future visualization
                await ai_image_generator.queue_generation({
                    "type": "future",
                    "data": {
                        "location": city,
                        "year": 2030,
                        "growth_rate": 25
                    },
                    "property_type": "smart_city"
                })

            logger.info(f"Queued future visuals for {len(top_cities)} cities")

        except Exception as e:
            logger.error(f"Future visual generation error: {e}")

    async def _generate_market_visuals(self):
        """Generate market trend visualizations"""
        try:
            # Get market data for top property types
            property_types = ["apartment", "villa", "penthouse", "studio"]

            for prop_type in property_types:
                # Queue market visualization
                await ai_image_generator.queue_generation({
                    "type": "market",
                    "data": {
                        "city": "All Major Cities",
                        "trend": "growing",
                        "property_type": prop_type
                    },
                    "chart_type": "trend"
                })

            logger.info(f"Queued market visuals for {len(property_types)} property types")

        except Exception as e:
            logger.error(f"Market visual generation error: {e}")


class SocialMediaContentTask:
    """Background task for social media content generation"""

    def __init__(self, database):
        self.database = database

    async def execute(self):
        """Execute social media content generation"""
        try:
            # Auto-generate posts from recent activity
            posts = await social_media_manager.auto_generate_posts(self.database, count=5)

            if posts:
                logger.info(f"Auto-generated {len(posts)} social media posts")

        except Exception as e:
            logger.error(f"Social media content task error: {e}")


class CacheMaintenanceTask:
    """Background task for cache maintenance"""

    def __init__(self, database):
        self.database = database

    async def execute(self):
        """Execute cache maintenance"""
        try:
            from app.persistent_cache import persistent_cache

            # Clean up expired cache entries
            cleaned = await persistent_cache.cleanup_expired(self.database)
            logger.info(f"Cleaned up {cleaned} expired cache entries")

            # Warm popular caches
            await cache_warmer.warm_property_cache(self.database, limit=50)

        except Exception as e:
            logger.error(f"Cache maintenance task error: {e}")


class AnalyticsCompilationTask:
    """Background task for compiling analytics"""

    def __init__(self, database):
        self.database = database

    async def execute(self):
        """Execute analytics compilation"""
        try:
            from app.timeseries import timeseries_manager, TimeSeriesGranularity

            # Compile daily aggregates
            await timeseries_manager.store_metric(
                "daily_active_users",
                0.0,  # Would calculate from actual data
                {},
                TimeSeriesGranularity.DAY,
                self.database
            )

            # Cleanup old time-series data
            from app.timeseries import timeseries_manager
            cleaned = await timeseries_manager.cleanup_old_data(self.database)
            logger.info(f"Cleaned up {cleaned} old time-series entries")

        except Exception as e:
            logger.error(f"Analytics compilation task error: {e}")


class DatabaseOptimizationTask:
    """Background task for database optimization"""

    def __init__(self, database):
        self.database = database

    async def execute(self):
        """Execute database optimization"""
        try:
            # This would run database maintenance operations
            # like reindexing, vacuuming, etc.
            logger.info("Database optimization task executed")

        except Exception as e:
            logger.error(f"Database optimization error: {e}")


class NewsGenerationTask:
    """Background task for generating news articles during idle time"""

    def __init__(self, database):
        self.database = database

    async def execute(self):
        """Execute news generation"""
        try:
            from app.news_service import ai_article_generator, article_manager
            from app.config import settings

            # Generate articles only if API key is configured
            if not ai_article_generator.api_key:
                return

            # Topics for article generation
            topics = [
                ("Real Estate Market Trends in India 2024", ArticleCategory.MARKET_TRENDS, ["market", "trends", "india", "2024"]),
                ("Top Investment Locations in Mumbai", ArticleCategory.INVESTMENT, ["mumbai", "investment", "property"]),
                ("Smart Home Technology Trends", ArticleCategory.TECHNOLOGY, ["smart home", "technology", "automation"]),
                ("Luxury Living: What Buyers Want", ArticleCategory.LIFESTYLE, ["luxury", "lifestyle", "buyers"]),
                ("RERA Guidelines for Home Buyers", ArticleCategory.LEGAL, ["rera", "legal", "guidelines"]),
            ]

            author_name = getattr(settings, 'NEWS_AUTHOR_NAME', 'PropertyYards Team')

            for topic, category, keywords in topics[:2]:  # Generate max 2 articles per idle cycle
                try:
                    # Check if similar article exists recently
                    existing = await self.database.news_articles.find_one({
                        "title": {"$regex": topic[:20], "$options": "i"},
                        "created_at": {"$gte": datetime.utcnow() - timedelta(days=7)}
                    })

                    if existing:
                        continue

                    article = await ai_article_generator.generate_article(
                        topic=topic,
                        category=category,
                        keywords=keywords,
                        tone="professional",
                        word_count=800
                    )

                    if article:
                        article.author = f"{author_name}"
                        article_id = await article_manager.create_article(article, self.database)

                        if article_id:
                            logger.info(f"Generated article during idle: {article.title[:50]}...")

                            # Auto-publish if enabled
                            if getattr(settings, 'AUTO_PUBLISH_NEWS', False):
                                await article_manager.publish_article(article_id, self.database)

                except Exception as e:
                    logger.error(f"News generation for topic '{topic}' failed: {e}")

        except Exception as e:
            logger.error(f"News generation task error: {e}")


# Global idle task processor
idle_task_processor = IdleTaskProcessor()


async def setup_idle_tasks(database):
    """Setup all idle tasks"""
    # AI Image Generation
    ai_task = AIImageGenerationTask(database)
    idle_task_processor.register_task(
        "ai_image_gen",
        "AI Image Generation",
        ai_task.execute,
        TaskPriority.MEDIUM,
        estimated_duration=300
    )

    # Social Media Content
    social_task = SocialMediaContentTask(database)
    idle_task_processor.register_task(
        "social_content",
        "Social Media Content",
        social_task.execute,
        TaskPriority.LOW,
        estimated_duration=60
    )

    # Cache Maintenance
    cache_task = CacheMaintenanceTask(database)
    idle_task_processor.register_task(
        "cache_maintenance",
        "Cache Maintenance",
        cache_task.execute,
        TaskPriority.MEDIUM,
        estimated_duration=120
    )

    # Analytics Compilation
    analytics_task = AnalyticsCompilationTask(database)
    idle_task_processor.register_task(
        "analytics_compile",
        "Analytics Compilation",
        analytics_task.execute,
        TaskPriority.LOW,
        estimated_duration=180
    )

    # Database Optimization
    db_task = DatabaseOptimizationTask(database)
    idle_task_processor.register_task(
        "db_optimize",
        "Database Optimization",
        db_task.execute,
        TaskPriority.LOW,
        estimated_duration=600
    )

    # News Article Generation (Idle time)
    from app.news_service import ArticleCategory
    news_task = NewsGenerationTask(database)
    idle_task_processor.register_task(
        "news_generation",
        "News Article Generation",
        news_task.execute,
        TaskPriority.LOW,
        estimated_duration=300
    )

    logger.info("All idle tasks registered")
