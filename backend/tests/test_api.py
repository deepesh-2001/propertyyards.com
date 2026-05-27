"""
Unit tests for Housing Platform API
"""
import pytest
from httpx import AsyncClient
from app.main import app
from app.database import SessionLocal, Base
from app.config import settings
from app.auth import hash_password
from app.models import User


@pytest.fixture
async def client():
    """Create test client"""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac


@pytest.fixture
def db():
    """Create test database"""
    # Create tables
    Base.metadata.create_all(bind=settings.DATABASE_URL)
    db = SessionLocal()
    yield db
    db.close()


class TestAuthAPI:
    """Test authentication endpoints"""

    @pytest.mark.asyncio
    async def test_register(self, client):
        """Test user registration"""
        response = await client.post(
            "/api/auth/register",
            json={
                "email": "test@housing.com",
                "first_name": "Test",
                "last_name": "User",
                "phone_number": "+1-555-0100",
                "password": "testpassword123",
                "role": "buyer"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "test@housing.com"
        assert data["role"] == "buyer"

    @pytest.mark.asyncio
    async def test_login(self, client, db):
        """Test user login"""
        # Create user first
        user = User(
            email="login@housing.com",
            first_name="Login",
            last_name="Test",
            password_hash=hash_password("testpassword123"),
            role="buyer",
            is_active=True
        )
        db.add(user)
        db.commit()

        # Test login
        response = await client.post(
            "/api/auth/login",
            json={
                "email": "login@housing.com",
                "password": "testpassword123"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data


class TestPropertyAPI:
    """Test property endpoints"""

    @pytest.mark.asyncio
    async def test_list_properties(self, client):
        """Test listing properties"""
        response = await client.get("/api/properties?page=1&limit=20")
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert "page" in data

    @pytest.mark.asyncio
    async def test_search_properties(self, client):
        """Test property search"""
        response = await client.get(
            "/api/properties/search?query=apartment&city=New+York&page=1&limit=20"
        )
        assert response.status_code == 200
        data = response.json()
        assert "items" in data


class TestHealthCheck:
    """Test health endpoints"""

    @pytest.mark.asyncio
    async def test_health_check(self, client):
        """Test health check endpoint"""
        response = await client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"

    @pytest.mark.asyncio
    async def test_api_info(self, client):
        """Test API info endpoint"""
        response = await client.get("/api/info")
        assert response.status_code == 200
        data = response.json()
        assert "version" in data
        assert "endpoints" in data


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

