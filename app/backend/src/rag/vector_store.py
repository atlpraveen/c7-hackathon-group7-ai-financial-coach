"""Vector store with a Qdrant backend and a pure-Python TF-IDF fallback.

When ``qdrant-client[fastembed]`` is installed and ``QDRANT_URL`` is set, text
is embedded (fastembed) and indexed in Qdrant — a real vector database, with a
per-user collection for multi-tenant isolation. If Qdrant or the embedding
model is unavailable (e.g. offline), it transparently falls back to the
dependency-free TF-IDF retriever so search always works.
"""
from __future__ import annotations

from typing import Optional

from src.core.config import settings
from src.core.logger import logger
from src.rag.retriever import TfidfRetriever


class VectorStore:
    def __init__(self, namespace: str = "default") -> None:
        self.namespace = namespace
        self.collection = f"{settings.QDRANT_COLLECTION}_{namespace}"
        self._tfidf = TfidfRetriever()  # always present as fallback / mirror
        self._qdrant = None
        self._count = 0
        self._init_qdrant()

    @property
    def backend(self) -> str:
        return "qdrant" if self._qdrant is not None else "tfidf"

    def _init_qdrant(self) -> None:
        if not settings.QDRANT_URL.strip():
            return
        try:
            from qdrant_client import QdrantClient

            url = settings.QDRANT_URL.strip()
            if url == ":memory:":
                client = QdrantClient(location=":memory:")
            elif url.startswith("http"):
                client = QdrantClient(url=url, api_key=settings.QDRANT_API_KEY or None)
            else:
                client = QdrantClient(path=url)  # embedded on-disk
            client.set_model(settings.EMBEDDING_MODEL)  # fastembed
            self._qdrant = client
            logger.info("Qdrant vector store ready (collection=%s).", self.collection)
        except Exception as exc:  # pragma: no cover - optional dependency / offline
            logger.warning("Qdrant unavailable (%s); using TF-IDF retriever.", exc)
            self._qdrant = None

    def add(self, chunks: list[str], meta: Optional[dict] = None) -> None:
        chunks = [c for c in chunks if c and c.strip()]
        if not chunks:
            return
        # Always keep the TF-IDF mirror so we can fall back per-query if needed.
        self._tfidf.add(chunks, meta=meta)
        if self._qdrant is not None:
            try:
                self._qdrant.add(
                    collection_name=self.collection,
                    documents=chunks,
                    metadata=[meta or {} for _ in chunks],
                )
            except Exception as exc:  # pragma: no cover
                logger.warning("Qdrant add failed (%s); disabling Qdrant.", exc)
                self._qdrant = None
        self._count += len(chunks)

    def search(self, query: str, k: int = 5) -> list[dict]:
        if self._qdrant is not None:
            try:
                hits = self._qdrant.query(
                    collection_name=self.collection, query_text=query, limit=k
                )
                return [
                    {
                        "text": h.document,
                        "score": round(float(h.score), 4),
                        "meta": h.metadata or {},
                    }
                    for h in hits
                ]
            except Exception as exc:  # pragma: no cover
                logger.warning("Qdrant query failed (%s); using TF-IDF.", exc)
        return self._tfidf.search(query, k=k)

    @property
    def size(self) -> int:
        return self._count or self._tfidf.size
