"""
Cron job scheduler for periodic tasks
"""
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from datetime import datetime
import logging
from app.cache import cache, get_from_cache, set_in_cache
from app.database import database
from app.config import settings

logger = logging.getLogger(__name__)

# Create scheduler
scheduler = AsyncIOScheduler()


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


def start_scheduler():
    """Start the cron job scheduler"""
    # Cache health check - every 1 minute
    scheduler.add_job(
        check_cache_health,
        trigger=IntervalTrigger(minutes=1),
        id='cache_health_check',
        name='Cache Health Check',
        replace_existing=True
    )
    
    # Cache data sync - every 5 minutes
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
    
    # System metrics monitoring - every 1 minute
    scheduler.add_job(
        monitor_system_metrics,
        trigger=IntervalTrigger(minutes=1),
        id='system_metrics',
        name='System Metrics Monitoring',
        replace_existing=True
    )
    
    scheduler.start()
    logger.info("Cron job scheduler started successfully")


def stop_scheduler():
    """Stop the cron job scheduler"""
    scheduler.shutdown()
    logger.info("Cron job scheduler stopped")


def get_scheduler_status():
    """Get current scheduler status"""
    jobs = []
    for job in scheduler.get_jobs():
        jobs.append({
            "id": job.id,
            "name": job.name,
            "next_run_time": job.next_run_time.isoformat() if job.next_run_time else None,
            "trigger": str(job.trigger)
        })
    
    return {
        "running": scheduler.running,
        "jobs": jobs,
        "job_count": len(jobs)
    }
