"""
Tests — Commission, Credit-Card Cashback, Reimbursement, Claims, Tax, Salary Integration
Run: pytest tests/test_commission_credit_salary.py -v
"""
import sys, os

# Make `app` package importable without installing the project
_BACKEND = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "backend"))
if _BACKEND not in sys.path:
    sys.path.insert(0, _BACKEND)

import pytest

pytest_plugins = ("anyio",)

from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

# ── helpers ───────────────────────────────────────────────────────────────────

def _make_db(**collections):
    """Build a mock motor-style database object."""
    db = MagicMock()
    for name, docs in collections.items():
        col = MagicMock()
        col.find_one = AsyncMock(return_value=docs[0] if docs else None)
        col.find = MagicMock(return_value=_async_cursor(docs))
        col.insert_one = AsyncMock(return_value=MagicMock(inserted_id="mock-id"))
        col.update_one = AsyncMock(return_value=MagicMock(modified_count=1))
        col.update_many = AsyncMock(return_value=MagicMock(modified_count=len(docs)))
        col.count_documents = AsyncMock(return_value=len(docs))
        setattr(db, name, col)
    return db


def _async_cursor(docs):
    """Motor-style async cursor stub."""
    cursor = MagicMock()
    cursor.to_list = AsyncMock(return_value=list(docs))
    cursor.sort = MagicMock(return_value=cursor)
    return cursor


# ═════════════════════════════════════════════════════════════════════════════
# 1. COMMISSION
# ═════════════════════════════════════════════════════════════════════════════

class TestCommissionCalculator:
    def setup_method(self):
        from app.commission import CommissionCalculator
        self.calc = CommissionCalculator()

    def test_property_sale_rate(self):
        from app.schemas import CommissionType
        rate = self.calc.default_rates[CommissionType.PROPERTY_SALE]
        assert rate == 2.0

    def test_builder_property_rate(self):
        from app.schemas import CommissionType
        rate = self.calc.default_rates[CommissionType.BUILDER_PROPERTY]
        assert rate == 3.0

    def test_loan_commission_rate(self):
        from app.schemas import CommissionType
        rate = self.calc.default_rates[CommissionType.LOAN_COMMISSION]
        assert rate == 0.5

    def test_credit_card_cashback_rate(self):
        from app.schemas import CommissionType
        rate = self.calc.default_rates[CommissionType.CREDIT_CARD_CASHBACK]
        assert rate == 1.0

    def test_calculate_commission_basic(self):
        from app.schemas import CommissionType
        result = self.calc.calculate_commission(
            deal_amount=100_000,
            commission_type=CommissionType.PROPERTY_SALE,
        )
        assert result["calculated_amount"] == pytest.approx(2_000.0)

    def test_calculate_commission_builder_property(self):
        from app.schemas import CommissionType
        result = self.calc.calculate_commission(
            deal_amount=50_000,
            commission_type=CommissionType.BUILDER_PROPERTY,
        )
        assert result["calculated_amount"] == pytest.approx(1_500.0)

    def test_calculate_commission_loan(self):
        from app.schemas import CommissionType
        result = self.calc.calculate_commission(
            deal_amount=200_000,
            commission_type=CommissionType.LOAN_COMMISSION,
        )
        assert result["calculated_amount"] == pytest.approx(1_000.0)


