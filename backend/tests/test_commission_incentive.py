"""
Commission & Incentive Test Suite
Covers per-user / per-product commission resolution, the incentive calculation
engine, the async processors (with a mocked database), and router RBAC.
"""
import pytest
from unittest.mock import MagicMock, AsyncMock

from app.commission import (
    CommissionCalculator,
    CommissionProcessor,
    IncentiveCalculator,
    IncentiveProcessor,
)
from app.schemas import CommissionType, CommissionStatus, IncentiveType, IncentiveStatus


def _mock_db():
    """Build a MagicMock database whose collection methods are AsyncMocks."""
    db = MagicMock()
    for coll in ("commission_rules", "commissions", "incentive_rules", "incentives", "users", "brokers"):
        getattr(db, coll).find_one = AsyncMock(return_value=None)
        getattr(db, coll).insert_one = AsyncMock(return_value=MagicMock(inserted_id="generated_id"))
    return db


# ==================== CommissionCalculator ====================

class TestCommissionCalculator:
    def setup_method(self):
        self.calc = CommissionCalculator()

    def test_default_rate(self):
        # property_sale default is 2%
        assert self.calc.calculate_commission(1_000_000, CommissionType.PROPERTY_SALE) == 20_000

    def test_base_rate_override(self):
        # per-user / per-product override beats the default
        assert self.calc.calculate_commission(
            1_000_000, CommissionType.PROPERTY_SALE, base_rate=3.0
        ) == 30_000

    def test_conditions_multiplier_and_bonus(self):
        # base 2% * 1.5 = 3%, + 1 bonus = 4% => 40_000
        amount = self.calc.calculate_commission(
            1_000_000, CommissionType.PROPERTY_SALE,
            conditions={"multiplier": 1.5, "bonus": 1.0}
        )
        assert amount == 40_000

    def test_conditions_cap(self):
        # 2% * 10 = 20% capped to 5% => 50_000
        amount = self.calc.calculate_commission(
            1_000_000, CommissionType.PROPERTY_SALE,
            conditions={"multiplier": 10, "cap": 5.0}
        )
        assert amount == 50_000

    def test_tiered_commission_takes_precedence(self):
        tiers = [
            {"min_amount": 0, "rate": 1.0},
            {"min_amount": 500_000, "rate": 2.0},
        ]
        # first 500k @1% = 5000, next 500k @2% = 10000 => 15000
        amount = self.calc.calculate_commission(
            1_000_000, CommissionType.PROPERTY_SALE, tier_rates=tiers, base_rate=99
        )
        assert amount == 15_000


class TestResolveRateConfig:
    def setup_method(self):
        self.calc = CommissionCalculator()

    def test_user_override_wins(self):
        rule = {
            "base_rate": 2.0,
            "tier_rates": None,
            "user_rates": [{"user_id": "agent1", "rate": 3.5}],
        }
        base, tiers = self.calc.resolve_rate_config(rule, "agent1")
        assert base == 3.5
        assert tiers is None

    def test_user_override_tiers(self):
        rule = {
            "base_rate": 2.0,
            "tier_rates": [{"min_amount": 0, "rate": 1}],
            "user_rates": [{"user_id": "agent1", "tier_rates": [{"min_amount": 0, "rate": 5}]}],
        }
        base, tiers = self.calc.resolve_rate_config(rule, "agent1")
        assert tiers == [{"min_amount": 0, "rate": 5}]

    def test_fallback_to_rule_default(self):
        rule = {"base_rate": 2.0, "tier_rates": None, "user_rates": [{"user_id": "other", "rate": 9}]}
        base, tiers = self.calc.resolve_rate_config(rule, "agent1")
        assert base == 2.0


# ==================== IncentiveCalculator ====================

class TestIncentiveCalculator:
    def setup_method(self):
        self.calc = IncentiveCalculator()

    def test_flat_bonus(self):
        rule = {"incentive_type": IncentiveType.FLAT_BONUS, "flat_amount": 5000}
        assert self.calc.calculate(rule) == 5000

    def test_product_bonus(self):
        rule = {"incentive_type": IncentiveType.PRODUCT_BONUS, "flat_amount": 2500}
        assert self.calc.calculate(rule) == 2500

    def test_per_unit(self):
        rule = {"incentive_type": IncentiveType.PER_UNIT, "per_unit_amount": 1000}
        assert self.calc.calculate(rule, units=6) == 6000

    def test_percentage_of_amount(self):
        rule = {"incentive_type": IncentiveType.PERCENTAGE_OF_AMOUNT, "rate": 2.0}
        assert self.calc.calculate(rule, amount=1_000_000) == 20_000

    def test_target_based_met(self):
        rule = {"incentive_type": IncentiveType.TARGET_BASED, "target": 10, "target_bonus": 7500}
        assert self.calc.calculate(rule, achievement=12) == 7500

    def test_target_based_not_met(self):
        rule = {"incentive_type": IncentiveType.TARGET_BASED, "target": 10, "target_bonus": 7500}
        assert self.calc.calculate(rule, achievement=8) == 0.0

    def test_slab_flat_amount(self):
        rule = {
            "incentive_type": IncentiveType.SLAB,
            "slabs": [{"min": 1, "max": 5, "amount": 5000}, {"min": 6, "amount": 12000}],
        }
        assert self.calc.calculate(rule, units=3) == 5000
        assert self.calc.calculate(rule, units=7) == 12000

    def test_slab_rate_of_amount(self):
        rule = {"incentive_type": IncentiveType.SLAB, "slabs": [{"min": 0, "rate": 2.0}]}
        assert self.calc.calculate(rule, amount=100_000) == 2000

    def test_unknown_type_returns_zero(self):
        assert self.calc.calculate({"incentive_type": "nope"}) == 0.0


