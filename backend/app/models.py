"""
SQLAlchemy ORM models
"""
from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime, ForeignKey, Table, Text, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime, timezone
import uuid
from app.database import Base


# Association table for amenities (many-to-many)
property_amenities = Table(
    'property_amenities',
    Base.metadata,
    Column('property_id', UUID(as_uuid=True), ForeignKey('properties.id')),
    Column('amenity', String)
)


class User(Base):
    """User model"""
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String, unique=True, index=True, nullable=False)
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    phone_number = Column(String, nullable=True)
    password_hash = Column(String, nullable=False)
    role = Column(String, default="buyer", nullable=False)  # admin, seller, buyer, agent
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Relationships
    properties = relationship("Property", back_populates="owner", cascade="all, delete-orphan")
    inquiries = relationship("Inquiry", back_populates="user", cascade="all, delete-orphan")
    wishlists = relationship("Wishlist", back_populates="user", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<User(id={self.id}, email={self.email}, role={self.role})>"


class Property(Base):
    """Property listing model"""
    __tablename__ = "properties"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=False, index=True)
    title = Column(String, nullable=False, index=True)
    description = Column(Text, nullable=True)
    location = Column(String, nullable=False, index=True)
    city = Column(String, nullable=False, index=True)
    state = Column(String, nullable=False)
    country = Column(String, nullable=False)
    price = Column(Float, nullable=False, index=True)
    property_type = Column(String, nullable=False, index=True)  # apartment, house, condo, etc.
    bedrooms = Column(Integer, nullable=False, index=True)
    bathrooms = Column(Integer, nullable=False)
    area = Column(Float, nullable=False)  # in sq ft
    amenities = Column(JSON, default=list)  # List of amenities
    images = Column(JSON, default=list)  # List of image URLs
    status = Column(String, default="listed", nullable=False, index=True)  # listed, sold, rented, pending
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Relationships
    owner = relationship("User", back_populates="properties")
    inquiries = relationship("Inquiry", back_populates="property", cascade="all, delete-orphan")
    wishlists = relationship("Wishlist", back_populates="property", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Property(id={self.id}, title={self.title}, price={self.price})>"


class Inquiry(Base):
    """Property inquiry model"""
    __tablename__ = "inquiries"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=False, index=True)
    property_id = Column(UUID(as_uuid=True), ForeignKey('properties.id'), nullable=False, index=True)
    message = Column(Text, nullable=False)
    status = Column(String, default="pending", nullable=False)  # pending, responded, closed
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Relationships
    user = relationship("User", back_populates="inquiries")
    property = relationship("Property", back_populates="inquiries")

    def __repr__(self):
        return f"<Inquiry(id={self.id}, user_id={self.user_id}, property_id={self.property_id})>"


class Wishlist(Base):
    """User wishlist model"""
    __tablename__ = "wishlists"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=False, index=True)
    property_id = Column(UUID(as_uuid=True), ForeignKey('properties.id'), nullable=False, index=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships
    user = relationship("User", back_populates="wishlists")
    property = relationship("Property", back_populates="wishlists")

    def __repr__(self):
        return f"<Wishlist(id={self.id}, user_id={self.user_id}, property_id={self.property_id})>"


class AuditLog(Base):
    """Audit log for admin actions"""
    __tablename__ = "audit_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=True)
    action = Column(String, nullable=False)
    resource_type = Column(String, nullable=False)
    resource_id = Column(String, nullable=True)
    details = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)

    def __repr__(self):
        return f"<AuditLog(id={self.id}, action={self.action}, resource_type={self.resource_type})>"

