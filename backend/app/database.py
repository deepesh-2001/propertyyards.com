"""
Database setup and configuration for MongoDB
Optimized for high throughput (10,000 QPM)
"""
from motor.motor_asyncio import AsyncIOMotorClient
from app.config import settings
import logging

logger = logging.getLogger(__name__)

# MongoDB client
client: AsyncIOMotorClient = None
database = None
read_replica_client: AsyncIOMotorClient = None
read_replica_database = None


async def init_database():
    """Initialize MongoDB connection with connection pooling for high throughput"""
    global client, database, read_replica_client, read_replica_database
    try:
        # Primary database connection with connection pooling
        client = AsyncIOMotorClient(
            settings.DATABASE_URL,
            maxPoolSize=settings.MAX_DB_CONNECTIONS,
            minPoolSize=settings.MIN_DB_CONNECTIONS,
            maxIdleTimeMS=settings.CONNECTION_POOL_RECYCLE * 1000,
            connectTimeoutMS=settings.CONNECTION_POOL_TIMEOUT * 1000,
            serverSelectionTimeoutMS=5000,
            retryWrites=True,
            w="majority",
            retryReads=True,
            socketTimeoutMS=30000,
            heartbeatFrequencyMS=10000
        )
        database = client.get_database()

        # Test connection
        await client.admin.command('ping')
        logger.info(f"MongoDB connected successfully with connection pool (max: {settings.MAX_DB_CONNECTIONS}, min: {settings.MIN_DB_CONNECTIONS})")

        # Initialize read replica if configured
        if hasattr(settings, 'READ_REPLICA_URL') and settings.READ_REPLICA_URL:
            read_replica_client = AsyncIOMotorClient(
                settings.READ_REPLICA_URL,
                maxPoolSize=settings.MAX_DB_CONNECTIONS // 2,
                minPoolSize=settings.MIN_DB_CONNECTIONS // 2,
                readPreference="secondaryPreferred",
                retryReads=True,
                socketTimeoutMS=30000,
                heartbeatFrequencyMS=10000
            )
            read_replica_database = read_replica_client.get_database()
            logger.info("MongoDB read replica connected successfully")

        # Create indexes for optimization
        await create_indexes()

    except Exception as e:
        logger.error(f"MongoDB connection error: {e}")
        raise


