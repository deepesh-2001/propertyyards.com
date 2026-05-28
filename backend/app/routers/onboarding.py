"""
Onboarding & Offboarding Router
Handles employee onboarding, offboarding, EPFO/ESI endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional
from datetime import datetime

from app.database import get_db
from app.schemas import (
    EmployeeOnboardingCreate,
    EmployeeOnboardingUpdate,
    EmployeeOnboardingResponse,
    EmployeeOffboardingCreate,
    EmployeeOffboardingUpdate,
    EmployeeOffboardingResponse,
    OnboardingAnalytics,
    OffboardingAnalytics,
    OnboardingStatus,
    OffboardingStatus,
    EPFODetails,
    ESIDetails,
    EPFOStatus
)
from app.onboarding import onboarding_manager, offboarding_manager, epfo_manager
from app.auth import get_current_user
from app.cache import get_from_cache, set_in_cache, generate_cache_key
from app.feature_flags import require_feature_flag

router = APIRouter(prefix="/api/onboarding", tags=["onboarding"])


# ========== Onboarding Endpoints ==========

@router.post("/onboardings", response_model=EmployeeOnboardingResponse, status_code=status.HTTP_201_CREATED)
@require_feature_flag("onboarding_enabled")
async def create_onboarding(
    onboarding: EmployeeOnboardingCreate,
    database=Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Create a new employee onboarding"""
    try:
        result = await onboarding_manager.create_onboarding(onboarding.dict(), database)
        return EmployeeOnboardingResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/onboardings/{onboarding_id}", response_model=EmployeeOnboardingResponse)
