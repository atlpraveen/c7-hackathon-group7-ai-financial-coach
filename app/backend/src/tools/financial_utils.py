"""Small shared numeric helpers used across the financial tools."""
from __future__ import annotations


def percentage(part: float, total: float) -> float:
    if not total:
        return 0.0
    return round((part / total) * 100, 2)


def currency(value: float) -> str:
    return f"${value:,.2f}"


def safe_div(a: float, b: float) -> float:
    return a / b if b else 0.0


def clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))
