"""
FastAPI application entry point
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import logging
import sys

from app.config import settings
from app.database import init_database, close_database
from app.cache import init_cache, close_cache
from app.routers import auth, users, properties, inquiries, admin, crm, referral, access, loan_calculator, contact, notifications, chatbot, brokers, reports, monitoring, recruitment, payments, self_healing, salary, commission, prediction, feedback, credit_card, reimbursement, claims, tax, onboarding, scraper, property_onboarding, feature_flags, whiteboard, analytics, cache_management, properties_cached
from app import health, cron
from app.access import AccessControl
from app.security import setup_security_middleware
from app.startup import initialize_system, shutdown_system

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
    """Handle app startup and shutdown with full system initialization"""
    # Startup
    logger.info("Starting Housing Platform API...")

    try:
        # Initialize full system (database, cache, background tasks, etc.)
        await initialize_system()

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
        await shutdown_system()
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
app.include_router(health.router)

# Setup security middleware
setup_security_middleware(app)


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
    return {"status": "healthy", "environment": settings.ENVIRONMENT}


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

