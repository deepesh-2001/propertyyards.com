"""
Test Suite for Onboarding & Offboarding Module
Tests employee onboarding, offboarding, EPFO/ESI integration, and notifications

Note: This test requires backend dependencies (pydantic, fastapi, motor, etc.)
Run from backend directory with: python -m pytest tests/test_onboarding.py -v
"""
import sys
import os

# Add parent directory to Python path for app imports
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

from app.onboarding import onboarding_manager, offboarding_manager, epfo_manager
from app.schemas import (
    OnboardingStatus,
    OffboardingStatus,
    EPFOStatus,
    EPFODetails,
    ESIDetails,
    BankAccountDetails,
    DocumentSubmission,
    OnboardingChecklist,
    EmployeeOnboardingCreate,
    EmployeeOffboardingCreate
)


# Mock database utilities
class MockDatabase:
    def __init__(self):
        self.data = {
            "employee_onboardings": {},
            "employee_offboardings": {},
            "epfo_records": {},
            "esi_records": {},
            "users": {}
        }
        self._id_counter = 1

    def _generate_id(self):
        _id = str(self._id_counter)
        self._id_counter += 1
        return _id

    async def insert_one(self, collection, data):
        _id = self._generate_id()
        data["_id"] = _id
        if collection not in self.data:
            self.data[collection] = {}
        self.data[collection][_id] = data
        return MagicMock(inserted_id=_id)

    async def find_one(self, collection, query):
        if collection not in self.data:
            return None
        if "_id" in query:
            return self.data[collection].get(query["_id"])
        if "employee_id" in query:
            for item in self.data[collection].values():
                if item.get("employee_id") == query["employee_id"]:
                    return item
        return None

    async def update_one(self, collection, query, update):
        if collection not in self.data:
            return MagicMock(modified_count=0)
        if "_id" in query:
            item = self.data[collection].get(query["_id"])
            if item:
                item.update(update["$set"])
                return MagicMock(modified_count=1)
        return MagicMock(modified_count=0)

    async def find(self, collection, query=None):
        if collection not in self.data:
            return MagicMock(to_list=AsyncMock(return_value=[]))
        return MagicMock(to_list=AsyncMock(return_value=list(self.data[collection].values())))

    async def count_documents(self, collection, query):
        if collection not in self.data:
            return 0
        return len(self.data[collection])


@pytest.fixture
def mock_db():
    return MockDatabase()


@pytest.fixture
def sample_bank_account():
    return BankAccountDetails(
        account_number="1234567890",
        bank_name="HDFC Bank",
        branch_name="Andheri East",
        ifsc_code="HDFC0001234",
        account_type="savings",
        is_primary=True
    )


@pytest.fixture
def sample_epfo_details():
    return EPFODetails(
        uan_number="100123456789",
        pf_account_number="MH/PUN/123456/123",
        establishment_id="EST123456",
        epfo_office="Mumbai",
        pf_contribution_rate=12.0,
        pension_contribution_rate=8.33,
        status=EPFOStatus.REGISTERED
    )


@pytest.fixture
def sample_esi_details():
    return ESIDetails(
        esi_number="ESI1234567890",
        establishment_id="EST123456",
        esi_office="Mumbai",
        esi_contribution_rate=1.0,
        status=EPFOStatus.REGISTERED
    )


@pytest.fixture
def sample_onboarding_data(sample_bank_account, sample_epfo_details, sample_esi_details):
    return {
        "employee_id": "emp-001",
        "employee_name": "John Doe",
        "email": "john@example.com",
        "phone_number": "+91-9876543210",
        "designation": "Software Engineer",
        "department": "Engineering",
        "reporting_manager_id": "mgr-001",
        "date_of_joining": datetime(2024, 6, 1),
        "employment_type": "full_time",
        "work_location": "Mumbai",
        "salary_offered": 1200000,
        "epfo_details": sample_epfo_details.dict(),
        "esi_details": sample_esi_details.dict(),
        "bank_account": sample_bank_account.dict(),
        "documents": [],
        "checklist": [],
        "notes": "New hire for backend team"
    }


@pytest.fixture
def sample_offboarding_data():
    return {
        "employee_id": "emp-001",
        "employee_name": "John Doe",
        "email": "john@example.com",
        "phone_number": "+91-9876543210",
        "designation": "Software Engineer",
        "department": "Engineering",
        "date_of_resignation": datetime(2024, 5, 15),
        "last_working_day": datetime(2024, 6, 15),
        "reason_for_leaving": "Better opportunity",
        "exit_type": "resignation",
        "is_eligible_rehire": True,
        "handover_to": "emp-002",
        "settlement_amount": 150000,
        "pending_leaves": 5,
        "encashable_leaves": 5,
        "assets_to_return": ["Laptop", "Access Card", "Monitor"],
        "clearance_checklist": [],
        "notes": "Standard resignation"
    }


