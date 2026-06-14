"""Debt analysis and payoff-plan optimisation.

Implements real month-by-month amortisation for the two canonical payoff
strategies — avalanche (highest APR first) and snowball (lowest balance
first) — so the API returns genuine, comparable payoff plans rather than
hand-wavy advice.
"""
from __future__ import annotations

import copy
from typing import Literal

Strategy = Literal["avalanche", "snowball"]

# Hard stop so a debt that can never be repaid (payment <= interest) doesn't
# loop forever.
_MAX_MONTHS = 1200


def simple_interest(balance: float, annual_rate: float, years: float) -> float:
    """Simple (non-compounding) interest — handy for quick estimates."""
    return round(balance * (annual_rate / 100) * years, 2)


def _order_debts(debts: list[dict], strategy: Strategy) -> list[dict]:
    if strategy == "avalanche":
        return sorted(debts, key=lambda d: (-d["interest_rate"], d["balance"]))
    return sorted(debts, key=lambda d: (d["balance"], -d["interest_rate"]))


def minimum_payment_floor(debts: list[dict]) -> float:
    return round(sum(d.get("min_payment", 0.0) for d in debts), 2)


def simulate_payoff(
    debts: list[dict],
    monthly_budget: float,
    strategy: Strategy = "avalanche",
) -> dict:
    """Simulate paying off a list of debts under a given strategy.

    Each debt dict needs: name, balance, interest_rate (annual %),
    min_payment. ``monthly_budget`` is the *total* the user can put toward all
    debts each month; minimum payments are always made, and any surplus is
    funnelled to the priority debt for that strategy.

    Returns total months, total interest paid, payoff order, a monthly balance
    timeline (for charting), and a per-debt summary.
    """
    debts = [copy.deepcopy(d) for d in debts if d.get("balance", 0) > 0]
    if not debts:
        return {
            "strategy": strategy,
            "months": 0,
            "total_interest": 0.0,
            "total_paid": 0.0,
            "payoff_order": [],
            "timeline": [],
            "per_debt": [],
            "feasible": True,
            "note": "No outstanding debt.",
        }

    for d in debts:
        d.setdefault("min_payment", 0.0)
        d["_interest_paid"] = 0.0
        d["_paid_off_month"] = None

    min_floor = minimum_payment_floor(debts)
    feasible = monthly_budget >= min_floor
    # Never let the budget drop below the sum of minimums — the schedule must
    # at least cover required payments.
    budget = max(monthly_budget, min_floor)

    timeline: list[dict] = []
    payoff_order: list[str] = []
    total_interest = 0.0
    month = 0

    def remaining() -> list[dict]:
        return [d for d in debts if d["balance"] > 0.005]

    while remaining() and month < _MAX_MONTHS:
        month += 1

        # 1. Accrue one month of interest on every active debt.
        for d in remaining():
            interest = d["balance"] * (d["interest_rate"] / 100) / 12
            d["balance"] += interest
            d["_interest_paid"] += interest
            total_interest += interest

        # 2. Pay minimums, then direct all surplus to the priority debt.
        pool = budget
        active = _order_debts(remaining(), strategy)

        for d in active:
            pay = min(d.get("min_payment", 0.0), d["balance"], pool)
            d["balance"] -= pay
            pool -= pay

        for d in _order_debts(remaining(), strategy):
            if pool <= 0:
                break
            extra = min(pool, d["balance"])
            d["balance"] -= extra
            pool -= extra

        # 3. Record any debts that were cleared this month.
        for d in debts:
            if d["balance"] <= 0.005 and d["_paid_off_month"] is None:
                d["balance"] = 0.0
                d["_paid_off_month"] = month
                payoff_order.append(d["name"])

        timeline.append(
            {
                "month": month,
                "total_balance": round(sum(d["balance"] for d in debts), 2),
                "balances": {d["name"]: round(d["balance"], 2) for d in debts},
            }
        )

    per_debt = [
        {
            "name": d["name"],
            "starting_balance": d.get("balance_start", None),
            "interest_paid": round(d["_interest_paid"], 2),
            "paid_off_month": d["_paid_off_month"],
        }
        for d in debts
    ]

    starting_total = sum(t["total_balance"] for t in timeline[:1]) if timeline else 0.0
    return {
        "strategy": strategy,
        "months": month,
        "years": round(month / 12, 1),
        "total_interest": round(total_interest, 2),
        "total_paid": round(sum(d["_interest_paid"] for d in debts) + _initial_principal(debts), 2),
        "payoff_order": payoff_order,
        "timeline": timeline,
        "per_debt": per_debt,
        "feasible": feasible,
        "monthly_budget_used": round(budget, 2),
        "note": (
            "Budget is below the sum of minimum payments; using the minimum "
            "floor instead."
            if not feasible
            else ""
        ),
    }


def _initial_principal(debts: list[dict]) -> float:
    return round(sum(d.get("balance_start", 0.0) for d in debts), 2)


def compare_strategies(debts: list[dict], monthly_budget: float) -> dict:
    """Run both strategies and surface which saves more interest / time."""
    enriched = [dict(d, balance_start=d["balance"]) for d in debts]
    avalanche = simulate_payoff(enriched, monthly_budget, "avalanche")
    snowball = simulate_payoff(enriched, monthly_budget, "snowball")

    interest_saved = round(snowball["total_interest"] - avalanche["total_interest"], 2)
    recommended = "avalanche" if avalanche["total_interest"] <= snowball["total_interest"] else "snowball"
    return {
        "avalanche": avalanche,
        "snowball": snowball,
        "recommended": recommended,
        "interest_saved_with_avalanche": interest_saved,
        "total_debt": round(sum(d["balance"] for d in debts), 2),
        "weighted_apr": _weighted_apr(debts),
    }


def _weighted_apr(debts: list[dict]) -> float:
    total = sum(d["balance"] for d in debts)
    if not total:
        return 0.0
    return round(sum(d["balance"] * d["interest_rate"] for d in debts) / total, 2)
