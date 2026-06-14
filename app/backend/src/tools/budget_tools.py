"""Budget analysis: categorisation, 50/30/20 framework, actionable advice."""
from __future__ import annotations

from .financial_utils import percentage, safe_div

# Map raw transaction categories to the three 50/30/20 buckets.
NEEDS = {
    "rent", "mortgage", "housing", "utilities", "groceries", "insurance",
    "healthcare", "transport", "transportation", "fuel", "loan", "debt",
    "childcare", "education",
}
WANTS = {
    "dining", "restaurants", "entertainment", "shopping", "travel", "subscriptions",
    "hobbies", "fitness", "personal", "gifts",
}
SAVINGS = {"savings", "investment", "retirement", "emergency_fund"}


def classify_bucket(category: str) -> str:
    c = (category or "").strip().lower()
    if c in NEEDS:
        return "needs"
    if c in SAVINGS:
        return "savings"
    if c in WANTS:
        return "wants"
    return "wants"  # default uncategorised discretionary spend to "wants"


def analyze_budget(monthly_income: float, expenses_by_category: dict[str, float]) -> dict:
    """Analyse spending against the 50/30/20 rule and flag overspending.

    Returns bucket totals/percentages, comparison to recommended targets,
    the largest expense categories, and concrete advice strings.
    """
    buckets = {"needs": 0.0, "wants": 0.0, "savings": 0.0}
    for cat, amount in expenses_by_category.items():
        buckets[classify_bucket(cat)] += amount

    total_expenses = round(sum(expenses_by_category.values()), 2)
    surplus = round(monthly_income - total_expenses, 2)
    # Money not spent is implicitly saved.
    buckets["savings"] += max(surplus, 0)

    targets = {"needs": 50.0, "wants": 30.0, "savings": 20.0}
    breakdown = {}
    advice: list[str] = []
    for name, amount in buckets.items():
        pct = percentage(amount, monthly_income)
        target = targets[name]
        status = "on_track"
        if name in ("needs", "wants") and pct > target + 5:
            status = "over"
            advice.append(
                f"Your {name} spending is {pct:.0f}% of income (target {target:.0f}%). "
                f"Trimming it toward {target:.0f}% frees up "
                f"${(amount - monthly_income * target / 100):,.0f}/mo."
            )
        elif name == "savings" and pct < target - 2:
            status = "under"
            advice.append(
                f"You're saving {pct:.0f}% of income (target {target:.0f}%). "
                f"Aim to redirect ${(monthly_income * target / 100 - amount):,.0f}/mo into savings."
            )
        breakdown[name] = {
            "amount": round(amount, 2),
            "pct_of_income": pct,
            "target_pct": target,
            "status": status,
        }

    top_expenses = sorted(
        ({"category": c, "amount": round(a, 2),
          "pct_of_income": percentage(a, monthly_income)}
         for c, a in expenses_by_category.items()),
        key=lambda x: x["amount"], reverse=True,
    )[:5]

    if surplus < 0:
        advice.insert(
            0,
            f"You're spending ${abs(surplus):,.0f}/mo more than you earn — this is "
            f"the most urgent thing to fix.",
        )

    if not advice:
        advice.append("Your budget is well balanced against the 50/30/20 framework — nice work.")

    return {
        "monthly_income": round(monthly_income, 2),
        "total_expenses": total_expenses,
        "surplus": surplus,
        "savings_rate": round(safe_div(max(surplus, 0), monthly_income) * 100, 1),
        "buckets": breakdown,
        "top_expenses": top_expenses,
        "advice": advice,
    }
