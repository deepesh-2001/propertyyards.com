"""
Tests for Enhanced Analytics Module
"""
import pytest
import sys
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock

# Add backend to path
sys.path.insert(0, 'C:/Users/deepe/PyCharmMiscProject/housing_platform/backend')

from app.analytics import analytics_manager


@pytest.fixture
def mock_database():
    """Mock database fixture"""
    db = MagicMock()
    db.properties = AsyncMock()
    db.users = AsyncMock()
    db.commissions = AsyncMock()
    db.inquiries = AsyncMock()
    return db


@pytest.fixture
def sample_start_date():
    """Sample start date"""
    return datetime(2024, 1, 1)


@pytest.fixture
def sample_end_date():
    """Sample end date"""
    return datetime(2024, 12, 31)


@pytest.mark.asyncio
async def test_get_property_analytics(mock_database):
    """Test getting property analytics"""
    # Mock aggregation results
    mock_database.properties.count_documents.return_value = 100
    mock_database.properties.aggregate.return_value.to_list.side_effect = [
        [{"_id": "apartment", "count": 50}, {"_id": "villa", "count": 30}],
        [{"_id": "Mumbai", "count": 40}, {"_id": "Delhi", "count": 30}],
        [{"price": 5000000}, {"price": 7000000}],
        [{"_id": None, "avg_price": 6000000}],
        [
            {"_id": {"year": 2024, "month": 1}, "count": 10},
            {"_id": {"year": 2024, "month": 2}, "count": 15}
        ],
        [
            {"_id": {"year": 2024, "month": 1}, "avg_price": 5500000},
            {"_id": {"year": 2024, "month": 2}, "avg_price": 6500000}
        ],
        [{"price": 5000000}, {"price": 7000000}]  # For price ranges
    ]

    result = await analytics_manager.get_property_analytics(
        database=mock_database,
        start_date=None,
        end_date=None
    )

    assert result is not None
    assert "total_properties" in result
    assert "by_type" in result
    assert "by_city" in result
    assert "average_price" in result
    assert "monthly_listings" in result


@pytest.mark.asyncio
async def test_get_user_analytics(mock_database):
    """Test getting user analytics"""
    mock_database.users.count_documents.return_value = 500
    mock_database.users.aggregate.return_value.to_list.side_effect = [
        [{"_id": "admin", "count": 10}, {"_id": "agent", "count": 100}],
        [{"_id": "Mumbai", "count": 200}, {"_id": "Delhi", "count": 150}],
        [
            {"_id": {"year": 2024, "month": 1}, "count": 50},
            {"_id": {"year": 2024, "month": 2}, "count": 60}
        ]
    ]

    result = await analytics_manager.get_user_analytics(
        database=mock_database,
        start_date=None,
        end_date=None
    )

    assert result is not None
    assert "total_users" in result
    assert "active_users" in result
    assert "by_role" in result
    assert "user_growth_trend" in result


@pytest.mark.asyncio
async def test_get_revenue_analytics(mock_database):
    """Test getting revenue analytics"""
    mock_database.commissions.aggregate.return_value.to_list.side_effect = [
        [{"_id": None, "total": 1000000}],
        [{"_id": None, "total": 100000}],
        [{"_id": None, "total": 300000}],
        [{"_id": None, "total": 900000}],
        [{"_id": "property_sale", "total": 600000}, {"_id": "loan", "total": 400000}],
        [
            {"_id": {"year": 2024, "month": 1}, "total": 80000},
            {"_id": {"year": 2024, "month": 2}, "total": 90000}
        ],
        [{"_id": None, "avg": 50000}]
    ]

    result = await analytics_manager.get_revenue_analytics(
        database=mock_database,
        start_date=None,
        end_date=None
    )

    assert result is not None
    assert "total_revenue" in result
    assert "revenue_this_month" in result
    assert "by_source" in result
    assert "monthly_revenue_trend" in result


