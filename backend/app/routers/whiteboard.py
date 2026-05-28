"""
Whiteboard Router
Handles collaborative whiteboard endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional

from app.database import get_db
from app.schemas import (
    WhiteboardCreate,
    WhiteboardUpdate,
    WhiteboardResponse,
    WhiteboardListResponse,
    WhiteboardItemCreate,
    WhiteboardItemUpdate,
    WhiteboardItemResponse,
    WhiteboardShareCreate,
    WhiteboardShareResponse,
    WhiteboardPermission
)
from app.whiteboard import whiteboard_manager
from app.auth import get_current_user
from app.cache import get_from_cache, set_in_cache, generate_cache_key, invalidate_cache_pattern
from app.feature_flags import require_feature_flag

router = APIRouter(prefix="/api/whiteboards", tags=["whiteboards"])


# ========== Whiteboard Endpoints ==========

@router.post("", response_model=WhiteboardResponse, status_code=status.HTTP_201_CREATED)
@require_feature_flag("whiteboard_enabled")
async def create_whiteboard(
    whiteboard: WhiteboardCreate,
    database=Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Create a new whiteboard"""
    try:
        result = await whiteboard_manager.create_whiteboard(
            whiteboard_data=whiteboard.dict(),
            owner_id=str(current_user.get("_id")),
            database=database
        )
        return WhiteboardResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("", response_model=List[WhiteboardListResponse])
@require_feature_flag("whiteboard_enabled")
async def list_whiteboards(
    is_public: Optional[bool] = None,
    tags: Optional[str] = None,
    database=Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """List whiteboards accessible to current user"""
    try:
        tag_list = tags.split(",") if tags else None
        whiteboards = await whiteboard_manager.list_whiteboards(
            user_id=str(current_user.get("_id")),
            is_public=is_public,
            tags=tag_list,
            database=database
        )
        return [WhiteboardListResponse(**wb) for wb in whiteboards]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{whiteboard_id}", response_model=WhiteboardResponse)
@require_feature_flag("whiteboard_enabled")
async def get_whiteboard(
    whiteboard_id: str,
    database=Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get a specific whiteboard"""
    try:
        whiteboard = await whiteboard_manager.get_whiteboard(
            whiteboard_id=whiteboard_id,
            user_id=str(current_user.get("_id")),
            database=database
        )
        if not whiteboard:
            raise HTTPException(status_code=404, detail="Whiteboard not found")
        return WhiteboardResponse(**whiteboard)
    except ValueError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{whiteboard_id}", response_model=WhiteboardResponse)
@require_feature_flag("whiteboard_enabled")
async def update_whiteboard(
    whiteboard_id: str,
    update: WhiteboardUpdate,
    database=Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Update a whiteboard"""
    try:
        result = await whiteboard_manager.update_whiteboard(
            whiteboard_id=whiteboard_id,
            update_data=update.dict(exclude_unset=True),
            user_id=str(current_user.get("_id")),
            database=database
        )
        return WhiteboardResponse(**result)
    except ValueError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{whiteboard_id}")
@require_feature_flag("whiteboard_enabled")
async def delete_whiteboard(
    whiteboard_id: str,
    database=Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Delete a whiteboard"""
    try:
        result = await whiteboard_manager.delete_whiteboard(
            whiteboard_id=whiteboard_id,
            user_id=str(current_user.get("_id")),
            database=database
        )
        if not result:
            raise HTTPException(status_code=404, detail="Whiteboard not found")
        return {"message": "Whiteboard deleted successfully"}
    except ValueError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ========== Whiteboard Item Endpoints ==========

@router.post("/{whiteboard_id}/items", response_model=WhiteboardItemResponse, status_code=status.HTTP_201_CREATED)
@require_feature_flag("whiteboard_enabled")
async def add_item(
    whiteboard_id: str,
    item: WhiteboardItemCreate,
    database=Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Add an item to a whiteboard"""
    try:
        result = await whiteboard_manager.add_item(
            whiteboard_id=whiteboard_id,
            item_data=item.dict(),
            user_id=str(current_user.get("_id")),
            database=database
        )
        return WhiteboardItemResponse(**result)
    except ValueError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{whiteboard_id}/items/{item_id}", response_model=WhiteboardItemResponse)
@require_feature_flag("whiteboard_enabled")
async def update_item(
    whiteboard_id: str,
    item_id: str,
    update: WhiteboardItemUpdate,
    database=Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Update a whiteboard item"""
    try:
        result = await whiteboard_manager.update_item(
            item_id=item_id,
            update_data=update.dict(exclude_unset=True),
            user_id=str(current_user.get("_id")),
            database=database
        )
        return WhiteboardItemResponse(**result)
    except ValueError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{whiteboard_id}/items/{item_id}")
@require_feature_flag("whiteboard_enabled")
async def delete_item(
    whiteboard_id: str,
    item_id: str,
    database=Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Delete a whiteboard item"""
    try:
        result = await whiteboard_manager.delete_item(
            item_id=item_id,
            user_id=str(current_user.get("_id")),
            database=database
        )
        if not result:
            raise HTTPException(status_code=404, detail="Item not found")
        return {"message": "Item deleted successfully"}
    except ValueError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ========== Whiteboard Share Endpoints ==========

@router.post("/{whiteboard_id}/share", response_model=WhiteboardShareResponse, status_code=status.HTTP_201_CREATED)
@require_feature_flag("whiteboard_enabled")
async def share_whiteboard(
    whiteboard_id: str,
    share: WhiteboardShareCreate,
    database=Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Share a whiteboard with another user"""
    try:
        result = await whiteboard_manager.share_whiteboard(
            whiteboard_id=whiteboard_id,
            user_id=str(current_user.get("_id")),
            target_user_id=share.user_id,
            permission=share.permission,
            shared_by=str(current_user.get("_id")),
            database=database
        )
        return WhiteboardShareResponse(**result)
    except ValueError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{whiteboard_id}/share/{target_user_id}")
@require_feature_flag("whiteboard_enabled")
async def unshare_whiteboard(
    whiteboard_id: str,
    target_user_id: str,
    database=Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Remove share from a whiteboard"""
    try:
        result = await whiteboard_manager.unshare_whiteboard(
            whiteboard_id=whiteboard_id,
            user_id=str(current_user.get("_id")),
            target_user_id=target_user_id,
            database=database
        )
        if not result:
            raise HTTPException(status_code=404, detail="Share not found")
        return {"message": "Share removed successfully"}
    except ValueError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{whiteboard_id}/shares", response_model=List[WhiteboardShareResponse])
@require_feature_flag("whiteboard_enabled")
async def get_shares(
    whiteboard_id: str,
    database=Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get all shares for a whiteboard"""
    try:
        shares = await whiteboard_manager.get_shares(
            whiteboard_id=whiteboard_id,
            user_id=str(current_user.get("_id")),
            database=database
        )
        return [WhiteboardShareResponse(**s) for s in shares]
    except ValueError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
