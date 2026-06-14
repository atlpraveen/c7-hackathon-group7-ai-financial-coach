"""Financial goal tracking: progress, projections, and required contributions.

Computes, for each goal, how far along it is, how many months it will take at
the current contribution (with optional expected return compounding), and the
monthly amount required to hit the target by the deadline.
"""
from __future__ import annotations

_MAX_MONTHS = 1200


def _months_to_target(current: float, monthly: float, target: float, annual_return: float) -> int | None:
    """Months for current + monthly SIP (compounded) to reach target."""
    if current >= target:
        return 0
    if monthly <= 0 and annual_return <= 0:
        return None
    r = annual_return / 100 / 12
    bal = current
    for m in range(1, _MAX_MONTHS + 1):
        bal = bal * (1 + r) + monthly
        if bal >= target:
            return m
    return None


def _required_monthly(current: float, target: float, months: int, annual_return: float) -> float:
    """Monthly contribution to reach target in `months` (future-value of annuity)."""
    months = max(int(months), 1)
    r = annual_return / 100 / 12
    if r == 0:
        return max((target - current) / months, 0.0)
    future_current = current * (1 + r) ** months
    needed = target - future_current
    if needed <= 0:
        return 0.0
    annuity_factor = ((1 + r) ** months - 1) / r
    return max(needed / annuity_factor, 0.0)


def goal_progress(goal: dict) -> dict:
    target = float(goal.get("target_amount") or 0.0)
    current = float(goal.get("current_amount") or 0.0)
    monthly = float(goal.get("monthly_contribution") or 0.0)
    target_months = int(goal.get("target_months") or 12)
    annual_return = float(goal.get("annual_return") or 0.0)

    pct = round(min(current / target * 100, 100), 1) if target > 0 else 0.0
    remaining = round(max(target - current, 0.0), 2)
    eta = _months_to_target(current, monthly, target, annual_return)
    required = round(_required_monthly(current, target, target_months, annual_return), 2)
    on_track = eta is not None and eta <= target_months

    return {
        **goal,
        "progress_pct": pct,
        "remaining": remaining,
        "projected_months": eta,
        "monthly_required_for_deadline": required,
        "monthly_shortfall": round(max(required - monthly, 0.0), 2),
        "on_track": on_track,
        "status": "complete" if pct >= 100 else ("on_track" if on_track else "behind"),
    }


def summarize_goals(goals: list[dict]) -> dict:
    enriched = [goal_progress(g) for g in goals]
    total_target = sum(float(g.get("target_amount") or 0) for g in goals)
    total_current = sum(float(g.get("current_amount") or 0) for g in goals)
    total_monthly = sum(float(g.get("monthly_contribution") or 0) for g in goals)
    return {
        "goals": enriched,
        "count": len(goals),
        "total_target": round(total_target, 2),
        "total_current": round(total_current, 2),
        "total_monthly_commitment": round(total_monthly, 2),
        "overall_progress_pct": round(total_current / total_target * 100, 1) if total_target else 0.0,
        "on_track_count": sum(1 for g in enriched if g["status"] in ("on_track", "complete")),
    }