@pytest.mark.asyncio
async def test_get_commission_analytics(mock_database):
    """Test getting commission analytics"""
    mock_database.commissions.aggregate.return_value.to_list.side_effect = [
        [{"_id": None, "total": 1000000}],
        [{"_id": None, "total": 200000}],
        [{"_id": None, "total": 800000}],
        [
            {"_id": "user1", "total": 500000, "count": 10},
            {"_id": "user2", "total": 300000, "count": 8}
        ],
        [{"_id": "property_sale", "total": 600000}, {"_id": "loan", "total": 400000}],
        [
            {"_id": {"year": 2024, "month": 1}, "total": 80000},
            {"_id": {"year": 2024, "month": 2}, "total": 90000}
        ],
        [{"_id": None, "avg": 50000}]
    ]

    result = await analytics_manager.get_commission_analytics(
        database=mock_database,
        start_date=None,
        end_date=None
    )

    assert result is not None
    assert "total_commissions" in result
    assert "pending_commissions" in result
    assert "paid_commissions" in result
    assert "by_recipient" in result
    assert "monthly_commission_trend" in result


@pytest.mark.asyncio
async def test_get_inquiry_analytics(mock_database):
    """Test getting inquiry analytics"""
    mock_database.inquiries.count_documents.return_value = 200
    mock_database.inquiries.aggregate.return_value.to_list.side_effect = [
        [{"_id": "pending", "count": 50}, {"_id": "responded", "count": 100}],
        [
            {"_id": "prop1", "count": 20},
            {"_id": "prop2", "count": 15}
        ],
        [
            {"_id": {"year": 2024, "month": 1}, "count": 30},
            {"_id": {"year": 2024, "month": 2}, "count": 35}
        ]
    ]

    result = await analytics_manager.get_inquiry_analytics(
        database=mock_database,
        start_date=None,
        end_date=None
    )

    assert result is not None
    assert "total_inquiries" in result
    assert "inquiries_this_month" in result
    assert "by_status" in result
    assert "monthly_inquiry_trend" in result


@pytest.mark.asyncio
async def test_get_dashboard_analytics(mock_database):
    """Test getting combined dashboard analytics"""
    # Mock all aggregation calls
    mock_database.properties.count_documents.return_value = 100
    mock_database.users.count_documents.return_value = 500
    mock_database.inquiries.count_documents.return_value = 200

    mock_database.properties.aggregate.return_value.to_list.side_effect = [
        [{"_id": "apartment", "count": 50}],
        [{"_id": "Mumbai", "count": 40}],
        [{"price": 5000000}],
        [{"_id": None, "avg_price": 6000000}],
        [{"_id": {"year": 2024, "month": 1}, "count": 10}],
        [{"_id": {"year": 2024, "month": 1}, "avg_price": 5500000}],
        [{"price": 5000000}]
    ]

    mock_database.users.aggregate.return_value.to_list.side_effect = [
        [{"_id": "admin", "count": 10}],
        [{"_id": "Mumbai", "count": 200}],
        [{"_id": {"year": 2024, "month": 1}, "count": 50}]
    ]

    mock_database.commissions.aggregate.return_value.to_list.side_effect = [
        [{"_id": None, "total": 1000000}],
        [{"_id": None, "total": 100000}],
        [{"_id": None, "total": 800000}],
        [{"_id": "user1", "total": 500000, "count": 10}],
        [{"_id": "property_sale", "total": 600000}],
        [{"_id": {"year": 2024, "month": 1}, "total": 80000}],
        [{"_id": None, "avg": 50000}]
    ]

    mock_database.inquiries.aggregate.return_value.to_list.side_effect = [
        [{"_id": "pending", "count": 50}],
        [{"_id": "prop1", "count": 20}],
        [{"_id": {"year": 2024, "month": 1}, "count": 30}]
    ]

    result = await analytics_manager.get_dashboard_analytics(
        database=mock_database,
        start_date=None,
        end_date=None
    )

    assert result is not None
    assert "property_analytics" in result
    assert "user_analytics" in result
    assert "revenue_analytics" in result
    assert "commission_analytics" in result
    assert "inquiry_analytics" in result
    assert "generated_at" in result


@pytest.mark.asyncio
async def test_analytics_caching(mock_database):
    """Test that analytics results are cached"""
    mock_database.properties.count_documents.return_value = 100
    mock_database.properties.aggregate.return_value.to_list.return_value = []

    # First call should hit database
    result1 = await analytics_manager.get_property_analytics(
        database=mock_database,
        start_date=None,
        end_date=None
    )

    # Second call should use cache (but we can't easily test this without actual Redis)
    # This test verifies the structure is correct
    assert result1 is not None
    assert "total_properties" in result1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
