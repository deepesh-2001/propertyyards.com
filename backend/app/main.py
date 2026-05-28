"""
FastAPI application entry point
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
from datetime import datetime
import logging
import sys

from app.config import settings
from app.routers import auth, users, properties, inquiries, admin, crm, referral, access, loan_calculator, contact, notifications, chatbot, brokers, reports, monitoring, recruitment, payments, self_healing, salary, commission, prediction, feedback, credit_card, reimbursement, claims, tax, onboarding, scraper, property_onboarding, feature_flags, whiteboard, analytics, cache_management, properties_cached, realtime, admin_portal, social_media, telegram, news, operations, architecture, ai_costs, ai_seo, comparison, cashback, insurance
from app import health, cron
from app.access import AccessControl
from app.security import setup_security_middleware
from app.https_middleware import enforce_https
from app.unified_startup import initialize_application, shutdown_application, get_application_health

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('app.log')
    ]
)
logger = logging.getLogger(__name__)


# Lifespan context manager
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle app startup and shutdown with unified service manager"""
    # Startup
    logger.info("Starting Housing Platform API...")

    try:
        # Initialize all services through unified bootstrapper
        await initialize_application()

        # Initialize access control roles
        try:
            from app.database import database
            access_control = AccessControl(database)
            await access_control.initialize_default_roles()
            logger.info("Access control roles initialized")
        except Exception as e:
            logger.error(f"Access control initialization error: {e}")

        # Start cron job scheduler
        cron.start_scheduler()

        logger.info("Housing Platform API started successfully")

    except Exception as e:
        logger.error(f"System initialization error: {e}")
        # Continue to allow app to start even if some components fail

    yield

    # Shutdown
    logger.info("Shutting down Housing Platform API...")
    cron.stop_scheduler()

    try:
        await shutdown_application()
    except Exception as e:
        logger.error(f"System shutdown error: {e}")

    logger.info("Housing Platform API shutdown complete")


# Create FastAPI app with performance optimizations
app = FastAPI(
    title=settings.API_TITLE,
    description=settings.API_DESCRIPTION,
    version=settings.API_VERSION,
    lifespan=lifespan,
    # Performance optimizations
    openapi_url="/openapi.json" if settings.DEBUG else None,
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
)

# Add response compression middleware first
from fastapi.middleware.gzip import GZipMiddleware
app.add_middleware(
    GZipMiddleware,
    minimum_size=1000,  # Only compress responses > 1KB
    compresslevel=6     # Balance between speed and compression
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=settings.CORS_CREDENTIALS,
    allow_methods=settings.CORS_METHODS,
    allow_headers=settings.CORS_HEADERS,
)

# Performance monitoring middleware
@app.middleware("http")
async def performance_monitor(request, call_next):
    """Monitor and optimize request performance"""
    import time

    start = time.perf_counter()

    # Check for duplicate requests
    from app.cache_pipeline import request_deduplicator

    request_key = f"{request.method}:{request.url.path}:{hash(str(request.query_params))}"

    response = await call_next(request)

    # Add performance headers
    duration = time.perf_counter() - start
    response.headers["X-Response-Time"] = f"{duration:.3f}s"

    # Log slow requests
    if duration > 1.0:
        logger.warning(f"Slow request: {request.method} {request.url.path} took {duration:.3f}s")

    return response


# Include routers
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(properties.router)
app.include_router(properties_cached.router)
app.include_router(inquiries.router)
app.include_router(admin.router)
app.include_router(crm.router)
app.include_router(referral.router)
app.include_router(access.router)
app.include_router(loan_calculator.router)
app.include_router(contact.router)
app.include_router(notifications.router)
app.include_router(chatbot.router)
app.include_router(brokers.router)
app.include_router(reports.router)
app.include_router(monitoring.router)
app.include_router(recruitment.router)
app.include_router(self_healing.router)
app.include_router(payments.router)
app.include_router(salary.router)
app.include_router(commission.router)
app.include_router(prediction.router)
app.include_router(feedback.router)
app.include_router(credit_card.router)
app.include_router(reimbursement.router)
app.include_router(claims.router)
app.include_router(tax.router)
app.include_router(onboarding.router)
app.include_router(scraper.router)
app.include_router(property_onboarding.router)
app.include_router(feature_flags.router)
app.include_router(whiteboard.router)
app.include_router(analytics.router)
app.include_router(cache_management.router)
app.include_router(realtime.router)
app.include_router(admin_portal.router)
app.include_router(social_media.router)
app.include_router(telegram.router)
app.include_router(news.router)
app.include_router(operations.router)
app.include_router(architecture.router)
app.include_router(ai_costs.router)
app.include_router(insurance.router)
app.include_router(ai_seo.router)
app.include_router(comparison.router)
app.include_router(cashback.router)
app.include_router(health.router)

