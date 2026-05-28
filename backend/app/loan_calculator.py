"""
Loan Calculator Module
Calculates various types of loans including mortgage, personal, car, student, etc.
"""
from datetime import datetime
from typing import Dict, Any, Optional, List
from enum import Enum
import logging
import math

logger = logging.getLogger(__name__)


class LoanType(str, Enum):
    """Types of loans"""
    MORTGAGE = "mortgage"
    PERSONAL = "personal"
    CAR = "car"
    STUDENT = "student"
    BUSINESS = "business"
    HOME_EQUITY = "home_equity"
    CONSTRUCTION = "construction"


class InterestRateType(str, Enum):
    """Interest rate types"""
    FIXED = "fixed"
    VARIABLE = "variable"
    ADJUSTABLE = "adjustable"


class RepaymentFrequency(str, Enum):
    """Repayment frequencies"""
    MONTHLY = "monthly"
    BI_WEEKLY = "bi_weekly"
    WEEKLY = "weekly"
    QUARTERLY = "quarterly"
    ANNUALLY = "annually"


class LoanCalculator:
    """Base loan calculator"""
    
    @staticmethod
    def calculate_monthly_payment(
        principal: float,
        annual_rate: float,
        years: int
    ) -> float:
        """Calculate monthly payment using standard amortization formula"""
        if annual_rate == 0:
            return principal / (years * 12)
        
        monthly_rate = annual_rate / 100 / 12
        num_payments = years * 12
        
        monthly_payment = principal * (monthly_rate * (1 + monthly_rate) ** num_payments) / ((1 + monthly_rate) ** num_payments - 1)
        
        return round(monthly_payment, 2)
    
    @staticmethod
    def calculate_total_payment(
        monthly_payment: float,
        years: int
    ) -> float:
        """Calculate total payment over loan term"""
        return round(monthly_payment * years * 12, 2)
    
    @staticmethod
    def calculate_total_interest(
        total_payment: float,
        principal: float
    ) -> float:
        """Calculate total interest paid"""
        return round(total_payment - principal, 2)
    
    @staticmethod
    def calculate_amortization_schedule(
        principal: float,
        annual_rate: float,
        years: int
    ) -> List[Dict[str, Any]]:
        """Generate amortization schedule"""
        monthly_payment = LoanCalculator.calculate_monthly_payment(principal, annual_rate, years)
        monthly_rate = annual_rate / 100 / 12
        num_payments = years * 12
        
        schedule = []
        remaining_balance = principal
        
        for month in range(1, num_payments + 1):
            interest_payment = remaining_balance * monthly_rate
            principal_payment = monthly_payment - interest_payment
            remaining_balance -= principal_payment
            
            if remaining_balance < 0:
                remaining_balance = 0
            
            schedule.append({
                "month": month,
                "payment": round(monthly_payment, 2),
                "principal_payment": round(principal_payment, 2),
                "interest_payment": round(interest_payment, 2),
                "remaining_balance": round(remaining_balance, 2)
            })
        
        return schedule


class MortgageCalculator(LoanCalculator):
    """Mortgage loan calculator"""
    
    @staticmethod
    def calculate_mortgage(
        principal: float,
        annual_rate: float,
        years: int,
        down_payment: float = 0,
        property_tax: float = 0,
        insurance: float = 0
    ) -> Dict[str, Any]:
        """Calculate mortgage payment with additional costs"""
        loan_amount = principal - down_payment
        monthly_payment = LoanCalculator.calculate_monthly_payment(loan_amount, annual_rate, years)
        
        # Add monthly property tax and insurance
        monthly_property_tax = property_tax / 12
        monthly_insurance = insurance / 12
        
        total_monthly = monthly_payment + monthly_property_tax + monthly_insurance
        
        total_payment = LoanCalculator.calculate_total_payment(total_monthly, years)
        total_interest = LoanCalculator.calculate_total_interest(total_payment, loan_amount)
        
        return {
            "loan_amount": loan_amount,
            "down_payment": down_payment,
            "principal_and_interest": round(monthly_payment, 2),
            "property_tax": round(monthly_property_tax, 2),
            "insurance": round(monthly_insurance, 2),
            "total_monthly_payment": round(total_monthly, 2),
            "total_payment": total_payment,
            "total_interest": total_interest,
            "loan_to_value": round((loan_amount / principal) * 100, 2) if principal > 0 else 0
        }
    
    @staticmethod
    def calculate_affordability(
        monthly_income: float,
        down_payment: float,
        annual_rate: float,
        years: int,
        debt_to_income_ratio: float = 0.28
    ) -> Dict[str, Any]:
        """Calculate how much house user can afford"""
        max_monthly_payment = monthly_income * debt_to_income_ratio
        property_tax = 0
        insurance = 0
        
        # Reverse calculate principal from monthly payment
        monthly_rate = annual_rate / 100 / 12
        num_payments = years * 12
        
        if monthly_rate == 0:
            max_loan = max_monthly_payment * num_payments
        else:
            max_loan = max_monthly_payment * ((1 + monthly_rate) ** num_payments - 1) / (monthly_rate * (1 + monthly_rate) ** num_payments)
        
        max_home_price = max_loan + down_payment
        
        return {
            "max_monthly_payment": round(max_monthly_payment, 2),
            "max_loan_amount": round(max_loan, 2),
            "max_home_price": round(max_home_price, 2),
            "down_payment": down_payment,
            "debt_to_income_ratio": debt_to_income_ratio
        }


