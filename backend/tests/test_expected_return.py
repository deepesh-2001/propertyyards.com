"""
Expected Return Calculator Test Suite
Covers capital appreciation, rental income, costs, inflation-adjusted (real)
returns, risk-adjusted returns, and the yearly breakdown.
"""
import pytest

from app.expected_return import ExpectedReturnCalculator


class TestExpectedReturnCalculator:
    def setup_method(self):
        self.calc = ExpectedReturnCalculator()

    def test_simple_one_year_compound(self):
        r = self.calc.calculate(principal=100_000, term_months=12, annual_return_rate=10)
        assert r["maturity_value"] == 110_000
        assert r["total_return"] == 10_000
        assert r["absolute_roi_pct"] == 10.0
        assert round(r["annualized_roi_pct"], 2) == 10.0
        assert r["currency"] == "INR"

    def test_two_year_compounding(self):
        r = self.calc.calculate(principal=100_000, term_months=24, annual_return_rate=10)
        assert r["maturity_value"] == 121_000  # 100000 * 1.1^2
        assert round(r["annualized_roi_pct"], 2) == 10.0
        assert len(r["yearly_breakdown"]) == 2

    def test_rental_yield_income(self):
        r = self.calc.calculate(
            principal=100_000, term_months=24, appreciation_annual=0, rental_yield_annual=5
        )
        assert r["capital_gain"] == 0
        assert r["total_rental_income"] == 10_000  # 5000/yr * 2
        assert round(r["monthly_income"], 2) == 416.67
        assert r["total_return"] == 10_000

    def test_one_time_costs_reduce_return(self):
        r = self.calc.calculate(
            principal=100_000, term_months=12, annual_return_rate=10, one_time_costs=2_000
        )
        assert r["total_return"] == 8_000
        assert r["maturity_value"] == 108_000

    def test_real_return_with_inflation(self):
        r = self.calc.calculate(
            principal=100_000, term_months=12, annual_return_rate=10, inflation_rate_annual=6
        )
        # (1.10 / 1.06 - 1) * 100
        assert round(r["real_annualized_roi_pct"], 2) == 3.77

    def test_risk_adjusted_return(self):
        r = self.calc.calculate(
            principal=100_000, term_months=12, annual_return_rate=10, risk_level="moderate"
        )
        assert r["risk_factor"] == 0.85
        assert r["risk_adjusted_roi_pct"] == 8.5

    def test_appreciation_plus_rental_combined(self):
        r = self.calc.calculate(
            principal=100_000, term_months=12,
            appreciation_annual=8, rental_yield_annual=4,
        )
        assert r["capital_gain"] == 8_000
        assert r["total_rental_income"] == 4_000
        assert r["total_return"] == 12_000
        assert r["effective_annual_rate"] == 12.0

    def test_monthly_compounding(self):
        r = self.calc.calculate(
            principal=100_000, term_months=12, annual_return_rate=12,
            compounding=True, compounding_frequency="monthly",
        )
        # 100000 * (1 + 0.12/12)^12 ~= 112682.50
        assert r["maturity_value"] == 112_682.5

    def test_simple_interest_no_compounding(self):
        r = self.calc.calculate(
            principal=100_000, term_months=24, annual_return_rate=10, compounding=False
        )
        assert r["maturity_value"] == 120_000  # 100000 * (1 + 0.1*2)

    def test_invalid_principal_raises(self):
        with pytest.raises(ValueError):
            self.calc.calculate(principal=0, term_months=12, annual_return_rate=10)

    def test_invalid_term_raises(self):
        with pytest.raises(ValueError):
            self.calc.calculate(principal=1000, term_months=0, annual_return_rate=10)