# ==================== Async processors ====================

class TestCommissionProcessorAsync:
    async def test_per_user_override_applied(self):
        db = _mock_db()
        db.commission_rules.find_one = AsyncMock(return_value={
            "_id": "rule1",
            "name": "Villa",
            "commission_type": CommissionType.PROPERTY_SALE,
            "base_rate": 2.0,
            "tier_rates": None,
            "conditions": None,
            "user_rates": [{"user_id": "agent1", "rate": 4.0}],
            "product_category": "villa",
            "product_id": None,
        })
        db.users.find_one = AsyncMock(return_value={"first_name": "Ann", "last_name": "Lee"})

        proc = CommissionProcessor()
        commission = await proc.calculate_deal_commission(
            deal_id="d1", deal_type="sale", deal_amount=1_000_000,
            recipient_id="agent1", recipient_type="employee",
            commission_rule_id="rule1", database=db,
        )

        assert commission["applied_base_rate"] == 4.0
        assert commission["calculated_amount"] == 40_000  # 4% of 1M
        assert commission["product_category"] == "villa"
        assert commission["currency"] == "INR"  # defaults to INR (India)
        assert commission["status"] == CommissionStatus.PENDING
        db.commissions.insert_one.assert_awaited_once()

    async def test_rule_currency_used(self):
        db = _mock_db()
        db.commission_rules.find_one = AsyncMock(return_value={
            "_id": "rule1", "name": "US deal",
            "commission_type": CommissionType.PROPERTY_SALE,
            "base_rate": 2.0, "tier_rates": None, "conditions": None,
            "user_rates": None, "currency": "USD",
        })
        db.users.find_one = AsyncMock(return_value={"first_name": "A", "last_name": "B"})
        proc = CommissionProcessor()
        commission = await proc.calculate_deal_commission(
            deal_id="d1", deal_type="sale", deal_amount=1_000,
            recipient_id="agent1", recipient_type="employee",
            commission_rule_id="rule1", database=db,
        )
        assert commission["currency"] == "USD"


class TestIncentiveProcessorAsync:
    async def test_award_incentive_persists(self):
        db = _mock_db()
        db.incentive_rules.find_one = AsyncMock(return_value={
            "_id": "irule1",
            "name": "Monthly units",
            "incentive_type": IncentiveType.PER_UNIT,
            "per_unit_amount": 1000,
            "product_category": "apartment",
            "is_active": True,
        })
        db.users.find_one = AsyncMock(return_value={"first_name": "Sam", "last_name": "Roy"})

        proc = IncentiveProcessor()
        incentive = await proc.award_incentive(
            recipient_id="agent1", recipient_type="employee",
            incentive_rule_id="irule1", database=db, units_sold=5, period="2026-05",
        )

        assert incentive["calculated_amount"] == 5000
        assert incentive["status"] == IncentiveStatus.PENDING
        assert incentive["recipient_name"] == "Sam Roy"
        assert incentive["product_category"] == "apartment"
        assert incentive["currency"] == "INR"  # defaults to INR when rule has none
        db.incentives.insert_one.assert_awaited_once()

    async def test_award_incentive_currency_override(self):
        db = _mock_db()
        db.incentive_rules.find_one = AsyncMock(return_value={
            "_id": "irule1", "name": "Flat", "incentive_type": IncentiveType.FLAT_BONUS,
            "flat_amount": 100, "is_active": True, "currency": "INR",
        })
        db.users.find_one = AsyncMock(return_value={"first_name": "S", "last_name": "R"})
        proc = IncentiveProcessor()
        incentive = await proc.award_incentive(
            recipient_id="a", recipient_type="employee",
            incentive_rule_id="irule1", database=db, currency="AED",
        )
        assert incentive["currency"] == "AED"  # award override beats rule currency

    async def test_award_incentive_unknown_rule_raises(self):
        db = _mock_db()
        db.incentive_rules.find_one = AsyncMock(return_value=None)
        proc = IncentiveProcessor()
        with pytest.raises(ValueError):
            await proc.award_incentive(
                recipient_id="a", recipient_type="employee",
                incentive_rule_id="missing", database=db,
            )

    async def test_award_incentive_inactive_rule_raises(self):
        db = _mock_db()
        db.incentive_rules.find_one = AsyncMock(return_value={
            "_id": "irule1", "name": "x", "incentive_type": IncentiveType.FLAT_BONUS,
            "flat_amount": 100, "is_active": False,
        })
        proc = IncentiveProcessor()
        with pytest.raises(ValueError):
            await proc.award_incentive(
                recipient_id="a", recipient_type="employee",
                incentive_rule_id="irule1", database=db,
            )


# ==================== Router RBAC ====================

class TestCommissionRBAC:
    def test_require_manage_access_blocks_non_privileged(self):
        from app.routers.commission import require_manage_access
        from fastapi import HTTPException
        with pytest.raises(HTTPException) as exc:
            require_manage_access({"role": "agent"})
        assert exc.value.status_code == 403

    def test_require_manage_access_allows_privileged(self):
        from app.routers.commission import require_manage_access
        # should not raise
        for role in ("admin", "manager", "finance"):
            require_manage_access({"role": role})
