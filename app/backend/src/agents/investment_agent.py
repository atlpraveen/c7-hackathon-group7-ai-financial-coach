"""Investment-allocation agent (educational)."""
from __future__ import annotations

from src.agents.base_agent import BaseAgent
from src.tools import investment_tools


class InvestmentAgent(BaseAgent):
    name = "investment"
    title = "Investment Advisor"

    def analyze(self, profile: dict, params: dict) -> dict:
        surplus = max(profile.get("monthly_income", 0) - profile.get("monthly_expenses", 0), 0)
        investable = params.get("investable_monthly")
        if investable is None:
            # Conservatively invest part of the surplus after a debt/savings buffer.
            investable = round(surplus * 0.4, 2)
        return investment_tools.build_investment_plan(
            risk_tolerance=profile.get("risk_tolerance", "moderate"),
            investable_monthly=investable,
            age=profile.get("age"),
            current_portfolio=profile.get("investment_balance", 0),
            horizon_years=params.get("horizon_years", 20),
        )

    def _system_prompt(self) -> str:
        return (
            "You are an investment educator (not a licensed advisor). Explain "
            "the recommended allocation given the user's risk tolerance and age, "
            "the long-run projection, and always include a brief disclaimer."
        )

    def _fallback_narrative(self, data: dict, profile: dict) -> str:
        a = data["allocation"]
        return (
            f"For a {data['risk_tolerance']} investor"
            + (f" at age {data['age']}" if data.get("age") else "")
            + f", a target mix of {a['equity']}% equities / {a['bonds']}% bonds / {a['cash']}% cash "
            f"carries an expected ~{data['expected_annual_return']:.1f}% annual return. "
            f"Investing ${data['investable_monthly']:,.0f}/mo for {data['horizon_years']} years could "
            f"grow to ~${data['projected_balance']:,.0f} (you'd contribute "
            f"${data['total_contributed']:,.0f}, with ~${data['projected_growth']:,.0f} of growth). "
            f"{data['disclaimer']}"
        )
