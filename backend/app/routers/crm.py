"""
CRM Router
Endpoints for CRM integration
"""
from fastapi import APIRouter, Depends, HTTPException, status, Header
from app.database import get_database
from app.crm import CRMIntegration, LeadStatus, LeadSource, InteractionType
from app.schemas import (
    LeadCreate, LeadUpdate, LeadResponse, InteractionCreate,
    LeadAssign, PipelineSummary, PaginatedResponse
)
from app.auth import decode_token
from app.feature_flags import require_feature_flag
from bson import ObjectId
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/crm", tags=["CRM"])


def get_current_user(authorization: str = Header(None)) -> dict:
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


# ========== Access control ==========
# admin/manager have full access to every lead; agents are limited to their own.
FULL_ACCESS_ROLES = {"admin", "manager"}
# Roles allowed to create leads.
CREATE_ROLES = {"admin", "manager", "agent"}


def require_roles(current_user: dict, allowed: set):
    """Raise 403 unless the user's role is in the allowed set."""
    if current_user.get("role") not in allowed:
        raise HTTPException(
            status_code=403,
            detail="You do not have permission to perform this action"
        )


def ensure_lead_access(current_user: dict, lead: dict):
    """Agents may only access leads assigned to them; admin/manager may access any."""
    if current_user.get("role") in FULL_ACCESS_ROLES:
        return
    if lead.get("assigned_to") != current_user.get("user_id"):
        raise HTTPException(
            status_code=403,
            detail="You can only access leads assigned to you"
        )


async def get_lead_or_404(crm, lead_id: str) -> dict:
    lead = await crm.leads.get_lead(lead_id)
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    return lead


async def user_exists(db, user_id: str) -> bool:
    """Check a user exists, tolerating both string and ObjectId _id storage."""
    candidate_ids = [user_id]
    try:
        candidate_ids.append(ObjectId(user_id))
    except Exception:
        pass
    user = await db.users.find_one({"_id": {"$in": candidate_ids}})
    return user is not None


@router.post("/leads", response_model=LeadResponse)
@require_feature_flag("crm_system")
async def create_lead(
    lead_data: LeadCreate,
    auto_assign: bool = False,
    authorization: str = Header(None),
    db = Depends(get_database)
):
    """Create a new CRM lead.

    Access: admin, manager, or agent.
    - admin/manager may assign the lead to any user.
    - agents may only create leads assigned to themselves.
    - pass ``auto_assign=true`` to auto-balance the lead across agents.
    """
    current_user = get_current_user(authorization)
    require_roles(current_user, CREATE_ROLES)

    crm = CRMIntegration(db)
    data = lead_data.dict()

    requested_assignee = data.get("assigned_to")
    if (
        requested_assignee
        and current_user["role"] not in FULL_ACCESS_ROLES
        and requested_assignee != current_user["user_id"]
    ):
        raise HTTPException(
            status_code=403,
            detail="Only admins or managers can assign leads to other users"
        )

    lead_id = await crm.leads.create_lead(data)

    # Resolve the final assignment.
    if auto_assign:
        assignee = await crm.auto_assign_lead(lead_id, assigned_by=current_user["user_id"])
    elif requested_assignee:
        assignee = requested_assignee
    elif current_user["role"] == "agent":
        await crm.leads.assign_lead(lead_id, current_user["user_id"], assigned_by=current_user["user_id"])
        assignee = current_user["user_id"]
    else:
        assignee = None

    await crm.activities.log_activity(
        current_user["user_id"], "create_lead", "lead", lead_id, {"assigned_to": assignee}
    )

    lead = await crm.leads.get_lead(lead_id)
    return LeadResponse(**lead)


@router.get("/leads/{lead_id}", response_model=LeadResponse)
@require_feature_flag("crm_system")
async def get_lead(
    lead_id: str,
    authorization: str = Header(None),
    db = Depends(get_database)
):
    """Get a specific lead"""
    current_user = get_current_user(authorization)
    
    crm = CRMIntegration(db)
    lead = await get_lead_or_404(crm, lead_id)
    ensure_lead_access(current_user, lead)

    return LeadResponse(**lead)


@router.put("/leads/{lead_id}", response_model=LeadResponse)
@require_feature_flag("crm_system")
async def update_lead(
    lead_id: str,
    lead_update: LeadUpdate,
    authorization: str = Header(None),
    db = Depends(get_database)
):
    """Update a lead"""
    current_user = get_current_user(authorization)
    
    crm = CRMIntegration(db)
    lead = await get_lead_or_404(crm, lead_id)
    ensure_lead_access(current_user, lead)

    update_data = lead_update.dict(exclude_unset=True)
    if "assigned_to" in update_data and current_user["role"] not in FULL_ACCESS_ROLES:
        raise HTTPException(
            status_code=403,
            detail="Only admins or managers can reassign leads"
        )

    await crm.leads.update_lead(lead_id, update_data)
    lead = await crm.leads.get_lead(lead_id)
    return LeadResponse(**lead)


