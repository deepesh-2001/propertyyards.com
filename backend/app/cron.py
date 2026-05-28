"""
Cron job scheduler for periodic tasks
Optimized to run during idle time with AI content generation
Sales product fetching limited to 4 times per day
"""
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime
import logging
from app.cache import cache, get_from_cache, set_in_cache
from app.database import database
from app.config import settings
from app.optimized_background_tasks import (
    optimized_scheduler, setup_optimized_tasks, get_scheduler_status as get_optimized_status
)

logger = logging.getLogger(__name__)

# Create scheduler
scheduler = AsyncIOScheduler()

# Sales fetch schedule: 4 times per day at 2 AM, 8 AM, 2 PM, 8 PM
SALES_FETCH_SCHEDULE = [2, 8, 14, 20]


async def check_cache_health():
    """Check cache health and sync status"""
    try:
        if not cache:
            logger.warning("Cache not initialized, skipping health check")
            return
        
        # Test cache connection
        await cache.ping()
        
        # Get cache stats
        info = await cache.info('stats')
        logger.info(f"Cache health check passed - Keys: {info.get('keyspace', 0)}, Memory: {info.get('used_memory_human', 'N/A')}")
        
        # Update cache health status in cache itself
        await set_in_cache("cache:health:last_check", datetime.utcnow().isoformat(), ttl=120)
        await set_in_cache("cache:health:status", "healthy", ttl=120)
        
    except Exception as e:
        logger.error(f"Cache health check failed: {e}")
        if cache:
            await set_in_cache("cache:health:last_check", datetime.utcnow().isoformat(), ttl=120)
            await set_in_cache("cache:health:status", "unhealthy", ttl=120)


async def sync_cache_data():
    """Sync important data to cache"""
    try:
        if not cache or not database:
            logger.warning("Cache or database not initialized, skipping sync")
            return
        
        logger.info("Starting cache data sync...")
        
        # Example: Sync popular properties to cache
        # This is a placeholder - implement based on your actual data needs
        # popular_properties = await database.properties.find({"status": "active"}).sort("views", -1).limit(20).to_list(None)
        # await set_in_cache("popular:properties", popular_properties, ttl=300)
        
        # Update last sync time
        await set_in_cache("cache:last_sync", datetime.utcnow().isoformat(), ttl=300)
        
        logger.info("Cache data sync completed")
        
    except Exception as e:
        logger.error(f"Cache data sync failed: {e}")


async def cleanup_expired_cache():
    """Clean up expired or stale cache entries"""
    try:
        if not cache:
            logger.warning("Cache not initialized, skipping cleanup")
            return
        
        logger.info("Starting cache cleanup...")
        
        # Get all keys
        keys = await cache.keys("*")
        
        # Check for keys that are too old or expired
        # This is a simplified version - implement based on your needs
        cleaned_count = 0
        for key in keys:
            ttl = await cache.ttl(key)
            if ttl == -1:  # No expiration
                # You might want to add logic to clean up old keys without expiration
                pass
        
        logger.info(f"Cache cleanup completed - Checked {len(keys)} keys")
        
    except Exception as e:
        logger.error(f"Cache cleanup failed: {e}")