class TestCommissionAnalytics:
    def setup_method(self):
        from app.commission import CommissionProcessor
        self.processor = CommissionProcessor()

    def _make_commission(self, amount, status, month=1):
        return {
            "calculated_amount": amount,
            "status": status,
            "recipient_id": "emp-1",
            "commission_rule_id": "rule-1",
            "created_at": datetime(2024, month, 15),
        }

    def test_monthly_returns_grouping(self):
        from app.schemas import CommissionStatus
        commissions = [
            self._make_commission(1000, CommissionStatus.PAID, month=1),
            self._make_commission(2000, CommissionStatus.PAID, month=1),
            self._make_commission(500,  CommissionStatus.PAID, month=2),
        ]
        result = self.processor._calculate_monthly_returns(commissions)
        assert len(result) == 2
        jan = next(r for r in result if r["month"] == "2024-01")
        assert jan["commission_returns"] == pytest.approx(3000.0)

    def test_yearly_returns_grouping(self):
        from app.schemas import CommissionStatus
        commissions = [
            self._make_commission(1000, CommissionStatus.PAID, month=1),
            self._make_commission(2000, CommissionStatus.PAID, month=6),
        ]
        result = self.processor._calculate_yearly_returns(commissions)
        assert len(result) == 1
        assert result[0]["commission_returns"] == pytest.approx(3000.0)

    @pytest.mark.asyncio
    async def test_analytics_date_filter_no_mutation(self):
        """Ensure the date filter dict is not mutated (regression)."""
        from app.commission import CommissionProcessor
        from app.schemas import CommissionStatus

        processor = CommissionProcessor()
        db = _make_db(
            commissions=[],
            commission_rules=[],
        )
        db.commissions.find = MagicMock(return_value=_async_cursor([]))
        db.commission_rules.find = MagicMock(return_value=_async_cursor([]))

        start = datetime(2024, 1, 1)
        end = datetime(2024, 12, 31)
        result = await processor.get_commission_analytics(
            database=db,
            start_date=start,
            end_date=end,
        )
        assert result["total_commissions"] == 0


# ═════════════════════════════════════════════════════════════════════════════
# 2. CREDIT CARD CASHBACK
# ═════════════════════════════════════════════════════════════════════════════

class TestRewardCalculator:
    def setup_method(self):
        from app.credit_card import RewardCalculator
        self.calc = RewardCalculator()

    def test_points_no_category(self):
        pts = self.calc.calculate_points(amount=1000, base_reward_rate=2)
        assert pts == 2000

    def test_points_with_travel_multiplier(self):
        from app.schemas import RewardCategory
        pts = self.calc.calculate_points(1000, 2, category=RewardCategory.TRAVEL)
        assert pts == 4000  # multiplier=2.0

    def test_cashback_from_points(self):
        cb = self.calc.calculate_cashback(points=10_000, cashback_rate=1.0)
        assert cb == pytest.approx(100.0)  # 10000 * 0.01 * 1.0

    def test_cashback_with_higher_rate(self):
        cb = self.calc.calculate_cashback(points=5_000, cashback_rate=2.0)
        assert cb == pytest.approx(100.0)  # 5000 * 0.01 * 2.0


class TestCreditCardComparator:
    def setup_method(self):
        from app.credit_card import CreditCardComparator
        self.comparator = CreditCardComparator()

    def test_get_best_cards_returns_list(self):
        results = self.comparator.get_best_cards_for_cashback(spend_amount=5000)
        assert isinstance(results, list)
        assert len(results) > 0

    def test_best_cards_sorted_by_net_cashback(self):
        results = self.comparator.get_best_cards_for_cashback(spend_amount=10_000)
        net_values = [r["net_cashback_after_fee"] for r in results]
        assert net_values == sorted(net_values, reverse=True)

    def test_best_cards_with_category(self):
        from app.schemas import RewardCategory
        results = self.comparator.get_best_cards_for_cashback(
            spend_amount=5000, category=RewardCategory.TRAVEL
        )
        assert all("card_name" in r for r in results)

    def test_best_cards_invalid_spend_raises(self):
        with pytest.raises(Exception):
            self.comparator.get_best_cards_for_cashback(spend_amount=-100)


# ═════════════════════════════════════════════════════════════════════════════
# 3. REIMBURSEMENT
# ═════════════════════════════════════════════════════════════════════════════