class PersonalLoanCalculator(LoanCalculator):
    """Personal loan calculator"""
    
    @staticmethod
    def calculate_personal_loan(
        principal: float,
        annual_rate: float,
        years: int,
        origination_fee: float = 0
    ) -> Dict[str, Any]:
        """Calculate personal loan payment"""
        monthly_payment = LoanCalculator.calculate_monthly_payment(principal, annual_rate, years)
        total_payment = LoanCalculator.calculate_total_payment(monthly_payment, years)
        total_interest = LoanCalculator.calculate_total_interest(total_payment, principal)
        
        # Add origination fee
        total_cost = total_payment + origination_fee
        apr = LoanCalculator.calculate_apr(principal, total_cost, years)
        
        return {
            "monthly_payment": monthly_payment,
            "total_payment": total_payment,
            "total_interest": total_interest,
            "origination_fee": origination_fee,
            "total_cost": total_cost,
            "apr": apr
        }
    
    @staticmethod
    def calculate_apr(principal: float, total_cost: float, years: int) -> float:
        """Calculate Annual Percentage Rate"""
        finance_charge = total_cost - principal
        n = years * 12
        apr = (finance_charge / principal) * (365 / (years * 365)) * 100
        return round(apr, 2)


class CarLoanCalculator(LoanCalculator):
    """Car loan calculator"""
    
    @staticmethod
    def calculate_car_loan(
        car_price: float,
        down_payment: float,
        annual_rate: float,
        years: int,
        trade_in_value: float = 0
    ) -> Dict[str, Any]:
        """Calculate car loan payment"""
        loan_amount = car_price - down_payment - trade_in_value
        
        if loan_amount <= 0:
            return {
                "loan_amount": 0,
                "monthly_payment": 0,
                "total_payment": 0,
                "total_interest": 0,
                "message": "No loan needed - down payment and trade-in cover the cost"
            }
        
        monthly_payment = LoanCalculator.calculate_monthly_payment(loan_amount, annual_rate, years)
        total_payment = LoanCalculator.calculate_total_payment(monthly_payment, years)
        total_interest = LoanCalculator.calculate_total_interest(total_payment, loan_amount)
        
        return {
            "car_price": car_price,
            "down_payment": down_payment,
            "trade_in_value": trade_in_value,
            "loan_amount": loan_amount,
            "monthly_payment": monthly_payment,
            "total_payment": total_payment,
            "total_interest": total_interest
        }


class StudentLoanCalculator(LoanCalculator):
    """Student loan calculator"""
    
    @staticmethod
    def calculate_student_loan(
        principal: float,
        annual_rate: float,
        years: int,
        grace_period_months: int = 6
    ) -> Dict[str, Any]:
        """Calculate student loan payment with grace period"""
        monthly_payment = LoanCalculator.calculate_monthly_payment(principal, annual_rate, years)
        total_payment = LoanCalculator.calculate_total_payment(monthly_payment, years)
        total_interest = LoanCalculator.calculate_total_interest(total_payment, principal)
        
        # Calculate interest accrued during grace period
        grace_period_interest = principal * (annual_rate / 100) * (grace_period_months / 12)
        
        return {
            "principal": principal,
            "monthly_payment": monthly_payment,
            "total_payment": total_payment,
            "total_interest": total_interest,
            "grace_period_months": grace_period_months,
            "grace_period_interest": round(grace_period_interest, 2)
        }
    
    @staticmethod
    def calculate_income_driven_repayment(
        annual_income: float,
        family_size: int,
        poverty_line: float = 14500
    ) -> Dict[str, Any]:
        """Calculate income-driven repayment plan"""
        # Simplified income-driven repayment calculation
        discretionary_income = max(0, annual_income - (poverty_line * 1.5))
        monthly_payment = discretionary_income * 0.10 / 12
        
        return {
            "annual_income": annual_income,
            "family_size": family_size,
            "discretionary_income": round(discretionary_income, 2),
            "monthly_payment": round(max(0, monthly_payment), 2),
            "repayment_plan": "income-driven"
        }