# ========== Onboarding Tests ==========

@pytest.mark.asyncio
async def test_create_onboarding(mock_db, sample_onboarding_data):
    """Test creating a new onboarding record"""
    with patch('app.onboarding.notification_manager') as mock_notification:
        mock_notification.email_service.send_onboarding_welcome = AsyncMock(return_value={"success": True})
        mock_notification.whatsapp_service.send_onboarding_welcome_whatsapp = AsyncMock(return_value={"success": True})

        result = await onboarding_manager.create_onboarding(sample_onboarding_data, mock_db)

        assert result["employee_id"] == "emp-001"
        assert result["employee_name"] == "John Doe"
        assert result["status"] == OnboardingStatus.PENDING
        assert result["designation"] == "Software Engineer"
        assert result["department"] == "Engineering"
        assert len(result["checklist"]) == 15  # Default checklist has 15 items
        assert "id" in result

        # Verify notifications were called
        mock_notification.email_service.send_onboarding_welcome.assert_called_once()
        mock_notification.whatsapp_service.send_onboarding_welcome_whatsapp.assert_called_once()


@pytest.mark.asyncio
async def test_create_onboarding_without_reporting_manager(mock_db, sample_onboarding_data):
    """Test creating onboarding without reporting manager"""
    sample_onboarding_data["reporting_manager_id"] = None
    sample_onboarding_data["reporting_manager_name"] = None

    with patch('app.onboarding.notification_manager') as mock_notification:
        mock_notification.email_service.send_onboarding_welcome = AsyncMock(return_value={"success": True})
        mock_notification.whatsapp_service.send_onboarding_welcome_whatsapp = AsyncMock(return_value={"success": True})

        result = await onboarding_manager.create_onboarding(sample_onboarding_data, mock_db)

        assert result["reporting_manager_id"] is None
        assert result["reporting_manager_name"] is None


@pytest.mark.asyncio
async def test_update_onboarding_status(mock_db, sample_onboarding_data):
    """Test updating onboarding status"""
    with patch('app.onboarding.notification_manager') as mock_notification:
        mock_notification.email_service.send_onboarding_welcome = AsyncMock(return_value={"success": True})
        mock_notification.whatsapp_service.send_onboarding_welcome_whatsapp = AsyncMock(return_value={"success": True})
        mock_notification.email_service.send_onboarding_status_update = AsyncMock(return_value={"success": True})
        mock_notification.whatsapp_service.send_onboarding_status_whatsapp = AsyncMock(return_value={"success": True})

        # Create onboarding first
        created = await onboarding_manager.create_onboarding(sample_onboarding_data, mock_db)

        # Update status
        update_data = {"status": OnboardingStatus.IN_PROGRESS}
        updated = await onboarding_manager.update_onboarding(created["id"], update_data, mock_db)

        assert updated["status"] == OnboardingStatus.IN_PROGRESS

        # Verify status update notifications were called
        mock_notification.email_service.send_onboarding_status_update.assert_called_once()
        mock_notification.whatsapp_service.send_onboarding_status_whatsapp.assert_called_once()


@pytest.mark.asyncio
async def test_update_onboarding_checklist_completion(mock_db, sample_onboarding_data):
    """Test that onboarding auto-approves when all checklist items are completed"""
    with patch('app.onboarding.notification_manager') as mock_notification:
        mock_notification.email_service.send_onboarding_welcome = AsyncMock(return_value={"success": True})
        mock_notification.whatsapp_service.send_onboarding_welcome_whatsapp = AsyncMock(return_value={"success": True})
        mock_notification.email_service.send_onboarding_status_update = AsyncMock(return_value={"success": True})
        mock_notification.whatsapp_service.send_onboarding_status_whatsapp = AsyncMock(return_value={"success": True})

        # Create onboarding
        created = await onboarding_manager.create_onboarding(sample_onboarding_data, mock_db)

        # Mark all checklist items as completed
        completed_checklist = [
            {**item, "completed": True, "completed_at": datetime.utcnow(), "completed_by": "hr-001"}
            for item in created["checklist"]
        ]

        update_data = {"checklist": completed_checklist}
        updated = await onboarding_manager.update_onboarding(created["id"], update_data, mock_db)

        assert updated["status"] == OnboardingStatus.APPROVED
        assert updated["completed_at"] is not None


