"""Orchestrated full review + document-grounded Q&A with conversation memory.

Includes a Server-Sent-Events streaming endpoint for real-time, token-by-token
chat responses.
"""
from __future__ import annotations

import json

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse

from src.agents.orchestrator import Orchestrator
from src.api.dependencies import UserContext, get_context, get_orchestrator
from src.api.schemas import AskRequest, CoachRequest
from src.db import repository as repo
from src.db.base import SessionLocal

router = APIRouter()


def _profile_summary(profile: dict) -> str:
    return (
        f"income Rs {profile['monthly_income']:,.0f}/mo, expenses "
        f"Rs {profile['monthly_expenses']:,.0f}/mo, savings "
        f"Rs {profile['savings_balance']:,.0f}, {len(profile['debts'])} debt(s)."
    )


@router.post("/review")
async def coach_review(
    body: CoachRequest = None,
    ctx: UserContext = Depends(get_context),
    orch: Orchestrator = Depends(get_orchestrator),
):
    """Route a query (or run all agents) and synthesise one prioritised plan."""
    body = body or CoachRequest()
    overrides = body.profile_overrides.model_dump() if body.profile_overrides else None
    profile = ctx.effective_profile(overrides)
    result = await orch.coach(profile, query=body.query, params=body.params)

    # Persist to conversation memory.
    conv = repo.get_or_create_conversation(ctx.db, ctx.user_id, body.conversation_id)
    repo.add_message(ctx.db, conv.id, "user", body.query or "Full financial review")
    repo.add_message(ctx.db, conv.id, "assistant", result["synthesis"])
    result["conversation_id"] = conv.id
    return result


@router.post("/ask")
def coach_ask(body: AskRequest, ctx: UserContext = Depends(get_context)):
    """Answer a free-form question grounded in the user's documents + chat memory."""
    profile = ctx.effective_profile()
    conv = repo.get_or_create_conversation(ctx.db, ctx.user_id, body.conversation_id)
    history = repo.recent_messages(ctx.db, conv.id, limit=8)

    result = ctx.rag.answer(body.question, profile_summary=_profile_summary(profile), history=history)

    repo.add_message(ctx.db, conv.id, "user", body.question)
    repo.add_message(ctx.db, conv.id, "assistant", result["answer"])
    result["conversation_id"] = conv.id
    return result


@router.post("/ask/stream")
def coach_ask_stream(body: AskRequest, ctx: UserContext = Depends(get_context)):
    """Stream the grounded answer token-by-token over Server-Sent Events."""
    profile = ctx.effective_profile()
    conv = repo.get_or_create_conversation(ctx.db, ctx.user_id, body.conversation_id)
    history = repo.recent_messages(ctx.db, conv.id, limit=8)
    summary = _profile_summary(profile)
    user_id = ctx.user_id
    conv_id = conv.id
    question = body.question

    def event_stream():
        yield f"data: {json.dumps({'type': 'meta', 'conversation_id': conv_id})}\n\n"
        collected = []
        for delta in ctx.rag.stream_answer(question, profile_summary=summary, history=history):
            collected.append(delta)
            yield f"data: {json.dumps({'type': 'delta', 'text': delta})}\n\n"
        answer = "".join(collected)
        # Persist the turn with a fresh session (request session may be closing).
        db = SessionLocal()
        try:
            repo.add_message(db, conv_id, "user", question)
            repo.add_message(db, conv_id, "assistant", answer)
        finally:
            db.close()
        yield f"data: {json.dumps({'type': 'done'})}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")


@router.get("/conversations")
def conversations(ctx: UserContext = Depends(get_context)):
    return {"conversations": repo.list_conversations(ctx.db, ctx.user_id)}


@router.get("/conversations/{conversation_id}")
def conversation_messages(conversation_id: int, ctx: UserContext = Depends(get_context)):
    return {"conversation_id": conversation_id, "messages": repo.recent_messages(ctx.db, conversation_id, limit=100)}