# Setup security middleware
setup_security_middleware(app)

# Setup HTTPS enforcement (redirect HTTP to HTTPS)
enforce_https(app)


# Root endpoint
@app.get("/")
async def root():
    """API root endpoint"""
    return {
        "message": "Welcome to Housing Platform API",
        "version": settings.API_VERSION,
        "docs": "/docs",
        "swagger": "/docs",
        "redoc": "/redoc"
    }


# Health check
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    health = await get_application_health()
    return health


@app.get("/status")
async def app_status():
    """Detailed application status"""
    from app.unified_startup import bootstrapper
    status = bootstrapper.get_status()
    return status


@app.get("/services")
async def services_status():
    """Get all service statuses"""
    from app.service_manager import service_manager
    return service_manager.get_all_status()


# Server Monitoring Endpoints
@app.get("/monitoring/performance")
async def get_performance_stats():
    """Get API performance statistics"""
    from app.server_monitoring import performance_monitor
    return performance_monitor.get_stats()


@app.get("/monitoring/system")
async def get_system_stats():
    """Get system resource statistics"""
    from app.server_monitoring import system_monitor
    return system_monitor.get_system_stats()


@app.get("/monitoring/cache")
async def get_cache_stats():
    """Get cache performance statistics"""
    from app.server_monitoring import cache_monitor
    return cache_monitor.get_stats()


@app.get("/monitoring/database")
async def get_database_stats():
    """Get database performance statistics"""
    from app.server_monitoring import database_monitor
    return database_monitor.get_stats()


@app.get("/monitoring/health")
async def get_full_health():
    """Get comprehensive health check"""
    from app.server_monitoring import HealthChecker
    return await HealthChecker.full_health_check()


@app.get("/monitoring/alerts")
async def get_system_alerts():
    """Get current system alerts"""
    from app.server_monitoring import system_monitor
    return {"alerts": await system_monitor.check_alerts()}


# Auto-Scaling Endpoints
@app.get("/scaling/status")
async def get_scaling_status():
    """Get auto-scaling status and configuration"""
    from app.auto_scaler import auto_scaler
    return auto_scaler.get_status()


@app.post("/scaling/manual")
async def manual_scale(target_instances: int):
    """Manually scale instances"""
    from app.auto_scaler import auto_scaler
    success = auto_scaler.manual_scale(target_instances)
    return {"success": success, "target": target_instances}


# Auto-Healing Endpoints
@app.get("/healing/status")
async def get_healing_status():
    """Get auto-healing service status"""
    from app.auto_healing import auto_healing
    return auto_healing.get_health_summary()


@app.post("/healing/enable")
async def enable_healing():
    """Enable auto-healing service"""
    from app.auto_healing import auto_healing
    auto_healing.enabled = True
    return {"enabled": True}


@app.post("/healing/disable")
async def disable_healing():
    """Disable auto-healing service"""
    from app.auto_healing import auto_healing
    auto_healing.enabled = False
    return {"enabled": False}


# AI Services Endpoints
@app.post("/ai/generate-image")
async def generate_ai_image(
    image_type: str = "property",
    prompt_data: dict = None
):
    """Generate AI image for properties/marketing"""
    from app.ai_image_service import ai_image_generator

    if image_type == "property":
        result = await ai_image_generator.generate_property_visualization(
            prompt_data or {},
            style=prompt_data.get("style", "modern")
        )
    elif image_type == "social":
        result = await ai_image_generator.generate_social_media_image(
            prompt_data.get("content_type", "new_property"),
            prompt_data.get("text", ""),
            prompt_data.get("theme", "professional")
        )
    else:
        result = None

    return {"generated": result is not None, "image_id": result.id if result else None}


