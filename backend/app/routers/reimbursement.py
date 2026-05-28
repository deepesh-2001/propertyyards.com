"""
Reimbursement Router
"""
from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional

from app.database import get_db
from app.auth import get_current_user
from app.reimbursement import reimbursement_manager
from app.schemas import (
    ReimbursementCreate,
    ReimbursementResponse,
    ReimbursementReview,
    ReimbursementAnalytics,
    ReimbursementStatus,
)

router = APIRouter(prefix="/api/reimbursements", tags=["reimbursements"])


# ── Submit ────────────────────────────────────────────────────────────────────

@router.post("", response_model=ReimbursementResponse, status_code=status.HTTP_201_CREATED)
async def submit_reimbursement(
    payload: ReimbursementCreate,
    database=Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    try:
        record = await reimbursement_manager.submit_reimbursement(payload.dict(), database)
        return ReimbursementResponse(**record)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ── Read ──────────────────────────────────────────────────────────────────────

@router.get("/{reimbursement_id}", response_model=ReimbursementResponse)
async def get_reimbursement(
    reimbursement_id: str,
    database=Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    record = await database.reimbursements.find_one({"_id": reimbursement_id})
    if not record:
        raise HTTPException(status_code=404, detail="Reimbursement not found")
    record["id"] = str(record["_id"])
    del record["_id"]
    return ReimbursementResponse(**record)


@router.get("/employees/{employee_id}/reimbursements", response_model=List[ReimbursementResponse])
async def get_employee_reimbursements(
    employee_id: str,
    status: Optional[ReimbursementStatus] = None,
    database=Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    query = {"employee_id": employee_id}
    if status:
        query["status"] = status
    cursor = database.reimbursements.find(query).sort("created_at", -1)
    records = await cursor.to_list(length=200)
    for r in records:
        r["id"] = str(r["_id"])
        del r["_id"]
    return [ReimbursementResponse(**r) for r in records]


# ── Review / approve / reject ─────────────────────────────────────────────────

@router.put("/{reimbursement_id}/approve", response_model=ReimbursementResponse)
async def approve_reimbursement(
    reimbursement_id: str,
    review: ReimbursementReview,
    database=Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    try:
        if review.approved_amount is None:
            raise HTTPException(status_code=400, detail="approved_amount is required for approval")
        record = await reimbursement_manager.approve_reimbursement(
            reimbursement_id=reimbursement_id,
            approved_amount=review.approved_amount,
            reviewed_by=str(current_user.get("_id", "")),
            database=database,
        )
        return ReimbursementResponse(**record)
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{reimbursement_id}/reject", response_model=ReimbursementResponse)
async def reject_reimbursement(
    reimbursement_id: str,
    review: ReimbursementReview,
    database=Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    try:
        if not review.rejection_reason:
            raise HTTPException(status_code=400, detail="rejection_reason is required")
        record = await reimbursement_manager.reject_reimbursement(
            reimbursement_id=reimbursement_id,
            reviewed_by=str(current_user.get("_id", "")),
            rejection_reason=review.rejection_reason,
            database=database,
        )
        return ReimbursementResponse(**record)
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ── Analytics ─────────────────────────────────────────────────────────────────

@router.get("/analytics/summary", response_model=ReimbursementAnalytics)
async def get_reimbursement_analytics(
    employee_id: Optional[str] = None,
    database=Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    try:
        data = await reimbursement_manager.get_analytics(employee_id, database)
        return ReimbursementAnalytics(**data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
