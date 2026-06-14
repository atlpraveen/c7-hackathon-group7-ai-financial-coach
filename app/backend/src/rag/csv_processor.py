"""Tabular ingestion: turn a transactions/statement CSV into structured rows.

This is the "tabular RAG" entry point — it normalises a messy real-world CSV
into a canonical list of transactions plus a human-readable text rendering that
feeds the semantic retriever.
"""
from __future__ import annotations

import io

import pandas as pd

# Candidate column names we try to map onto the canonical schema. Ordered by
# priority (most specific first) so matching is deterministic. Note that
# "category" and "type" are SEPARATE slots — "type" is the income/expense
# direction, never the spending category, so it is excluded from the category
# candidates to avoid the two columns colliding.
_DATE_COLS = ("date", "transaction date", "posted date", "posted", "time")
_DESC_COLS = ("description", "desc", "details", "memo", "merchant", "payee", "name")
_AMOUNT_COLS = ("amount", "transaction amount", "value", "amt", "debit/credit")
_CATEGORY_COLS = ("category", "tag", "classification", "bucket")
_TYPE_COLS = ("type", "transaction type", "direction", "flow")


def _match(columns: list[str], candidates) -> str | None:
    lower = {c.lower().strip(): c for c in columns}
    # 1) exact match, honouring candidate priority order
    for cand in candidates:
        if cand in lower:
            return lower[cand]
    # 2) substring fallback, again in candidate priority order
    for cand in candidates:
        for low, original in lower.items():
            if cand in low:
                return original
    return None


class CSVProcessor:
    def parse(self, csv_bytes: bytes) -> dict:
        df = pd.read_csv(io.BytesIO(csv_bytes))
        df.columns = [str(c).strip() for c in df.columns]
        cols = list(df.columns)

        date_c = _match(cols, _DATE_COLS)
        desc_c = _match(cols, _DESC_COLS)
        amount_c = _match(cols, _AMOUNT_COLS)
        category_c = _match(cols, _CATEGORY_COLS)
        type_c = _match(cols, _TYPE_COLS)

        transactions: list[dict] = []
        for _, row in df.iterrows():
            amount = _to_float(row.get(amount_c)) if amount_c else 0.0
            ttype = str(row.get(type_c, "")).strip().lower() if type_c else ""
            category = str(row.get(category_c, "")).strip() if category_c else ""

            # Determine income vs expense. Prefer an explicit type column; else
            # fall back to the sign of the amount.
            if ttype in {"income", "credit", "deposit", "in"}:
                kind = "income"
            elif ttype in {"expense", "debit", "withdrawal", "out"}:
                kind = "expense"
            else:
                kind = "income" if amount > 0 else "expense"

            transactions.append(
                {
                    "date": str(row.get(date_c, "")) if date_c else "",
                    "description": str(row.get(desc_c, "")) if desc_c else "",
                    "amount": abs(amount),
                    "category": category or _infer_category(str(row.get(desc_c, "")) if desc_c else ""),
                    "kind": kind,
                }
            )

        return {
            "transactions": transactions,
            "columns": cols,
            "mapped": {
                "date": date_c, "description": desc_c, "amount": amount_c,
                "category": category_c, "type": type_c,
            },
            "row_count": len(transactions),
            "text": self._to_text(transactions),
        }

    def _to_text(self, transactions: list[dict]) -> str:
        """Render transactions as natural-language lines for the retriever."""
        lines = []
        for t in transactions:
            lines.append(
                f"On {t['date']} a {t['kind']} of Rs {t['amount']:,.2f} "
                f"categorised as {t['category']} ({t['description']})."
            )
        return "\n".join(lines)


def _to_float(v) -> float:
    if v is None:
        return 0.0
    try:
        s = str(v).replace(",", "").replace("$", "").strip()
        if s in ("", "nan", "None"):
            return 0.0
        if s.startswith("(") and s.endswith(")"):  # accounting negatives
            s = "-" + s[1:-1]
        return float(s)
    except (ValueError, TypeError):
        return 0.0


def _infer_category(description: str) -> str:
    """Infer a category from the description using the Indian-merchant keyword
    map shared with the AI categorization service."""
    from src.services.categorization import keyword_category

    return keyword_category(description)
