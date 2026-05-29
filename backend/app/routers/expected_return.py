"""
Expected Return Router
Projects expected returns for any investment, and for every future project /
investment opportunity in the platform.
"""
from fastapi import APIRouter, Depends, HTTPException
from typing import Optional

from app.database import get_db
from app.schemas import ExpectedReturnRequest, ExpectedReturnResponse
from app.expected_return import expected_return_calculator
from app.auth import get_current_user

router = APIRouter(prefix="/api/expected-return", tags=["expected-return"])


async def _find_doc(collection, doc_id: str):
    """Fetch a document by its `_id` or `id` field."""
    doc = await collection.find_one({"_id": doc_id})
    if not doc:
        doc = await collection.find_one({"id": doc_id})
    return doc


def _doc_id(doc: dict) -> str:
    return str(doc.get("_id") or doc.get("id", ""))


# ========== Generic calculator ==========

@router.post("/calculate", response_model=ExpectedReturnResponse)
async def calculate_expected_return(
    request: ExpectedReturnRequest,
    current_user: dict = Depends(get_current_user),
):
    """Calculate expected return for any investment (works for everything)."""
    try:
        result = expected_return_calculator.calculate(
            principal=request.principal,
            term_months=request.term_months,
            annual_return_rate=request.annual_return_rate,
            appreciation_annual=request.appreciation_annual,
            rental_yield_annual=request.rental_yield_annual,
            compounding=request.compounding,
            compounding_frequency=request.compounding_frequency,
            one_time_costs=request.one_time_costs,
            recurring_monthly_costs=request.recurring_monthly_costs,
            inflation_rate_annual=request.inflation_rate_annual,
            risk_level=request.risk_level,
            currency=request.currency,
        )
        return ExpectedReturnResponse(**result)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ========== Per investment opportunity ==========

@router.get("/investments/{opportunity_id}", response_model=ExpectedReturnResponse)
async def expected_return_for_investment(
    opportunity_id: str,
    principal: Optional[float] = None,
    inflation_rate_annual: Optional[float] = None,
    compounding: bool = True,
    database=Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Expected return for a specific investment opportunity."""
    opp = await _find_doc(database.investment_opportunities, opportunity_id)
    if not opp:
        raise HTTPException(status_code=404, detail="Investment opportunity not found")

    result = expected_return_calculator.calculate(
        principal=principal or opp.get("minimum_investment", 0),
        term_months=opp.get("investment_term_months", 12),
        annual_return_rate=opp.get("expected_roi_annual", 0),
        compounding=compounding,
        inflation_rate_annual=inflation_rate_annual,
        risk_level=opp.get("risk_level"),
        currency=opp.get("currency", "INR"),
    )
    return ExpectedReturnResponse(**result)


# ========== Per future project ==========

@router.get("/projects/{project_id}", response_model=ExpectedReturnResponse)
async def expected_return_for_project(
    project_id: str,
    principal: Optional[float] = None,
    term_months: int = 60,
    rental_yield_annual: Optional[float] = None,
    inflation_rate_annual: Optional[float] = None,
    compounding: bool = True,
    database=Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Expected return for a specific future project.

    Uses the project's `expected_roi` for capital appreciation and the midpoint
    of its price range as the default principal.
    """
    project = await _find_doc(database.future_projects, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Future project not found")

    midpoint = (project.get("price_range_min", 0) + project.get("price_range_max", 0)) / 2
    result = expected_return_calculator.calculate(
        principal=principal or midpoint,
        term_months=term_months,
        appreciation_annual=project.get("expected_roi", 0),
        rental_yield_annual=rental_yield_annual,
        compounding=compounding,
        inflation_rate_annual=inflation_rate_annual,
        currency=project.get("currency", "INR"),
    )
    return ExpectedReturnResponse(**result)


# ========== Bulk: every investment opportunity ==========

@router.get("/investments")
async def expected_returns_all_investments(
    status: str = "open",
    inflation_rate_annual: Optional[float] = None,
    database=Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Expected returns for every investment opportunity."""
    query = {"status": status} if status else {}
    opportunities = await database.investment_opportunities.find(query).to_list(length=1000)

    results = []
    for opp in opportunities:
        try:
            projection = expected_return_calculator.calculate(
                principal=opp.get("minimum_investment", 0),
                term_months=opp.get("investment_term_months", 12),
                annual_return_rate=opp.get("expected_roi_annual", 0),
                inflation_rate_annual=inflation_rate_annual,
                risk_level=opp.get("risk_level"),
                currency=opp.get("currency", "INR"),
            )
        except ValueError:
            continue
        results.append({
            "opportunity_id": _doc_id(opp),
            "title": opp.get("title", ""),
            "investment_type": opp.get("investment_type", ""),
            "city": opp.get("city", ""),
            "risk_level": opp.get("risk_level"),
            "expected_return": projection,
        })

    results.sort(key=lambda r: r["expected_return"]["annualized_roi_pct"], reverse=True)
    return {"count": len(results), "results": results}


# ========== Bulk: every future project ==========

@router.get("/projects")
async def expected_returns_all_projects(
    term_months: int = 60,
    city: Optional[str] = None,
    inflation_rate_annual: Optional[float] = None,
    database=Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Expected returns for every future project."""
    query = {}
    if city:
        query["city"] = city
    projects = await database.future_projects.find(query).to_list(length=1000)

    results = []
    for project in projects:
        midpoint = (project.get("price_range_min", 0) + project.get("price_range_max", 0)) / 2
        if midpoint <= 0:
            continue
        try:
            projection = expected_return_calculator.calculate(
                principal=midpoint,
                term_months=term_months,
                appreciation_annual=project.get("expected_roi", 0),
                inflation_rate_annual=inflation_rate_annual,
                currency=project.get("currency", "INR"),
            )
        except ValueError:
            continue
        results.append({
            "project_id": _doc_id(project),
            "project_name": project.get("project_name", ""),
            "developer_name": project.get("developer_name", ""),
            "city": project.get("city", ""),
            "construction_status": project.get("construction_status", ""),
            "expected_return": projection,
        })

    results.sort(key=lambda r: r["expected_return"]["annualized_roi_pct"], reverse=True)
    return {"count": len(results), "results": results}
