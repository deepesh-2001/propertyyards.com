"""
CRM Router
Endpoints for CRM integration
"""
from fastapi import APIRouter, Depends, HTTPException, status
from app.database import get_database
from app.crm import CRMIntegration, LeadStatus, LeadSource, InteractionType
from app.schemas import (
    LeadCreate, LeadUpdate, LeadResponse, InteractionCreate,
    PipelineSummary, PaginatedResponse
)
from app.auth import decode_token
from app.feature_flags import require_feature_flag
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/crm", tags=["CRM"])


def get_current_user(authorization: str = None) -> dict:
    """Extract current user from authorization header"""
    if not authorization:
        raise HTTPException(status_code=401, detail="Not authenticated")

    try:
        token = authorization.split(" ")[1]
        token_data = decode_token(token)
        if token_data:
            return {"user_id": token_data.user_id, "email": token_data.email, "role": token_data.role}
    except Exception:
        pass

    raise HTTPException(status_code=401, detail="Invalid token")


@router.post("/leads", response_model=LeadResponse)
@require_feature_flag("crm_system")
async def create_lead(
    lead_data: LeadCreate,
    authorization: str = None,
    db = Depends(get_database)
):
    """Create a new CRM lead"""
    current_user = get_current_user(authorization)
    
    crm = CRMIntegration(db)
    lead_id = await crm.leads.create_lead(lead_data.dict())
    
    lead = await crm.leads.get_lead(lead_id)
    return LeadResponse(**lead)


@router.get("/leads/{lead_id}", response_model=LeadResponse)
@require_feature_flag("crm_system")
async def get_lead(
    lead_id: str,
    authorization: str = None,
    db = Depends(get_database)
):
    """Get a specific lead"""
    current_user = get_current_user(authorization)
    
    crm = CRMIntegration(db)
    lead = await crm.leads.get_lead(lead_id)
    
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    
    return LeadResponse(**lead)


@router.put("/leads/{lead_id}", response_model=LeadResponse)
@require_feature_flag("crm_system")
async def update_lead(
    lead_id: str,
    lead_update: LeadUpdate,
    authorization: str = None,
    db = Depends(get_database)
):
    """Update a lead"""
    current_user = get_current_user(authorization)
    
    crm = CRMIntegration(db)
    updated = await crm.leads.update_lead(lead_id, lead_update.dict(exclude_unset=True))
    
    if not updated:
        raise HTTPException(status_code=404, detail="Lead not found")
    
    lead = await crm.leads.get_lead(lead_id)
    return LeadResponse(**lead)


@router.delete("/leads/{lead_id}")
@require_feature_flag("crm_system")
async def delete_lead(
    lead_id: str,
    authorization: str = None,
    db = Depends(get_database)
):
    """Delete a lead"""
    current_user = get_current_user(authorization)
    
    crm = CRMIntegration(db)
    deleted = await crm.leads.delete_lead(lead_id)
    
    if not deleted:
        raise HTTPException(status_code=404, detail="Lead not found")
    
    return {"message": "Lead deleted successfully"}


@router.get("/leads", response_model=PaginatedResponse)
@require_feature_flag("crm_system")
async def list_leads(
    status: LeadStatus = None,
    source: LeadSource = None,
    assigned_to: str = None,
    page: int = 1,
    limit: int = 50,
    authorization: str = None,
    db = Depends(get_database)
):
    """List leads with filters"""
    current_user = get_current_user(authorization)
    
    crm = CRMIntegration(db)
    leads = await crm.leads.list_leads(
        status=status,
        source=source,
        assigned_to=assigned_to,
        skip=(page - 1) * limit,
        limit=limit
    )
    
    # Get total count
    query_filter = {}
    if status:
        query_filter["status"] = status
    if source:
        query_filter["source"] = source
    if assigned_to:
        query_filter["assigned_to"] = assigned_to
    
    total = await db.crm_leads.count_documents(query_filter)
    
    return {
        "items": leads,
        "total": total,
        "page": page,
        "limit": limit,
        "pages": (total + limit - 1) // limit
    }


@router.post("/leads/{lead_id}/interactions")
@require_feature_flag("crm_system")
async def add_interaction(
    lead_id: str,
    interaction: InteractionCreate,
    authorization: str = None,
    db = Depends(get_database)
):
    """Add an interaction to a lead"""
    current_user = get_current_user(authorization)
    
    crm = CRMIntegration(db)
    added = await crm.leads.add_interaction(
        lead_id,
        interaction.interaction_type,
        interaction.notes,
        current_user["user_id"]
    )
    
    if not added:
        raise HTTPException(status_code=404, detail="Lead not found")
    
    return {"message": "Interaction added successfully"}


@router.put("/leads/{lead_id}/status")
@require_feature_flag("crm_pipeline")
async def update_lead_status(
    lead_id: str,
    status: LeadStatus,
    authorization: str = None,
    db = Depends(get_database)
):
    """Update lead status in pipeline"""
    current_user = get_current_user(authorization)
    
    crm = CRMIntegration(db)
    updated = await crm.leads.update_lead_status(lead_id, status)
    
    if not updated:
        raise HTTPException(status_code=404, detail="Lead not found")
    
    return {"message": f"Lead status updated to {status}"}


@router.get("/pipeline/summary", response_model=PipelineSummary)
@require_feature_flag("crm_pipeline")
async def get_pipeline_summary(
    authorization: str = None,
    db = Depends(get_database)
):
    """Get CRM pipeline summary"""
    current_user = get_current_user(authorization)
    
    crm = CRMIntegration(db)
    summary = await crm.leads.get_pipeline_summary()
    
    return PipelineSummary(**summary)


@router.get("/activities")
@require_feature_flag("crm_system")
async def get_user_activities(
    page: int = 1,
    limit: int = 50,
    authorization: str = None,
    db = Depends(get_database)
):
    """Get CRM activities for current user"""
    current_user = get_current_user(authorization)
    
    crm = CRMIntegration(db)
    activities = await crm.activities.get_user_activities(
        current_user["user_id"],
        skip=(page - 1) * limit,
        limit=limit
    )
    
    total = await db.crm_activities.count_documents({"user_id": current_user["user_id"]})
    
    return {
        "items": activities,
        "total": total,
        "page": page,
        "limit": limit,
        "pages": (total + limit - 1) // limit
    }
