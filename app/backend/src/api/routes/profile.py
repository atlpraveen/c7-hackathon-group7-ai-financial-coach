"""Read / set / reset the user's financial profile (DB-backed overrides)."""
from __future__ import annotations

from fastapi import APIRouter, Depends

from src.api.dependencies import UserContext, get_context
from src.api.schemas import ProfileInput
from src.db import repository as repo

router = APIRouter()


@router.get("")
def get_profile(ctx: UserContext = Depends(get_context)):
    return {
        "profile": ctx.effective_profile(),
        "derived_from_documents": ctx.rag.profile() is not None,
        "user_overrides": repo.get_profile_overrides(ctx.db, ctx.user_id),
    }


@router.put("")
def set_profile(payload: ProfileInput, ctx: UserContext = Depends(get_context)):
    repo.set_profile_overrides(ctx.db, ctx.user_id, payload.model_dump())
    return {"profile": ctx.effective_profile()}


@router.post("/reset")
def reset_profile(ctx: UserContext = Depends(get_context)):
    repo.reset_profile_overrides(ctx.db, ctx.user_id)
    return {"profile": ctx.effective_profile()}
