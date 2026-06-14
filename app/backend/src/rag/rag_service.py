"""RAG orchestration over a user's uploaded financial documents.

Holds the (per-user) vector store + accumulated transactions, derives a
financial profile from tabular data, and answers free-form questions by
retrieving relevant chunks and (optionally) having an LLM ground its answer in
them — with conversation memory threaded in. Without an API key it returns an
extractive, deterministic answer.
"""
from __future__ import annotations

from collections.abc import Iterator
from typing import Optional

from src.llm import client as llm
from src.rag.chunking import chunk_text
from src.rag.document_loader import DocumentLoader
from src.rag.profile_extractor import extract_profile
from src.rag.vector_store import VectorStore

_SYSTEM = (
    "You are a careful personal-finance coach for an Indian user (amounts in INR / Rs). "
    "Answer ONLY using the user's financial context below. Be concrete, cite "
    "numbers, and if the context doesn't contain the answer, say so plainly. "
    "Keep it to a few sentences."
)


class RAGService:
    def __init__(self, namespace: str = "default") -> None:
        self.retriever = VectorStore(namespace)
        self.loader = DocumentLoader()
        self.transactions: list[dict] = []
        self.documents: list[dict] = []

    def ingest(self, filename: str, content: bytes) -> dict:
        loaded = self.loader.load(filename, content)
        chunks = chunk_text(loaded["text"])
        self.retriever.add(chunks, meta={"source": filename, "kind": loaded["kind"]})
        if loaded.get("transactions"):
            self.transactions.extend(loaded["transactions"])
        record = {
            "filename": filename,
            "kind": loaded["kind"],
            "chunks": len(chunks),
            "transactions": len(loaded.get("transactions", [])),
        }
        self.documents.append(record)
        return record

    def add_transactions(self, txns: list[dict]) -> None:
        """Register transactions (e.g. reloaded from the DB) for profiling."""
        self.transactions.extend(txns)

    def profile(self) -> Optional[dict]:
        if not self.transactions:
            return None
        return extract_profile(self.transactions)

    def _build_prompt(self, question: str, hits: list[dict], profile_summary: str) -> str:
        context = "\n".join(f"- {h['text']}" for h in hits)
        return (
            f"User financial profile:\n{profile_summary or '(not provided)'}\n\n"
            f"Relevant excerpts from the user's documents:\n{context or '(no documents uploaded yet)'}\n\n"
            f"Question: {question}"
        )

    def answer(
        self, question: str, profile_summary: str = "", history: Optional[list[dict]] = None
    ) -> dict:
        hits = self.retriever.search(question, k=5)
        prompt = self._build_prompt(question, hits, profile_summary)
        text = llm.narrate_with_history(_SYSTEM, history or [], prompt, max_tokens=600)
        if text is None:
            text = self._fallback_answer(question, hits, profile_summary)
            source = "deterministic"
        else:
            source = "llm"
        return {
            "answer": text,
            "sources": [{"text": h["text"], "score": h["score"], "meta": h["meta"]} for h in hits],
            "generated_by": source,
            "retriever": self.retriever.backend,
        }

    def stream_answer(
        self, question: str, profile_summary: str = "", history: Optional[list[dict]] = None
    ) -> Iterator[str]:
        """Yield the answer token-by-token, falling back to a single block."""
        hits = self.retriever.search(question, k=5)
        prompt = self._build_prompt(question, hits, profile_summary)
        streamed = False
        for delta in llm.stream_narrate(_SYSTEM, history or [], prompt, max_tokens=600):
            streamed = True
            yield delta
        if not streamed:
            yield self._fallback_answer(question, hits, profile_summary)

    def _fallback_answer(self, question: str, hits: list[dict], profile_summary: str) -> str:
        if not hits and not profile_summary:
            return (
                "I don't have any of your financial documents yet. Upload a "
                "transactions CSV or statement, and I'll be able to answer "
                "questions grounded in your own data."
            )
        parts = []
        if profile_summary:
            parts.append(f"Based on your profile — {profile_summary}")
        if hits:
            parts.append("From your documents, the most relevant records are:")
            parts.extend(f"  • {h['text']}" for h in hits[:3])
        parts.append("(Set OPENROUTER_API_KEY to get a fully written, conversational answer.)")
        return "\n".join(parts)
