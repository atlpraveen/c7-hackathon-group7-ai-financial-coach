"""Actionable budget-advice agent."""
from __future__ import annotations

from src.agents.base_agent import BaseAgent
from src.tools import budget_tools


class BudgetAgent(BaseAgent):
    name = "budget"
    title = "Budget Advisor"

    def analyze(self, profile: dict, params: dict) -> dict:
        return budget_tools.analyze_budget(
            monthly_income=profile.get("monthly_income", 0),
            expenses_by_category=profile.get("expenses_by_category", {}) or {},
        )

    def _system_prompt(self) -> str:
        return (
            "You are a budgeting coach using the 50/30/20 framework. Point out "
            "where the user is over/under target, name the biggest line items, "
            "and give 2-3 concrete cuts or moves."
        )

    def _fallback_narrative(self, data: dict, profile: dict) -> str:
        b = data["buckets"]
        top = data["top_expenses"][:3]
        top_str = ", ".join(f"{t['category']} (${t['amount']:,.0f})" for t in top) or "n/a"
        head = (
            f"On ${data['monthly_income']:,.0f}/mo income you spend "
            f"${data['total_expenses']:,.0f}, leaving a ${data['surplus']:,.0f} surplus "
            f"({data['savings_rate']:.0f}% savings rate). Against 50/30/20 you're at "
            f"{b['needs']['pct_of_income']:.0f}% needs / {b['wants']['pct_of_income']:.0f}% wants / "
            f"{b['savings']['pct_of_income']:.0f}% savings. Top categories: {top_str}."
        )
        return head + " " + " ".join(data.get("advice", []))