@pytest.mark.asyncio
async def test_approve_onboarding(mock_db, sample_onboarding_data):
    """Test approving an onboarding"""
    with patch('app.onboarding.notification_manager') as mock_notification:
        mock_notification.email_service.send_onboarding_welcome = AsyncMock(return_value={"success": True})
        mock_notification.whatsapp_service.send_onboarding_welcome_whatsapp = AsyncMock(return_value={"success": True})

        created = await onboarding_manager.create_onboarding(sample_onboarding_data, mock_db)

        approved = await onboarding_manager.approve_onboarding(created["id"], "admin-001", mock_db)

        assert approved["status"] == OnboardingStatus.APPROVED
        assert approved["approved_by"] == "admin-001"


@pytest.mark.asyncio
async def test_reject_onboarding(mock_db, sample_onboarding_data):
    """Test rejecting an onboarding"""
    with patch('app.onboarding.notification_manager') as mock_notification:
        mock_notification.email_service.send_onboarding_welcome = AsyncMock(return_value={"success": True})
        mock_notification.whatsapp_service.send_onboarding_welcome_whatsapp = AsyncMock(return_value={"success": True})

        created = await onboarding_manager.create_onboarding(sample_onboarding_data, mock_db)

        rejected = await onboarding_manager.reject_onboarding(
            created["id"],
            "Background verification failed",
            mock_db
        )

        assert rejected["status"] == OnboardingStatus.REJECTED
        assert rejected["rejection_reason"] == "Background verification failed"


@pytest.mark.asyncio
async def test_get_onboarding_analytics(mock_db, sample_onboarding_data):
    """Test onboarding analytics"""
    with patch('app.onboarding.notification_manager') as mock_notification:
        mock_notification.email_service.send_onboarding_welcome = AsyncMock(return_value={"success": True})
        mock_notification.whatsapp_service.send_onboarding_welcome_whatsapp = AsyncMock(return_value={"success": True})

        # Create multiple onboardings
        for i in range(5):
            data = sample_onboarding_data.copy()
            data["employee_id"] = f"emp-{i:03d}"
            await onboarding_manager.create_onboarding(data, mock_db)

        analytics = await onboarding_manager.get_onboarding_analytics(mock_db)

        assert analytics["total_onboardings"] == 5
        assert analytics["pending_onboardings"] == 5
        assert "by_department" in analytics
        assert "by_status" in analytics
        assert "monthly_trend" in analytics


# ========== Offboarding Tests ==========

@pytest.mark.asyncio
async def test_create_offboarding(mock_db, sample_offboarding_data):
    """Test creating a new offboarding record"""
    with patch('app.onboarding.notification_manager') as mock_notification:
        mock_notification.email_service.send_offboarding_notification = AsyncMock(return_value={"success": True})
        mock_notification.whatsapp_service.send_offboarding_whatsapp = AsyncMock(return_value={"success": True})

        result = await offboarding_manager.create_offboarding(sample_offboarding_data, mock_db)

        assert result["employee_id"] == "emp-001"
        assert result["employee_name"] == "John Doe"
        assert result["status"] == OffboardingStatus.PENDING
        assert result["reason_for_leaving"] == "Better opportunity"
        assert result["is_eligible_rehire"] is True
        assert len(result["clearance_checklist"]) == 10  # Default checklist has 10 items
        assert "id" in result

        # Verify notifications were called
        mock_notification.email_service.send_offboarding_notification.assert_called_once()
        mock_notification.whatsapp_service.send_offboarding_whatsapp.assert_called_once()


@pytest.mark.asyncio
async def test_update_offboarding_clearance_completion(mock_db, sample_offboarding_data):
    """Test that offboarding auto-approves when all clearance items are completed"""
    with patch('app.onboarding.notification_manager') as mock_notification:
        mock_notification.email_service.send_offboarding_notification = AsyncMock(return_value={"success": True})
        mock_notification.whatsapp_service.send_offboarding_whatsapp = AsyncMock(return_value={"success": True})

        created = await offboarding_manager.create_offboarding(sample_offboarding_data, mock_db)

        # Mark all clearance items as completed
        completed_checklist = [
            {**item, "completed": True, "completed_at": datetime.utcnow(), "completed_by": "hr-001"}
            for item in created["clearance_checklist"]
        ]

        update_data = {"clearance_checklist": completed_checklist}
        updated = await offboarding_manager.update_offboarding(created["id"], update_data, mock_db)

        assert updated["status"] == OffboardingStatus.APPROVED


@pytest.mark.asyncio
async def test_complete_offboarding(mock_db, sample_offboarding_data):
    """Test completing an offboarding"""
    with patch('app.onboarding.notification_manager') as mock_notification:
        mock_notification.email_service.send_offboarding_notification = AsyncMock(return_value={"success": True})
        mock_notification.whatsapp_service.send_offboarding_whatsapp = AsyncMock(return_value={"success": True})

        created = await offboarding_manager.create_offboarding(sample_offboarding_data, mock_db)

        completed = await offboarding_manager.complete_offboarding(created["id"], mock_db)

        assert completed["status"] == OffboardingStatus.COMPLETED
        assert completed["completed_at"] is not None


