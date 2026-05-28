"""
Unified Startup Script
Single entry point for all services with proper monolithic architecture
"""
import asyncio
import logging
from datetime import datetime
from typing import Dict

from app.config import settings
from app.database import init_database, close_database, get_db
from app.cache import init_cache, close_cache
from app.service_manager import (
    service_manager, cache_manager, connection_pool,
    initialize_services, shutdown_services
)

logger = logging.getLogger(__name__)


class ApplicationBootstrapper:
    """
    Main application bootstrapper
    Handles complete initialization and shutdown
    """

    def __init__(self):
        self.started_at = None
        self.database = None

    async def bootstrap(self):
        """Bootstrap the entire application"""
        logger.info("=" * 50)
        logger.info("PropertyYards Application Starting...")
        logger.info("=" * 50)

        self.started_at = datetime.utcnow()

        try:
            # Step 1: Initialize database
            logger.info("[1/5] Initializing database...")
            await init_database()
            self.database = get_db()
            logger.info("Database initialized")

            # Step 2: Initialize cache
            logger.info("[2/5] Initializing cache...")
            await init_cache()
            logger.info("Cache initialized")

            # Step 3: Initialize all services through service manager
            logger.info("[3/5] Initializing services...")
            await initialize_services(self.database, settings)

            # Get status
            status = service_manager.get_all_status()
            ready_services = sum(1 for s in status.values() if s["status"] == "ready")
            logger.info(f"Services ready: {ready_services}/{len(status)}")

            # Step 4: Warm caches
            logger.info("[4/5] Warming caches...")
            await self._warm_caches()

            # Step 5: Final setup
            logger.info("[5/5] Finalizing startup...")
            await self._finalize_startup()

            duration = (datetime.utcnow() - self.started_at).total_seconds()
            logger.info("=" * 50)
            logger.info(f"Application started successfully in {duration:.2f}s")
            logger.info("=" * 50)

            return True

        except Exception as e:
            logger.error(f"Bootstrap failed: {e}")
            await self.emergency_shutdown()
            raise

    async def _warm_caches(self):
        """Warm critical caches"""
        try:
            from app.analytics import analytics_manager
            from app.cache_pipeline import cache_warmer
            from app.persistent_cache import persistent_cache

            # Warm analytics caches
            cache_entries = {
                "analytics:dashboard": lambda: analytics_manager.get_dashboard_analytics(self.database),
                "analytics:property": lambda: analytics_manager.get_property_analytics(self.database),
                "analytics:user": lambda: analytics_manager.get_user_analytics(self.database),
            }

            await persistent_cache.warm_cache(
                cache_entries,
                database=self.database,
                ttl=3600
            )

            # Warm property cache
            await cache_warmer.warm_property_cache(self.database, limit=50)

            logger.info("Caches warmed successfully")

        except Exception as e:
            logger.warning(f"Cache warming warning: {e}")

    async def _finalize_startup(self):
        """Final startup tasks"""
        # Create indexes if needed
        await self._ensure_indexes()

        # Log startup completion
        health = await service_manager.health_check()
        logger.info(f"Health check: {health['overall']}")

    async def _ensure_indexes(self):
        """Ensure all database indexes exist"""
        try:
            # The database.py create_indexes should handle this
            # But we can add additional indexes here if needed
            pass
        except Exception as e:
            logger.warning(f"Index check warning: {e}")

    async def graceful_shutdown(self):
        """Graceful shutdown sequence"""
        logger.info("=" * 50)
        logger.info("Initiating graceful shutdown...")
        logger.info("=" * 50)

        shutdown_start = datetime.utcnow()

        try:
            # Step 1: Stop accepting new requests
            logger.info("[1/4] Stopping service manager...")
            await shutdown_services()

            # Step 2: Close connection pools
            logger.info("[2/4] Closing connection pools...")
            await connection_pool.close_all()

            # Step 3: Close cache
            logger.info("[3/4] Closing cache...")
            await close_cache()

            # Step 4: Close database
            logger.info("[4/4] Closing database...")
            await close_database()

            duration = (datetime.utcnow() - shutdown_start).total_seconds()
            total_uptime = (datetime.utcnow() - self.started_at).total_seconds() if self.started_at else 0

            logger.info("=" * 50)
            logger.info(f"Shutdown completed in {duration:.2f}s")
            logger.info(f"Total uptime: {total_uptime:.0f}s")
            logger.info("=" * 50)

        except Exception as e:
            logger.error(f"Shutdown error: {e}")
            await self.emergency_shutdown()

    async def emergency_shutdown(self):
        """Emergency shutdown - force close everything"""
        logger.warning("EMERGENCY SHUTDOWN - Force closing all connections")

        try:
            await close_cache()
        except:
            pass

        try:
            await close_database()
        except:
            pass

    async def health_check(self) -> Dict:
        """Get full health status"""
        return await service_manager.health_check()

    def get_status(self) -> Dict:
        """Get application status"""
        return {
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "uptime_seconds": (datetime.utcnow() - self.started_at).total_seconds() if self.started_at else 0,
            "services": service_manager.get_all_status(),
            "cache_stats": cache_manager.get_stats()
        }


# Global bootstrapper instance
bootstrapper = ApplicationBootstrapper()


# Convenience functions for main.py
async def initialize_application():
    """Main initialization function called by main.py"""
    return await bootstrapper.bootstrap()


async def shutdown_application():
    """Main shutdown function called by main.py"""
    return await bootstrapper.graceful_shutdown()


async def get_application_health():
    """Get health status"""
    return await bootstrapper.health_check()


def get_application_status():
    """Get application status"""
    return bootstrapper.get_status()
