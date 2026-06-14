"""Savings strategy calculations: emergency fund, goal planning, savings rate."""
from __future__ import annotations

from .financial_utils import safe_div


def emergency_fund_target(monthly_expenses: float, months: int = 6) -> float:
    return round(monthly_expenses * months, 2)


def savings_rate(monthly_income: float, monthly_savings: float) -> float:
    return round(safe_div(monthly_savings, monthly_income) * 100, 2)


def monthly_required_for_goal(target_amount: float, months: int, current: float = 0.0) -> float:
    months = max(months, 1)
    return round(max(target_amount - current, 0) / months, 2)


def project_savings(monthly_contribution: float, months: int, current: float = 0.0,
                    annual_return: float = 0.0) -> list[dict]:
    """Project a savings balance forward, optionally with a return rate."""
    balance = current
    rate = annual_return / 100 / 12
    out = []
    for m in range(1, months + 1):
        balance = balance * (1 + rate) + monthly_contribution
        out.append({"month": m, "balance": round(balance, 2)})
    return out


def build_savings_plan(
    monthly_income: float,
    monthly_expenses: float,
    current_savings: float,
    emergency_months: int = 6,
    goals: list[dict] | None = None,
) -> dict:
    """Build a custom savings strategy.

    Returns the emergency-fund target/gap, current savings rate, a recommended
    target rate, and a per-goal funding schedule.
    """
    goals = goals or []
    surplus = round(monthly_income - monthly_expenses, 2)
    ef_target = emergency_fund_target(monthly_expenses, emergency_months)
    ef_gap = round(max(ef_target - current_savings, 0), 2)
    months_to_ef = (
        int(-(-ef_gap // surplus)) if surplus > 0 and ef_gap > 0 else (0 if ef_gap == 0 else None)
    )

    current_rate = savings_rate(monthly_income, surplus)
    # Recommend stepping toward 20% if below it, else celebrate.
    target_rate = 20.0 if current_rate < 20 else round(current_rate, 2)

    goal_plans = []
    for g in goals:
        months = max(int(g.get("months", 12)), 1)
        required = monthly_required_for_goal(
            g["target_amount"], months, g.get("current", 0.0)
        )
        goal_plans.append(
            {
                "name": g.get("name", "Goal"),
                "target_amount": g["target_amount"],
                "months": months,
                "monthly_required": required,
                "projection": project_savings(
                    required, months, g.get("current", 0.0), g.get("annual_return", 0.0)
                ),
            }
        )

    return {
        "monthly_surplus": surplus,
        "current_savings": round(current_savings, 2),
        "current_savings_rate": current_rate,
        "target_savings_rate": target_rate,
        "emergency_fund": {
            "months_of_expenses": emergency_months,
            "target": ef_target,
            "gap": ef_gap,
            "funded_pct": round(min(safe_div(current_savings, ef_target) * 100, 100), 1),
            "months_to_fully_fund": months_to_ef,
        },
        "goals": goal_plans,
    }
