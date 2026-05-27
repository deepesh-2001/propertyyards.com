"""
Database initialization script
"""
from sqlalchemy import create_engine
from app.database import Base
from app.models import User, Property, Inquiry, Wishlist, AuditLog
from app.config import settings
from app.auth import hash_password
import uuid
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def init_db():
    """Initialize database with tables and sample data"""
    # Create engine
    engine = create_engine(settings.DATABASE_URL)

    # Create all tables
    logger.info("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    logger.info("✓ Database tables created")

    # Create session
    from sqlalchemy.orm import sessionmaker
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()

    try:
        # Check if admin user exists
        admin = db.query(User).filter(User.role == "admin").first()
        if not admin:
            # Create admin user
            logger.info("Creating admin user...")
            admin_user = User(
                id=uuid.uuid4(),
                email="admin@housing.com",
                first_name="Admin",
                last_name="User",
                phone_number="+1-800-ADMIN-1",
                password_hash=hash_password("admin@housing123"),
                role="admin",
                is_active=True
            )
            db.add(admin_user)
            logger.info(f"✓ Admin user created: admin@housing.com")

        # Check if test users exist
        test_seller = db.query(User).filter(User.email == "seller@housing.com").first()
        if not test_seller:
            logger.info("Creating test seller user...")
            seller_user = User(
                id=uuid.uuid4(),
                email="seller@housing.com",
                first_name="John",
                last_name="Seller",
                phone_number="+1-555-0101",
                password_hash=hash_password("seller@housing123"),
                role="seller",
                is_active=True
            )
            db.add(seller_user)
            logger.info(f"✓ Test seller user created: seller@housing.com")

        test_buyer = db.query(User).filter(User.email == "buyer@housing.com").first()
        if not test_buyer:
            logger.info("Creating test buyer user...")
            buyer_user = User(
                id=uuid.uuid4(),
                email="buyer@housing.com",
                first_name="Jane",
                last_name="Buyer",
                phone_number="+1-555-0102",
                password_hash=hash_password("buyer@housing123"),
                role="buyer",
                is_active=True
            )
            db.add(buyer_user)
            logger.info(f"✓ Test buyer user created: buyer@housing.com")

        db.commit()
        logger.info("✓ Database initialization completed successfully!")

    except Exception as e:
        logger.error(f"Error during database initialization: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    init_db()