async def create_indexes():
    """Create database indexes for query optimization"""
    try:
        # Users collection indexes
        await database.users.create_index([("email", 1)], unique=True)
        await database.users.create_index([("first_name", 1), ("last_name", 1)])
        await database.users.create_index([("role", 1)])
        await database.users.create_index([("created_at", -1)])
        
        # Properties collection indexes
        await database.properties.create_index([("user_id", 1)])
        await database.properties.create_index([("city", 1), ("state", 1)])
        await database.properties.create_index([("price", 1)])
        await database.properties.create_index([("property_type", 1)])
        await database.properties.create_index([("status", 1)])
        await database.properties.create_index([("created_at", -1)])
        await database.properties.create_index([("location", "2dsphere")])
        
        # Inquiries collection indexes
        await database.inquiries.create_index([("user_id", 1)])
        await database.inquiries.create_index([("property_id", 1)])
        await database.inquiries.create_index([("created_at", -1)])
        
        # Leave requests collection indexes
        await database.leave_requests.create_index([("user_id", 1)])
        await database.leave_requests.create_index([("status", 1)])
        await database.leave_requests.create_index([("start_date", 1), ("end_date", 1)])
        await database.leave_requests.create_index([("leave_type", 1)])
        
        # Leave balances collection indexes
        await database.leave_balances.create_index([("user_id", 1), ("leave_type", 1)], unique=True)
        
        # Attendance records collection indexes
        await database.attendance_records.create_index([("user_id", 1)])
        await database.attendance_records.create_index([("date", -1)])
        await database.attendance_records.create_index([("status", 1)])
        await database.attendance_records.create_index([("user_id", 1), ("date", -1)])
        
        # Commission collection indexes
        await database.commissions.create_index([("recipient_id", 1)])
        await database.commissions.create_index([("status", 1)])
        await database.commissions.create_index([("created_at", -1)])
        
        # Credit cards collection indexes
        await database.credit_cards.create_index([("user_id", 1)])
        await database.credit_cards.create_index([("card_number_last_4", 1)])
        
        # Reward transactions collection indexes
        await database.reward_transactions.create_index([("credit_card_id", 1)])
        await database.reward_transactions.create_index([("transaction_date", -1)])
        
        # Loan applications collection indexes
        await database.loan_applications.create_index([("user_id", 1)])
        await database.loan_applications.create_index([("status", 1)])
        await database.loan_applications.create_index([("loan_type", 1)])
        
        # Job postings collection indexes
        await database.job_postings.create_index([("status", 1)])
        await database.job_postings.create_index([("department", 1)])
        await database.job_postings.create_index([("created_at", -1)])

        # Employee onboarding collection indexes
        await database.employee_onboardings.create_index([("employee_id", 1)])
        await database.employee_onboardings.create_index([("status", 1)])
        await database.employee_onboardings.create_index([("department", 1)])
        await database.employee_onboardings.create_index([("created_at", -1)])

        # Employee offboarding collection indexes
        await database.employee_offboardings.create_index([("employee_id", 1)])
        await database.employee_offboardings.create_index([("status", 1)])
        await database.employee_offboardings.create_index([("department", 1)])
        await database.employee_offboardings.create_index([("created_at", -1)])

        # EPFO records collection indexes
        await database.epfo_records.create_index([("employee_id", 1)], unique=True)
        await database.epfo_records.create_index([("uan_number", 1)])
        await database.epfo_records.create_index([("status", 1)])

        # ESI records collection indexes
        await database.esi_records.create_index([("employee_id", 1)], unique=True)
        await database.esi_records.create_index([("esi_number", 1)])
        await database.esi_records.create_index([("status", 1)])

        # Property onboarding collection indexes
        await database.property_onboardings.create_index([("submitted_by", 1)])
        await database.property_onboardings.create_index([("source", 1)])
        await database.property_onboardings.create_index([("status", 1)])
        await database.property_onboardings.create_index([("property_data.city", 1)])
        await database.property_onboardings.create_index([("created_at", -1)])

        # Feature flags collection indexes
        await database.feature_flags.create_index([("key", 1)], unique=True)
        await database.feature_flags.create_index([("is_enabled", 1)])

        # Whiteboards collection indexes
        await database.whiteboards.create_index([("owner_id", 1)])
        await database.whiteboards.create_index([("is_public", 1)])
        await database.whiteboards.create_index([("tags", 1)])
        await database.whiteboards.create_index([("created_at", -1)])
        await database.whiteboards.create_index([("updated_at", -1)])

        # Whiteboard items collection indexes
        await database.whiteboard_items.create_index([("whiteboard_id", 1)])
        await database.whiteboard_items.create_index([("item_type", 1)])
        await database.whiteboard_items.create_index([("z_index", 1)])

        # Whiteboard shares collection indexes
        await database.whiteboard_shares.create_index([("whiteboard_id", 1)])
        await database.whiteboard_shares.create_index([("user_id", 1)])
        await database.whiteboard_shares.create_index([("whiteboard_id", 1), ("user_id", 1)], unique=True)

        # Persistent cache collection indexes
        await database.cache.create_index([("key", 1)], unique=True)
        await database.cache.create_index([("expires_at", 1)])
        await database.cache.create_index([("access_count", -1)])

        # Time-series collection indexes
        await database.timeseries.create_index([("metric_name", 1), ("timestamp", -1)])
        await database.timeseries.create_index([("metric_name", 1), ("granularity", 1), ("timestamp", -1)])
        await database.timeseries.create_index([("tags", 1)])
        await database.timeseries.create_index([("timestamp", 1)])

        # Analytics history collection indexes
        await database.analytics_history.create_index([("type", 1), ("date", -1)])
        await database.analytics_history.create_index([("date", -1)])

        # Sales records collection indexes
        await database.sales_records.create_index([("property_id", 1)])
        await database.sales_records.create_index([("seller_id", 1)])
        await database.sales_records.create_index([("buyer_id", 1)])
        await database.sales_records.create_index([("broker_id", 1)])
        await database.sales_records.create_index([("sale_date", -1)])
        await database.sales_records.create_index([("sale_type", 1)])
        await database.sales_records.create_index([("status", 1)])
        await database.sales_records.create_index([("sale_date", -1), ("status", 1)])

        # Projections collection indexes
        await database.projections.create_index([("projection_type", 1)])
        await database.projections.create_index([("location_filter", 1)])
        await database.projections.create_index([("property_type_filter", 1)])
        await database.projections.create_index([("created_by", 1)])
        await database.projections.create_index([("created_at", -1)])
        await database.projections.create_index([("period_start", 1), ("period_end", 1)])
        await database.projections.create_index([("confidence_level", -1)])

        # Future growth collection indexes
        await database.future_growth.create_index([("location", 1)])
        await database.future_growth.create_index([("time_horizon_years", 1)])
        await database.future_growth.create_index([("growth_rate_projected", -1)])
        await database.future_growth.create_index([("ai_confidence_score", -1)])
        await database.future_growth.create_index([("created_at", -1)])
        await database.future_growth.create_index([("location", 1), ("time_horizon_years", 1)])

        # Future projects collection indexes
        await database.future_projects.create_index([("city", 1)])
        await database.future_projects.create_index([("state", 1)])
        await database.future_projects.create_index([("project_type", 1)])
        await database.future_projects.create_index([("construction_status", 1)])
        await database.future_projects.create_index([("developer_name", 1)])
        await database.future_projects.create_index([("launch_date", 1)])
        await database.future_projects.create_index([("completion_date", 1)])
        await database.future_projects.create_index([("is_verified", 1)])
        await database.future_projects.create_index([("is_featured", 1)])
        await database.future_projects.create_index([("city", 1), ("construction_status", 1)])
        await database.future_projects.create_index([("price_range_min", 1), ("price_range_max", 1)])

        # Investment opportunities collection indexes
        await database.investment_opportunities.create_index([("investment_type", 1)])
        await database.investment_opportunities.create_index([("location", 1)])
        await database.investment_opportunities.create_index([("city", 1)])
        await database.investment_opportunities.create_index([("state", 1)])
        await database.investment_opportunities.create_index([("risk_level", 1)])
        await database.investment_opportunities.create_index([("status", 1)])
        await database.investment_opportunities.create_index([("created_by", 1)])
        await database.investment_opportunities.create_index([("expected_roi_annual", -1)])
        await database.investment_opportunities.create_index([("minimum_investment", 1)])
        await database.investment_opportunities.create_index([("closing_date", 1)])
        await database.investment_opportunities.create_index([("status", 1), ("risk_level", 1)])
        await database.investment_opportunities.create_index([("location", 1), ("investment_type", 1)])

        # Stakeholder reports collection indexes
        await database.stakeholder_reports.create_index([("report_id", 1)], unique=True)
        await database.stakeholder_reports.create_index([("generated_by", 1)])
        await database.stakeholder_reports.create_index([("report_type", 1)])
        await database.stakeholder_reports.create_index([("created_at", -1)])

        # Insurance quotes collection indexes
        await database.insurance_quotes.create_index([("id", 1)], unique=True)
        await database.insurance_quotes.create_index([("sale_id", 1)])
        await database.insurance_quotes.create_index([("customer_id", 1)])
        await database.insurance_quotes.create_index([("property_id", 1)])
        await database.insurance_quotes.create_index([("insurance_type", 1)])
        await database.insurance_quotes.create_index([("status", 1)])
        await database.insurance_quotes.create_index([("created_at", -1)])
        await database.insurance_quotes.create_index([("sale_id", 1), ("status", 1)])
        await database.insurance_quotes.create_index([("customer_id", 1), ("status", 1)])

        # Insurance plans collection indexes (for cached scraped data)
        await database.insurance_plans.create_index([("id", 1)], unique=True)
        await database.insurance_plans.create_index([("provider", 1)])
        await database.insurance_plans.create_index([("insurance_type", 1)])
        await database.insurance_plans.create_index([("coverage_amount", -1)])
        await database.insurance_plans.create_index([("premium_yearly", 1)])
        await database.insurance_plans.create_index([("rating", -1)])
        await database.insurance_plans.create_index([("is_active", 1)])
        await database.insurance_plans.create_index([("insurance_type", 1), ("provider", 1)])
        await database.insurance_plans.create_index([("insurance_type", 1), ("rating", -1)])

        logger.info("Database indexes created successfully")
        
    except Exception as e:
        logger.error(f"Index creation error: {e}")
        # Don't raise error, allow app to continue even if indexes fail


async def close_database():
    """Close MongoDB connections"""
    global client, read_replica_client
    if client:
        client.close()
        logger.info("MongoDB connection closed")
    if read_replica_client:
        read_replica_client.close()
        logger.info("MongoDB read replica connection closed")


async def get_database():
    """Dependency to get primary database"""
    return database


async def get_read_replica_database():
    """Dependency to get read replica database for read operations"""
    if read_replica_database:
        return read_replica_database
    return database  # Fallback to primary if read replica not configured


# For backward compatibility with routers that still use get_db
def get_db():
    """Legacy dependency for backward compatibility - returns database"""
    return database

