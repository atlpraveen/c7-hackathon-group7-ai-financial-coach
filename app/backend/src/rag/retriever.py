"""Dependency-light TF-IDF retriever.

A small, transparent vector store: it tokenises chunks, builds TF-IDF vectors,
and ranks by cosine similarity. Pure Python/stdlib (no sentence-transformers or
external vector DB) keeps the app trivial to install and run while still
demonstrating real semantic-ish retrieval over the user's documents.
"""
from __future__ import annotations

import math
import re
from collections import Counter

_TOKEN_RE = re.compile(r"[a-z0-9$]+")
_STOP = {
    "the", "a", "an", "of", "to", "and", "in", "on", "for", "is", "was", "were",
    "as", "at", "by", "with", "this", "that", "it", "be", "are", "from", "or",
}


def _tokenize(text: str) -> list[str]:
    return [t for t in _TOKEN_RE.findall((text or "").lower()) if t not in _STOP and len(t) > 1]


class TfidfRetriever:
    def __init__(self) -> None:
        self.chunks: list[str] = []
        self.metas: list[dict] = []
        self._doc_tokens: list[Counter] = []
        self._idf: dict[str, float] = {}
        self._vectors: list[dict[str, float]] = []

    def add(self, chunks: list[str], meta: dict | None = None) -> None:
        for c in chunks:
            self.chunks.append(c)
            self.metas.append(meta or {})
            self._doc_tokens.append(Counter(_tokenize(c)))
        self._reindex()

    def _reindex(self) -> None:
        n = len(self._doc_tokens)
        if n == 0:
            self._idf, self._vectors = {}, []
            return
        df: Counter = Counter()
        for tokens in self._doc_tokens:
            df.update(set(tokens))
        self._idf = {term: math.log((1 + n) / (1 + d)) + 1 for term, d in df.items()}
        self._vectors = [self._vectorize(tokens) for tokens in self._doc_tokens]

    def _vectorize(self, tokens: Counter) -> dict[str, float]:
        total = sum(tokens.values()) or 1
        return {t: (c / total) * self._idf.get(t, 0.0) for t, c in tokens.items()}

    @staticmethod
    def _cosine(a: dict[str, float], b: dict[str, float]) -> float:
        if not a or not b:
            return 0.0
        common = set(a) & set(b)
        dot = sum(a[t] * b[t] for t in common)
        na = math.sqrt(sum(v * v for v in a.values()))
        nb = math.sqrt(sum(v * v for v in b.values()))
        return dot / (na * nb) if na and nb else 0.0

    def search(self, query: str, k: int = 4) -> list[dict]:
        if not self.chunks:
            return []
        qv = self._vectorize(Counter(_tokenize(query)))
        scored = [
            {"text": self.chunks[i], "score": round(self._cosine(qv, v), 4), "meta": self.metas[i]}
            for i, v in enumerate(self._vectors)
        ]
        scored.sort(key=lambda x: x["score"], reverse=True)
        return [s for s in scored[:k] if s["score"] > 0] or scored[:k]

    @property
    def size(self) -> int:
        return len(self.chunks)
