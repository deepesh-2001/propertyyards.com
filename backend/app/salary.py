"""
Salary Processing Module
Handles payroll calculations, salary components, and salary slip generation
"""
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import logging

from app.schemas import (
    SalaryComponentType,
    PayrollFrequency,
    PayrollStatus
)

logger = logging.getLogger(__name__)


class SalaryCalculator:
    """Salary calculation engine"""
    
    def __init__(self):
        self.tax_rates = {
            "0-250000": 0,
            "250001-500000": 5,
            "500001-1000000": 20,
            "1000001+": 30
        }
        self.pf_rate = 0.12  # 12% of basic salary
        self.esi_rate = 0.01  # 1% of gross salary
    
    def calculate_tax(self, annual_income: float) -> float:
        """Calculate income tax based on annual income"""
        if annual_income <= 250000:
            return 0
        elif annual_income <= 500000:
            return (annual_income - 250000) * 0.05
        elif annual_income <= 1000000:
            return 12500 + (annual_income - 500000) * 0.20
        else:
            return 112500 + (annual_income - 1000000) * 0.30
    
    def calculate_pf(self, basic_salary: float) -> float:
        """Calculate Provident Fund deduction"""
        return basic_salary * self.pf_rate
    
    def calculate_esi(self, gross_salary: float) -> float:
        """Calculate ESI deduction"""
        if gross_salary <= 21000:  # ESI threshold
            return gross_salary * self.esi_rate
        return 0
    
    def calculate_overtime(
        self,
        overtime_hours: float,
        overtime_rate: float,
        basic_salary: float,
        working_days: int = 30
    ) -> float:
        """Calculate overtime amount"""
        hourly_rate = basic_salary / (working_days * 8)  # Assuming 8 hours/day
        return overtime_hours * overtime_rate * hourly_rate
    
    def calculate_net_salary(
        self,
        basic_salary: float,
        allowances: Dict[str, float],
        deductions: Dict[str, float],
        bonuses: Dict[str, float],
        overtime_hours: float = 0,
        overtime_rate: float = 1.5,
        working_days: int = 30
    ) -> Dict[str, Any]:
        """Calculate complete salary breakdown"""
        # Calculate overtime
        overtime_amount = self.calculate_overtime(
            overtime_hours, overtime_rate, basic_salary, working_days
        )
        
        # Calculate gross salary
        total_allowances = sum(allowances.values())
        total_bonuses = sum(bonuses.values())
        gross_salary = basic_salary + total_allowances + total_bonuses + overtime_amount
        
        # Calculate deductions
        pf_deduction = self.calculate_pf(basic_salary)
        esi_deduction = self.calculate_esi(gross_salary)
        monthly_tax = self.calculate_tax(gross_salary * 12) / 12
        
        total_deductions = sum(deductions.values()) + pf_deduction + esi_deduction + monthly_tax
        
        # Calculate net salary
        net_salary = gross_salary - total_deductions
        
        return {
            "basic_salary": basic_salary,
            "allowances": allowances,
            "total_allowances": total_allowances,
            "bonuses": bonuses,
            "total_bonuses": total_bonuses,
            "overtime_hours": overtime_hours,
            "overtime_amount": overtime_amount,
            "gross_salary": gross_salary,
            "deductions": deductions,
            "pf_deduction": pf_deduction,
            "esi_deduction": esi_deduction,
            "tax_deduction": monthly_tax,
            "total_deductions": total_deductions,
            "net_salary": net_salary,
            "employer_pf_contribution": pf_deduction,
            "employer_esi_contribution": esi_deduction * 4  # Employer contributes 4% for ESI
        }