@app.post("/ai/generate-article")
async def generate_ai_article(
    topic: str,
    category: str = "PROPERTY_NEWS",
    keywords: list = None
):
    """Generate AI article"""
    from app.news_service import ai_article_generator, ArticleCategory

    category_enum = ArticleCategory(category) if category else ArticleCategory.PROPERTY_NEWS

    article = await ai_article_generator.generate_article(
        topic=topic,
        category=category_enum,
        keywords=keywords or ["real estate", "property"],
        tone="professional",
        word_count=800
    )

    return {
        "generated": article is not None,
        "title": article.title if article else None,
        "article_id": article.id if article else None
    }


@app.post("/social/schedule")
async def schedule_social_post(
    platform: str,
    content: str,
    scheduled_time: str = None
):
    """Schedule social media post"""
    from app.social_media_manager import social_media_manager, Platform, SocialPost

    platform_enum = Platform(platform.lower())

    post = SocialPost(
        id=f"post_{datetime.utcnow().timestamp()}",
        platform=platform_enum,
        content=content,
        scheduled_time=datetime.fromisoformat(scheduled_time) if scheduled_time else None,
        status="scheduled" if scheduled_time else "draft"
    )

    # Queue for posting
    await social_media_manager.post_queue.put(post)

    return {
        "scheduled": True,
        "platform": platform,
        "post_id": post.id,
        "status": post.status
    }


# Sales Report Enhancement Endpoints
@app.get("/reports/sales/enhanced")
async def get_enhanced_sales_report(
    start_date: str = None,
    end_date: str = None,
    include_trends: bool = True,
    include_broker_performance: bool = True
):
    """Get enhanced sales report with trends and analytics"""
    from app.report_generator import ReportGenerator, ReportConfig, ReportType

    config = ReportConfig(
        report_type=ReportType.SALES_RECORDS,
        date_range_days=30,
        filters={
            "start_date": start_date,
            "end_date": end_date,
            "include_trends": include_trends,
            "include_broker_performance": include_broker_performance
        }
    )

    # Generate report
    generator = ReportGenerator()
    report_data = await generator._gather_sales_data(config, None)  # db passed separately

    return {
        "report_type": "enhanced_sales",
        "generated_at": datetime.utcnow().isoformat(),
        "data": report_data
    }


# Future Projection Endpoints
@app.post("/projections/forecast")
async def create_future_forecast(
    location: str,
    property_type: str,
    years: int = 5,
    use_ai: bool = True
):
    """Create future market forecast with AI"""
    from app.predictive_analytics import predictive_analytics

    forecast = await predictive_analytics.predict_future_growth(
        location=location,
        property_type=property_type,
        years=years,
        use_ai=use_ai
    )

    return {
        "forecast": forecast,
        "location": location,
        "years": years,
        "ai_enhanced": use_ai
    }


# Logging and Audit Endpoints
@app.get("/logs/recent")
async def get_recent_logs(
    level: str = None,
    service: str = None,
    limit: int = 100
):
    """Get recent application logs"""
    from app.server_monitoring import structured_logger

    # Return logging configuration info
    return {
        "logging_enabled": True,
        "structured_format": "json",
        "services": [
            "api", "database", "cache", "ai_image", "social_media",
            "news", "auto_healing", "auto_scaler"
        ],
        "levels": ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        "filters": {
            "level": level,
            "service": service,
            "limit": limit
        }
    }


# API Info
@app.get("/api/info")
async def api_info():
    """Get API information"""
    return {
        "title": settings.API_TITLE,
        "version": settings.API_VERSION,
        "description": settings.API_DESCRIPTION,
        "endpoints": {
            "auth": "/api/auth",
            "users": "/api/users",
            "properties": "/api/properties",
            "inquiries": "/api/inquiries",
            "admin": "/api/admin"
        },
        "documentation": {
            "swagger": "/docs",
            "redoc": "/redoc"
        }
    }


# Error handlers
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler"""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=settings.DEBUG,
        log_level="info"
    )

