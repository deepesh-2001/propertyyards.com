"""
Centralized Service Manager
Monolithic architecture with proper connection management and caching
"""
import asyncio
import logging
from typing import Dict, Any, Optional, List, Callable
from datetime import datetime
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


class ServiceStatus(Enum):
    """Service status enumeration"""
    INITIALIZING = "initializing"
    READY = "ready"
    ERROR = "error"
    STOPPED = "stopped"


@dataclass
class ServiceInfo:
    """Service information"""
    name: str
    status: ServiceStatus
    initialized_at: Optional[datetime] = None
    error_message: Optional[str] = None
    dependencies: List[str] = field(default_factory=list)
    health_check: Optional[Callable] = None


class ServiceManager:
    """
    Centralized service manager for monolithic architecture
    Handles initialization, dependencies, and health monitoring
    """

    def __init__(self):
        self.services: Dict[str, Any] = {}
        self.service_info: Dict[str, ServiceInfo] = {}
        self.initialized = False
        self._lock = asyncio.Lock()

    async def initialize_all_services(self, database, settings):
        """Initialize all services in correct order"""
        async with self._lock:
            if self.initialized:
                logger.info("Services already initialized")
                return

            logger.info("Starting service initialization...")

            # Define initialization order with dependencies
            init_sequence = [
                ("cache", self._init_cache, []),
                ("database_pool", self._init_database_pool, ["cache"]),
                ("realtime_analytics", self._init_realtime_analytics, ["cache"]),
                ("background_tasks", self._init_background_tasks, ["cache", "database_pool"]),
                ("predictive_analytics", self._init_predictive_analytics, ["database_pool"]),
                ("ai_image_service", self._init_ai_image_service, ["settings"]),
                ("social_media", self._init_social_media, ["settings"]),
                ("telegram_bot", self._init_telegram_bot, ["settings"]),
                ("news_service", self._init_news_service, ["settings", "ai_image_service"]),
                ("usage_tracker", self._init_usage_tracker, []),
                ("auto_scaler", self._init_auto_scaler, []),
                ("auto_healing", self._init_auto_healing, []),
                ("flight_comparison", self._init_flight_comparison, []),
                ("price_comparison", self._init_price_comparison, []),
                ("cashback", self._init_cashback, []),
                ("rewards", self._init_rewards, []),
                ("ticket_booking", self._init_ticket_booking, []),
                ("deployment", self._init_deployment, []),
                ("idle_processor", self._init_idle_processor, ["all"]),
            ]

            for service_name, init_func, dependencies in init_sequence:
                try:
                    await self._initialize_service(service_name, init_func, database, settings)
                except Exception as e:
                    logger.error(f"Failed to initialize {service_name}: {e}")
                    self.service_info[service_name] = ServiceInfo(
                        name=service_name,
                        status=ServiceStatus.ERROR,
                        error_message=str(e)
                    )

            self.initialized = True
            logger.info("Service initialization completed")

    async def _initialize_service(self, name: str, init_func: Callable, database, settings):
        """Initialize a single service"""
        logger.info(f"Initializing service: {name}")

        self.service_info[name] = ServiceInfo(
            name=name,
            status=ServiceStatus.INITIALIZING
        )

        try:
            service_instance = await init_func(database, settings)
            self.services[name] = service_instance

            self.service_info[name] = ServiceInfo(
                name=name,
                status=ServiceStatus.READY,
                initialized_at=datetime.utcnow()
            )

            logger.info(f"Service {name} initialized successfully")

        except Exception as e:
            self.service_info[name] = ServiceInfo(
                name=name,
                status=ServiceStatus.ERROR,
                error_message=str(e)
            )
            raise

    async def _init_cache(self, database, settings):
        """Initialize cache service"""
        from app.cache import init_cache, cache
        await init_cache()
        return cache

    async def _init_database_pool(self, database, settings):
        """Initialize database connection pool"""
        from app.db_optimized import query_optimizer, batch_operations, cursor_pagination
        return {
            "query_optimizer": query_optimizer,
            "batch_operations": batch_operations,
            "cursor_pagination": cursor_pagination,
            "database": database
        }

    async def _init_realtime_analytics(self, database, settings):
        """Initialize real-time analytics"""
        from app.realtime_analytics import realtime_collector, alert_manager, change_detector

        await realtime_collector.start()

        return {
            "collector": realtime_collector,
            "alert_manager": alert_manager,
            "change_detector": change_detector
        }

    async def _init_background_tasks(self, database, settings):
        """Initialize background task processor"""
        from app.background_tasks import background_processor, analytics_processor

        await background_processor.start()

        # Schedule periodic tasks
        await self._schedule_periodic_tasks(database)

        return {
            "processor": background_processor,
            "analytics_processor": analytics_processor
        }

    async def _schedule_periodic_tasks(self, database):
        """Schedule all periodic background tasks"""
        from app.background_tasks import background_processor, analytics_processor

        tasks = [
            ("precompute_analytics", analytics_processor.precompute_daily_analytics, 3600),
            ("update_timeseries", analytics_processor.update_timeseries_metrics, 900),
            ("warm_caches", analytics_processor.warm_frequently_used_caches, 1800),
            ("cleanup_data", analytics_processor.cleanup_old_data, 86400),
        ]

        for task_name, task_func, interval in tasks:
            await background_processor.schedule_periodic_task(
                task_name, task_func, interval, database
            )

    async def _init_predictive_analytics(self, database, settings):
        """Initialize predictive analytics"""
        from app.predictive_analytics import predictive_analytics
        return predictive_analytics

    async def _init_ai_image_service(self, database, settings):
        """Initialize AI image generation service"""
        from app.ai_image_service import ai_image_generator, image_cache_manager

        if hasattr(settings, 'OPENAI_API_KEY') and settings.OPENAI_API_KEY:
            await ai_image_generator.initialize(settings.OPENAI_API_KEY)

        return {
            "generator": ai_image_generator,
            "cache_manager": image_cache_manager
        }

    async def _init_social_media(self, database, settings):
        """Initialize social media manager"""
        from app.social_media_manager import social_media_manager

        # Initialize platforms if configured
        platforms = [
            ("facebook", settings.FACEBOOK_ACCESS_TOKEN if hasattr(settings, 'FACEBOOK_ACCESS_TOKEN') else None),
            ("instagram", settings.INSTAGRAM_ACCESS_TOKEN if hasattr(settings, 'INSTAGRAM_ACCESS_TOKEN') else None),
            ("twitter", settings.TWITTER_API_KEY if hasattr(settings, 'TWITTER_API_KEY') else None),
            ("linkedin", settings.LINKEDIN_ACCESS_TOKEN if hasattr(settings, 'LINKEDIN_ACCESS_TOKEN') else None),
        ]

        for platform_name, token in platforms:
            if token:
                from app.social_media_manager import Platform
                await social_media_manager.initialize_platform(
                    Platform(platform_name), token
                )

        await social_media_manager.start_scheduler()

        return social_media_manager

    async def _init_telegram_bot(self, database, settings):
        """Initialize Telegram bot"""
        from app.telegram_bot import telegram_bot

        if hasattr(settings, 'TELEGRAM_BOT_TOKEN') and settings.TELEGRAM_BOT_TOKEN:
            await telegram_bot.initialize(settings.TELEGRAM_BOT_TOKEN)

        return telegram_bot

    async def _init_news_service(self, database, settings):
        """Initialize news service"""
        from app.news_service import news_fetcher, ai_article_generator, article_manager

        await news_fetcher.initialize()

        if hasattr(settings, 'OPENAI_API_KEY') and settings.OPENAI_API_KEY:
            author_name = getattr(settings, 'NEWS_AUTHOR_NAME', 'PropertyYards Team')
            await ai_article_generator.initialize(settings.OPENAI_API_KEY, author_name)

        return {
            "fetcher": news_fetcher,
            "generator": ai_article_generator,
            "manager": article_manager
        }

    async def _init_cashback(self, database, settings):
        """Initialize cashback service"""
        from app.cashback_service import cashback_service
        await cashback_service.initialize()
        logger.info("Cashback Service initialized")
        return cashback_service

    async def _init_rewards(self, database, settings):
        """Initialize rewards service"""
        from app.rewards_service import rewards_service
        await rewards_service.initialize()
        logger.info("Rewards Service initialized")
        return rewards_service

    async def _init_ticket_booking(self, database, settings):
        """Initialize ticket booking service"""
        from app.ticket_booking_service import ticket_booking
        
        provider_keys = {
            "amadeus": getattr(settings, 'AMADEUS_API_KEY', None),
            "skyscanner": getattr(settings, 'SKYSCANNER_BOOKING_KEY', None),
            "cleartrip": getattr(settings, 'CLEARTRIP_API_KEY', None),
            "make_my_trip": getattr(settings, 'MMT_API_KEY', None)
        }
        
        await ticket_booking.initialize(provider_keys)
        logger.info("Ticket Booking Service initialized")
        return ticket_booking

    async def _init_deployment(self, database, settings):
        """Initialize deployment service"""
        from app.deployment_service import deployment_service
        await deployment_service.initialize()
        logger.info("Deployment Service initialized")
        return deployment_service

    async def _init_idle_processor(self, database, settings):
        """Initialize idle task processor"""
        from app.idle_task_processor import idle_task_processor, setup_idle_tasks

        await setup_idle_tasks(database)
        await idle_task_processor.start()

        return idle_task_processor

    async def _init_i18n(self, database, settings):
        """Initialize internationalization"""
        from app.i18n_manager import i18n

        default_locale = getattr(settings, 'DEFAULT_LOCALE', 'en')
        i18n.set_locale(default_locale)

        return i18n

    async def _init_currency(self, database, settings):
        """Initialize currency manager"""
        from app.currency_manager import currency_manager

        api_key = getattr(settings, 'EXCHANGE_RATE_API_KEY', None)
        if api_key:
            currency_manager.set_api_key(api_key)
            await currency_manager.update_exchange_rates()

        return currency_manager

    async def _init_timezone(self, database, settings):
        """Initialize timezone manager"""
        from app.timezone_manager import timezone_manager

        default_tz = getattr(settings, 'DEFAULT_TIMEZONE', 'UTC')
        timezone_manager.default_timezone = default_tz

        return timezone_manager

    async def _init_phone_validator(self, database, settings):
        """Initialize phone validator"""
        from app.phone_validator import phone_validator
        return phone_validator

    async def _init_gdpr(self, database, settings):
        """Initialize GDPR manager"""
        from app.gdpr_manager import gdpr_manager
        return gdpr_manager

    async def _init_region(self, database, settings):
        """Initialize region manager"""
        from app.region_manager import region_manager

        default_region = getattr(settings, 'DEFAULT_REGION', 'na')
        # Note: region is set per-user, this just initializes the manager

        return region_manager

    async def _init_flight_comparison(self, database, settings):
        """Initialize flight comparison service"""
        from app.flight_comparison_service import flight_comparison_service
        await flight_comparison_service.initialize()
        logger.info("Flight Comparison Service initialized")
        return flight_comparison_service

    async def _init_price_comparison(self, database, settings):
        """Initialize price comparison service"""
        from app.price_comparison_service import price_comparison_service
        await price_comparison_service.initialize()
        logger.info("Price Comparison Service initialized")
        return price_comparison_service

    async def _init_usage_tracker(self, database, settings):
        """Initialize usage tracker"""
        from app.usage_tracker import usage_tracker
        await usage_tracker.start()
        return usage_tracker

    async def _init_auto_scaler(self, database, settings):
        """Initialize auto-scaler"""
        from app.auto_scaler import auto_scaler
        await auto_scaler.start()
        return auto_scaler

    async def _init_auto_healing(self, database, settings):
        """Initialize auto-healing service"""
        from app.auto_healing import auto_healing
        await auto_healing.start()
        return auto_healing

    def get_service(self, name: str) -> Optional[Any]:
        """Get a service by name"""
        return self.services.get(name)

    def get_service_status(self, name: str) -> Optional[ServiceInfo]:
        """Get service status"""
        return self.service_info.get(name)

    def get_all_status(self) -> Dict[str, Dict[str, Any]]:
        """Get status of all services"""
        return {
            name: {
                "status": info.status.value,
                "initialized_at": info.initialized_at.isoformat() if info.initialized_at else None,
                "error": info.error_message
            }
            for name, info in self.service_info.items()
        }

    async def health_check(self) -> Dict[str, Any]:
        """Perform health check on all services"""
        health_status = {
            "overall": "healthy",
            "services": {},
            "timestamp": datetime.utcnow().isoformat()
        }

        failed_services = []

        for name, info in self.service_info.items():
            service_health = "healthy"

            if info.status == ServiceStatus.ERROR:
                service_health = "unhealthy"
                failed_services.append(name)
            elif info.status == ServiceStatus.INITIALIZING:
                service_health = "initializing"

            health_status["services"][name] = {
                "status": service_health,
                "initialized": info.status == ServiceStatus.READY
            }

        if failed_services:
            health_status["overall"] = "degraded"
            health_status["failed_services"] = failed_services

        return health_status

    async def shutdown_all(self):
        """Shutdown all services gracefully"""
        logger.info("Shutting down all services...")

        shutdown_sequence = [
            "idle_processor",
            "background_tasks",
            "realtime_analytics",
            "social_media",
            "telegram_bot",
            "ai_image_service",
            "news_service",
        ]

        for service_name in shutdown_sequence:
            try:
                await self._shutdown_service(service_name)
            except Exception as e:
                logger.error(f"Error shutting down {service_name}: {e}")

        self.initialized = False
        logger.info("All services shut down")

    async def _shutdown_service(self, name: str):
        """Shutdown a specific service"""
        service = self.services.get(name)
        if not service:
            return

        logger.info(f"Shutting down service: {name}")

        if name == "idle_processor":
            await service.stop()
        elif name == "background_tasks":
            await service["processor"].stop()
        elif name == "realtime_analytics":
            await service["collector"].stop()
        elif name == "social_media":
            await service.stop_scheduler()
        elif name == "news_service":
            await service["fetcher"].close()

        self.service_info[name].status = ServiceStatus.STOPPED