@pytest.mark.asyncio
async def test_get_offboarding_analytics(mock_db, sample_offboarding_data):
    """Test offboarding analytics"""
    with patch('app.onboarding.notification_manager') as mock_notification:
        mock_notification.email_service.send_offboarding_notification = AsyncMock(return_value={"success": True})
        mock_notification.whatsapp_service.send_offboarding_whatsapp = AsyncMock(return_value={"success": True})

        # Create multiple offboardings
        for i in range(3):
            data = sample_offboarding_data.copy()
            data["employee_id"] = f"emp-{i:03d}"
            await offboarding_manager.create_offboarding(data, mock_db)

        analytics = await offboarding_manager.get_offboarding_analytics(mock_db)

        assert analytics["total_offboardings"] == 3
        assert analytics["pending_offboardings"] == 3
        assert "by_department" in analytics
        assert "by_reason" in analytics
        assert "by_exit_type" in analytics
        assert "monthly_trend" in analytics


# ========== EPFO/ESI Tests ==========

@pytest.mark.asyncio
async def test_register_epfo(mock_db, sample_epfo_details):
    """Test EPFO registration"""
    result = await epfo_manager.register_epfo("emp-001", sample_epfo_details, mock_db)

    assert result["employee_id"] == "emp-001"
    assert result["uan_number"] == "100123456789"
    assert result["status"] == EPFOStatus.REGISTERED
    assert result["registered_at"] is not None
    assert "id" in result


@pytest.mark.asyncio
async def test_register_esi(mock_db, sample_esi_details):
    """Test ESI registration"""
    result = await epfo_manager.register_esi("emp-001", sample_esi_details, mock_db)

    assert result["employee_id"] == "emp-001"
    assert result["esi_number"] == "ESI1234567890"
    assert result["status"] == EPFOStatus.REGISTERED
    assert result["registered_at"] is not None
    assert "id" in result


@pytest.mark.asyncio
async def test_withdraw_epfo(mock_db, sample_epfo_details):
    """Test EPFO withdrawal"""
    # First register
    await epfo_manager.register_epfo("emp-001", sample_epfo_details, mock_db)

    # Then withdraw
    result = await epfo_manager.withdraw_epfo("emp-001", mock_db)

    assert result["success"] is True
    assert result["employee_id"] == "emp-001"
    assert result["status"] == EPFOStatus.WITHDRAWN


@pytest.mark.asyncio
async def test_transfer_epfo(mock_db, sample_epfo_details):
    """Test EPFO transfer"""
    # First register
    await epfo_manager.register_epfo("emp-001", sample_epfo_details, mock_db)

    # Then transfer
    result = await epfo_manager.transfer_epfo("emp-001", "NEW_EST456", mock_db)

    assert result["success"] is True
    assert result["employee_id"] == "emp-001"
    assert result["new_establishment_id"] == "NEW_EST456"


@pytest.mark.asyncio
async def test_get_epfo_details(mock_db, sample_epfo_details):
    """Test getting EPFO details"""
    await epfo_manager.register_epfo("emp-001", sample_epfo_details, mock_db)

    details = await epfo_manager.get_epfo_details("emp-001", mock_db)

    assert details is not None
    assert details["employee_id"] == "emp-001"
    assert details["uan_number"] == "100123456789"


@pytest.mark.asyncio
async def test_get_esi_details(mock_db, sample_esi_details):
    """Test getting ESI details"""
    await epfo_manager.register_esi("emp-001", sample_esi_details, mock_db)

    details = await epfo_manager.get_esi_details("emp-001", mock_db)

    assert details is not None
    assert details["employee_id"] == "emp-001"
    assert details["esi_number"] == "ESI1234567890"


# ========== Notification Tests ==========

@pytest.mark.asyncio
async def test_notification_failure_does_not_block_onboarding(mock_db, sample_onboarding_data):
    """Test that notification failure doesn't block onboarding creation"""
    with patch('app.onboarding.notification_manager') as mock_notification:
        # Simulate notification failure
        mock_notification.email_service.send_onboarding_welcome = AsyncMock(
            side_effect=Exception("SMTP connection failed")
        )
        mock_notification.whatsapp_service.send_onboarding_welcome_whatsapp = AsyncMock(
            side_effect=Exception("WhatsApp API error")
        )

        # Onboarding should still succeed
        result = await onboarding_manager.create_onboarding(sample_onboarding_data, mock_db)

        assert result["employee_id"] == "emp-001"
        assert result["status"] == OnboardingStatus.PENDING


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
