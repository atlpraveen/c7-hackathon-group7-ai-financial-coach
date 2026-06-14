"""Custom savings-strategy agent."""
from __future__ import annotations

from src.agents.base_agent import BaseAgent
from src.tools import savings_tools


class SavingsAgent(BaseAgent):
    name = "savings"
    title = "Savings Strategist"

    def analyze(self, profile: dict, params: dict) -> dict:
        return savings_tools.build_savings_plan(
            monthly_income=profile.get("monthly_income", 0),
            monthly_expenses=profile.get("monthly_expenses", 0),
            current_savings=profile.get("savings_balance", 0),
            emergency_months=params.get("emergency_months", 6),
            goals=params.get("goals", profile.get("goals", [])),
        )

    def _system_prompt(self) -> str:
        return (
            "You are a savings strategist. Assess the user's emergency fund, "
            "savings rate vs the 20% benchmark, and progress toward their goals. "
            "Give a clear next step."
        )

    def _fallback_narrative(self, data: dict, profile: dict) -> str:
        ef = data["emergency_fund"]
        lines = [
            f"You're saving ${data['monthly_surplus']:,.0f}/mo — a "
            f"{data['current_savings_rate']:.0f}% savings rate (target {data['target_savings_rate']:.0f}%).",
        ]
        if ef["gap"] > 0:
            months = ef["months_to_fully_fund"]
            when = f"in about {months} month(s)" if months else "once you free up surplus"
            lines.append(
                f"Your emergency fund is {ef['funded_pct']:.0f}% funded "
                f"(${profile.get('savings_balance', 0):,.0f} of a ${ef['target']:,.0f} target). "
                f"Closing the ${ef['gap']:,.0f} gap should be priority #1 — reachable {when}."
            )
        else:
            lines.append(
                f"Your {ef['months_of_expenses']}-month emergency fund is fully funded "
                f"(${ef['target']:,.0f}) — excellent foundation."
            )
        for g in data.get("goals", []):
            lines.append(
                f"Goal '{g['name']}': set aside ${g['monthly_required']:,.0f}/mo to hit "
                f"${g['target_amount']:,.0f} in {g['months']} months."
            )
        return " ".join(lines)