async def get_onboarding(
    onboarding_id: str,
    database=Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get a specific onboarding"""
    onboarding = await onboarding_manager.get_onboarding(onboarding_id, database)
    if not onboarding:
        raise HTTPException(status_code=404, detail="Onboarding not found")
    return EmployeeOnboardingResponse(**onboarding)


@router.get("/onboardings/employees/{employee_id}", response_model=List[EmployeeOnboardingResponse])
async def get_employee_onboardings(
    employee_id: str,
    database=Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get all onboardings for an employee"""
    onboardings = await onboarding_manager.get_employee_onboardings(employee_id, database)
    return [EmployeeOnboardingResponse(**o) for o in onboardings]


@router.get("/onboardings", response_model=List[EmployeeOnboardingResponse])
async def list_onboardings(
    status: Optional[OnboardingStatus] = None,
    department: Optional[str] = None,
    database=Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """List all onboardings with optional filters"""
    query = {}
    if status:
        query["status"] = status
    if department:
        query["department"] = department

    cursor = database.employee_onboardings.find(query).sort("created_at", -1)
    onboardings = await cursor.to_list(length=100)

    for onboarding in onboardings:
        onboarding["id"] = str(onboarding["_id"])
        del onboarding["_id"]

    return [EmployeeOnboardingResponse(**o) for o in onboardings]


@router.put("/onboardings/{onboarding_id}", response_model=EmployeeOnboardingResponse)
async def update_onboarding(
    onboarding_id: str,
    update: EmployeeOnboardingUpdate,
    database=Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Update an onboarding"""
    try:
        result = await onboarding_manager.update_onboarding(
            onboarding_id,
            update.dict(exclude_unset=True),
            database
        )
        return EmployeeOnboardingResponse(**result)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/onboardings/{onboarding_id}/approve", response_model=EmployeeOnboardingResponse)
async def approve_onboarding(
    onboarding_id: str,
    database=Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Approve an onboarding"""
    try:
        result = await onboarding_manager.approve_onboarding(
            onboarding_id,
            str(current_user.get("_id")),
            database
        )
        return EmployeeOnboardingResponse(**result)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/onboardings/{onboarding_id}/reject", response_model=EmployeeOnboardingResponse)
async def reject_onboarding(
    onboarding_id: str,
    rejection_reason: str,
    database=Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Reject an onboarding"""
    try:
        result = await onboarding_manager.reject_onboarding(
            onboarding_id,
            rejection_reason,
            database
        )
        return EmployeeOnboardingResponse(**result)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/onboardings/analytics", response_model=OnboardingAnalytics)
async def get_onboarding_analytics(
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    database=Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get onboarding analytics"""
    try:
        # Check cache (5 minutes for analytics)
        cache_key = generate_cache_key(
            "onboarding_analytics",
            start_date.isoformat() if start_date else "none",
            end_date.isoformat() if end_date else "none"
        )
        cached_result = await get_from_cache(cache_key)
        if cached_result:
            return OnboardingAnalytics(**cached_result)

        analytics = await onboarding_manager.get_onboarding_analytics(
            database,
            start_date=start_date,
            end_date=end_date
        )

        # Cache the result
        await set_in_cache(cache_key, analytics, ttl=300)

        return OnboardingAnalytics(**analytics)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ========== Offboarding Endpoints ==========

@router.post("/offboardings", response_model=EmployeeOffboardingResponse, status_code=status.HTTP_201_CREATED)
async def create_offboarding(
    offboarding: EmployeeOffboardingCreate,
    database=Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Create a new employee offboarding"""
    try:
        result = await offboarding_manager.create_offboarding(offboarding.dict(), database)
        return EmployeeOffboardingResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/offboardings/{offboarding_id}", response_model=EmployeeOffboardingResponse)
async def get_offboarding(
    offboarding_id: str,
    database=Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get a specific offboarding"""
    offboarding = await offboarding_manager.get_offboarding(offboarding_id, database)
    if not offboarding:
        raise HTTPException(status_code=404, detail="Offboarding not found")
    return EmployeeOffboardingResponse(**offboarding)


@router.get("/offboardings/employees/{employee_id}", response_model=List[EmployeeOffboardingResponse])
async def get_employee_offboardings(
    employee_id: str,
    database=Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get all offboardings for an employee"""
    offboardings = await offboarding_manager.get_employee_offboardings(employee_id, database)
    return [EmployeeOffboardingResponse(**o) for o in offboardings]


@router.get("/offboardings", response_model=List[EmployeeOffboardingResponse])
async def list_offboardings(
    status: Optional[OffboardingStatus] = None,
    department: Optional[str] = None,
    database=Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """List all offboardings with optional filters"""
    query = {}
    if status:
        query["status"] = status
    if department:
        query["department"] = department

    cursor = database.employee_offboardings.find(query).sort("created_at", -1)
    offboardings = await cursor.to_list(length=100)

    for offboarding in offboardings:
        offboarding["id"] = str(offboarding["_id"])
        del offboarding["_id"]

    return [EmployeeOffboardingResponse(**o) for o in offboardings]


@router.put("/offboardings/{offboarding_id}", response_model=EmployeeOffboardingResponse)
async def update_offboarding(
    offboarding_id: str,
    update: EmployeeOffboardingUpdate,
    database=Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Update an offboarding"""
    try:
        result = await offboarding_manager.update_offboarding(
            offboarding_id,
            update.dict(exclude_unset=True),
            database
        )
        return EmployeeOffboardingResponse(**result)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/offboardings/{offboarding_id}/approve", response_model=EmployeeOffboardingResponse)
async def approve_offboarding(
    offboarding_id: str,
    database=Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Approve an offboarding"""
    try:
        result = await offboarding_manager.approve_offboarding(
            offboarding_id,
            str(current_user.get("_id")),
            database
        )
        return EmployeeOffboardingResponse(**result)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/offboardings/{offboarding_id}/complete", response_model=EmployeeOffboardingResponse)
async def complete_offboarding(
    offboarding_id: str,
    database=Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Complete an offboarding"""
    try:
        result = await offboarding_manager.complete_offboarding(offboarding_id, database)
        return EmployeeOffboardingResponse(**result)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/offboardings/analytics", response_model=OffboardingAnalytics)
async def get_offboarding_analytics(
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    database=Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get offboarding analytics"""
    try:
        # Check cache (5 minutes for analytics)
        cache_key = generate_cache_key(
            "offboarding_analytics",
            start_date.isoformat() if start_date else "none",
            end_date.isoformat() if end_date else "none"
        )
        cached_result = await get_from_cache(cache_key)
        if cached_result:
            return OffboardingAnalytics(**cached_result)

        analytics = await offboarding_manager.get_offboarding_analytics(
            database,
            start_date=start_date,
            end_date=end_date
        )

        # Cache the result
        await set_in_cache(cache_key, analytics, ttl=300)

        return OffboardingAnalytics(**analytics)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ========== EPFO/ESI Endpoints ==========

@router.post("/epfo/register")
@require_feature_flag("epfo_integration")
async def register_epfo(
    employee_id: str,
    epfo_details: EPFODetails,
    database=Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Register employee with EPFO"""
    try:
        result = await epfo_manager.register_epfo(employee_id, epfo_details, database)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/epfo/{employee_id}")
async def get_epfo_details(
    employee_id: str,
    database=Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get EPFO details for an employee"""
    epfo = await epfo_manager.get_epfo_details(employee_id, database)
    if not epfo:
        raise HTTPException(status_code=404, detail="EPFO record not found")
    return epfo


@router.post("/epfo/{employee_id}/withdraw")
async def withdraw_epfo(
    employee_id: str,
    database=Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Process EPFO withdrawal"""
    try:
        result = await epfo_manager.withdraw_epfo(employee_id, database)
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/epfo/{employee_id}/transfer")
async def transfer_epfo(
    employee_id: str,
    new_establishment_id: str,
    database=Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Transfer EPFO account to new establishment"""
    try:
        result = await epfo_manager.transfer_epfo(employee_id, new_establishment_id, database)
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/esi/register")
async def register_esi(
    employee_id: str,
    esi_details: ESIDetails,
    database=Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Register employee with ESI"""
    try:
        result = await epfo_manager.register_esi(employee_id, esi_details, database)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/esi/{employee_id}")
async def get_esi_details(
    employee_id: str,
    database=Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get ESI details for an employee"""
    esi = await epfo_manager.get_esi_details(employee_id, database)
    if not esi:
        raise HTTPException(status_code=404, detail="ESI record not found")
    return esi
