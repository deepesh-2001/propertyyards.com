"""
Salary Router
Handles payroll processing, salary components, and salary slip generation
"""
from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional
from datetime import datetime

from app.database import get_db
from app.schemas import (
    SalaryComponentCreate,
    SalaryComponentResponse,
    PayrollPeriodCreate,
    PayrollPeriodResponse,
    PayrollEntryCreate,
    PayrollEntryResponse,
    SalarySlipCreate,
    SalarySlipResponse,
    PayrollFrequency,
    PayrollStatus
)
from app.salary import payroll_processor
from app.auth import get_current_user

router = APIRouter(prefix="/api/salary", tags=["salary"])


# ========== Salary Components Endpoints ==========

@router.post("/components", response_model=SalaryComponentResponse, status_code=status.HTTP_201_CREATED)
async def create_salary_component(
    component: SalaryComponentCreate,
    database=Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Create a new salary component"""
    try:
        component_data = component.dict()
        component_data.update({
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        })
        
        result = await database.salary_components.insert_one(component_data)
        component_data["id"] = str(result.inserted_id)
        
        return SalaryComponentResponse(**component_data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/components/{component_id}", response_model=SalaryComponentResponse)
async def get_salary_component(
    component_id: str,
    database=Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get a specific salary component"""
    component = await database.salary_components.find_one({"_id": component_id})
    if not component:
        raise HTTPException(status_code=404, detail="Salary component not found")
    
    component["id"] = str(component["_id"])
    del component["_id"]
    
    return SalaryComponentResponse(**component)


@router.get("/employees/{employee_id}/components", response_model=List[SalaryComponentResponse])
async def get_employee_salary_components(
    employee_id: str,
    database=Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get all salary components for an employee"""
    cursor = database.salary_components.find({"employee_id": employee_id}).sort("created_at", -1)
    components = await cursor.to_list(length=100)
    
    for component in components:
        component["id"] = str(component["_id"])
        del component["_id"]
    
    return [SalaryComponentResponse(**c) for c in components]


# ========== Payroll Periods Endpoints ==========

@router.post("/periods", response_model=PayrollPeriodResponse, status_code=status.HTTP_201_CREATED)
async def create_payroll_period(
    period: PayrollPeriodCreate,
    database=Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Create a new payroll period"""
    try:
        period_data = period.dict()
        period_data.update({
            "status": PayrollStatus.DRAFT,
            "total_employees": 0,
            "total_amount": 0,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        })
        
        result = await database.payroll_periods.insert_one(period_data)
        period_data["id"] = str(result.inserted_id)
        
        return PayrollPeriodResponse(**period_data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/periods/{period_id}", response_model=PayrollPeriodResponse)
async def get_payroll_period(
    period_id: str,
    database=Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get a specific payroll period"""
    period = await database.payroll_periods.find_one({"_id": period_id})
    if not period:
        raise HTTPException(status_code=404, detail="Payroll period not found")
    
    period["id"] = str(period["_id"])
    del period["_id"]
    
    return PayrollPeriodResponse(**period)


@router.get("/periods", response_model=List[PayrollPeriodResponse])
async def get_payroll_periods(
    status: Optional[PayrollStatus] = None,
    database=Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get all payroll periods"""
    query = {}
    if status:
        query["status"] = status
    
    cursor = database.payroll_periods.find(query).sort("created_at", -1)
    periods = await cursor.to_list(length=100)
    
    for period in periods:
        period["id"] = str(period["_id"])
        del period["_id"]
    
    return [PayrollPeriodResponse(**p) for p in periods]


# ========== Payroll Entries Endpoints ==========

@router.post("/entries", response_model=PayrollEntryResponse, status_code=status.HTTP_201_CREATED)
async def create_payroll_entry(
    entry: PayrollEntryCreate,
    database=Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Create a payroll entry"""
    try:
        from app.salary import SalaryCalculator
        calculator = SalaryCalculator()
        
        # Calculate salary breakdown
        breakdown = calculator.calculate_net_salary(
            basic_salary=entry.basic_salary,
            allowances=entry.allowances or {},
            deductions=entry.deductions or {},
            bonuses=entry.bonuses or {},
            overtime_hours=entry.overtime_hours,
            overtime_rate=entry.overtime_rate,
            working_days=entry.working_days
        )
        
        # Get employee details
        employee = await database.users.find_one({"_id": entry.employee_id})
        
        entry_data = entry.dict()
        entry_data.update({
            "employee_name": f"{employee.get('first_name', '')} {employee.get('last_name', '')}" if employee else "",
            "employee_designation": employee.get("designation", "N/A") if employee else "N/A",
            **breakdown,
            "status": PayrollStatus.PENDING,
            "payment_date": None,
            "payment_method": None,
            "transaction_id": None,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        })
        
        result = await database.payroll_entries.insert_one(entry_data)
        entry_data["id"] = str(result.inserted_id)
        
        return PayrollEntryResponse(**entry_data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/entries/{entry_id}", response_model=PayrollEntryResponse)
async def get_payroll_entry(
    entry_id: str,
    database=Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get a specific payroll entry"""
    entry = await database.payroll_entries.find_one({"_id": entry_id})
    if not entry:
        raise HTTPException(status_code=404, detail="Payroll entry not found")
    
    entry["id"] = str(entry["_id"])
    del entry["_id"]
    
    return PayrollEntryResponse(**entry)


@router.get("/periods/{period_id}/entries", response_model=List[PayrollEntryResponse])
async def get_period_payroll_entries(
    period_id: str,
    database=Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get all payroll entries for a period"""
    cursor = database.payroll_entries.find({"payroll_period_id": period_id}).sort("created_at", -1)
    entries = await cursor.to_list(length=1000)
    
    for entry in entries:
        entry["id"] = str(entry["_id"])
        del entry["_id"]
    
    return [PayrollEntryResponse(**e) for e in entries]


@router.get("/employees/{employee_id}/entries", response_model=List[PayrollEntryResponse])
async def get_employee_payroll_entries(
    employee_id: str,
    database=Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get all payroll entries for an employee"""
    cursor = database.payroll_entries.find({"employee_id": employee_id}).sort("created_at", -1)
    entries = await cursor.to_list(length=100)
    
    for entry in entries:
        entry["id"] = str(entry["_id"])
        del entry["_id"]
    
    return [PayrollEntryResponse(**e) for e in entries]


# ========== Payroll Processing Endpoints ==========

@router.post("/periods/{period_id}/process")
async def process_payroll_period(
    period_id: str,
    database=Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Process payroll for a period"""
    try:
        result = await payroll_processor.process_payroll_period(period_id, database)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ========== Salary Slips Endpoints ==========

@router.post("/slips", response_model=SalarySlipResponse, status_code=status.HTTP_201_CREATED)
async def generate_salary_slip(
    slip: SalarySlipCreate,
    database=Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Generate a salary slip"""
    try:
        salary_slip = await payroll_processor.generate_salary_slip(slip.payroll_entry_id, database)
        return SalarySlipResponse(**salary_slip)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/slips/{slip_id}", response_model=SalarySlipResponse)
async def get_salary_slip(
    slip_id: str,
    database=Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get a specific salary slip"""
    slip = await database.salary_slips.find_one({"_id": slip_id})
    if not slip:
        raise HTTPException(status_code=404, detail="Salary slip not found")
    
    slip["id"] = str(slip["_id"])
    del slip["_id"]
    
    return SalarySlipResponse(**slip)


@router.get("/employees/{employee_id}/slips", response_model=List[SalarySlipResponse])
async def get_employee_salary_slips(
    employee_id: str,
    database=Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get all salary slips for an employee"""
    cursor = database.salary_slips.find({"employee_id": employee_id}).sort("generated_at", -1)
    slips = await cursor.to_list(length=100)
    
    for slip in slips:
        slip["id"] = str(slip["_id"])
        del slip["_id"]
    
    return [SalarySlipResponse(**s) for s in slips]
