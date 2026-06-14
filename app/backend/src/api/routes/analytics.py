"""PostgreSQL-backed financial analytics (spend trends, category mix, MoM)."""
from fastapi import APIRouter, Depends

from src.api.dependencies import UserContext, get_context
from src.db import repository as repo

router = APIRouter()


@router.get("/summary")
def analytics_summary(ctx: UserContext = Depends(get_context)):
    return repo.analytics_summary(ctx.db, ctx.user_id)
