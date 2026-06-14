"""Document upload + ingestion (tabular RAG entry points).

On ingest we: index chunks in the vector store, run AI-assisted categorization
over newly parsed transactions, and persist both the document record and the
normalised transactions to the database (powering analytics + multi-user).
"""
from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, UploadFile

from src.api.dependencies import UserContext, get_context
from src.db import repository as repo
from src.services.categorization import categorize

router = APIRouter()

_SAMPLE = Path(__file__).resolve().parents[3] / "sample_data" / "transactions.csv"


def _ingest(ctx: UserContext, filename: str, content: bytes) -> dict:
    rag = ctx.rag
    before = len(rag.transactions)
    record = rag.ingest(filename, content)
    new_txns = rag.transactions[before:]

    # AI-assisted categorization: fill in anything the parser left as "other".
    if new_txns:
        result = categorize([{"description": t.get("description", "")} for t in new_txns])
        for txn, res in zip(new_txns, result["results"]):
            if (txn.get("category") or "other") == "other":
                txn["category"] = res["category"]
        repo.add_transactions(ctx.db, ctx.user_id, new_txns, source=filename)

    repo.add_document(
        ctx.db, ctx.user_id, filename, record["kind"], record["chunks"], record["transactions"]
    )
    return record


@router.post("/upload")
async def upload_document(file: UploadFile, ctx: UserContext = Depends(get_context)):
    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="Empty file.")
    record = _ingest(ctx, file.filename or "upload", content)
    return {
        "ingested": record,
        "documents": repo.list_documents_dicts(ctx.db, ctx.user_id),
        "derived_profile": ctx.rag.profile(),
        "index_size": ctx.rag.retriever.size,
        "retriever": ctx.rag.retriever.backend,
    }


@router.post("/sample")
def load_sample(ctx: UserContext = Depends(get_context)):
    """Load the bundled sample transactions CSV so the app is usable instantly."""
    if not _SAMPLE.exists():
        raise HTTPException(status_code=404, detail="Sample data not found.")
    record = _ingest(ctx, _SAMPLE.name, _SAMPLE.read_bytes())
    return {
        "ingested": record,
        "documents": repo.list_documents_dicts(ctx.db, ctx.user_id),
        "derived_profile": ctx.rag.profile(),
    }


@router.get("")
def list_documents(ctx: UserContext = Depends(get_context)):
    return {
        "documents": repo.list_documents_dicts(ctx.db, ctx.user_id),
        "index_size": ctx.rag.retriever.size,
        "retriever": ctx.rag.retriever.backend,
        "derived_profile": ctx.rag.profile(),
    }