class UnifiedCacheManager:
    """
    Unified caching layer for all services
    Provides consistent caching interface
    """

    def __init__(self):
        self.cache_hits = 0
        self.cache_misses = 0
        self.local_cache = {}

    async def get(self, key: str, use_local: bool = True) -> Optional[Any]:
        """Get value from cache (tries local first, then Redis)"""
        if use_local and key in self.local_cache:
            self.cache_hits += 1
            return self.local_cache[key]

        from app.cache import get_from_cache
        value = await get_from_cache(key)

        if value is not None:
            self.cache_hits += 1
            # Store in local cache for faster access
            self.local_cache[key] = value
        else:
            self.cache_misses += 1

        return value

    async def set(self, key: str, value: Any, ttl: int = 3600, use_local: bool = True):
        """Set value in cache (both local and Redis)"""
        from app.cache import set_in_cache

        await set_in_cache(key, value, ttl)

        if use_local:
            self.local_cache[key] = value

    async def delete(self, key: str):
        """Delete from all cache layers"""
        from app.cache import delete_from_cache

        await delete_from_cache(key)
        self.local_cache.pop(key, None)

    async def invalidate_pattern(self, pattern: str):
        """Invalidate cache by pattern"""
        from app.cache import invalidate_cache_pattern
        await invalidate_cache_pattern(pattern)

        # Clear local cache keys matching pattern
        import fnmatch
        keys_to_delete = [k for k in self.local_cache.keys() if fnmatch.fnmatch(k, pattern)]
        for key in keys_to_delete:
            self.local_cache.pop(key, None)

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        total = self.cache_hits + self.cache_misses
        hit_rate = (self.cache_hits / total * 100) if total > 0 else 0

        return {
            "hits": self.cache_hits,
            "misses": self.cache_misses,
            "hit_rate": round(hit_rate, 2),
            "local_cache_size": len(self.local_cache)
        }


