"""
Property Onboarding Router
Handles easy property onboarding with multiple import methods
"""
from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional
from datetime import datetime

from app.database import get_db
from app.schemas import (
    QuickPropertyCreate,
    URLPropertyImport,
    TextPropertyImport,
    BulkPropertyImport,
    PropertyOnboardingUpdate,
    PropertyOnboardingResponse,
    PropertyOnboardingAnalytics,
    PropertyOnboardingSource,
    PropertyOnboardingStatus
)
from app.property_onboarding import property_onboarding_manager
from app.auth import get_current_user
from app.cache import get_from_cache, set_in_cache, generate_cache_key
from app.feature_flags import require_feature_flag

router = APIRouter(prefix="/api/property-onboarding", tags=["property-onboarding"])


@router.post("/quick", response_model=PropertyOnboardingResponse, status_code=status.HTTP_201_CREATED)
@require_feature_flag("property_onboarding")
async def create_quick_property(
    property_data: QuickPropertyCreate,
    database=Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Create property from quick form"""
    try:
        result = await property_onboarding_manager.create_quick_property(
            property_data,
            str(current_user.get("_id")),
            database
        )
        return PropertyOnboardingResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/import-url", response_model=PropertyOnboardingResponse, status_code=status.HTTP_201_CREATED)
@require_feature_flag("property_url_import")
async def import_from_url(
    import_data: URLPropertyImport,
    database=Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Import property from external URL"""
    try:
        result = await property_onboarding_manager.import_from_url(
            import_data,
            str(current_user.get("_id")),
            database
        )
        return PropertyOnboardingResponse(**result)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/import-text", response_model=PropertyOnboardingResponse, status_code=status.HTTP_201_CREATED)
@require_feature_flag("property_text_import")
async def import_from_text(
    import_data: TextPropertyImport,
    database=Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Extract property from text description"""
    try:
        result = await property_onboarding_manager.import_from_text(
            import_data,
            str(current_user.get("_id")),
            database
        )
        return PropertyOnboardingResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/bulk-import")
@require_feature_flag("property_bulk_import")
async def bulk_import(
    import_data: BulkPropertyImport,
    database=Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Bulk import properties from CSV/JSON data"""
    try:
        result = await property_onboarding_manager.bulk_import(
            import_data,
            str(current_user.get("_id")),
            database
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/onboardings/{onboarding_id}", response_model=PropertyOnboardingResponse)
async def get_onboarding(
    onboarding_id: str,
    database=Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get a specific property onboarding"""
    onboarding = await database.property_onboardings.find_one({"_id": onboarding_id})
    if not onboarding:
        raise HTTPException(status_code=404, detail="Onboarding not found")
    
    onboarding["id"] = str(onboarding["_id"])
    del onboarding["_id"]
    
    return PropertyOnboardingResponse(**onboarding)


@router.get("/onboardings", response_model=List[PropertyOnboardingResponse])
async def list_onboardings(
    source: Optional[PropertyOnboardingSource] = None,
    status: Optional[PropertyOnboardingStatus] = None,
    city: Optional[str] = None,
    database=Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """List property onboardings with filters"""
    query = {}
    if source:
        query["source"] = source
    if status:
        query["status"] = status
    if city:
        query["property_data.city"] = city

    cursor = database.property_onboardings.find(query).sort("created_at", -1)
    onboardings = await cursor.to_list(length=100)

    for onboarding in onboardings:
        onboarding["id"] = str(onboarding["_id"])
        del onboarding["_id"]

    return [PropertyOnboardingResponse(**o) for o in onboardings]


@router.put("/onboardings/{onboarding_id}", response_model=PropertyOnboardingResponse)
async def update_onboarding(
    onboarding_id: str,
    update: PropertyOnboardingUpdate,
    database=Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Update property onboarding status (approve/reject/publish)"""
    try:
        result = await property_onboarding_manager.update_onboarding(
            onboarding_id,
            update,
            str(current_user.get("_id")),
            database
        )
        return PropertyOnboardingResponse(**result)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/onboardings/analytics", response_model=PropertyOnboardingAnalytics)
async def get_onboarding_analytics(
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    database=Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get property onboarding analytics"""
    try:
        # Check cache (5 minutes for analytics)
        cache_key = generate_cache_key(
            "property_onboarding_analytics",
            start_date.isoformat() if start_date else "none",
            end_date.isoformat() if end_date else "none"
        )
        cached_result = await get_from_cache(cache_key)
        if cached_result:
            return PropertyOnboardingAnalytics(**cached_result)

        analytics = await property_onboarding_manager.get_onboarding_analytics(
            database,
            start_date=start_date,
            end_date=end_date
        )

        # Cache the result
        await set_in_cache(cache_key, analytics, ttl=300)

        return PropertyOnboardingAnalytics(**analytics)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/my-onboardings", response_model=List[PropertyOnboardingResponse])
async def get_my_onboardings(
    database=Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get onboardings submitted by current user"""
    query = {"submitted_by": str(current_user.get("_id"))}
    cursor = database.property_onboardings.find(query).sort("created_at", -1)
    onboardings = await cursor.to_list(length=50)

    for onboarding in onboardings:
        onboarding["id"] = str(onboarding["_id"])
        del onboarding["_id"]

    return [PropertyOnboardingResponse(**o) for o in onboardings]
