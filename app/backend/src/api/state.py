"""Per-user session state + effective-profile assembly (multi-user).

The vector index (RAG) lives in-process, keyed by user id, so each user has an
isolated document workspace. Durable data — transactions, profile overrides,
and goals — lives in the database, so a user's profile survives restarts and is
shared across their sessions. ``build_profile`` merges all sources in priority
order: defaults < document/transaction-derived < stored overrides < request
overrides, with tracked goals injected from the goals table.
"""
from __future__ import annotations

from typing import Optional

from sqlalchemy.orm import Session

from src.db import repository as repo
from src.rag.rag_service import RAGService

_DEFAULTS: dict = {
    "monthly_income": 0.0,
    "monthly_expenses": 0.0,
    "expenses_by_category": {},
    "debts": [],
    "savings_balance": 0.0,
    "investment_balance": 0.0,
    "age": None,
    "risk_tolerance": "moderate",
    "goals": [],
    "currency": "INR",
}


class SessionStore:
    """Process-level registry of per-user RAG services."""

    def __init__(self) -> None:
        self._rags: dict[int, RAGService] = {}
        self._loaded: set[int] = set()

    def rag_for(self, user_id: int) -> RAGService:
        if user_id not in self._rags:
            self._rags[user_id] = RAGService(namespace=str(user_id))
        return self._rags[user_id]

    def ensure_loaded(self, db: Session, user_id: int) -> RAGService:
        """Hydrate the in-memory profile cache from the DB once per process."""
        rag = self.rag_for(user_id)
        if user_id not in self._loaded:
            txns = repo.get_transactions(db, user_id)
            if txns:
                rag.add_transactions(txns)
            self._loaded.add(user_id)
        return rag

    def invalidate(self, user_id: int) -> None:
        self._loaded.discard(user_id)
        self._rags.pop(user_id, None)


store = SessionStore()


def _goal_to_profile(goal) -> dict:
    return {
        "name": goal.name,
        "target_amount": goal.target_amount,
        "months": goal.target_months,
        "current": goal.current_amount,
        "annual_return": goal.annual_return,
    }


def build_profile(db: Session, user_id: int, rag: RAGService, overrides: Optional[dict] = None) -> dict:
    profile = dict(_DEFAULTS)

    derived = rag.profile()
    if derived:
        profile["monthly_income"] = derived["monthly_income"]
        profile["monthly_expenses"] = derived["monthly_expenses"]
        profile["expenses_by_category"] = derived["expenses_by_category"]
        if derived["inferred_debts"]:
            profile["debts"] = derived["inferred_debts"]

    stored = repo.get_profile_overrides(db, user_id)
    profile.update({k: v for k, v in stored.items() if v is not None})

    if overrides:
        profile.update({k: v for k, v in overrides.items() if v is not None})

    # Tracked goals (DB) are the source of truth for the goals list.
    db_goals = repo.list_goals(db, user_id)
    if db_goals:
        profile["goals"] = [_goal_to_profile(g) for g in db_goals]

    if not profile["monthly_expenses"] and profile["expenses_by_category"]:
        profile["monthly_expenses"] = round(sum(profile["expenses_by_category"].values()), 2)

    profile["debts"] = [d if isinstance(d, dict) else d.model_dump() for d in profile["debts"]]
    profile["goals"] = [g if isinstance(g, dict) else g.model_dump() for g in profile["goals"]]
    return profile
