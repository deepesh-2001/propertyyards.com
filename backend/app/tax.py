"""
Tax Module
Indian income-tax computation (FY 2024-25) supporting old and new regimes.
Covers: slab tax, surcharge, cess, TDS, Form-16 generation, and monthly TDS scheduling.
"""
from typing import Dict, Any, Optional, List
from datetime import datetime
import logging

from app.schemas import TaxRegime

logger = logging.getLogger(__name__)


# ── Built-in slab tables (FY 2024-25) ────────────────────────────────────────

_NEW_REGIME_SLABS: List[Dict[str, Any]] = [
    {"min": 0,        "max": 300_000,    "rate": 0.00},
    {"min": 300_001,  "max": 600_000,    "rate": 0.05},
    {"min": 600_001,  "max": 900_000,    "rate": 0.10},
    {"min": 900_001,  "max": 1_200_000,  "rate": 0.15},
    {"min": 1_200_001,"max": 1_500_000,  "rate": 0.20},
    {"min": 1_500_001,"max": None,       "rate": 0.30},
]

_OLD_REGIME_SLABS: List[Dict[str, Any]] = [
    {"min": 0,        "max": 250_000,    "rate": 0.00},
    {"min": 250_001,  "max": 500_000,    "rate": 0.05},
    {"min": 500_001,  "max": 1_000_000,  "rate": 0.20},
    {"min": 1_000_001,"max": None,       "rate": 0.30},
]

# Standard deduction (FY 2024-25)
_STANDARD_DEDUCTION_NEW = 75_000
_STANDARD_DEDUCTION_OLD = 50_000