class BusinessLoanCalculator(LoanCalculator):
    """Business loan calculator"""
    
    @staticmethod
    def calculate_business_loan(
        principal: float,
        annual_rate: float,
        years: int,
        collateral_value: float = 0
    ) -> Dict[str, Any]:
        """Calculate business loan payment"""
        monthly_payment = LoanCalculator.calculate_monthly_payment(principal, annual_rate, years)
        total_payment = LoanCalculator.calculate_total_payment(monthly_payment, years)
        total_interest = LoanCalculator.calculate_total_interest(total_payment, principal)
        
        loan_to_value = (principal / collateral_value * 100) if collateral_value > 0 else 0
        
        return {
            "principal": principal,
            "monthly_payment": monthly_payment,
            "total_payment": total_payment,
            "total_interest": total_interest,
            "collateral_value": collateral_value,
            "loan_to_value": round(loan_to_value, 2)
        }


class HomeEquityCalculator(LoanCalculator):
    """Home equity loan calculator"""
    
    @staticmethod
    def calculate_home_equity_loan(
        home_value: float,
        current_mortgage: float,
        annual_rate: float,
        years: int,
        max_ltv_ratio: float = 0.85
    ) -> Dict[str, Any]:
        """Calculate home equity loan"""
        available_equity = home_value - current_mortgage
        max_loan_amount = home_value * max_ltv_ratio - current_mortgage
        max_loan_amount = max(0, max_loan_amount)
        
        monthly_payment = LoanCalculator.calculate_monthly_payment(max_loan_amount, annual_rate, years)
        total_payment = LoanCalculator.calculate_total_payment(monthly_payment, years)
        total_interest = LoanCalculator.calculate_total_interest(total_payment, max_loan_amount)
        
        return {
            "home_value": home_value,
            "current_mortgage": current_mortgage,
            "available_equity": available_equity,
            "max_loan_amount": max_loan_amount,
            "monthly_payment": monthly_payment,
            "total_payment": total_payment,
            "total_interest": total_interest,
            "combined_ltv": round((current_mortgage + max_loan_amount) / home_value * 100, 2)
        }


class ConstructionLoanCalculator(LoanCalculator):
    """Construction loan calculator"""
    
    @staticmethod
    def calculate_construction_loan(
        total_cost: float,
        down_payment: float,
        annual_rate: float,
        construction_months: int,
        permanent_loan_years: int
    ) -> Dict[str, Any]:
        """Calculate construction loan with interest-only period"""
        loan_amount = total_cost - down_payment
        
        # Interest-only period during construction
        monthly_interest_only = loan_amount * (annual_rate / 100 / 12)
        total_construction_interest = monthly_interest_only * construction_months
        
        # Convert to permanent mortgage
        monthly_payment = LoanCalculator.calculate_monthly_payment(loan_amount, annual_rate, permanent_loan_years)
        total_payment = LoanCalculator.calculate_total_payment(monthly_payment, permanent_loan_years)
        total_interest = LoanCalculator.calculate_total_interest(total_payment, loan_amount)
        
        return {
            "total_cost": total_cost,
            "down_payment": down_payment,
            "loan_amount": loan_amount,
            "construction_months": construction_months,
            "monthly_interest_only": round(monthly_interest_only, 2),
            "total_construction_interest": round(total_construction_interest, 2),
            "permanent_loan_years": permanent_loan_years,
            "monthly_payment": monthly_payment,
            "total_payment": total_payment,
            "total_interest": total_interest
        }


class LoanComparison:
    """Compare different loan options"""
    
    @staticmethod
    def compare_loans(
        principal: float,
        loan_options: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Compare multiple loan options"""
        results = []
        
        for option in loan_options:
            annual_rate = option.get("annual_rate", 0)
            years = option.get("years", 30)
            
            monthly_payment = LoanCalculator.calculate_monthly_payment(principal, annual_rate, years)
            total_payment = LoanCalculator.calculate_total_payment(monthly_payment, years)
            total_interest = LoanCalculator.calculate_total_interest(total_payment, principal)
            
            results.append({
                "option_name": option.get("name", "Option"),
                "annual_rate": annual_rate,
                "years": years,
                "monthly_payment": monthly_payment,
                "total_payment": total_payment,
                "total_interest": total_interest,
                "apr": round((total_interest / principal) * 100, 2)
            })
        
        # Sort by total payment
        results.sort(key=lambda x: x["total_payment"])
        
        return results
