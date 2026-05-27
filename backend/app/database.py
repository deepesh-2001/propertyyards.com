"""
Database setup and configuration for MongoDB
"""
from motor.motor_asyncio import AsyncIOMotorClient
from app.config import settings
import logging

logger = logging.getLogger(__name__)

# MongoDB client
client: AsyncIOMotorClient = None
database = None


async def init_database():
    """Initialize MongoDB connection"""
    global client, database
    try:
        client = AsyncIOMotorClient(settings.DATABASE_URL)
        database = client.get_database()
        # Test connection
        await client.admin.command('ping')
        logger.info("MongoDB connected successfully")
    except Exception as e:
        logger.error(f"MongoDB connection error: {e}")
        raise


async def close_database():
    """Close MongoDB connection"""
    global client
    if client:
        client.close()
        logger.info("MongoDB connection closed")


async def get_database():
    """Dependency to get database"""
    return database


# For backward compatibility with routers that still use get_db
def get_db():
    """Legacy dependency for backward compatibility - returns database"""
    return database