class PayrollProcessor:
    """Payroll processing engine"""
    
    def __init__(self):
        self.calculator = SalaryCalculator()
    
    async def process_payroll_period(
        self,
        payroll_period_id: str,
        database
    ) -> Dict[str, Any]:
        """Process payroll for a specific period"""
        try:
            # Get payroll period
            payroll_period = await database.payroll_periods.find_one({"_id": payroll_period_id})
            if not payroll_period:
                raise ValueError("Payroll period not found")
            
            # Get all active employees
            employees = await database.users.find({"role": "employee", "is_active": True}).to_list(length=1000)
            
            processed_entries = []
            total_amount = 0
            
            for employee in employees:
                # Get salary components for employee
                components = await database.salary_components.find({
                    "employee_id": str(employee["_id"]),
                    "effective_date": {"$lte": payroll_period["end_date"]},
                    "$or": [
                        {"expiry_date": None},
                        {"expiry_date": {"$gte": payroll_period["start_date"]}}
                    ]
                }).to_list(length=50)
                
                # Calculate salary
                salary_breakdown = self._calculate_employee_salary(
                    employee,
                    components,
                    payroll_period
                )
                
                # Create payroll entry
                payroll_entry = {
                    "payroll_period_id": payroll_period_id,
                    "employee_id": str(employee["_id"]),
                    "employee_name": f"{employee.get('first_name', '')} {employee.get('last_name', '')}",
                    "employee_designation": employee.get("designation", "N/A"),
                    **salary_breakdown,
                    "status": PayrollStatus.PROCESSED,
                    "created_at": datetime.utcnow(),
                    "updated_at": datetime.utcnow()
                }
                
                result = await database.payroll_entries.insert_one(payroll_entry)
                payroll_entry["id"] = str(result.inserted_id)
                
                processed_entries.append(payroll_entry)
                total_amount += salary_breakdown["net_salary"]
            
            # Update payroll period
            await database.payroll_periods.update_one(
                {"_id": payroll_period_id},
                {
                    "$set": {
                        "status": PayrollStatus.PROCESSED,
                        "total_employees": len(employees),
                        "total_amount": total_amount,
                        "updated_at": datetime.utcnow()
                    }
                }
            )
            
            return {
                "success": True,
                "payroll_period_id": payroll_period_id,
                "processed_entries": len(processed_entries),
                "total_amount": total_amount,
                "entries": processed_entries
            }
            
        except Exception as e:
            logger.error(f"Payroll processing error: {e}")
            raise
    
    def _calculate_employee_salary(
        self,
        employee: Dict[str, Any],
        components: List[Dict[str, Any]],
        payroll_period: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Calculate salary for a single employee"""
        allowances = {}
        deductions = {}
        bonuses = {}
        basic_salary = 0
        
        # Process components
        for component in components:
            component_type = component["component_type"]
            amount = component["amount"]
            
            if component_type == SalaryComponentType.BASIC:
                basic_salary = amount
            elif component_type in [SalaryComponentType.HRA, SalaryComponentType.DA, 
                                   SalaryComponentType.TA, SalaryComponentType.MA]:
                allowances[component["name"]] = amount
            elif component_type in [SalaryComponentType.BONUS, SalaryComponentType.OVERTIME]:
                bonuses[component["name"]] = amount
            elif component_type.startswith("DEDUCTION"):
                deductions[component["name"]] = amount
        
        # Calculate using salary calculator
        breakdown = self.calculator.calculate_net_salary(
            basic_salary=basic_salary,
            allowances=allowances,
            deductions=deductions,
            bonuses=bonuses,
            working_days=30
        )
        
        return breakdown
    
    async def generate_salary_slip(
        self,
        payroll_entry_id: str,
        database
    ) -> Dict[str, Any]:
        """Generate salary slip for a payroll entry"""
        try:
            # Get payroll entry
            payroll_entry = await database.payroll_entries.find_one({"_id": payroll_entry_id})
            if not payroll_entry:
                raise ValueError("Payroll entry not found")
            
            # Get payroll period
            payroll_period = await database.payroll_periods.find_one({"_id": payroll_entry["payroll_period_id"]})
            
            # Get employee details
            employee = await database.users.find_one({"_id": payroll_entry["employee_id"]})
            
            # Generate slip number
            slip_count = await database.salary_slips.count_documents({})
            slip_number = f"SLIP-{datetime.utcnow().strftime('%Y%m')}-{slip_count + 1:04d}"
            
            salary_slip = {
                "payroll_entry_id": payroll_entry_id,
                "employee_id": str(employee["_id"]),
                "employee_name": f"{employee.get('first_name', '')} {employee.get('last_name', '')}",
                "employee_email": employee.get("email", ""),
                "employee_phone": employee.get("phone_number", ""),
                "period_name": payroll_period["name"],
                "period_start": payroll_period["start_date"],
                "period_end": payroll_period["end_date"],
                "payment_date": payroll_period["payment_date"],
                "basic_salary": payroll_entry["basic_salary"],
                "allowances": payroll_entry["allowances"],
                "deductions": payroll_entry["deductions"],
                "bonuses": payroll_entry["bonuses"],
                "gross_salary": payroll_entry["gross_salary"],
                "total_deductions": payroll_entry["total_deductions"],
                "net_salary": payroll_entry["net_salary"],
                "employer_pf_contribution": payroll_entry["employer_pf_contribution"],
                "employer_esi_contribution": payroll_entry["employer_esi_contribution"],
                "generated_at": datetime.utcnow(),
                "slip_number": slip_number
            }
            
            result = await database.salary_slips.insert_one(salary_slip)
            salary_slip["id"] = str(result.inserted_id)
            
            return salary_slip
            
        except Exception as e:
            logger.error(f"Salary slip generation error: {e}")
            raise


# Global payroll processor instance
payroll_processor = PayrollProcessor()
