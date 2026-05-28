"""
Feature Flags Router
Handles feature flag management endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional, Dict, Any
from pydantic import BaseModel

from app.database import get_db
from app.feature_flags import feature_flag_manager
from app.auth import get_current_user

router = APIRouter(prefix="/api/feature-flags", tags=["feature-flags"])


# Schemas
class FeatureFlagUpdate(BaseModel):
    is_enabled: bool
    enabled_for_roles: Optional[List[str]] = None
    enabled_for_users: Optional[List[str]] = None
    percentage: Optional[float] = None
    metadata: Optional[Dict[str, Any]] = None


class FeatureFlagResponse(BaseModel):
    key: str
    name: str
    description: str
    is_enabled: bool
    enabled_for_roles: List[str]
    enabled_for_users: List[str]
    percentage: Optional[float]
    metadata: Dict[str, Any]


# ========== Admin Endpoints ==========

@router.get("", response_model=List[FeatureFlagResponse])
async def get_all_feature_flags(
    database=Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get all feature flags (admin only)"""
    # Check if user is admin
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")

    try:
        flags = await feature_flag_manager.get_all_flags(database)
        return [FeatureFlagResponse(**f) for f in flags]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{flag_key}", response_model=FeatureFlagResponse)
async def get_feature_flag(
    flag_key: str,
    database=Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get a specific feature flag (admin only)"""
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")

    try:
        flag = await feature_flag_manager.get_flag(flag_key, database)
        if not flag:
            raise HTTPException(status_code=404, detail="Feature flag not found")
        return FeatureFlagResponse(**flag.to_dict())
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{flag_key}", response_model=FeatureFlagResponse)
async def update_feature_flag(
    flag_key: str,
    update: FeatureFlagUpdate,
    database=Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Update a feature flag (admin only)"""
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")

    try:
        flag = await feature_flag_manager.set_flag(
            key=flag_key,
            is_enabled=update.is_enabled,
            enabled_for_roles=update.enabled_for_roles,
            enabled_for_users=update.enabled_for_users,
            percentage=update.percentage,
            metadata=update.metadata,
            database=database
        )
        return FeatureFlagResponse(**flag.to_dict())
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/initialize")
async def initialize_feature_flags(
    database=Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Initialize default feature flags in database (admin only)"""
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")

    try:
        await feature_flag_manager.initialize_default_flags(database)
        return {"message": "Feature flags initialized successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ========== UI Endpoints ==========

@router.get("/ui/flags")
async def get_ui_feature_flags(
    database=Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get enabled feature flags for UI (based on user role)"""
    try:
        user_id = str(current_user.get("_id"))
        user_role = current_user.get("role")

        flags = await feature_flag_manager.get_flags_for_ui(
            user_id=user_id,
            user_role=user_role,
            database=database
        )
        return flags
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/ui/check/{flag_key}")
async def check_feature_flag(
    flag_key: str,
    database=Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Check if a specific feature flag is enabled for current user"""
    try:
        user_id = str(current_user.get("_id"))
        user_role = current_user.get("role")

        is_enabled = await feature_flag_manager.is_enabled(
            key=flag_key,
            user_id=user_id,
            user_role=user_role,
            database=database
        )
        return {"key": flag_key, "enabled": is_enabled}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
