"""
Tax Router
"""
from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional
from datetime import datetime

from app.database import get_db
from app.auth import get_current_user
from app.tax import tax_engine
from app.schemas import (
    TaxSlabCreate,
    TaxSlabResponse,
    TaxComputationRequest,
    TaxComputationResponse,
    Form16Summary,
    TaxRegime,
)

router = APIRouter(prefix="/api/tax", tags=["tax"])


# ── Tax Slabs (admin-managed) ─────────────────────────────────────────────────

@router.post("/slabs", response_model=TaxSlabResponse, status_code=status.HTTP_201_CREATED)
async def create_tax_slab(
    slab: TaxSlabCreate,
    database=Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    try:
        data = slab.dict()
        data["created_at"] = datetime.utcnow()
        result = await database.tax_slabs.insert_one(data)
        data["id"] = str(result.inserted_id)
        return TaxSlabResponse(**data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/slabs", response_model=List[TaxSlabResponse])
async def list_tax_slabs(
    regime: Optional[TaxRegime] = None,
    financial_year: Optional[str] = None,
    database=Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    query = {}
    if regime:
        query["regime"] = regime
    if financial_year:
        query["financial_year"] = financial_year
    cursor = database.tax_slabs.find(query).sort("min_income", 1)
    slabs = await cursor.to_list(length=100)
    for s in slabs:
        s["id"] = str(s["_id"])
        del s["_id"]
    return [TaxSlabResponse(**s) for s in slabs]


# ── Tax Computation ───────────────────────────────────────────────────────────

@router.post("/compute", response_model=TaxComputationResponse)
async def compute_tax(
    request: TaxComputationRequest,
    database=Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    try:
        result = tax_engine.compute(
            gross_annual_income=request.gross_annual_income,
            regime=request.regime,
            hra_exemption=request.hra_exemption,
            section_80c=request.section_80c,
            section_80d=request.section_80d,
            section_80ccd=request.section_80ccd,
            other_deductions=request.other_deductions,
            tds_already_deducted=request.tds_already_deducted,
        )
        return TaxComputationResponse(
            employee_id=request.employee_id,
            financial_year=request.financial_year,
            regime=request.regime,
            **result,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ── Form-16 ───────────────────────────────────────────────────────────────────

@router.post("/form16/{employee_id}", response_model=Form16Summary)
async def generate_form16(
    employee_id: str,
    financial_year: str,
    database=Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    try:
        form16 = await tax_engine.generate_form16(employee_id, financial_year, database)
        return Form16Summary(**form16)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/form16/{employee_id}", response_model=List[Form16Summary])
async def get_employee_form16(
    employee_id: str,
    database=Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    cursor = database.form16.find({"employee_id": employee_id}).sort("financial_year", -1)
    records = await cursor.to_list(length=20)
    for r in records:
        r.pop("_id", None)
    return [Form16Summary(**r) for r in records]


# ── Monthly TDS estimate ──────────────────────────────────────────────────────

@router.get("/tds/monthly-estimate")
async def monthly_tds_estimate(
    monthly_gross: float,
    regime: TaxRegime = TaxRegime.NEW,
    current_user: dict = Depends(get_current_user),
):
    if monthly_gross <= 0:
        raise HTTPException(status_code=400, detail="monthly_gross must be > 0")
    tds = tax_engine.monthly_tds_for_salary(monthly_gross, regime)
    return {"monthly_gross": monthly_gross, "regime": regime, "estimated_monthly_tds": tds}