class TestReimbursementManager:
    def setup_method(self):
        from app.reimbursement import ReimbursementManager
        self.mgr = ReimbursementManager()

    @pytest.mark.asyncio
    async def test_submit_creates_record(self):
        employee = {"_id": "emp-1", "first_name": "Alice", "last_name": "Smith"}
        db = _make_db(users=[employee], reimbursements=[])

        data = {
            "employee_id": "emp-1",
            "category": "travel",
            "title": "Client Visit",
            "amount": 3500.0,
            "expense_date": datetime.utcnow(),
        }
        record = await self.mgr.submit_reimbursement(data, db)
        assert record["status"] == "submitted"
        assert record["employee_name"] == "Alice Smith"
        assert record["approved_amount"] is None

    @pytest.mark.asyncio
    async def test_approve_updates_status(self):
        existing = {
            "_id": "reimb-1",
            "status": "submitted",
            "amount": 1000.0,
            "employee_name": "Bob",
        }
        db = _make_db(reimbursements=[existing])
        db.reimbursements.find_one = AsyncMock(return_value=existing)

        result = await self.mgr.approve_reimbursement(
            reimbursement_id="reimb-1",
            approved_amount=900.0,
            reviewed_by="mgr-1",
            database=db,
        )
        assert result["status"] == "approved"
        assert result["approved_amount"] == 900.0

    @pytest.mark.asyncio
    async def test_reject_sets_reason(self):
        existing = {
            "_id": "reimb-2",
            "status": "submitted",
            "amount": 500.0,
            "employee_name": "Carol",
        }
        db = _make_db(reimbursements=[existing])
        db.reimbursements.find_one = AsyncMock(return_value=existing)

        result = await self.mgr.reject_reimbursement(
            reimbursement_id="reimb-2",
            reviewed_by="mgr-1",
            rejection_reason="Missing receipt",
            database=db,
        )
        assert result["status"] == "rejected"
        assert result["rejection_reason"] == "Missing receipt"

    @pytest.mark.asyncio
    async def test_analytics_totals(self):
        records = [
            {"amount": 1000.0, "status": "approved",  "approved_amount": 900.0, "category": "travel"},
            {"amount": 500.0,  "status": "submitted",  "approved_amount": None,  "category": "meals"},
            {"amount": 300.0,  "status": "paid",       "approved_amount": 300.0, "category": "travel"},
        ]
        db = _make_db(reimbursements=records)
        db.reimbursements.find = MagicMock(return_value=_async_cursor(records))

        analytics = await self.mgr.get_analytics(None, db)
        assert analytics["total_submitted"] == pytest.approx(1800.0)
        assert analytics["total_paid"] == pytest.approx(300.0)
        assert analytics["total_pending"] == pytest.approx(500.0)


# ═════════════════════════════════════════════════════════════════════════════
# 4. CLAIMS
# ═════════════════════════════════════════════════════════════════════════════

class TestClaimsManager:
    def setup_method(self):
        from app.claims import ClaimsManager
        self.mgr = ClaimsManager()

    @pytest.mark.asyncio
    async def test_create_claim(self):
        employee = {"_id": "emp-1", "first_name": "Dave", "last_name": "Lee"}
        db = _make_db(users=[employee], claims=[])
        db.claims.count_documents = AsyncMock(return_value=0)

        data = {
            "employee_id": "emp-1",
            "claim_type": "medical",
            "title": "Hospital Bill",
            "description": "Emergency surgery",
            "claimed_amount": 50_000.0,
            "incident_date": datetime.utcnow(),
            "priority": "high",
        }
        record = await self.mgr.create_claim(data, db)
        assert record["status"] == "open"
        assert record["claim_number"].startswith("CLM-")

    @pytest.mark.asyncio
    async def test_resolve_claim_approved(self):
        from app.schemas import ClaimStatus
        existing = {
            "_id": "clm-1",
            "status": "under_investigation",
            "claimed_amount": 20_000.0,
            "employee_name": "Eve",
        }
        db = _make_db(claims=[existing])
        db.claims.find_one = AsyncMock(return_value=existing)

        result = await self.mgr.resolve_claim(
            claim_id="clm-1",
            status=ClaimStatus.APPROVED,
            resolution_notes="Verified and approved",
            approved_amount=18_000.0,
            database=db,
        )
        assert result["status"] == "approved"
        assert result["approved_amount"] == 18_000.0

    @pytest.mark.asyncio
    async def test_resolve_closed_claim_raises(self):
        from app.schemas import ClaimStatus
        existing = {"_id": "clm-2", "status": "closed", "claimed_amount": 1000.0}
        db = _make_db(claims=[existing])
        db.claims.find_one = AsyncMock(return_value=existing)

        with pytest.raises(ValueError, match="already closed"):
            await self.mgr.resolve_claim(
                claim_id="clm-2",
                status=ClaimStatus.APPROVED,
                resolution_notes="Try again",
                approved_amount=1000.0,
                database=db,
            )

    @pytest.mark.asyncio
    async def test_analytics_counts(self):
        records = [
            {"status": "open",               "claimed_amount": 1000, "claim_type": "medical",   "priority": "high"},
            {"status": "approved",           "claimed_amount": 2000, "claim_type": "accident",  "priority": "medium", "approved_amount": 1800},
            {"status": "rejected",           "claimed_amount": 500,  "claim_type": "medical",   "priority": "low",    "approved_amount": None},
            {"status": "partially_approved", "claimed_amount": 3000, "claim_type": "salary_dispute", "priority": "urgent", "approved_amount": 1500},
        ]
        db = _make_db(claims=records)
        db.claims.find = MagicMock(return_value=_async_cursor(records))

        analytics = await self.mgr.get_analytics(db)
        assert analytics["total_claims"] == 4
        assert analytics["open_claims"] == 1
        assert analytics["rejected_claims"] == 1
        assert analytics["approved_claims"] == 2  # approved + partially_approved


