"""AI-assisted transaction categorization.

Two-tier: a fast deterministic keyword classifier tuned for Indian merchants
(Swiggy, Zomato, Ola, Jio, SIP/NACH mandates, etc.), upgraded by an LLM batch
classifier when ``OPENROUTER_API_KEY`` is set. The LLM handles the long tail of
descriptions the keyword map can't place; everything else stays instant and free.
"""
from __future__ import annotations

from src.llm import openrouter

# Canonical category set surfaced to the user and the LLM.
CATEGORIES = [
    "salary", "income", "food", "groceries", "rent", "utilities", "transport",
    "shopping", "entertainment", "subscriptions", "health", "education",
    "insurance", "investment", "emi", "loan", "travel", "fees", "other",
]

# Indian-context keyword → category map (lowercased substring match).
_KEYWORDS: dict[str, str] = {
    "salary": "salary", "payroll": "salary", "credit interest": "income",
    "swiggy": "food", "zomato": "food", "dominos": "food", "restaurant": "food", "cafe": "food",
    "bigbasket": "groceries", "blinkit": "groceries", "dmart": "groceries", "grofers": "groceries",
    "reliance fresh": "groceries", "kirana": "groceries",
    "rent": "rent", "landlord": "rent", "lease": "rent",
    "electricity": "utilities", "bescom": "utilities", "water bill": "utilities",
    "gas": "utilities", "jio": "utilities", "airtel": "utilities", "vodafone": "utilities", "broadband": "utilities",
    "uber": "transport", "ola": "transport", "rapido": "transport", "metro": "transport",
    "petrol": "transport", "fuel": "transport", "irctc": "travel", "indigo": "travel", "makemytrip": "travel",
    "amazon": "shopping", "flipkart": "shopping", "myntra": "shopping", "ajio": "shopping",
    "netflix": "subscriptions", "hotstar": "subscriptions", "spotify": "subscriptions",
    "prime": "subscriptions", "youtube": "subscriptions",
    "pharmacy": "health", "apollo": "health", "hospital": "health", "medical": "health", "1mg": "health",
    "school": "education", "college": "education", "tuition": "education", "udemy": "education", "byju": "education",
    "insurance": "insurance", "lic": "insurance", "premium": "insurance",
    "sip": "investment", "mutual fund": "investment", "zerodha": "investment", "groww": "investment",
    "nps": "investment", "ppf": "investment", "elss": "investment",
    "emi": "emi", "loan": "loan", "credit card payment": "emi",
    "tax": "fees", "gst": "fees", "fee": "fees", "charges": "fees",
}


def keyword_category(description: str) -> str:
    text = (description or "").lower()
    for kw, cat in _KEYWORDS.items():
        if kw in text:
            return cat
    return "other"


def categorize(transactions: list[dict], use_llm: bool = True) -> dict:
    """Return categorization results for a list of transactions.

    ``transactions`` items need a ``description``. Returns a dict with the
    per-transaction assignments and which method produced each.
    """
    descriptions = [str(t.get("description") or "") for t in transactions]

    # Tier 1: keyword pass.
    assignments = [keyword_category(d) for d in descriptions]

    # Tier 2: LLM pass for the ones keywords couldn't place.
    method = ["keyword"] * len(descriptions)
    llm_used = False
    if use_llm and openrouter.enabled():
        unknown_idx = [i for i, c in enumerate(assignments) if c == "other" and descriptions[i].strip()]
        if unknown_idx:
            mapping = openrouter.categorize_transactions(
                [descriptions[i] for i in unknown_idx], CATEGORIES
            )
            if mapping:
                llm_used = True
                for i in unknown_idx:
                    cat = mapping.get(descriptions[i])
                    if cat in CATEGORIES:
                        assignments[i] = cat
                        method[i] = "llm"

    results = [
        {"description": descriptions[i], "category": assignments[i], "method": method[i]}
        for i in range(len(descriptions))
    ]
    return {
        "results": results,
        "categories": CATEGORIES,
        "ai_used": llm_used,
        "counts": _counts(assignments),
    }


def _counts(cats: list[str]) -> dict:
    out: dict[str, int] = {}
    for c in cats:
        out[c] = out.get(c, 0) + 1
    return dict(sorted(out.items(), key=lambda kv: kv[1], reverse=True))
