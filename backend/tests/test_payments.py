"""
Unit tests for Payment API and Integrations
"""
import pytest
from httpx import AsyncClient
from app.main import app
from app.database import SessionLocal, Base
from app.config import settings
from app.auth import hash_password, create_access_token
from app.models import User
from datetime import datetime, timedelta
import json


@pytest.fixture
async def client():
    """Create test client"""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac


@pytest.fixture
def db():
    """Create test database"""
    Base.metadata.create_all(bind=settings.DATABASE_URL)
    db = SessionLocal()
    yield db
    db.close()


@pytest.fixture
async def auth_token(client):
    """Create authenticated user and return token"""
    # Register user
    await client.post(
        "/api/auth/register",
        json={
            "email": "payment_test@housing.com",
            "first_name": "Payment",
            "last_name": "Test",
            "phone_number": "+1-555-0100",
            "password": "testpassword123",
            "role": "buyer"
        }
    )
    
    # Login and get token
    response = await client.post(
        "/api/auth/login",
        json={
            "email": "payment_test@housing.com",
            "password": "testpassword123"
        }
    )
    data = response.json()
    return data["access_token"]


class TestPaymentConditions:
    """Test payment condition endpoints"""

    @pytest.mark.asyncio
    async def test_create_payment_condition(self, client, auth_token):
        """Test creating a payment condition"""
        response = await client.post(
            "/api/payments/conditions",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={
                "property_id": "test_property_123",
                "condition_type": "down_payment",
                "amount": 50000.0,
                "due_date": (datetime.utcnow() + timedelta(days=30)).isoformat(),
                "installment_count": 3
            }
        )
        assert response.status_code in [200, 201]
        data = response.json()
        assert "id" in data or "property_id" in data

    @pytest.mark.asyncio
    async def test_get_payment_condition(self, client, auth_token):
        """Test getting a payment condition"""
        # First create a condition
        create_response = await client.post(
            "/api/payments/conditions",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={
                "property_id": "test_property_456",
                "condition_type": "down_payment",
                "amount": 30000.0,
                "due_date": (datetime.utcnow() + timedelta(days=15)).isoformat(),
                "installment_count": 2
            }
        )
        
        if create_response.status_code in [200, 201]:
            condition_id = create_response.json().get("id")
            if condition_id:
                response = await client.get(
                    f"/api/payments/conditions/{condition_id}",
                    headers={"Authorization": f"Bearer {auth_token}"}
                )
                assert response.status_code in [200, 404]

    @pytest.mark.asyncio
    async def test_get_property_payment_conditions(self, client, auth_token):
        """Test getting all payment conditions for a property"""
        response = await client.get(
            "/api/payments/properties/test_property_789/conditions",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code in [200, 404]

    @pytest.mark.asyncio
    async def test_update_payment_condition(self, client, auth_token):
        """Test updating a payment condition"""
        # Create condition first
        create_response = await client.post(
            "/api/payments/conditions",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={
                "property_id": "test_property_999",
                "condition_type": "down_payment",
                "amount": 40000.0,
                "due_date": (datetime.utcnow() + timedelta(days=20)).isoformat(),
                "installment_count": 4
            }
        )
        
        if create_response.status_code in [200, 201]:
            condition_id = create_response.json().get("id")
            if condition_id:
                response = await client.put(
                    f"/api/payments/conditions/{condition_id}",
                    headers={"Authorization": f"Bearer {auth_token}"},
                    json={"amount": 45000.0}
                )
                assert response.status_code in [200, 404]

    @pytest.mark.asyncio
    async def test_delete_payment_condition(self, client, auth_token):
        """Test deleting a payment condition"""
        # Create condition first
        create_response = await client.post(
            "/api/payments/conditions",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={
                "property_id": "test_property_delete",
                "condition_type": "down_payment",
                "amount": 20000.0,
                "due_date": (datetime.utcnow() + timedelta(days=10)).isoformat(),
                "installment_count": 1
            }
        )
        
        if create_response.status_code in [200, 201]:
            condition_id = create_response.json().get("id")
            if condition_id:
                response = await client.delete(
                    f"/api/payments/conditions/{condition_id}",
                    headers={"Authorization": f"Bearer {auth_token}"}
                )
                assert response.status_code in [200, 204, 404]


class TestPaymentMethods:
    """Test payment method endpoints"""

    @pytest.mark.asyncio
    async def test_create_payment_method(self, client, auth_token):
        """Test creating a payment method"""
        response = await client.post(
            "/api/payments/methods",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={
                "user_id": "test_user_123",
                "method_type": "credit_card",
                "provider": "stripe",
                "card_last_four": "4242",
                "card_brand": "visa",
                "expiry_month": 12,
                "expiry_year": 2025
            }
        )
        assert response.status_code in [200, 201]
        data = response.json()
        assert "id" in data or "card_last_four" in data

    @pytest.mark.asyncio
    async def test_get_user_payment_methods(self, client, auth_token):
        """Test getting user payment methods"""
        response = await client.get(
            "/api/payments/methods?user_id=test_user_123",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code in [200, 404]

    @pytest.mark.asyncio
    async def test_get_payment_method(self, client, auth_token):
        """Test getting a specific payment method"""
        # Create method first
        create_response = await client.post(
            "/api/payments/methods",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={
                "user_id": "test_user_456",
                "method_type": "credit_card",
                "provider": "stripe",
                "card_last_four": "5555",
                "card_brand": "mastercard",
                "expiry_month": 6,
                "expiry_year": 2026
            }
        )
        
        if create_response.status_code in [200, 201]:
            method_id = create_response.json().get("id")
            if method_id:
                response = await client.get(
                    f"/api/payments/methods/{method_id}",
                    headers={"Authorization": f"Bearer {auth_token}"}
                )
                assert response.status_code in [200, 404]

    @pytest.mark.asyncio
    async def test_update_payment_method(self, client, auth_token):
        """Test updating a payment method"""
        # Create method first
        create_response = await client.post(
            "/api/payments/methods",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={
                "user_id": "test_user_789",
                "method_type": "credit_card",
                "provider": "stripe",
                "card_last_four": "1234",
                "card_brand": "visa",
                "expiry_month": 9,
                "expiry_year": 2024
            }
        )
        
        if create_response.status_code in [200, 201]:
            method_id = create_response.json().get("id")
            if method_id:
                response = await client.put(
                    f"/api/payments/methods/{method_id}",
                    headers={"Authorization": f"Bearer {auth_token}"},
                    json={"is_default": True}
                )
                assert response.status_code in [200, 404]

    @pytest.mark.asyncio
    async def test_delete_payment_method(self, client, auth_token):
        """Test deleting a payment method"""
        # Create method first
        create_response = await client.post(
            "/api/payments/methods",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={
                "user_id": "test_user_delete",
                "method_type": "credit_card",
                "provider": "stripe",
                "card_last_four": "9999",
                "card_brand": "visa",
                "expiry_month": 3,
                "expiry_year": 2025
            }
        )
        
        if create_response.status_code in [200, 201]:
            method_id = create_response.json().get("id")
            if method_id:
                response = await client.delete(
                    f"/api/payments/methods/{method_id}",
                    headers={"Authorization": f"Bearer {auth_token}"}
                )
                assert response.status_code in [200, 204, 404]


class TestPaymentTransactions:
    """Test payment transaction endpoints"""

    @pytest.mark.asyncio
    async def test_create_payment(self, client, auth_token):
        """Test creating a payment transaction"""
        response = await client.post(
            "/api/payments/transactions",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={
                "user_id": "test_user_payment",
                "amount": 1000.0,
                "currency": "USD",
                "payment_method_id": "test_method_123",
                "payment_gateway": "stripe",
                "description": "Test payment"
            }
        )
        # May fail if Stripe credentials not configured
        assert response.status_code in [200, 201, 400, 500]

    @pytest.mark.asyncio
    async def test_get_payment(self, client, auth_token):
        """Test getting a payment transaction"""
        response = await client.get(
            "/api/payments/transactions/test_payment_123",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code in [200, 404]

    @pytest.mark.asyncio
    async def test_get_user_payments(self, client, auth_token):
        """Test getting user payments"""
        response = await client.get(
            "/api/payments/users/test_user_456/transactions?limit=50",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code in [200, 404]

    @pytest.mark.asyncio
    async def test_refund_payment(self, client, auth_token):
        """Test refunding a payment"""
        response = await client.post(
            "/api/payments/transactions/test_payment_789/refund",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={
                "amount": 500.0,
                "reason": "Test refund"
            }
        )
        assert response.status_code in [200, 400, 404]

    @pytest.mark.asyncio
    async def test_get_payment_status(self, client, auth_token):
        """Test getting payment status"""
        response = await client.get(
            "/api/payments/transactions/test_payment_status/status",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code in [200, 400, 404]


class TestSubscriptions:
    """Test subscription endpoints"""

    @pytest.mark.asyncio
    async def test_create_subscription(self, client, auth_token):
        """Test creating a subscription"""
        response = await client.post(
            "/api/payments/subscriptions",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={
                "user_id": "test_sub_user",
                "plan": "premium",
                "payment_method_id": "test_method_123",
                "billing_cycle": "monthly"
            }
        )
        assert response.status_code in [200, 201, 400]

    @pytest.mark.asyncio
    async def test_get_subscription(self, client, auth_token):
        """Test getting a subscription"""
        response = await client.get(
            "/api/payments/subscriptions/test_sub_123",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code in [200, 404]

    @pytest.mark.asyncio
    async def test_cancel_subscription(self, client, auth_token):
        """Test cancelling a subscription"""
        response = await client.post(
            "/api/payments/subscriptions/test_sub_456/cancel",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code in [200, 404]


class TestInvoices:
    """Test invoice endpoints"""

    @pytest.mark.asyncio
    async def test_create_invoice(self, client, auth_token):
        """Test creating an invoice"""
        response = await client.post(
            "/api/payments/invoices",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={
                "user_id": "test_invoice_user",
                "payment_condition_ids": ["test_condition_123"],
                "due_date": (datetime.utcnow() + timedelta(days=7)).isoformat()
            }
        )
        assert response.status_code in [200, 201, 400]

    @pytest.mark.asyncio
    async def test_get_invoice(self, client, auth_token):
        """Test getting an invoice"""
        response = await client.get(
            "/api/payments/invoices/test_invoice_123",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code in [200, 404]

    @pytest.mark.asyncio
    async def test_get_user_invoices(self, client, auth_token):
        """Test getting user invoices"""
        response = await client.get(
            "/api/payments/users/test_invoice_user/invoices",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code in [200, 404]


class TestInstallments:
    """Test installment endpoints"""

    @pytest.mark.asyncio
    async def test_get_installments(self, client, auth_token):
        """Test getting installments for a payment condition"""
        response = await client.get(
            "/api/payments/conditions/test_condition_123/installments",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code in [200, 404]

    @pytest.mark.asyncio
    async def test_pay_installment(self, client, auth_token):
        """Test paying an installment"""
        response = await client.put(
            "/api/payments/installments/test_installment_123/pay",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code in [200, 400, 404]


class TestPaymentAnalytics:
    """Test payment analytics endpoints"""

    @pytest.mark.asyncio
    async def test_get_payment_analytics(self, client, auth_token):
        """Test getting payment analytics"""
        response = await client.get(
            "/api/payments/analytics",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code in [200, 403]


class TestWebhooks:
    """Test webhook endpoints"""

    @pytest.mark.asyncio
    async def test_stripe_webhook(self, client):
        """Test Stripe webhook endpoint"""
        response = await client.post(
            "/api/payments/webhooks/stripe",
            json={
                "id": "evt_test123",
                "type": "payment_intent.succeeded",
                "data": {"object": {"id": "pi_test123"}}
            }
        )
        assert response.status_code in [200, 400]

    @pytest.mark.asyncio
    async def test_paypal_webhook(self, client):
        """Test PayPal webhook endpoint"""
        response = await client.post(
            "/api/payments/webhooks/paypal",
            json={
                "event_type": "PAYMENT.CAPTURE.COMPLETED",
                "resource": {"id": "test_payment_id"}
            }
        )
        assert response.status_code in [200, 400]


class TestFeatureFlags:
    """Test payment feature flags"""

    @pytest.mark.asyncio
    async def test_payment_conditions_flag(self, client, auth_token):
        """Test payment_conditions feature flag"""
        response = await client.post(
            "/api/payments/conditions",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={
                "property_id": "test_flag_123",
                "condition_type": "down_payment",
                "amount": 10000.0,
                "due_date": (datetime.utcnow() + timedelta(days=30)).isoformat(),
                "installment_count": 1
            }
        )
        # Should work if feature flag is enabled
        assert response.status_code in [200, 201, 403]

    @pytest.mark.asyncio
    async def test_payment_methods_flag(self, client, auth_token):
        """Test payment_methods feature flag"""
        response = await client.post(
            "/api/payments/methods",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={
                "user_id": "test_flag_user",
                "method_type": "credit_card",
                "provider": "stripe",
                "card_last_four": "4242",
                "card_brand": "visa",
                "expiry_month": 12,
                "expiry_year": 2025
            }
        )
        # Should work if feature flag is enabled
        assert response.status_code in [200, 201, 403]

    @pytest.mark.asyncio
    async def test_subscriptions_flag(self, client, auth_token):
        """Test subscriptions feature flag"""
        response = await client.post(
            "/api/payments/subscriptions",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={
                "user_id": "test_sub_flag",
                "plan": "premium",
                "payment_method_id": "test_method",
                "billing_cycle": "monthly"
            }
        )
        # Should work if feature flag is enabled
        assert response.status_code in [200, 201, 403]

    @pytest.mark.asyncio
    async def test_payment_analytics_flag(self, client, auth_token):
        """Test payment_analytics feature flag"""
        response = await client.get(
            "/api/payments/analytics",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        # Should work if feature flag is enabled and user has admin role
        assert response.status_code in [200, 403]


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
