"""
Database initialization script for MongoDB
"""
from app.database import init_database, close_database, database
from app.models import User, UserRole
from app.auth import hash_password
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def init_db():
    """Initialize MongoDB database with sample data"""
    try:
        # Initialize database connection
        await init_database()
        logger.info("✓ MongoDB connected successfully")

        # Check if admin user exists
        admin = await database.users.find_one({"role": "admin"})
        if not admin:
            logger.info("Creating admin user...")
            admin_user = User(
                email="admin@housing.com",
                first_name="Admin",
                last_name="User",
                phone_number="+1-800-ADMIN-1",
                password_hash=hash_password("admin@housing123"),
                role=UserRole.ADMIN,
                is_active=True
            )
            await database.users.insert_one(admin_user.dict())
            logger.info(f"✓ Admin user created: admin@housing.com")

        # Check if test seller exists
        seller = await database.users.find_one({"email": "seller@housing.com"})
        if not seller:
            logger.info("Creating test seller user...")
            seller_user = User(
                email="seller@housing.com",
                first_name="John",
                last_name="Seller",
                phone_number="+1-555-0101",
                password_hash=hash_password("seller@housing123"),
                role=UserRole.SELLER,
                is_active=True
            )
            await database.users.insert_one(seller_user.dict())
            logger.info(f"✓ Test seller user created: seller@housing.com")

        # Check if test buyer exists
        buyer = await database.users.find_one({"email": "buyer@housing.com"})
        if not buyer:
            logger.info("Creating test buyer user...")
            buyer_user = User(
                email="buyer@housing.com",
                first_name="Jane",
                last_name="Buyer",
                phone_number="+1-555-0102",
                password_hash=hash_password("buyer@housing123"),
                role=UserRole.BUYER,
                is_active=True
            )
            await database.users.insert_one(buyer_user.dict())
            logger.info(f"✓ Test buyer user created: buyer@housing.com")

        logger.info("✓ Database initialization completed successfully!")

    except Exception as e:
        logger.error(f"Error during database initialization: {e}")
        raise
    finally:
        await close_database()


if __name__ == "__main__":
    import asyncio
    asyncio.run(init_db())

