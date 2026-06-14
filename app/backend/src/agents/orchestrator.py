"""Orchestrator: routes a user query to the right specialist agents, runs them,
then synthesises a single prioritised financial plan.

Routing uses the LLM (OpenRouter) when available, falling back to a keyword
table. Execution uses a LangGraph StateGraph when installed, falling back to a
concurrent asyncio engine. Either way the result shape is identical.
"""
from __future__ import annotations

import asyncio
import json

from src.agents.budget_agent import BudgetAgent
from src.agents.debt_agent import DebtAgent
from src.agents.graph import build_graph
from src.agents.india_agent import IndiaAgent
from src.agents.investment_agent import InvestmentAgent
from src.agents.portfolio_agent import PortfolioAgent
from src.agents.savings_agent import SavingsAgent
from src.llm import client as llm
from src.llm import openrouter

# Keyword → agent routing fallback (used when the LLM router is unavailable).
_ROUTES = {
    "debt": ["debt", "loan", "payoff", "emi", "credit card", "avalanche", "snowball", "interest", "owe"],
    "savings": ["save", "saving", "emergency", "fund", "rainy day", "nest egg"],
    "budget": ["budget", "spend", "spending", "expense", "cut", "50/30/20", "overspend", "afford"],
    "investment": ["invest", "investment", "allocation", "retire", "stocks", "mutual fund", "etf"],
    "portfolio": ["portfolio", "optimize", "optimisation", "diversify", "sharpe", "rebalance", "asset"],
    "india": ["tax", "epf", "pf", "nps", "elss", "sip", "80c", "regime", "ppf", "hra", "india"],
}


class Orchestrator:
    def __init__(self) -> None:
        self.agents = {
            "debt": DebtAgent(),
            "savings": SavingsAgent(),
            "budget": BudgetAgent(),
            "investment": InvestmentAgent(),
            "portfolio": PortfolioAgent(),
            "india": IndiaAgent(),
        }
        # Compile the LangGraph once; None if langgraph isn't installed.
        self._graph = build_graph(self.agents, self.route, self._synthesize)

    @property
    def engine(self) -> str:
        return "langgraph" if self._graph is not None else "asyncio"

    def route(self, query: str | None) -> list[str]:
        """Pick which agents to run. No query → run them all."""
        if not query or not query.strip():
            return list(self.agents.keys())
        # 1) LLM router (semantic).
        if openrouter.enabled():
            picked = openrouter.route_agents(query, list(self.agents.keys()))
            if picked:
                return picked
        # 2) Keyword fallback.
        q = query.lower()
        selected = [name for name, kws in _ROUTES.items() if any(kw in q for kw in kws)]
        return selected or list(self.agents.keys())

    async def _run_agent(self, name: str, profile: dict, params: dict) -> dict:
        return await asyncio.to_thread(self.agents[name].run, profile, params)

    async def coach(self, profile: dict, query: str | None = None, params: dict | None = None) -> dict:
        params = params or {}
        if self._graph is not None:
            state = {"profile": profile, "query": query, "params": params, "results": []}
            final = await asyncio.to_thread(self._graph.invoke, state)
            selected = final.get("selected", [])
            results = final.get("results", [])
            synthesis = final.get("synthesis", "")
            generated_by = final.get("generated_by", "deterministic")
        else:
            selected = self.route(query)
            results = await asyncio.gather(
                *(self._run_agent(name, profile, params) for name in selected)
            )
            synthesis, generated_by = self._synthesize(results, profile, query)
        return {
            "query": query,
            "engine": self.engine,
            "routed_by": "llm" if openrouter.enabled() else "keyword",
            "agents_run": selected,
            "results": {r["agent"]: r for r in results},
            "synthesis": synthesis,
            "synthesis_generated_by": generated_by,
        }

    def _synthesize(self, results: list[dict], profile: dict, query: str | None) -> tuple[str, str]:
        system = (
            "You are the lead financial coach coordinating a team of specialist "
            "agents (debt, savings, budget, investment, portfolio, Indian tax & "
            "retirement). Synthesise their findings into ONE prioritised action "
            "plan: 3-5 ranked, concrete next steps tailored to this user. Amounts "
            "are in Indian Rupees (INR). Be motivating and specific."
        )
        prompt = (
            f"User question: {query or 'Give me a full financial review.'}\n\n"
            f"PROFILE:\n{json.dumps(profile, default=str)}\n\n"
            "SPECIALIST FINDINGS:\n"
            + "\n\n".join(f"[{r['title']}]\n{r['narrative']}" for r in results)
        )
        text = llm.narrate(system, prompt, max_tokens=1000)
        if text:
            return text, "llm"
        return self._fallback_synthesis(results, profile), "deterministic"

    def _fallback_synthesis(self, results: list[dict], profile: dict) -> str:
        by = {r["agent"]: r for r in results}
        steps: list[str] = []

        def rupees(n: float) -> str:
            return f"₹{n:,.0f}"

        surplus = profile.get("monthly_income", 0) - profile.get("monthly_expenses", 0)
        if surplus < 0:
            steps.append(
                f"Fix the deficit first: you're {rupees(abs(surplus))}/mo cash-flow negative — "
                f"trim spending before anything else."
            )

        if "savings" in by:
            ef = by["savings"]["data"].get("emergency_fund", {})
            if ef.get("gap", 0) > 0:
                steps.append(
                    f"Build your emergency fund — it's {ef.get('funded_pct', 0):.0f}% funded; "
                    f"close the {rupees(ef['gap'])} gap."
                )

        if "debt" in by and by["debt"]["data"].get("has_debt"):
            d = by["debt"]["data"]
            steps.append(
                f"Attack debt with the {d['recommended']} method "
                f"({rupees(d['total_debt'])} at {d['weighted_apr']:.1f}% APR) — "
                f"saves {rupees(d['interest_saved_with_avalanche'])} in interest."
            )

        if "india" in by:
            tc = by["india"]["data"].get("tax_comparison", {})
            if tc.get("savings", 0) > 0:
                steps.append(
                    f"Pick the {tc.get('recommended', 'new')} tax regime — saves about "
                    f"{rupees(tc['savings'])}/yr; route 80C investments into ELSS/EPF."
                )

        if "budget" in by:
            adv = by["budget"]["data"].get("advice", [])
            if adv:
                steps.append(adv[0])

        if "portfolio" in by:
            p = by["portfolio"]["data"]
            steps.append(
                f"Invest your surplus via the optimised allocation (expected "
                f"{p.get('expected_annual_return', 0):.1f}% return) — projected "
                f"{rupees(p.get('projected_balance', 0))} in {p.get('horizon_years', 15)} yrs."
            )
        elif "investment" in by and by["investment"]["data"].get("investable_monthly", 0) > 0:
            inv = by["investment"]["data"]
            steps.append(
                f"Invest {rupees(inv['investable_monthly'])}/mo per your "
                f"{inv['risk_tolerance']} allocation."
            )

        if not steps:
            steps.append("Your finances look healthy across the board — keep the momentum going!")

        numbered = "\n".join(f"{i}. {s}" for i, s in enumerate(steps, 1))
        return "Here's your prioritised action plan:\n" + numbered
