"""FastAPI application wiring for the AI Financial Coach."""
from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from src.api.routes import (
    analytics,
    auth,
    budget,
    coach,
    debt,
    documents,
    goals,
    health,
    india,
    investment,
    portfolio,
    profile,
    savings,
    transactions,
)
from src.core.config import settings
from src.core.logger import logger
from src.db.base import init_db

app = FastAPI(
    title="AI Financial Coach API",
    version="2.0.0",
    description=(
        "A personalised multi-agent financial advisor with LLM routing, LangGraph "
        "orchestration, Qdrant RAG, JWT/OAuth auth, real-time streaming, "
        "PostgreSQL analytics, conversation memory, portfolio optimization, goal "
        "tracking, and Indian-finance (EPF/NPS/ELSS/SIP/tax) support."
    ),
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    logger.exception("Unhandled error on %s %s", request.method, request.url.path)
    return JSONResponse(status_code=500, content={"error": str(exc)})


app.include_router(health.router, tags=["Health"])
app.include_router(auth.router, prefix="/auth", tags=["Auth"])
app.include_router(documents.router, prefix="/documents", tags=["Documents"])
app.include_router(transactions.router, prefix="/transactions", tags=["Transactions"])
app.include_router(profile.router, prefix="/profile", tags=["Profile"])
app.include_router(analytics.router, prefix="/analytics", tags=["Analytics"])
app.include_router(goals.router, prefix="/goals", tags=["Goals"])
app.include_router(debt.router, prefix="/debt", tags=["Debt"])
app.include_router(savings.router, prefix="/savings", tags=["Savings"])
app.include_router(budget.router, prefix="/budget", tags=["Budget"])
app.include_router(investment.router, prefix="/investment", tags=["Investment"])
app.include_router(portfolio.router, prefix="/portfolio", tags=["Portfolio"])
app.include_router(india.router, prefix="/india", tags=["India"])
app.include_router(coach.router, prefix="/coach", tags=["Coach"])


@app.get("/")
def root():
    return {
        "app": settings.APP_NAME,
        "currency": settings.CURRENCY,
        "docs": "/docs",
        "narration": "llm" if settings.llm_enabled else "deterministic",
    }


@app.on_event("startup")
async def startup():
    init_db()
    # Seed the shared guest account so the first anonymous requests never race
    # to create it.
    from src.auth.deps import get_or_create_guest
    from src.db.base import SessionLocal

    db = SessionLocal()
    try:
        get_or_create_guest(db)
    finally:
        db.close()
    if settings.OPENROUTER_API_KEY.strip():
        logger.info("OPENROUTER_API_KEY is set — LLM routing via OpenRouter enabled.")
    logger.info(
        "%s started. LLM: %s | DB: %s | Vector: %s",
        settings.APP_NAME,
        "OpenRouter" if settings.openrouter_enabled else ("Anthropic" if settings.ANTHROPIC_API_KEY else "deterministic"),
        "postgres" if settings.is_postgres else "sqlite",
        "qdrant" if settings.QDRANT_URL.strip() else "tfidf",
    )
