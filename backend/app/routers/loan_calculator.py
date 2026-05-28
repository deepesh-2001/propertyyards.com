"""
Loan Calculator Router
Endpoints for various loan calculators
"""
from fastapi import APIRouter
from app.loan_calculator import (
    MortgageCalculator, PersonalLoanCalculator, CarLoanCalculator,
    StudentLoanCalculator, BusinessLoanCalculator, HomeEquityCalculator,
    ConstructionLoanCalculator, LoanComparison, LoanCalculator
)
from app.schemas import (
    MortgageLoanRequest, MortgageLoanResponse, AffordabilityRequest, AffordabilityResponse,
    PersonalLoanRequest, PersonalLoanResponse, CarLoanRequest, CarLoanResponse,
    StudentLoanRequest, StudentLoanResponse, IncomeDrivenRepaymentRequest, IncomeDrivenRepaymentResponse,
    BusinessLoanRequest, BusinessLoanResponse, HomeEquityLoanRequest, HomeEquityLoanResponse,
    ConstructionLoanRequest, ConstructionLoanResponse, LoanComparisonRequest, LoanComparisonResponse,
    AmortizationScheduleRequest, AmortizationScheduleItem
)
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/loans", tags=["Loan Calculator"])


@router.post("/mortgage", response_model=MortgageLoanResponse)
async def calculate_mortgage(loan_request: MortgageLoanRequest):
    """Calculate mortgage payment"""
    result = MortgageCalculator.calculate_mortgage(
        principal=loan_request.principal,
        annual_rate=loan_request.annual_rate,
        years=loan_request.years,
        down_payment=loan_request.down_payment,
        property_tax=loan_request.property_tax,
        insurance=loan_request.insurance
    )
    return MortgageLoanResponse(**result)


@router.post("/mortgage/affordability", response_model=AffordabilityResponse)
async def calculate_affordability(affordability_request: AffordabilityRequest):
    """Calculate how much house user can afford"""
    result = MortgageCalculator.calculate_affordability(
        monthly_income=affordability_request.monthly_income,
        down_payment=affordability_request.down_payment,
        annual_rate=affordability_request.annual_rate,
        years=affordability_request.years,
        debt_to_income_ratio=affordability_request.debt_to_income_ratio
    )
    return AffordabilityResponse(**result)


@router.post("/personal", response_model=PersonalLoanResponse)
async def calculate_personal_loan(loan_request: PersonalLoanRequest):
    """Calculate personal loan payment"""
    result = PersonalLoanCalculator.calculate_personal_loan(
        principal=loan_request.principal,
        annual_rate=loan_request.annual_rate,
        years=loan_request.years,
        origination_fee=loan_request.origination_fee
    )
    return PersonalLoanResponse(**result)


@router.post("/car", response_model=CarLoanResponse)
async def calculate_car_loan(loan_request: CarLoanRequest):
    """Calculate car loan payment"""
    result = CarLoanCalculator.calculate_car_loan(
        car_price=loan_request.car_price,
        down_payment=loan_request.down_payment,
        annual_rate=loan_request.annual_rate,
        years=loan_request.years,
        trade_in_value=loan_request.trade_in_value
    )
    return CarLoanResponse(**result)


@router.post("/student", response_model=StudentLoanResponse)
async def calculate_student_loan(loan_request: StudentLoanRequest):
    """Calculate student loan payment"""
    result = StudentLoanCalculator.calculate_student_loan(
        principal=loan_request.principal,
        annual_rate=loan_request.annual_rate,
        years=loan_request.years,
        grace_period_months=loan_request.grace_period_months
    )
    return StudentLoanResponse(**result)


@router.post("/student/income-driven", response_model=IncomeDrivenRepaymentResponse)
async def calculate_income_driven_repayment(request: IncomeDrivenRepaymentRequest):
    """Calculate income-driven repayment plan"""
    result = StudentLoanCalculator.calculate_income_driven_repayment(
        annual_income=request.annual_income,
        family_size=request.family_size,
        poverty_line=request.poverty_line
    )
    return IncomeDrivenRepaymentResponse(**result)


@router.post("/business", response_model=BusinessLoanResponse)
async def calculate_business_loan(loan_request: BusinessLoanRequest):
    """Calculate business loan payment"""
    result = BusinessLoanCalculator.calculate_business_loan(
        principal=loan_request.principal,
        annual_rate=loan_request.annual_rate,
        years=loan_request.years,
        collateral_value=loan_request.collateral_value
    )
    return BusinessLoanResponse(**result)


@router.post("/home-equity", response_model=HomeEquityLoanResponse)
async def calculate_home_equity_loan(loan_request: HomeEquityLoanRequest):
    """Calculate home equity loan payment"""
    result = HomeEquityCalculator.calculate_home_equity_loan(
        home_value=loan_request.home_value,
        current_mortgage=loan_request.current_mortgage,
        annual_rate=loan_request.annual_rate,
        years=loan_request.years,
        max_ltv_ratio=loan_request.max_ltv_ratio
    )
    return HomeEquityLoanResponse(**result)


@router.post("/construction", response_model=ConstructionLoanResponse)
async def calculate_construction_loan(loan_request: ConstructionLoanRequest):
    """Calculate construction loan payment"""
    result = ConstructionLoanCalculator.calculate_construction_loan(
        total_cost=loan_request.total_cost,
        down_payment=loan_request.down_payment,
        annual_rate=loan_request.annual_rate,
        construction_months=loan_request.construction_months,
        permanent_loan_years=loan_request.permanent_loan_years
    )
    return ConstructionLoanResponse(**result)


@router.post("/compare", response_model=list[LoanComparisonResponse])
async def compare_loans(comparison_request: LoanComparisonRequest):
    """Compare multiple loan options"""
    results = LoanComparison.compare_loans(
        principal=comparison_request.principal,
        loan_options=comparison_request.loan_options
    )
    return [LoanComparisonResponse(**result) for result in results]


@router.post("/amortization", response_model=list[AmortizationScheduleItem])
async def generate_amortization_schedule(schedule_request: AmortizationScheduleRequest):
    """Generate amortization schedule"""
    schedule = LoanCalculator.calculate_amortization_schedule(
        principal=schedule_request.principal,
        annual_rate=schedule_request.annual_rate,
        years=schedule_request.years
    )
    return [AmortizationScheduleItem(**item) for item in schedule]
