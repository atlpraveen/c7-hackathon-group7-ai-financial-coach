"""Indian personal-finance planning agent (educational)."""
from __future__ import annotations

from src.agents.base_agent import BaseAgent
from src.tools.india_tools import build_india_plan


class IndiaAgent(BaseAgent):
    name = "india"
    title = "Indian Finance Planner"

    def analyze(self, profile: dict, params: dict | None = None) -> dict:
        return build_india_plan(profile, params)

    def _system_prompt(self) -> str:
        return (
            "You are an Indian personal-finance coach (educational, not a licensed advisor). "
            "You help salaried individuals understand EPF, NPS, ELSS SIPs, regular mutual-fund "
            "SIPs and the choice between the old and new income-tax regimes under the "
            "Income Tax Act 1961 (FY 2024-25 rules). "
            "Always express monetary amounts in ₹ (INR) using Indian number formatting "
            "(e.g. ₹12,34,567). Reference only the numbers provided — never invent figures. "
            "Be warm, specific and actionable. End with a brief disclaimer that this is "
            "educational information and not personalised tax or investment advice."
        )

    def _fallback_narrative(self, data: dict, profile: dict) -> str:
        sip = data.get("sip", {})
        epf = data.get("epf", {})
        nps = data.get("nps", {})
        elss = data.get("elss", {})
        tax = data.get("tax_comparison", {})
        rec = tax.get("recommended", "new").upper()
        savings = tax.get("savings", 0)
        years = sip.get("years", 0)

        # ---- paragraph 1: SIP & ELSS wealth creation ----
        para1_parts = []
        if sip.get("maturity", 0) > 0:
            para1_parts.append(
                f"A monthly SIP of ₹{sip.get('monthly_investment', 0):,} at "
                f"{sip.get('annual_return_pct', 12)}% p.a. over {years} years "
                f"could grow to ₹{sip.get('maturity', 0):,}, turning an invested "
                f"₹{sip.get('invested', 0):,} into ₹{sip.get('gains', 0):,} of gains."
            )
        if elss.get("maturity", 0) > 0:
            para1_parts.append(
                f"Your ELSS SIP of ₹{elss.get('monthly_investment', 0):,}/month "
                f"also qualifies for an 80C deduction of ₹{elss.get('eligible_80c', 0):,}/year, "
                f"saving ₹{elss.get('tax_saved_per_year', 0):,} in tax annually — "
                f"with a projected maturity of ₹{elss.get('maturity', 0):,} after {years} years."
            )
        para1 = "  ".join(para1_parts) if para1_parts else (
            "Start a SIP to build long-term wealth through the power of compounding."
        )

        # ---- paragraph 2: EPF & NPS retirement corpus ----
        para2_parts = []
        if epf.get("maturity", 0) > 0:
            para2_parts.append(
                f"Your EPF corpus is projected to reach ₹{epf.get('maturity', 0):,} "
                f"over {epf.get('years', years)} years "
                f"(interest earned: ₹{epf.get('interest_earned', 0):,})."
            )
        if nps.get("maturity_corpus", 0) > 0:
            para2_parts.append(
                f"NPS contributions of ₹{nps.get('monthly_investment', 0):,}/month "
                f"could build a corpus of ₹{nps.get('maturity_corpus', 0):,}; "
                f"at maturity you may receive a lump sum of ₹{nps.get('lump_sum', 0):,} "
                f"and an estimated monthly pension of ₹{nps.get('est_monthly_pension', 0):,}."
            )
        para2 = "  ".join(para2_parts) if para2_parts else (
            "Consider maximising EPF and NPS contributions for a secure retirement."
        )

        # ---- paragraph 3: tax regime recommendation ----
        old_tax = tax.get("old", {}).get("total_tax", 0)
        new_tax = tax.get("new", {}).get("total_tax", 0)
        para3 = (
            f"On the tax front, the {rec} regime is more beneficial for you — "
            f"it results in a total tax of "
            f"₹{(old_tax if rec == 'OLD' else new_tax):,} vs. "
            f"₹{(new_tax if rec == 'OLD' else old_tax):,} under the other regime, "
            f"saving you ₹{savings:,} per year.  "
            f"Remember: this is an educational illustration — please verify against the "
            f"latest IT rules and consult a qualified tax advisor before filing."
        )

        return f"{para1}\n\n{para2}\n\n{para3}"
