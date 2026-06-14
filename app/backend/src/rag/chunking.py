"""Text chunking for retrieval."""
from __future__ import annotations


def chunk_text(text: str, chunk_size: int = 600, overlap: int = 80) -> list[str]:
    """Split text into overlapping word-bounded chunks.

    Word-aware (rather than raw character slicing) so chunks stay readable and
    retrieval scores are meaningful.
    """
    text = (text or "").strip()
    if not text:
        return []
    words = text.split()
    chunks: list[str] = []
    step = max(chunk_size - overlap, 1)
    # Approximate words-per-chunk from an average word length of ~6 chars.
    words_per_chunk = max(chunk_size // 6, 20)
    words_step = max(step // 6, 10)
    for i in range(0, len(words), words_step):
        chunk = " ".join(words[i : i + words_per_chunk])
        if chunk:
            chunks.append(chunk)
        if i + words_per_chunk >= len(words):
            break
    return chunks