class TaxEngine:
    """Core income-tax computation engine."""

    # ── Slab tax calculation ──────────────────────────────────────────────────

    def _apply_slabs(self, taxable_income: float, slabs: List[Dict[str, Any]]) -> float:
        tax = 0.0
        for slab in slabs:
            if taxable_income <= 0:
                break
            lower = slab["min"]
            upper = slab["max"]
            rate = slab["rate"]
            if upper is None:
                slab_income = max(0, taxable_income - lower + 1)
            else:
                slab_income = max(0, min(taxable_income, upper) - lower + 1)
            tax += slab_income * rate
        return tax

    def _surcharge(self, basic_tax: float, taxable_income: float) -> float:
        """Surcharge on basic tax (same for both regimes FY 2024-25)."""
        if taxable_income <= 5_000_000:
            return 0.0
        elif taxable_income <= 10_000_000:
            return basic_tax * 0.10
        elif taxable_income <= 20_000_000:
            return basic_tax * 0.15
        elif taxable_income <= 50_000_000:
            return basic_tax * 0.25
        else:
            return basic_tax * 0.37

    def compute(
        self,
        gross_annual_income: float,
        regime: TaxRegime,
        hra_exemption: float = 0,
        section_80c: float = 0,
        section_80d: float = 0,
        section_80ccd: float = 0,
        other_deductions: float = 0,
        tds_already_deducted: float = 0,
    ) -> Dict[str, Any]:
        """Compute annual tax liability."""
        cess_rate = 0.04

        if regime == TaxRegime.NEW:
            std_deduction = _STANDARD_DEDUCTION_NEW
            # New regime: no 80C/80D/HRA except NPS (80CCD 1B up to 50k)
            total_exemptions = std_deduction + min(section_80ccd, 50_000)
            slabs = _NEW_REGIME_SLABS
        else:
            std_deduction = _STANDARD_DEDUCTION_OLD
            # Old regime: all deductions apply
            total_exemptions = (
                std_deduction
                + hra_exemption
                + min(section_80c, 150_000)
                + min(section_80d, 75_000)
                + min(section_80ccd, 50_000)
                + other_deductions
            )
            slabs = _OLD_REGIME_SLABS

        taxable_income = max(0, gross_annual_income - total_exemptions)

        # Rebate u/s 87A
        basic_tax = self._apply_slabs(taxable_income, slabs)
        if regime == TaxRegime.NEW and taxable_income <= 700_000:
            basic_tax = max(0, basic_tax - 25_000)
        elif regime == TaxRegime.OLD and taxable_income <= 500_000:
            basic_tax = max(0, basic_tax - 12_500)

        surcharge = self._surcharge(basic_tax, taxable_income)
        cess = (basic_tax + surcharge) * cess_rate
        total_tax = basic_tax + surcharge + cess

        balance = max(0, total_tax - tds_already_deducted)
        monthly_tds = round(balance / 12, 2)
        effective_rate = (total_tax / gross_annual_income * 100) if gross_annual_income else 0

        return {
            "gross_annual_income": round(gross_annual_income, 2),
            "total_exemptions": round(total_exemptions, 2),
            "taxable_income": round(taxable_income, 2),
            "basic_tax": round(basic_tax, 2),
            "surcharge": round(surcharge, 2),
            "cess": round(cess, 2),
            "total_tax_liability": round(total_tax, 2),
            "tds_already_deducted": round(tds_already_deducted, 2),
            "balance_tax_payable": round(balance, 2),
            "monthly_tds": monthly_tds,
            "effective_tax_rate": round(effective_rate, 4),
            "computed_at": datetime.utcnow(),
        }

    # ── Monthly TDS for payroll ───────────────────────────────────────────────

    def monthly_tds_for_salary(
        self,
        monthly_gross: float,
        regime: TaxRegime = TaxRegime.NEW,
    ) -> float:
        """Quick monthly TDS estimate used during payroll run."""
        annual = monthly_gross * 12
        result = self.compute(gross_annual_income=annual, regime=regime)
        return result["monthly_tds"]

    # ── Form-16 generation ───────────────────────────────────────────────────

    async def generate_form16(
        self,
        employee_id: str,
        financial_year: str,
        database,
    ) -> Dict[str, Any]:
        """Generate Form-16 summary from salary slips for the financial year."""
        try:
            employee = await database.users.find_one({"_id": employee_id})
            if not employee:
                raise ValueError("Employee not found")

            # Aggregate salary slips for the FY
            slips = await database.salary_slips.find(
                {"employee_id": employee_id}
            ).to_list(length=500)

            gross_salary = sum(s.get("gross_salary", 0) for s in slips)
            tds_deducted = sum(s.get("tax_deduction", 0) for s in slips)

            # Use new regime by default; can be parameterised later
            tax_result = self.compute(
                gross_annual_income=gross_salary,
                regime=TaxRegime.NEW,
                tds_already_deducted=tds_deducted,
            )

            from app.config import settings
            employer_name = getattr(settings, "COMPANY_NAME", "Housing Platform Pvt Ltd")

            form16: Dict[str, Any] = {
                "employee_id": employee_id,
                "employee_name": f"{employee.get('first_name', '')} {employee.get('last_name', '')}",
                "employee_pan": employee.get("pan_number"),
                "financial_year": financial_year,
                "employer_name": employer_name,
                "gross_salary": gross_salary,
                "exempt_allowances": tax_result["total_exemptions"],
                "net_salary": gross_salary,
                "deductions_80c": 0.0,
                "deductions_80d": 0.0,
                "other_deductions": 0.0,
                "taxable_income": tax_result["taxable_income"],
                "total_tax": tax_result["total_tax_liability"],
                "tds_deducted": tds_deducted,
                "balance_payable": tax_result["balance_tax_payable"],
                "generated_at": datetime.utcnow(),
            }

            # Persist to database
            result = await database.form16.insert_one({**form16})
            form16["id"] = str(result.inserted_id)

            logger.info(f"Form-16 generated for {employee_id} FY {financial_year}")
            return form16
        except Exception as e:
            logger.error(f"Form-16 generation error: {e}")
            raise


tax_engine = TaxEngine()