async def monitor_system_metrics():
    """Monitor and log system metrics"""
    try:
        import psutil
        
        cpu_percent = psutil.cpu_percent(interval=0.1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        metrics = {
            "timestamp": datetime.utcnow().isoformat(),
            "cpu_percent": cpu_percent,
            "memory_percent": memory.percent,
            "disk_percent": disk.percent
        }
        
        # Store metrics in cache for quick access
        await set_in_cache("system:metrics:latest", metrics, ttl=120)
        
        # Log if metrics are concerning
        if cpu_percent > 80:
            logger.warning(f"High CPU usage: {cpu_percent}%")
        if memory.percent > 80:
            logger.warning(f"High memory usage: {memory.percent}%")
        if disk.percent > 80:
            logger.warning(f"High disk usage: {disk.percent}%")
        
    except Exception as e:
        logger.error(f"System metrics monitoring failed: {e}")


async def sales_product_fetching():
    """
    Fetch sales products - LIMITED TO 4 TIMES PER DAY
    Schedule: 2:00 AM, 8:00 AM, 2:00 PM, 8:00 PM
    Only runs if system is idle (load < 30%)
    """
    try:
        # Check system load
        import psutil
        cpu_percent = psutil.cpu_percent(interval=0.1)
        memory_percent = psutil.virtual_memory().percent
        current_load = (cpu_percent + memory_percent) / 2 / 100
        
        if current_load > 0.3:
            logger.info(f"Sales fetch deferred - system busy (load: {current_load:.2f})")
            return
        
        logger.info("Starting sales product fetching (4x/day limit enforced)")
        
        # Update fetch tracking
        now = datetime.utcnow()
        await set_in_cache("sales:last_fetch", now.isoformat(), ttl=21600)  # 6 hours
        await set_in_cache("sales:fetch_count_today", 
                          await _get_fetch_count_today() + 1, ttl=86400)
        
        # Trigger optimized background task
        from app.optimized_background_tasks import optimized_scheduler
        await optimized_scheduler.refresh_insurance_data_idle(database)
        
        logger.info("Sales product fetching completed during idle time")
        
    except Exception as e:
        logger.error(f"Sales product fetching failed: {e}")


async def _get_fetch_count_today() -> int:
    """Get number of sales fetches today"""
    try:
        count = await get_from_cache("sales:fetch_count_today")
        return int(count) if count else 0
    except:
        return 0


async def generate_ai_content_idle():
    """Generate beautiful AI content during idle time"""
    try:
        from app.optimized_background_tasks import optimized_scheduler
        
        # Check if system is idle enough for AI tasks
        import psutil
        cpu_percent = psutil.cpu_percent(interval=0.1)
        if cpu_percent > 20:  # Only run if CPU < 20%
            return
        
        # Generate beautiful property content
        await optimized_scheduler.generate_beautiful_property_content(database)
        
        # Generate social media content
        await optimized_scheduler.generate_social_media_content(database)
        
        # Generate AI images (only if very idle)
        if cpu_percent < 10:
            await optimized_scheduler.generate_ai_images_idle(database)
        
        logger.info("AI content generation completed during idle time")
        
    except Exception as e:
        logger.error(f"AI content generation failed: {e}")


def start_scheduler():
    """Start the cron job scheduler with optimized idle-time processing"""
    
    # Light-weight tasks - can run anytime
    # Cache health check - every 1 minute
    scheduler.add_job(
        check_cache_health,
        trigger=IntervalTrigger(minutes=1),
        id='cache_health_check',
        name='Cache Health Check',
        replace_existing=True
    )
    
    # System metrics monitoring - every 1 minute
    scheduler.add_job(
        monitor_system_metrics,
        trigger=IntervalTrigger(minutes=1),
        id='system_metrics',
        name='System Metrics Monitoring',
        replace_existing=True
    )
    
    # Sales product fetching - 4 times per day at specific hours
    # STRICT LIMIT: 2 AM, 8 AM, 2 PM, 8 PM
    for hour in SALES_FETCH_SCHEDULE:
        scheduler.add_job(
            sales_product_fetching,
            trigger=CronTrigger(hour=hour, minute=0),
            id=f'sales_fetch_{hour}',
            name=f'Sales Product Fetch ({hour}:00)',
            replace_existing=True
        )
    
    # Cache data sync - every 5 minutes (lightweight)
    scheduler.add_job(
        sync_cache_data,
        trigger=IntervalTrigger(minutes=5),
        id='cache_data_sync',
        name='Cache Data Sync',
        replace_existing=True
    )
    
    # Cache cleanup - every 10 minutes
    scheduler.add_job(
        cleanup_expired_cache,
        trigger=IntervalTrigger(minutes=10),
        id='cache_cleanup',
        name='Cache Cleanup',
        replace_existing=True
    )
    
    # AI Content generation - runs during idle time every 30 minutes
    scheduler.add_job(
        generate_ai_content_idle,
        trigger=IntervalTrigger(minutes=30),
        id='ai_content_idle',
        name='AI Content Generation (Idle Time)',
        replace_existing=True
    )
    
    # Start the optimized background scheduler
    import asyncio
    asyncio.create_task(optimized_scheduler.start())
    asyncio.create_task(setup_optimized_tasks(database))
    
    scheduler.start()
    logger.info("Cron job scheduler started successfully with optimized idle-time processing")
    logger.info(f"Sales product fetching limited to 4 times per day: {SALES_FETCH_SCHEDULE}")


def stop_scheduler():
    """Stop the cron job scheduler"""
    scheduler.shutdown()
    logger.info("Cron job scheduler stopped")


def get_scheduler_status():
    """Get current scheduler status including optimized background tasks"""
    jobs = []
    for job in scheduler.get_jobs():
        jobs.append({
            "id": job.id,
            "name": job.name,
            "next_run_time": job.next_run_time.isoformat() if job.next_run_time else None,
            "trigger": str(job.trigger)
        })
    
    # Get optimized scheduler status (async, run separately)
    import asyncio
    try:
        optimized_status = asyncio.run(get_optimized_status())
    except:
        optimized_status = {"error": "Could not retrieve optimized scheduler status"}
    
    return {
        "running": scheduler.running,
        "jobs": jobs,
        "job_count": len(jobs),
        "sales_fetch_schedule": SALES_FETCH_SCHEDULE,
        "sales_fetch_limit": "4 times per day",
        "optimized_scheduler": optimized_status,
        "optimization_features": [
            "Idle-time task execution",
            "System load monitoring",
            "AI content generation during low load",
            "Sales fetching limited to 4x/day",
            "Cache maintenance in background",
            "Database optimization when idle"
        ]
    }
