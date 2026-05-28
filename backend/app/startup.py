"""
Startup Script
Initializes background tasks, cache warming, and system setup
"""
import asyncio
import logging
from datetime import datetime, timedelta
from app.background_tasks import background_processor, analytics_processor
from app.persistent_cache import persistent_cache
from app.cache import init_cache
from app.database import init_database, get_database
from app.realtime_analytics import realtime_collector

logger = logging.getLogger(__name__)


async def initialize_system():
    """Initialize all system components"""
    logger.info("Starting system initialization...")

    try:
        # Initialize database
        await init_database()
        database = get_database()

        # Initialize cache
        await init_cache()

        # Start background task processor
        await background_processor.start()

        # Start real-time analytics collector
        await realtime_collector.start()
        logger.info("Real-time analytics collector started")

        # Schedule periodic tasks
        await schedule_periodic_tasks(database)

        # Warm caches
        await warm_initial_caches(database)

        logger.info("System initialization completed successfully")

    except Exception as e:
        logger.error(f"System initialization failed: {e}")
        raise


async def schedule_periodic_tasks(database):
    """Schedule periodic background tasks"""
    logger.info("Scheduling periodic tasks...")

    # Pre-compute daily analytics every hour
    await background_processor.schedule_periodic_task(
        "precompute_analytics",
        analytics_processor.precompute_daily_analytics,
        3600,  # Every hour
        database
    )

    # Update time-series metrics every 15 minutes
    await background_processor.schedule_periodic_task(
        "update_timeseries",
        analytics_processor.update_timeseries_metrics,
        900,  # Every 15 minutes
        database
    )

    # Warm caches every 30 minutes
    await background_processor.schedule_periodic_task(
        "warm_caches",
        analytics_processor.warm_frequently_used_caches,
        1800,  # Every 30 minutes
        database
    )

    # Cleanup old data daily
    await background_processor.schedule_periodic_task(
        "cleanup_data",
        analytics_processor.cleanup_old_data,
        86400,  # Every 24 hours
        database
    )

    logger.info("Periodic tasks scheduled")


async def warm_initial_caches(database):
    """Warm initial caches on startup"""
    logger.info("Warming initial caches...")

    try:
        # Warm dashboard analytics cache
        from app.analytics import analytics_manager

        cache_entries = {
            "analytics:dashboard": lambda: analytics_manager.get_dashboard_analytics(database),
            "analytics:property": lambda: analytics_manager.get_property_analytics(database),
            "analytics:user": lambda: analytics_manager.get_user_analytics(database),
        }

        await persistent_cache.warm_cache(
            cache_entries,
            database=database,
            ttl=3600
        )

        logger.info("Initial caches warmed successfully")

    except Exception as e:
        logger.error(f"Cache warming failed: {e}")
        # Don't raise - app can still function without warmed caches


async def shutdown_system():
    """Gracefully shutdown system"""
    logger.info("Shutting down system...")

    try:
        # Stop background processor
        await background_processor.stop()

        # Stop real-time analytics collector
        await realtime_collector.stop()
        logger.info("Real-time analytics collector stopped")

        # Close cache
        from app.cache import close_cache
        await close_cache()

        # Close database
        from app.database import close_database
        await close_database()

        logger.info("System shutdown completed")

    except Exception as e:
        logger.error(f"System shutdown error: {e}")
        raise
