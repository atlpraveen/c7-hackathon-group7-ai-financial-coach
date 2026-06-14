"""Investment allocation guidance based on risk tolerance and horizon.

Educational only — not personalised financial advice.
"""
from __future__ import annotations

from .financial_utils import clamp

_PROFILES = {
    "conservative": {"equity": 40, "bonds": 50, "cash": 10},
    "moderate": {"equity": 65, "bonds": 25, "cash": 10},
    "aggressive": {"equity": 85, "bonds": 10, "cash": 5},
}


def allocation_for(risk_tolerance: str, age: int | None = None) -> dict:
    """Return a target asset allocation.

    Starts from a risk-tolerance baseline, then nudges equity using a
    "110 - age" heuristic when age is provided.
    """
    base = dict(_PROFILES.get((risk_tolerance or "moderate").lower(), _PROFILES["moderate"]))
    if age:
        age_equity = clamp(110 - age, 20, 90)
        # Blend the risk-based equity with the age-based equity.
        equity = round((base["equity"] + age_equity) / 2)
        equity = int(clamp(equity, 10, 95))
        # Re-split the remainder between bonds and cash, keeping cash modest.
        remainder = 100 - equity
        cash = int(clamp(remainder * 0.2, 3, 15))
        bonds = remainder - cash
        base = {"equity": equity, "bonds": bonds, "cash": cash}
    return base


def project_growth(principal: float, monthly_contribution: float, years: int,
                   annual_return: float) -> list[dict]:
    """Compound-growth projection of an investment account, yearly snapshots."""
    balance = principal
    monthly_rate = annual_return / 100 / 12
    out = [{"year": 0, "balance": round(balance, 2), "contributed": round(principal, 2)}]
    contributed = principal
    for year in range(1, years + 1):
        for _ in range(12):
            balance = balance * (1 + monthly_rate) + monthly_contribution
            contributed += monthly_contribution
        out.append(
            {"year": year, "balance": round(balance, 2), "contributed": round(contributed, 2)}
        )
    return out


def build_investment_plan(
    risk_tolerance: str,
    investable_monthly: float,
    age: int | None = None,
    current_portfolio: float = 0.0,
    horizon_years: int = 20,
) -> dict:
    alloc = allocation_for(risk_tolerance, age)
    # Expected long-run nominal returns per asset class (illustrative).
    exp_returns = {"equity": 7.0, "bonds": 3.0, "cash": 1.5}
    blended_return = round(
        sum(alloc[a] / 100 * exp_returns[a] for a in alloc), 2
    )
    projection = project_growth(
        current_portfolio, max(investable_monthly, 0), horizon_years, blended_return
    )
    final = projection[-1]
    return {
        "risk_tolerance": (risk_tolerance or "moderate").lower(),
        "age": age,
        "allocation": alloc,
        "expected_annual_return": blended_return,
        "investable_monthly": round(investable_monthly, 2),
        "horizon_years": horizon_years,
        "projection": projection,
        "projected_balance": final["balance"],
        "total_contributed": final["contributed"],
        "projected_growth": round(final["balance"] - final["contributed"], 2),
        "disclaimer": "Illustrative, educational projections — not personalised investment advice.",
    }