class ConnectionPoolManager:
    """
    Manages connection pools for database, Redis, and external APIs
    """

    def __init__(self):
        self.pools = {}
        self.max_connections = {
            "mongodb": 100,
            "redis": 50,
            "http": 20
        }

    async def get_mongodb_connection(self):
        """Get MongoDB connection from pool"""
        from app.database import get_db
        return get_db()

    async def get_redis_connection(self):
        """Get Redis connection from pool"""
        from app.cache import cache
        return cache

    async def get_http_session(self) -> Any:
        """Get HTTP session for API calls"""
        import aiohttp

        if "http" not in self.pools:
            connector = aiohttp.TCPConnector(
                limit=self.max_connections["http"],
                limit_per_host=10,
                enable_cleanup_closed=True,
                force_close=True,
            )
            timeout = aiohttp.ClientTimeout(total=30, connect=10)
            self.pools["http"] = aiohttp.ClientSession(
                connector=connector,
                timeout=timeout
            )

        return self.pools["http"]

    async def close_all(self):
        """Close all connection pools"""
        if "http" in self.pools:
            await self.pools["http"].close()
            del self.pools["http"]

        logger.info("All connection pools closed")


# Global instances
service_manager = ServiceManager()
cache_manager = UnifiedCacheManager()
connection_pool = ConnectionPoolManager()


async def initialize_services(database, settings):
    """Initialize all services - main entry point"""
    await service_manager.initialize_all_services(database, settings)


async def shutdown_services():
    """Shutdown all services - main exit point"""
    await service_manager.shutdown_all()
    await connection_pool.close_all()


def get_service(name: str) -> Optional[Any]:
    """Get service by name - convenience function"""
    return service_manager.get_service(name)
