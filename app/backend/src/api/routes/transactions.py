"""Transactions: listing, AI categorization, and manual re-categorization."""
from fastapi import APIRouter, Depends, HTTPException

from src.api import state
from src.api.dependencies import UserContext, get_context
from src.api.schemas import CategorizeRequest, RecategorizeRequest
from src.db import repository as repo
from src.services.categorization import categorize

router = APIRouter()


@router.get("")
def list_transactions(ctx: UserContext = Depends(get_context)):
    return {"transactions": repo.get_transactions(ctx.db, ctx.user_id)}


@router.post("/categorize")
def categorize_transactions(body: CategorizeRequest = None, ctx: UserContext = Depends(get_context)):
    """AI-categorize provided descriptions, or all of the user's stored ones."""
    body = body or CategorizeRequest()
    if body.descriptions:
        items = [{"description": d} for d in body.descriptions]
    else:
        items = [{"description": t["description"]} for t in repo.get_transactions(ctx.db, ctx.user_id)]
    if not items:
        raise HTTPException(status_code=400, detail="No transactions to categorize.")
    return categorize(items, use_llm=body.use_llm)


@router.put("/category")
def set_category(body: RecategorizeRequest, ctx: UserContext = Depends(get_context)):
    if not repo.update_transaction_category(ctx.db, ctx.user_id, body.transaction_id, body.category):
        raise HTTPException(status_code=404, detail="Transaction not found.")
    # Profile/analytics derive from transactions — refresh the cached session.
    state.store.invalidate(ctx.user_id)
    return {"ok": True}
