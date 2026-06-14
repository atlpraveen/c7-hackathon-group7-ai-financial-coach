"""Extract text — and structured transactions — from PDF statements.

pypdf gives us the raw page text; on top of that we run a best-effort parser for
the common "merchant - amount" statement layout (e.g. credit-card statements)
so that uploaded PDFs feed the analytics/profile layer, not just semantic search.
Currency glyphs frequently fail to map during PDF text extraction (the ₹ sign
often comes through as ■ or �), so the amount matcher ignores any leading
non-digit prefix entirely.
"""
from __future__ import annotations

import re

# A statement line like "Amazon India - ₹8,450" / "Swiggy - ■2,180".
# Group 1: merchant/description. Group 2: the (Indian-grouped) amount digits.
# The separator is an en/em/hyphen dash; metadata lines (which use ":") are
# deliberately excluded so "Statement Balance: ₹1,24,850" is not parsed.
_TXN_RE = re.compile(
    r"^\s*(.+?)\s+[-–—]\s+[^\d]*([\d][\d,]*(?:\.\d{1,2})?)\s*$"
)

# Lines we never treat as transactions even if they match the shape.
_SKIP = (
    "statement balance", "minimum due", "interest rate", "credit limit",
    "cardholder", "total", "previous balance", "available credit",
)

_MONTHS = {
    "january": 1, "february": 2, "march": 3, "april": 4, "may": 5, "june": 6,
    "july": 7, "august": 8, "september": 9, "october": 10, "november": 11,
    "december": 12,
}
_MONTH_RE = re.compile(
    r"\b(" + "|".join(_MONTHS) + r")\s+(\d{4})\b", re.IGNORECASE
)


class PDFProcessor:
    def extract_text(self, pdf_bytes: bytes) -> str:
        import io

        from pypdf import PdfReader

        reader = PdfReader(io.BytesIO(pdf_bytes))
        return "\n".join(page.extract_text() or "" for page in reader.pages)

    def parse(self, pdf_bytes: bytes) -> dict:
        """Return {text, transactions} extracted from a statement PDF."""
        text = self.extract_text(pdf_bytes)
        return {"text": text, "transactions": self._parse_transactions(text)}

    def _parse_transactions(self, text: str) -> list[dict]:
        from src.services.categorization import keyword_category

        transactions: list[dict] = []
        # Statements span one period each; track the most recent month header so
        # multi-page (multi-month) PDFs date each charge correctly. This lets the
        # profile extractor average across the real number of months.
        current_date = ""
        for raw in text.splitlines():
            line = raw.strip()
            if not line:
                continue
            m = _MONTH_RE.search(line)
            if m:
                current_date = f"{int(m.group(2)):04d}-{_MONTHS[m.group(1).lower()]:02d}-01"
                # A period header (e.g. "...Statement - January 2026") is never
                # itself a charge; capture its date and move on.
                continue
            if any(s in line.lower() for s in _SKIP):
                continue
            match = _TXN_RE.match(line)
            if not match:
                continue
            desc = match.group(1).strip()
            amount = _to_float(match.group(2))
            if not desc or amount <= 0:
                continue
            transactions.append(
                {
                    "date": current_date,
                    "description": desc,
                    "amount": amount,
                    # Credit-card statement lines are charges → expenses.
                    "kind": "expense",
                    "category": keyword_category(desc),
                }
            )
        return transactions


def _to_float(v: str) -> float:
    try:
        s = str(v).replace(",", "").strip()
        return float(s) if s else 0.0
    except (ValueError, TypeError):
        return 0.0
