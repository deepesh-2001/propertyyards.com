"""
Loan Application Module
Handles loan applications, approvals, disbursements, and eligibility checks
"""
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import logging
import math

from app.schemas import (
    LoanType,
    LoanApplicationStatus
)

logger = logging.getLogger(__name__)


class LoanApplicationManager:
    """Loan application management engine"""
    
    def __init__(self):
        self.interest_rates = {
            LoanType.HOME_LOAN: {"min": 6.5, "max": 12.0},
            LoanType.PERSONAL_LOAN: {"min": 10.0, "max": 24.0},
            LoanType.CAR_LOAN: {"min": 7.5, "max": 15.0},
            LoanType.EDUCATION_LOAN: {"min": 8.0, "max": 14.0},
            LoanType.BUSINESS_LOAN: {"min": 9.0, "max": 18.0},
            LoanType.PROPERTY_LOAN: {"min": 7.0, "max": 13.0}
        }
        self.max_dti_ratio = 0.5  # Debt-to-income ratio threshold
        self.min_credit_score = 650
    
    def calculate_emi(
        self,
        principal: float,
        annual_rate: float,
        months: int
    ) -> float:
        """Calculate EMI using reducing balance method"""
        if principal <= 0 or annual_rate <= 0 or months <= 0:
            return 0
        
        monthly_rate = annual_rate / 12 / 100
        emi = principal * monthly_rate * (1 + monthly_rate) ** months / ((1 + monthly_rate) ** months - 1)
        return round(emi, 2)
    
    def calculate_total_payable(
        self,
        emi: float,
        months: int
    ) -> float:
        """Calculate total payable amount"""
        return round(emi * months, 2)
    
    async def create_loan_application(
        self,
        application_data: Dict[str, Any],
        database
    ) -> Dict[str, Any]:
        """Create a new loan application"""
        try:
            user = await database.users.find_one({"_id": application_data["user_id"]})
            if not user:
                raise ValueError("User not found")
            
            # Get property details if applicable
            property_title = None
            if application_data.get("property_id"):
                property = await database.properties.find_one({"_id": application_data["property_id"]})
                property_title = property.get("title") if property else None
            
            # Get co-applicant details if applicable
            co_applicant_name = None
            if application_data.get("co_applicant_id"):
                co_applicant = await database.users.find_one({"_id": application_data["co_applicant_id"]})
                co_applicant_name = f"{co_applicant.get('first_name', '')} {co_applicant.get('last_name', '')}" if co_applicant else None
            
            # Calculate EMI and total payable
            emi = self.calculate_emi(
                application_data["loan_amount"],
                application_data["interest_rate"],
                application_data["loan_term_months"]
            )
            total_payable = self.calculate_total_payable(emi, application_data["loan_term_months"])
            
            application = {
                **application_data,
                "user_name": f"{user.get('first_name', '')} {user.get('last_name', '')}",
                "property_title": property_title,
                "co_applicant_name": co_applicant_name,
                "emi": emi,
                "total_payable": total_payable,
                "status": LoanApplicationStatus.SUBMITTED,
                "credit_score": None,
                "approval_amount": None,
                "rejection_reason": None,
                "approved_by": None,
                "approved_by_name": None,
                "approved_at": None,
                "disbursed_at": None,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }
            
            result = await database.loan_applications.insert_one(application)
            application["id"] = str(result.inserted_id)
            return application
        except Exception as e:
            logger.error(f"Loan application creation error: {e}")
            raise
    
    async def check_eligibility(
        self,
        user_id: str,
        loan_type: LoanType,
        database
    ) -> Dict[str, Any]:
        """Check loan eligibility for a user"""
        try:
            user = await database.users.find_one({"_id": user_id})
            if not user:
                raise ValueError("User not found")
            
            # Simulate credit score (in real app, integrate with credit bureau)
            credit_score = 700  # Default score
            
            # Calculate debt-to-income ratio
            income = user.get("income", 50000)
            existing_loans = user.get("existing_loans", 0)
            dti_ratio = existing_loans / income if income > 0 else 0
            
            # Determine eligibility
            eligible = credit_score >= self.min_credit_score and dti_ratio < self.max_dti_ratio
            
            # Calculate max loan amount based on income
            max_loan_amount = income * 60 if eligible else 0  # 60x monthly income
            
            # Get interest rate range
            rate_range = self.interest_rates.get(loan_type, {"min": 10.0, "max": 20.0})
            max_interest_rate = rate_range["min"] if credit_score > 750 else rate_range["max"]
            
            # Factors affecting eligibility
            factors = [
                {"factor": "credit_score", "value": credit_score, "status": "pass" if credit_score >= self.min_credit_score else "fail"},
                {"factor": "dti_ratio", "value": dti_ratio, "status": "pass" if dti_ratio < self.max_dti_ratio else "fail"},
                {"factor": "income", "value": income, "status": "pass"}
            ]
            
            return {
                "user_id": user_id,
                "eligible": eligible,
                "max_loan_amount": max_loan_amount,
                "max_interest_rate": max_interest_rate,
                "max_term_months": 360,  # 30 years
                "credit_score": credit_score,
                "debt_to_income_ratio": dti_ratio,
                "factors": factors,
                "created_at": datetime.utcnow()
            }
        except Exception as e:
            logger.error(f"Eligibility check error: {e}")
            raise
    
    async def approve_loan_application(
        self,
        loan_application_id: str,
        approved_by: str,
        approval_amount: Optional[float] = None,
        interest_rate: Optional[float] = None,
        notes: Optional[str] = None,
        database
    ) -> Dict[str, Any]:
        """Approve a loan application"""
        try:
            loan_application = await database.loan_applications.find_one({"_id": loan_application_id})
            if not loan_application:
                raise ValueError("Loan application not found")
            
            approver = await database.users.find_one({"_id": approved_by})
            approver_name = f"{approver.get('first_name', '')} {approver.get('last_name', '')}" if approver else ""
            
            # Use approval amount or requested amount
            final_amount = approval_amount or loan_application["loan_amount"]
            final_rate = interest_rate or loan_application["interest_rate"]
            
            # Recalculate EMI
            emi = self.calculate_emi(final_amount, final_rate, loan_application["loan_term_months"])
            total_payable = self.calculate_total_payable(emi, loan_application["loan_term_months"])
            
            await database.loan_applications.update_one(
                {"_id": loan_application_id},
                {
                    "$set": {
                        "status": LoanApplicationStatus.APPROVED,
                        "approval_amount": final_amount,
                        "interest_rate": final_rate,
                        "emi": emi,
                        "total_payable": total_payable,
                        "approved_by": approved_by,
                        "approved_by_name": approver_name,
                        "approved_at": datetime.utcnow(),
                        "updated_at": datetime.utcnow()
                    }
                }
            )
            
            updated = await database.loan_applications.find_one({"_id": loan_application_id})
            updated["id"] = str(updated["_id"])
            del updated["_id"]
            return updated
        except Exception as e:
            logger.error(f"Loan approval error: {e}")
            raise
    
    async def reject_loan_application(
        self,
        loan_application_id: str,
        approved_by: str,
        rejection_reason: str,
        database
    ) -> Dict[str, Any]:
        """Reject a loan application"""
        try:
            approver = await database.users.find_one({"_id": approved_by})
            approver_name = f"{approver.get('first_name', '')} {approver.get('last_name', '')}" if approver else ""
            
            await database.loan_applications.update_one(
                {"_id": loan_application_id},
                {
                    "$set": {
                        "status": LoanApplicationStatus.REJECTED,
                        "rejection_reason": rejection_reason,
                        "approved_by": approved_by,
                        "approved_by_name": approver_name,
                        "approved_at": datetime.utcnow(),
                        "updated_at": datetime.utcnow()
                    }
                }
            )
            
            updated = await database.loan_applications.find_one({"_id": loan_application_id})
            updated["id"] = str(updated["_id"])
            del updated["_id"]
            return updated
        except Exception as e:
            logger.error(f"Loan rejection error: {e}")
            raise
    
    async def disburse_loan(
        self,
        loan_application_id: str,
        disbursement_data: Dict[str, Any],
        database
    ) -> Dict[str, Any]:
        """Disburse approved loan"""
        try:
            loan_application = await database.loan_applications.find_one({"_id": loan_application_id})
            if not loan_application:
                raise ValueError("Loan application not found")
            
            if loan_application["status"] != LoanApplicationStatus.APPROVED:
                raise ValueError("Loan must be approved before disbursement")
            
            await database.loan_applications.update_one(
                {"_id": loan_application_id},
                {
                    "$set": {
                        "status": LoanApplicationStatus.DISBURSED,
                        "disbursed_at": datetime.utcnow(),
                        "updated_at": datetime.utcnow()
                    }
                }
            )
            
            # Create disbursement record
            disbursement = {
                **disbursement_data,
                "loan_application_id": loan_application_id,
                "disbursed_at": datetime.utcnow(),
                "created_at": datetime.utcnow()
            }
            await database.loan_disbursements.insert_one(disbursement)
            
            updated = await database.loan_applications.find_one({"_id": loan_application_id})
            updated["id"] = str(updated["_id"])
            del updated["_id"]
            return updated
        except Exception as e:
            logger.error(f"Loan disbursement error: {e}")
            raise


# Global manager instance
loan_application_manager = LoanApplicationManager()
