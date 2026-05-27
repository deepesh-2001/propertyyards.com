"""
Load testing script for Housing Platform
Tests 1000+ concurrent users with various endpoints
"""
import time
import random
import string
from locust import HttpUser, task, between, events
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class HousingUser(HttpUser):
    """Simulates a user interacting with the Housing Platform"""

    wait_time = between(1, 3)

    def on_start(self):
        """Called when a simulated user starts"""
        self.auth_token = None
        self.user_id = None
        self.property_id = None
        self.register_and_login()

    def register_and_login(self):
        """Register and login a new user"""
        # Generate unique email
        unique_id = ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
        email = f"user_{unique_id}@housing.com"

        # Register
        register_data = {
            "email": email,
            "first_name": f"User_{unique_id}",
            "last_name": "LoadTest",
            "phone_number": "+1-555-0100",
            "password": "testpassword123",
            "role": "buyer"
        }

        with self.client.post("/api/auth/register", json=register_data, catch_response=True) as response:
            if response.status_code == 200:
                logger.info(f"✓ User registered: {email}")

        # Login
        login_data = {
            "email": email,
            "password": "testpassword123"
        }

        with self.client.post("/api/auth/login", json=login_data, catch_response=True) as response:
            if response.status_code == 200:
                data = response.json()
                self.auth_token = data.get("access_token")
                logger.info(f"✓ User logged in: {email}")

    @task(5)
    def list_properties(self):
        """List properties"""
        headers = {"Authorization": f"Bearer {self.auth_token}"} if self.auth_token else {}

        with self.client.get("/api/properties?page=1&limit=20", headers=headers, catch_response=True) as response:
            if response.status_code == 200:
                data = response.json()
                if data.get("items"):
                    self.property_id = data["items"][0].get("id")

    @task(3)
    def search_properties(self):
        """Search properties with filters"""
        headers = {"Authorization": f"Bearer {self.auth_token}"} if self.auth_token else {}

        search_params = {
            "query": "apartment",
            "city": "New York",
            "min_price": 100000,
            "max_price": 1000000,
            "page": 1,
            "limit": 20
        }

        with self.client.get("/api/properties/search", params=search_params, headers=headers, catch_response=True) as response:
            pass

    @task(2)
    def get_property_details(self):
        """Get property details"""
        if self.property_id:
            headers = {"Authorization": f"Bearer {self.auth_token}"} if self.auth_token else {}

            with self.client.get(f"/api/properties/{self.property_id}", headers=headers, catch_response=True) as response:
                pass

    @task(2)
    def get_user_profile(self):
        """Get current user profile"""
        if self.auth_token:
            headers = {"Authorization": f"Bearer {self.auth_token}"}

            with self.client.get("/api/users/me", headers=headers, catch_response=True) as response:
                pass

    @task(2)
    def wishlist_operations(self):
        """Add/remove from wishlist"""
        if self.property_id and self.auth_token:
            headers = {"Authorization": f"Bearer {self.auth_token}"}

            # Add to wishlist
            with self.client.post(f"/api/properties/{self.property_id}/wishlist", headers=headers, catch_response=True) as response:
                pass

    @task(1)
    def create_inquiry(self):
        """Create property inquiry"""
        if self.property_id and self.auth_token:
            headers = {"Authorization": f"Bearer {self.auth_token}"}

            inquiry_data = {
                "property_id": self.property_id,
                "message": "I'm interested in this property. Please contact me."
            }

            with self.client.post("/api/inquiries", json=inquiry_data, headers=headers, catch_response=True) as response:
                pass

    @task(1)
    def get_inquiries(self):
        """Get user inquiries"""
        if self.auth_token:
            headers = {"Authorization": f"Bearer {self.auth_token}"}

            with self.client.get("/api/inquiries", headers=headers, catch_response=True) as response:
                pass

    @task(1)
    def get_api_info(self):
        """Get API info"""
        with self.client.get("/api/info", catch_response=True) as response:
            pass

    @task(1)
    def check_health(self):
        """Health check"""
        with self.client.get("/health", catch_response=True) as response:
            pass


# Event handlers for statistics
@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    logger.info("=" * 80)
    logger.info("LOAD TEST STARTED")
    logger.info("Testing Housing Platform with up to 1000 concurrent users")
    logger.info("=" * 80)


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    logger.info("=" * 80)
    logger.info("LOAD TEST COMPLETED")
    logger.info("=" * 80)

    # Print statistics
    if environment.stats:
        logger.info("\nResponse Time Statistics (ms):")
        for method, stats in environment.stats.entries.items():
            logger.info(f"  {method}: min={stats.min}, avg={stats.avg:.2f}, max={stats.max}, median={stats.median}, quantile_0.95={stats.get_response_time_percentile(0.95):.2f}")


# Command to run load test:
# locust -f tests/test_load.py --host=http://localhost:8000 --users 1000 --spawn-rate 100 --run-time 5m

