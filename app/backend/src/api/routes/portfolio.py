"""Portfolio optimization agent (Markowitz mean-variance)."""
from typing import Optional

from fastapi import APIRouter, Depends

from src.agents.orchestrator import Orchestrator
from src.api.dependencies import UserContext, get_context, get_orchestrator
from src.api.schemas import AgentRequest

router = APIRouter()


@router.post("/optimize")
def optimize_portfolio(
    body: Optional[AgentRequest] = None,
    ctx: UserContext = Depends(get_context),
    orch: Orchestrator = Depends(get_orchestrator),
):
    body = body or AgentRequest()
    overrides = body.profile_overrides.model_dump() if body.profile_overrides else None
    profile = ctx.effective_profile(overrides)
    return orch.agents["portfolio"].run(profile, body.params)
