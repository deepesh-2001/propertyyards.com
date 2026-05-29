"""
Shared pytest fixtures for all test modules.
Provides: app client, JWT tokens, mock DB, mock cache, sample data.
"""
import sys
import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.testclient import TestClient
from datetime import datetime, timezone

sys.path.insert(0, 'C:/Users/deepe/PyCharmMiscProject/housing_platform/backend')

# ── JWT helpers (no running server needed) ─────────────────────────────────
from app.auth import (
    create_access_token,
    create_refresh_token,
    hash_password,
    verify_password,
    decode_token,
)

# ── Token factories ────────────────────────────────────────────────────────
BUYER_ID   = "buyer_000000000001"
SELLER_ID  = "seller_00000000001"
AGENT_ID   = "agent_000000000001"
ADMIN_ID   = "admin_000000000001"

@pytest.fixture(scope="session")
def buyer_token():
    return create_access_token(BUYER_ID, "buyer@test.com", "buyer")

@pytest.fixture(scope="session")
def seller_token():
    return create_access_token(SELLER_ID, "seller@test.com", "seller")

@pytest.fixture(scope="session")
def agent_token():
    return create_access_token(AGENT_ID, "agent@test.com", "agent")

@pytest.fixture(scope="session")
def admin_token():
    return create_access_token(ADMIN_ID, "admin@test.com", "admin")

@pytest.fixture(scope="session")
def buyer_headers(buyer_token):
    return {"Authorization": f"Bearer {buyer_token}"}

@pytest.fixture(scope="session")
def seller_headers(seller_token):
    return {"Authorization": f"Bearer {seller_token}"}

@pytest.fixture(scope="session")
def agent_headers(agent_token):
    return {"Authorization": f"Bearer {agent_token}"}

@pytest.fixture(scope="session")
def admin_headers(admin_token):
    return {"Authorization": f"Bearer {admin_token}"}


# ── Mock cache (Redis substitute) ─────────────────────────────────────────
class InMemoryCache:
    """Thread-safe in-memory cache that mimics the Redis cache interface."""
    def __init__(self):
        self._store = {}

    async def get(self, key):
        return self._store.get(key)

    async def set(self, key, value, ttl=None):
        self._store[key] = value

    async def delete(self, key):
        self._store.pop(key, None)

    async def keys(self, pattern):
        import fnmatch
        return [k for k in self._store if fnmatch.fnmatch(k, pattern.replace('*', '*'))]

    async def setex(self, key, ttl, value):
        self._store[key] = value

    def clear(self):
        self._store.clear()

    def __len__(self):
        return len(self._store)


@pytest.fixture
def mock_cache():
    c = InMemoryCache()
    with patch('app.cache.cache', c):
        yield c
    c.clear()


# ── Mock MongoDB database ──────────────────────────────────────────────────
@pytest.fixture
def mock_db():
    """Returns an AsyncMock that mimics motor AsyncIOMotorDatabase."""
    db = MagicMock()

    def make_collection():
        col = MagicMock()
        col.find_one = AsyncMock(return_value=None)
        col.insert_one = AsyncMock(return_value=MagicMock(inserted_id="new_id_001"))
        col.update_one = AsyncMock(return_value=MagicMock(modified_count=1))
        col.delete_one = AsyncMock(return_value=MagicMock(deleted_count=1))
        col.find = MagicMock(return_value=AsyncMockCursor([]))
        col.count_documents = AsyncMock(return_value=0)
        return col

    db.users       = make_collection()
    db.properties  = make_collection()
    db.inquiries   = make_collection()
    db.payments    = make_collection()
    db.rewards     = make_collection()
    db.feedback    = make_collection()
    db.crm_leads   = make_collection()
    return db


class AsyncMockCursor:
    """Async iterator that yields items like motor cursor."""
    def __init__(self, items):
        self._items = iter(items)

    def __aiter__(self):
        return self

    async def __anext__(self):
        try:
            return next(self._items)
        except StopIteration:
            raise StopAsyncIteration

    def to_list(self, length=None):
        return AsyncMock(return_value=[])()


# ── Sample data factories ──────────────────────────────────────────────────
@pytest.fixture
def sample_user():
    return {
        "_id": "user_001",
        "id": "user_001",
        "email": "test@propertyyards.com",
        "first_name": "Test",
        "last_name": "User",
        "phone_number": "9876543210",
        "password_hash": hash_password("Test@1234"),
        "role": "buyer",
        "is_active": True,
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc),
    }

@pytest.fixture
def sample_seller():
    return {
        "_id": SELLER_ID,
        "id": SELLER_ID,
        "email": "seller@propertyyards.com",
        "first_name": "Seller",
        "last_name": "One",
        "phone_number": "9876543211",
        "password_hash": hash_password("Seller@1234"),
        "role": "seller",
        "is_active": True,
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc),
    }

@pytest.fixture
def sample_property():
    return {
        "_id": "prop_001",
        "id": "prop_001",
        "user_id": SELLER_ID,
        "title": "3BHK in Gurgaon Sector 56",
        "description": "Spacious 3BHK with modern amenities",
        "location": "Sector 56",
        "city": "Gurgaon",
        "state": "Haryana",
        "country": "India",
        "price": 9500000,
        "property_type": "apartment",
        "listing_type": "sale",
        "bedrooms": 3,
        "bathrooms": 2,
        "area": 1450,
        "amenities": ["gym", "pool", "parking"],
        "images": ["https://picsum.photos/seed/p1/800/500"],
        "status": "active",
        "featured": False,
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc),
    }

@pytest.fixture
def sample_property_create_payload():
    return {
        "title": "2BHK in Noida",
        "description": "Modern 2BHK flat near metro",
        "location": "Sector 18",
        "city": "Noida",
        "state": "Uttar Pradesh",
        "country": "India",
        "price": 6500000,
        "property_type": "apartment",
        "listing_type": "sale",
        "bedrooms": 2,
        "bathrooms": 2,
        "area": 1100,
        "amenities": ["parking"],
        "images": [],
    }

@pytest.fixture
def sample_register_payload():
    return {
        "email": "newuser@propertyyards.com",
        "first_name": "New",
        "last_name": "User",
        "phone_number": "9812345678",
        "password": "NewUser@1234",
        "role": "buyer",
    }

@pytest.fixture
def sample_login_payload():
    return {
        "email": "seller@propertyyards.com",
        "password": "Seller@1234",
    }
