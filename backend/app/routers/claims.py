"""
Claims Router
"""
from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional

from app.database import get_db
from app.auth import get_current_user
from app.claims import claims_manager
from app.schemas import (
    ClaimCreate,
    ClaimResponse,
    ClaimResolution,
    ClaimAnalytics,
    ClaimStatus,
)

router = APIRouter(prefix="/api/claims", tags=["claims"])


# ── Create ────────────────────────────────────────────────────────────────────

@router.post("", response_model=ClaimResponse, status_code=status.HTTP_201_CREATED)
async def create_claim(
    payload: ClaimCreate,
    database=Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    try:
        record = await claims_manager.create_claim(payload.dict(), database)
        return ClaimResponse(**record)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ── Read ──────────────────────────────────────────────────────────────────────

@router.get("/{claim_id}", response_model=ClaimResponse)
async def get_claim(
    claim_id: str,
    database=Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    record = await database.claims.find_one({"_id": claim_id})
    if not record:
        raise HTTPException(status_code=404, detail="Claim not found")
    record["id"] = str(record["_id"])
    del record["_id"]
    return ClaimResponse(**record)


@router.get("/employees/{employee_id}/claims", response_model=List[ClaimResponse])
async def get_employee_claims(
    employee_id: str,
    claim_status: Optional[ClaimStatus] = None,
    database=Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    records = await claims_manager.get_employee_claims(employee_id, claim_status, database)
    return [ClaimResponse(**r) for r in records]


@router.get("", response_model=List[ClaimResponse])
async def list_claims(
    claim_status: Optional[ClaimStatus] = None,
    database=Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    query = {}
    if claim_status:
        query["status"] = claim_status
    cursor = database.claims.find(query).sort("created_at", -1)
    records = await cursor.to_list(length=500)
    for r in records:
        r["id"] = str(r["_id"])
        del r["_id"]
    return [ClaimResponse(**r) for r in records]


# ── Assign ────────────────────────────────────────────────────────────────────

@router.put("/{claim_id}/assign", response_model=ClaimResponse)
async def assign_claim(
    claim_id: str,
    assigned_to: str,
    database=Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    try:
        record = await claims_manager.assign_claim(claim_id, assigned_to, database)
        return ClaimResponse(**record)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ── Resolve ───────────────────────────────────────────────────────────────────

@router.put("/{claim_id}/resolve", response_model=ClaimResponse)
async def resolve_claim(
    claim_id: str,
    resolution: ClaimResolution,
    database=Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    try:
        record = await claims_manager.resolve_claim(
            claim_id=claim_id,
            status=resolution.status,
            resolution_notes=resolution.resolution_notes,
            approved_amount=resolution.approved_amount,
            database=database,
        )
        return ClaimResponse(**record)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ── Analytics ─────────────────────────────────────────────────────────────────

@router.get("/analytics/summary", response_model=ClaimAnalytics)
async def get_claims_analytics(
    employee_id: Optional[str] = None,
    database=Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    try:
        data = await claims_manager.get_analytics(database, employee_id)
        return ClaimAnalytics(**data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
