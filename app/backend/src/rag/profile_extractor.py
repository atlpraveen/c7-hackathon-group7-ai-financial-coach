"""Derive a structured financial profile from parsed transactions.

Bridges the tabular RAG layer and the financial engine: it turns a raw list of
transactions into monthly income, expenses-by-category, an estimated savings
balance, and inferred debts that the agents can reason over.
"""
from __future__ import annotations


def _distinct_months(transactions: list[dict]) -> int:
    months = set()
    for t in transactions:
        d = (t.get("date") or "").strip()
        # Best-effort YYYY-MM extraction from common date formats.
        if len(d) >= 7 and d[4] in "-/":
            months.add(d[:7])
        elif len(d) >= 7 and d[2] in "-/" and d[5] in "-/":
            months.add(d[6:] + d[2:5])  # MM/DD/YYYY-ish
    return max(len(months), 1)


def extract_profile(transactions: list[dict]) -> dict:
    months = _distinct_months(transactions)

    total_income = sum(t["amount"] for t in transactions if t["kind"] == "income")
    expenses_by_category: dict[str, float] = {}
    debt_payments: dict[str, float] = {}

    for t in transactions:
        if t["kind"] != "expense":
            continue
        cat = (t.get("category") or "other").lower()
        expenses_by_category[cat] = expenses_by_category.get(cat, 0.0) + t["amount"]
        if cat in {"loan", "debt", "emi", "credit card"}:
            key = t.get("description") or cat
            debt_payments[key] = debt_payments.get(key, 0.0) + t["amount"]

    # Normalise to monthly averages.
    monthly_income = round(total_income / months, 2)
    monthly_expenses_by_category = {
        c: round(v / months, 2) for c, v in expenses_by_category.items()
    }
    monthly_expenses = round(sum(monthly_expenses_by_category.values()), 2)

    # Infer debts from recurring loan/debt payments (rough heuristic so the
    # debt agent has something to work with even from a statement alone).
    inferred_debts = []
    for name, total in debt_payments.items():
        monthly_pay = round(total / months, 2)
        if monthly_pay <= 0:
            continue
        # Assume a representative APR and back out an approximate balance.
        apr = 18.0
        approx_balance = round(monthly_pay * 24, 2)  # ~2yr horizon placeholder
        inferred_debts.append(
            {
                "name": name[:40],
                "balance": approx_balance,
                "interest_rate": apr,
                "min_payment": monthly_pay,
                "inferred": True,
            }
        )

    return {
        "months_of_data": months,
        "monthly_income": monthly_income,
        "monthly_expenses": monthly_expenses,
        "expenses_by_category": monthly_expenses_by_category,
        "estimated_monthly_surplus": round(monthly_income - monthly_expenses, 2),
        "inferred_debts": inferred_debts,
        "transaction_count": len(transactions),
    }
