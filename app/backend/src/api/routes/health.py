from fastapi import APIRouter

from src.api.dependencies import get_orchestrator
from src.core.config import settings
from src.llm import client as llm

router = APIRouter()


@router.get("/health")
def health():
    orch = get_orchestrator()
    return {
        "status": "healthy",
        "app": settings.APP_NAME,
        "currency": settings.CURRENCY,
        "llm_enabled": llm.available(),
        "narration": "llm" if llm.available() else "deterministic",
        "capabilities": {
            "llm_provider": "openrouter" if settings.openrouter_enabled else (
                "anthropic" if settings.ANTHROPIC_API_KEY.strip() else "none"
            ),
            "routing": "llm" if settings.openrouter_enabled else "keyword",
            "orchestration": orch.engine,
            "database": "postgres" if settings.is_postgres else "sqlite",
            "vector_store": "qdrant" if settings.QDRANT_URL.strip() else "tfidf",
            "google_oauth": settings.google_oauth_enabled,
            "streaming": settings.openrouter_enabled,
        },
        "agents": list(orch.agents.keys()),
    }
