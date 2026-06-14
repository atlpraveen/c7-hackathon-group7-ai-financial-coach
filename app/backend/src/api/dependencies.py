"""Shared singletons + per-request user context via FastAPI dependency injection."""
from __future__ import annotations

from typing import Optional

from fastapi import Depends
from sqlalchemy.orm import Session

from src.agents.orchestrator import Orchestrator
from src.api import state
from src.auth.deps import get_current_user
from src.db.base import get_db
from src.db.models import User
from src.rag.rag_service import RAGService

_orchestrator = Orchestrator()


def get_orchestrator() -> Orchestrator:
    return _orchestrator


class UserContext:
    """Everything a route needs: the authenticated user, a DB session, the
    user's RAG workspace, and a one-call effective-profile builder."""

    def __init__(self, db: Session, user: User, rag: RAGService) -> None:
        self.db = db
        self.user = user
        self.rag = rag

    @property
    def user_id(self) -> int:
        return self.user.id

    def effective_profile(self, overrides: Optional[dict] = None) -> dict:
        return state.build_profile(self.db, self.user.id, self.rag, overrides)


def get_context(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> UserContext:
    rag = state.store.ensure_loaded(db, user.id)
    return UserContext(db, user, rag)