@router.delete("/leads/{lead_id}")
@require_feature_flag("crm_system")
async def delete_lead(
    lead_id: str,
    authorization: str = Header(None),
    db = Depends(get_database)
):
    """Delete a lead (admin/manager only)"""
    current_user = get_current_user(authorization)
    require_roles(current_user, FULL_ACCESS_ROLES)
    
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
    authorization: str = Header(None),
    db = Depends(get_database)
):
    """List leads with filters. Agents only ever see leads assigned to them."""
    current_user = get_current_user(authorization)
    if current_user["role"] not in FULL_ACCESS_ROLES:
        assigned_to = current_user["user_id"]
    
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
    authorization: str = Header(None),
    db = Depends(get_database)
):
    """Add an interaction to a lead"""
    current_user = get_current_user(authorization)
    
    crm = CRMIntegration(db)
    lead = await get_lead_or_404(crm, lead_id)
    ensure_lead_access(current_user, lead)

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
    authorization: str = Header(None),
    db = Depends(get_database)
):
    """Update lead status in pipeline"""
    current_user = get_current_user(authorization)
    
    crm = CRMIntegration(db)
    lead = await get_lead_or_404(crm, lead_id)
    ensure_lead_access(current_user, lead)

    await crm.leads.update_lead_status(lead_id, status)
    return {"message": f"Lead status updated to {status}"}


@router.post("/leads/{lead_id}/assign", response_model=LeadResponse)
@require_feature_flag("crm_system")
async def assign_lead(
    lead_id: str,
    assignment: LeadAssign,
    authorization: str = Header(None),
    db = Depends(get_database)
):
    """Assign a lead to a specific user (admin/manager only)."""
    current_user = get_current_user(authorization)
    require_roles(current_user, FULL_ACCESS_ROLES)

    crm = CRMIntegration(db)
    await get_lead_or_404(crm, lead_id)

    if not await user_exists(db, assignment.assigned_to):
        raise HTTPException(status_code=404, detail="Assignee user not found")

    await crm.leads.assign_lead(lead_id, assignment.assigned_to, assigned_by=current_user["user_id"])
    await crm.activities.log_activity(
        current_user["user_id"], "assign_lead", "lead", lead_id,
        {"assigned_to": assignment.assigned_to}
    )

    lead = await crm.leads.get_lead(lead_id)
    return LeadResponse(**lead)


@router.post("/leads/{lead_id}/auto-assign", response_model=LeadResponse)
@require_feature_flag("crm_system")
async def auto_assign_lead(
    lead_id: str,
    authorization: str = Header(None),
    db = Depends(get_database)
):
    """Auto-assign a lead to the least-loaded eligible agent (admin/manager only)."""
    current_user = get_current_user(authorization)
    require_roles(current_user, FULL_ACCESS_ROLES)

    crm = CRMIntegration(db)
    await get_lead_or_404(crm, lead_id)

    assignee = await crm.auto_assign_lead(lead_id, assigned_by=current_user["user_id"])
    if not assignee:
        raise HTTPException(
            status_code=409,
            detail="No eligible agent available for auto-assignment"
        )

    lead = await crm.leads.get_lead(lead_id)
    return LeadResponse(**lead)


@router.delete("/leads/{lead_id}/assign", response_model=LeadResponse)
@require_feature_flag("crm_system")
async def unassign_lead(
    lead_id: str,
    authorization: str = Header(None),
    db = Depends(get_database)
):
    """Remove the current assignee from a lead (admin/manager only)."""
    current_user = get_current_user(authorization)
    require_roles(current_user, FULL_ACCESS_ROLES)

    crm = CRMIntegration(db)
    await get_lead_or_404(crm, lead_id)

    await crm.leads.unassign_lead(lead_id, unassigned_by=current_user["user_id"])
    await crm.activities.log_activity(
        current_user["user_id"], "unassign_lead", "lead", lead_id, {}
    )

    lead = await crm.leads.get_lead(lead_id)
    return LeadResponse(**lead)


@router.get("/pipeline/summary", response_model=PipelineSummary)
@require_feature_flag("crm_pipeline")
async def get_pipeline_summary(
    authorization: str = Header(None),
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
    authorization: str = Header(None),
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