# ═════════════════════════════════════════════════════════════════════════════
# 5. TAX ENGINE
# ═════════════════════════════════════════════════════════════════════════════

class TestTaxEngine:
    def setup_method(self):
        from app.tax import TaxEngine
        self.engine = TaxEngine()

    def test_zero_tax_below_threshold_new_regime(self):
        from app.schemas import TaxRegime
        result = self.engine.compute(
            gross_annual_income=300_000, regime=TaxRegime.NEW
        )
        assert result["total_tax_liability"] == pytest.approx(0.0)

    def test_rebate_87a_new_regime(self):
        """Income of 700k under new regime qualifies for full 87A rebate → 0 tax."""
        from app.schemas import TaxRegime
        result = self.engine.compute(
            gross_annual_income=700_000, regime=TaxRegime.NEW
        )
        assert result["total_tax_liability"] == pytest.approx(0.0)

    def test_old_regime_deductions_reduce_tax(self):
        from app.schemas import TaxRegime
        no_deductions = self.engine.compute(
            gross_annual_income=1_200_000, regime=TaxRegime.OLD
        )
        with_deductions = self.engine.compute(
            gross_annual_income=1_200_000,
            regime=TaxRegime.OLD,
            section_80c=150_000,
            section_80d=25_000,
        )
        assert with_deductions["total_tax_liability"] < no_deductions["total_tax_liability"]

    def test_monthly_tds_is_annual_divided_by_12(self):
        from app.schemas import TaxRegime
        annual = 1_500_000.0
        result = self.engine.compute(gross_annual_income=annual, regime=TaxRegime.NEW)
        expected_monthly = result["total_tax_liability"] / 12
        monthly = self.engine.monthly_tds_for_salary(annual / 12, regime=TaxRegime.NEW)
        assert monthly == pytest.approx(expected_monthly, rel=1e-2)

    def test_effective_rate_is_positive_for_high_income(self):
        from app.schemas import TaxRegime
        result = self.engine.compute(gross_annual_income=2_000_000, regime=TaxRegime.NEW)
        assert result["effective_tax_rate"] > 0

    def test_surcharge_kicks_in_above_5m(self):
        from app.schemas import TaxRegime
        result_low  = self.engine.compute(gross_annual_income=4_000_000, regime=TaxRegime.NEW)
        result_high = self.engine.compute(gross_annual_income=6_000_000, regime=TaxRegime.NEW)
        assert result_high["surcharge"] > result_low["surcharge"]

    def test_tds_already_deducted_reduces_balance(self):
        from app.schemas import TaxRegime
        base = self.engine.compute(gross_annual_income=1_200_000, regime=TaxRegime.NEW)
        with_tds = self.engine.compute(
            gross_annual_income=1_200_000,
            regime=TaxRegime.NEW,
            tds_already_deducted=50_000,
        )
        assert with_tds["balance_tax_payable"] == pytest.approx(
            max(0, base["total_tax_liability"] - 50_000), rel=1e-3
        )


