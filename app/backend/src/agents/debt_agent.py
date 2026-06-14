"""Debt analyser + payoff-optimisation agent."""
from __future__ import annotations

from src.agents.base_agent import BaseAgent
from src.tools import debt_tools


class DebtAgent(BaseAgent):
    name = "debt"
    title = "Debt Analyser"

    def analyze(self, profile: dict, params: dict) -> dict:
        debts = profile.get("debts", []) or []
        surplus = max(profile.get("monthly_income", 0) - profile.get("monthly_expenses", 0), 0)
        min_floor = debt_tools.minimum_payment_floor(debts)
        # Extra toward debt: explicit param, else half of any surplus.
        extra = params.get("extra_payment")
        if extra is None:
            extra = round(surplus * 0.5, 2)
        budget = round(min_floor + extra, 2)

        if not debts:
            return {
                "has_debt": False,
                "message": "No debts on file — nothing to optimise. 🎉",
                "monthly_budget": budget,
            }

        comparison = debt_tools.compare_strategies(debts, budget)
        return {
            "has_debt": True,
            "monthly_budget": budget,
            "extra_payment": round(extra, 2),
            "minimum_payments": min_floor,
            **comparison,
        }

    def _system_prompt(self) -> str:
        return (
            "You are a debt-payoff coach. Explain the avalanche vs snowball "
            "tradeoff for THIS user, recommend one, and quantify the interest "
            "and months saved. Be encouraging but direct."
        )

    def _fallback_narrative(self, data: dict, profile: dict) -> str:
        if not data.get("has_debt"):
            return "You have no outstanding debt on record — keep it that way and redirect that capacity toward savings and investing."
        rec = data["recommended"]
        av, sn = data["avalanche"], data["snowball"]
        chosen = data[rec]
        return (
            f"You're carrying ${data['total_debt']:,.0f} across {len(chosen['per_debt'])} "
            f"debt(s) at a blended {data['weighted_apr']:.1f}% APR. Putting "
            f"${data['monthly_budget']:,.0f}/mo toward debt, the **{rec}** method is your best "
            f"play: it clears everything in {chosen['months']} months "
            f"({chosen['years']} yrs) with ${chosen['total_interest']:,.0f} in interest. "
            f"For comparison, avalanche costs ${av['total_interest']:,.0f} and snowball "
            f"${sn['total_interest']:,.0f} — choosing avalanche saves "
            f"${data['interest_saved_with_avalanche']:,.0f} in interest. "
            f"Payoff order: {', '.join(chosen['payoff_order']) or 'n/a'}. "
            f"Every extra dollar above the ${data['minimum_payments']:,.0f} minimums goes to the "
            f"top-priority debt and accelerates the whole plan."
        )
