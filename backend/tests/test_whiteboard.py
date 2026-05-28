"""
Tests for Whiteboard Module
"""
import pytest
import sys
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock

# Add backend to path
sys.path.insert(0, 'C:/Users/deepe/PyCharmMiscProject/housing_platform/backend')

from app.whiteboard import whiteboard_manager
from app.schemas import WhiteboardItemType, WhiteboardPermission


@pytest.fixture
def mock_database():
    """Mock database fixture"""
    db = MagicMock()
    db.whiteboards = AsyncMock()
    db.whiteboard_items = AsyncMock()
    db.whiteboard_shares = AsyncMock()
    db.users = AsyncMock()
    return db


@pytest.fixture
def sample_user_id():
    """Sample user ID"""
    return "507f1f77bcf86cd799439011"


@pytest.fixture
def sample_whiteboard_id():
    """Sample whiteboard ID"""
    return "507f1f77bcf86cd799439012"


@pytest.fixture
def sample_item_id():
    """Sample item ID"""
    return "507f1f77bcf86cd799439013"


@pytest.mark.asyncio
async def test_create_whiteboard(mock_database, sample_user_id):
    """Test creating a whiteboard"""
    whiteboard_data = {
        "title": "Test Whiteboard",
        "description": "Test description",
        "background_color": "#ffffff",
        "grid_enabled": True,
        "is_public": False,
        "tags": ["test"]
    }

    mock_database.whiteboards.insert_one.return_value = MagicMock(inserted_id="test_id")

    result = await whiteboard_manager.create_whiteboard(
        whiteboard_data=whiteboard_data,
        owner_id=sample_user_id,
        database=mock_database
    )

    assert result["title"] == "Test Whiteboard"
    assert result["owner_id"] == sample_user_id
    assert "id" in result
    assert "created_at" in result


@pytest.mark.asyncio
async def test_get_whiteboard(mock_database, sample_whiteboard_id, sample_user_id):
    """Test getting a whiteboard"""
    mock_whiteboard = {
        "_id": sample_whiteboard_id,
        "title": "Test Whiteboard",
        "owner_id": sample_user_id,
        "is_public": False,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }

    mock_database.whiteboards.find_one.return_value = mock_whiteboard
    mock_database.whiteboard_items.find.return_value.to_list.return_value = []

    result = await whiteboard_manager.get_whiteboard(
        whiteboard_id=sample_whiteboard_id,
        user_id=sample_user_id,
        database=mock_database
    )

    assert result is not None
    assert result["title"] == "Test Whiteboard"
    assert result["id"] == sample_whiteboard_id


@pytest.mark.asyncio
async def test_add_item(mock_database, sample_whiteboard_id, sample_user_id):
    """Test adding an item to a whiteboard"""
    item_data = {
        "item_type": WhiteboardItemType.TEXT,
        "x": 100,
        "y": 100,
        "content": "Test text",
        "color": "#000000"
    }

    mock_database.whiteboard_items.insert_one.return_value = MagicMock(inserted_id="item_id")
    mock_database.whiteboards.update_one.return_value = MagicMock(modified_count=1)

    result = await whiteboard_manager.add_item(
        whiteboard_id=sample_whiteboard_id,
        item_data=item_data,
        user_id=sample_user_id,
        database=mock_database
    )

    assert result["item_type"] == WhiteboardItemType.TEXT
    assert result["x"] == 100
    assert result["y"] == 100
    assert result["content"] == "Test text"


@pytest.mark.asyncio
async def test_share_whiteboard(mock_database, sample_whiteboard_id, sample_user_id):
    """Test sharing a whiteboard"""
    target_user_id = "507f1f77bcf86cd799439014"

    mock_database.whiteboard_shares.find_one.return_value = None
    mock_database.whiteboard_shares.insert_one.return_value = MagicMock(inserted_id="share_id")

    result = await whiteboard_manager.share_whiteboard(
        whiteboard_id=sample_whiteboard_id,
        user_id=sample_user_id,
        target_user_id=target_user_id,
        permission=WhiteboardPermission.VIEW,
        shared_by=sample_user_id,
        database=mock_database
    )

    assert result["whiteboard_id"] == sample_whiteboard_id
    assert result["user_id"] == target_user_id
    assert result["permission"] == WhiteboardPermission.VIEW


@pytest.mark.asyncio
async def test_delete_whiteboard(mock_database, sample_whiteboard_id, sample_user_id):
    """Test deleting a whiteboard"""
    mock_whiteboard = {
        "_id": sample_whiteboard_id,
        "owner_id": sample_user_id,
        "title": "Test Whiteboard"
    }

    mock_database.whiteboards.find_one.return_value = mock_whiteboard
    mock_database.whiteboard_items.delete_many.return_value = MagicMock(deleted_count=1)
    mock_database.whiteboard_shares.delete_many.return_value = MagicMock(deleted_count=1)
    mock_database.whiteboards.delete_one.return_value = MagicMock(deleted_count=1)

    result = await whiteboard_manager.delete_whiteboard(
        whiteboard_id=sample_whiteboard_id,
        user_id=sample_user_id,
        database=mock_database
    )

    assert result is True


@pytest.mark.asyncio
async def test_permission_check_owner(mock_database, sample_whiteboard_id, sample_user_id):
    """Test permission check for owner"""
    mock_whiteboard = {
        "_id": sample_whiteboard_id,
        "owner_id": sample_user_id,
        "is_public": False
    }

    mock_database.whiteboards.find_one.return_value = mock_whiteboard

    has_permission = await whiteboard_manager._has_permission(
        whiteboard_id=sample_whiteboard_id,
        user_id=sample_user_id,
        required_permission="edit",
        database=mock_database
    )

    assert has_permission is True


@pytest.mark.asyncio
async def test_permission_check_public(mock_database, sample_whiteboard_id, sample_user_id):
    """Test permission check for public whiteboard"""
    mock_whiteboard = {
        "_id": sample_whiteboard_id,
        "owner_id": "other_user",
        "is_public": True
    }

    mock_database.whiteboards.find_one.return_value = mock_whiteboard

    has_permission = await whiteboard_manager._has_permission(
        whiteboard_id=sample_whiteboard_id,
        user_id=sample_user_id,
        required_permission="view",
        database=mock_database
    )

    assert has_permission is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
