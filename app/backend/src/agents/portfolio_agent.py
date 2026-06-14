"""Portfolio-optimisation agent (Markowitz mean-variance, educational)."""
from __future__ import annotations

from src.agents.base_agent import BaseAgent
from src.tools import portfolio_tools


class PortfolioAgent(BaseAgent):
    name = "portfolio"
    title = "Portfolio Optimizer"

    def analyze(self, profile: dict, params: dict | None = None) -> dict:
        """Return a mean-variance-optimised portfolio plan for the user.

        Reads monthly_income, monthly_expenses, risk_tolerance,
        investment_balance from *profile*; reads horizon_years from *params*.
        """
        params = params or {}
        monthly_income = profile.get("monthly_income", 0)
        monthly_expenses = profile.get("monthly_expenses", 0)
        investable_monthly = max(monthly_income - monthly_expenses, 0)

        risk_tolerance = profile.get("risk_tolerance", "moderate")
        current_portfolio = float(profile.get("investment_balance", 0))
        horizon_years = int(params.get("horizon_years", 15))

        return portfolio_tools.build_portfolio_plan(
            risk_tolerance=risk_tolerance,
            investable_monthly=investable_monthly,
            current_portfolio=current_portfolio,
            horizon_years=horizon_years,
        )

    def _system_prompt(self) -> str:
        return (
            "You are a portfolio strategist (educational, not a licensed advisor). "
            "Explain the mean-variance optimised allocation across Indian equity "
            "(large-cap and mid-cap), debt, gold, and international assets. "
            "Cover diversification benefits, the trade-off between expected return "
            "and volatility, the Sharpe ratio, and the projected ₹ corpus. "
            "Quote all monetary amounts in Indian Rupees (₹). "
            "Close with a brief disclaimer that these are illustrative projections."
        )

    def _fallback_narrative(self, data: dict, profile: dict) -> str:
        """Deterministic prose when no LLM is configured."""
        rt = data.get("risk_tolerance", "moderate")
        rec = data.get("optimization", {}).get("recommended", {})
        wts = rec.get("weights", {})
        exp_ret = data.get("expected_annual_return", 0.0)
        exp_vol = data.get("expected_volatility", 0.0)
        sharpe = data.get("sharpe", 0.0)
        projected = data.get("projected_balance", 0.0)
        contributed = data.get("total_contributed", 0.0)
        horizon = data.get("horizon_years", 15)
        monthly = data.get("investable_monthly", 0.0)

        # Build weight summary string
        wt_parts = [f"{asset.replace('_', ' ').title()} {pct}%" for asset, pct in wts.items()]
        wt_str = ", ".join(wt_parts)

        return (
            f"Based on a {rt} risk profile, mean-variance optimisation recommends "
            f"a diversified allocation of: {wt_str}. "
            f"This blend targets an expected annual return of {exp_ret:.1f}% with "
            f"an annualised volatility of {exp_vol:.1f}% and a Sharpe ratio of "
            f"{sharpe:.2f} (vs. a 6.5% Indian risk-free rate). "
            f"Investing ₹{monthly:,.0f}/month for {horizon} years could grow your "
            f"corpus to approximately ₹{projected:,.0f} "
            f"(total contributions ₹{contributed:,.0f}, "
            f"investment growth ₹{projected - contributed:,.0f}). "
            f"The allocation spreads risk across domestic equities, debt instruments, "
            f"gold as a hedge, and international diversification — reducing "
            f"concentration in any single asset class. "
            f"{data.get('disclaimer', '')}"
        )
