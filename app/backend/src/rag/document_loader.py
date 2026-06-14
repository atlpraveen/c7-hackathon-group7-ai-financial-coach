"""Dispatch an uploaded file to the right processor by extension/content type."""
from __future__ import annotations

from .csv_processor import CSVProcessor
from .pdf_processor import PDFProcessor


class DocumentLoader:
    def __init__(self) -> None:
        self.csv = CSVProcessor()
        self.pdf = PDFProcessor()

    def load(self, filename: str, content: bytes) -> dict:
        """Return {kind, text, transactions?} for an uploaded document."""
        name = (filename or "").lower()
        if name.endswith(".csv"):
            parsed = self.csv.parse(content)
            return {"kind": "tabular", "text": parsed["text"], **parsed}
        if name.endswith(".pdf"):
            parsed = self.pdf.parse(content)
            kind = "tabular" if parsed["transactions"] else "document"
            return {"kind": kind, **parsed}
        # Plain text / markdown / anything else decodable.
        try:
            text = content.decode("utf-8", errors="ignore")
        except Exception:
            text = ""
        return {"kind": "document", "text": text, "transactions": []}