# ═════════════════════════════════════════════════════════════════════════════
# 6. SALARY INTEGRATION (reimbursement + tax wired into payroll)
# ═════════════════════════════════════════════════════════════════════════════

class TestSalaryCalculator:
    def setup_method(self):
        from app.salary import SalaryCalculator
        self.calc = SalaryCalculator()

    def test_net_salary_basic(self):
        result = self.calc.calculate_net_salary(
            basic_salary=30_000,
            allowances={"hra": 10_000},
            deductions={},
            bonuses={},
        )
        assert result["gross_salary"] == pytest.approx(40_000.0)
        assert result["net_salary"] < result["gross_salary"]
        assert result["pf_deduction"] == pytest.approx(3_600.0)  # 12% of 30k

    def test_other_deductions_field_present(self):
        result = self.calc.calculate_net_salary(
            basic_salary=20_000,
            allowances={},
            deductions={"loan": 1000},
            bonuses={},
        )
        assert "other_deductions" in result
        assert result["other_deductions"] == pytest.approx(1000.0)

    def test_reimbursement_total_initialised_to_zero(self):
        result = self.calc.calculate_net_salary(
            basic_salary=25_000,
            allowances={},
            deductions={},
            bonuses={},
        )
        assert "reimbursement_total" in result
        assert result["reimbursement_total"] == pytest.approx(0.0)

    def test_tax_delegation_to_tax_engine(self):
        """calculate_tax should delegate to TaxEngine and return a positive number for high income."""
        from app.schemas import TaxRegime
        tax = self.calc.calculate_tax(annual_income=1_500_000, regime=TaxRegime.NEW)
        assert tax > 0

    def test_esi_only_below_threshold(self):
        assert self.calc.calculate_esi(21_000) > 0
        assert self.calc.calculate_esi(21_001) == 0.0


class TestPayrollIntegration:
    """End-to-end payroll run with reimbursements wired in."""

    @pytest.mark.asyncio
    async def test_payroll_adds_reimbursement_to_net(self):
        from app.salary import PayrollProcessor

        period = {
            "_id": "period-1",
            "name": "May 2024",
            "start_date": datetime(2024, 5, 1),
            "end_date": datetime(2024, 5, 31),
            "payment_date": datetime(2024, 6, 1),
            "frequency": "monthly",
        }
        employee = {
            "_id": "emp-1",
            "first_name": "Frank",
            "last_name": "Green",
            "role": "employee",
            "is_active": True,
            "designation": "Engineer",
        }
        component = {
            "_id": "comp-1",
            "employee_id": "emp-1",
            "component_type": "basic",
            "name": "Basic",
            "amount": 40_000.0,
            "effective_date": datetime(2024, 1, 1),
            "expiry_date": None,
        }
        reimbursement = {
            "id": "reimb-1",
            "employee_id": "emp-1",
            "status": "approved",
            "approved_amount": 2_500.0,
        }

        db = MagicMock()
        db.payroll_periods.find_one = AsyncMock(return_value=period)
        db.payroll_periods.update_one = AsyncMock()
        db.users.find = MagicMock(return_value=_async_cursor([employee]))
        db.salary_components.find = MagicMock(return_value=_async_cursor([component]))
        db.payroll_entries.insert_one = AsyncMock(
            return_value=MagicMock(inserted_id="entry-1")
        )
        db.reimbursements.find = MagicMock(return_value=_async_cursor([reimbursement]))
        db.reimbursements.update_many = AsyncMock(return_value=MagicMock(modified_count=1))

        processor = PayrollProcessor()
        result = await processor.process_payroll_period("period-1", db)

        assert result["processed_entries"] == 1
        entry = result["entries"][0]
        assert entry["reimbursement_total"] == pytest.approx(2_500.0)
        # Net salary includes the reimbursement
        assert entry["net_salary"] > entry["basic_salary"]
