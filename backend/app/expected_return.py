"""
Expected Return Calculator
A general-purpose engine to project expected returns for any investable item
(properties, future projects, investment opportunities, loans, REITs, etc.).

It supports capital appreciation (compounded), rental/income yield, one-time and
recurring costs, inflation-adjusted (real) returns, and risk-adjusted returns.
"""
import math
from typing import Dict, Any, List, Optional

# Compounding periods per year by frequency name.
COMPOUNDING_FREQUENCIES = {
    "annual": 1,
    "semi_annual": 2,
    "quarterly": 4,
    "monthly": 12,
}

# Indicative haircut applied to projected return based on risk level.
RISK_FACTORS = {
    "low": 0.95,
    "moderate": 0.85,
    "high": 0.70,
    "speculative": 0.55,
}


class ExpectedReturnCalculator:
    """Projects expected returns for an investment."""

    def calculate(
        self,
        principal: float,
        term_months: int,
        annual_return_rate: Optional[float] = None,
        appreciation_annual: Optional[float] = None,
        rental_yield_annual: Optional[float] = None,
        compounding: bool = True,
        compounding_frequency: str = "annual",
        one_time_costs: float = 0.0,
        recurring_monthly_costs: float = 0.0,
        inflation_rate_annual: Optional[float] = None,
        risk_level: Optional[str] = None,
        currency: str = "INR",
    ) -> Dict[str, Any]:
        """Compute the expected return projection.

        - ``annual_return_rate`` / ``appreciation_annual`` drive capital growth.
          If ``appreciation_annual`` is given it is used; otherwise the
          ``annual_return_rate`` is treated as the capital growth rate.
        - ``rental_yield_annual`` adds income on top of capital growth.
        - Provide either an overall ``annual_return_rate`` (simple case) or a
          ``appreciation_annual`` + ``rental_yield_annual`` split.
        """
        if principal <= 0:
            raise ValueError("principal must be positive")
        if term_months <= 0:
            raise ValueError("term_months must be positive")

        years = term_months / 12.0
        periods_per_year = COMPOUNDING_FREQUENCIES.get(compounding_frequency, 1)

        # Capital growth rate (% per year).
        if appreciation_annual is not None:
            capital_rate = appreciation_annual
        elif annual_return_rate is not None:
            capital_rate = annual_return_rate
        else:
            capital_rate = 0.0

        income_rate = rental_yield_annual or 0.0

        # Capital value at maturity.
        maturity_capital = self._grow(
            principal, capital_rate, years, compounding, periods_per_year
        )
        capital_gain = maturity_capital - principal

        # Income (not reinvested), net of recurring costs.
        gross_annual_income = principal * (income_rate / 100.0)
        net_annual_income = gross_annual_income - (recurring_monthly_costs * 12.0)
        total_income = net_annual_income * years
        monthly_income = net_annual_income / 12.0

        # Totals.
        total_return = capital_gain + total_income - one_time_costs
        maturity_value = principal + total_return
        absolute_roi_pct = (total_return / principal) * 100.0

        # Annualized return (CAGR) on total value.
        if maturity_value > 0 and years > 0:
            annualized_roi_pct = ((maturity_value / principal) ** (1.0 / years) - 1.0) * 100.0
        else:
            annualized_roi_pct = 0.0

        # Inflation-adjusted (real) annualized return.
        real_annualized_roi_pct = None
        if inflation_rate_annual is not None:
            real_annualized_roi_pct = (
                (1.0 + annualized_roi_pct / 100.0) / (1.0 + inflation_rate_annual / 100.0) - 1.0
            ) * 100.0

        # Risk-adjusted return.
        risk_adjusted_roi_pct = None
        risk_factor = None
        if risk_level is not None:
            risk_factor = RISK_FACTORS.get(risk_level.lower())
            if risk_factor is not None:
                risk_adjusted_roi_pct = absolute_roi_pct * risk_factor

        effective_annual_rate = capital_rate + income_rate

        return {
            "currency": currency,
            "principal": round(principal, 2),
            "term_months": term_months,
            "years": round(years, 4),
            "effective_annual_rate": round(effective_annual_rate, 4),
            "capital_appreciation_rate": round(capital_rate, 4),
            "rental_yield_rate": round(income_rate, 4),
            "maturity_value": round(maturity_value, 2),
            "total_return": round(total_return, 2),
            "capital_gain": round(capital_gain, 2),
            "total_rental_income": round(total_income, 2),
            "monthly_income": round(monthly_income, 2),
            "one_time_costs": round(one_time_costs, 2),
            "absolute_roi_pct": round(absolute_roi_pct, 4),
            "annualized_roi_pct": round(annualized_roi_pct, 4),
            "real_annualized_roi_pct": round(real_annualized_roi_pct, 4) if real_annualized_roi_pct is not None else None,
            "risk_level": risk_level,
            "risk_factor": risk_factor,
            "risk_adjusted_roi_pct": round(risk_adjusted_roi_pct, 4) if risk_adjusted_roi_pct is not None else None,
            "yearly_breakdown": self._yearly_breakdown(
                principal, capital_rate, net_annual_income, years,
                compounding, periods_per_year, one_time_costs
            ),
        }

    def _grow(
        self,
        principal: float,
        rate_pct: float,
        years: float,
        compounding: bool,
        periods_per_year: int,
    ) -> float:
        """Grow a principal at an annual rate over a number of years."""
        if compounding:
            n = periods_per_year * years
            period_rate = (rate_pct / 100.0) / periods_per_year
            return principal * ((1.0 + period_rate) ** n)
        return principal * (1.0 + (rate_pct / 100.0) * years)

    def _yearly_breakdown(
        self,
        principal: float,
        capital_rate: float,
        net_annual_income: float,
        years: float,
        compounding: bool,
        periods_per_year: int,
        one_time_costs: float,
    ) -> List[Dict[str, Any]]:
        """Year-by-year projection of capital value, income, and cumulative value."""
        breakdown = []
        total_full_years = max(1, math.ceil(years))
        prev_value = principal
        for y in range(1, total_full_years + 1):
            t = min(float(y), years)
            capital_value = self._grow(principal, capital_rate, t, compounding, periods_per_year)
            cumulative_income = net_annual_income * t
            costs = one_time_costs if y == 1 else 0.0
            cumulative_value = capital_value + cumulative_income - one_time_costs
            year_return = cumulative_value - prev_value
            breakdown.append({
                "year": y,
                "capital_value": round(capital_value, 2),
                "cumulative_income": round(cumulative_income, 2),
                "cumulative_value": round(cumulative_value, 2),
                "year_return": round(year_return, 2),
            })
            prev_value = cumulative_value
        return breakdown


# Global instance
expected_return_calculator = ExpectedReturnCalculator()
