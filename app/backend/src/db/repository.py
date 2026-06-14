"""Data-access helpers over the ORM models.

Routes and services call these instead of touching SQLAlchemy directly. Also
houses the financial-analytics aggregations (spend trends, category breakdowns,
month-over-month deltas) computed in SQL — the PostgreSQL-backed analytics.
"""
from __future__ import annotations

from typing import Optional

from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from src.db.models import (
    Conversation,
    Document,
    Goal,
    Message,
    ProfileOverride,
    Transaction,
    User,
)


# --------------------------------------------------------------------------- #
# Users
# --------------------------------------------------------------------------- #
def get_user_by_email(db: Session, email: str) -> Optional[User]:
    return db.scalar(select(User).where(User.email == email.lower().strip()))


def get_user(db: Session, user_id: int) -> Optional[User]:
    return db.get(User, user_id)


def create_user(
    db: Session,
    email: str,
    hashed_password: Optional[str] = None,
    full_name: str = "",
    oauth_provider: Optional[str] = None,
) -> User:
    user = User(
        email=email.lower().strip(),
        hashed_password=hashed_password,
        full_name=full_name,
        oauth_provider=oauth_provider,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


# --------------------------------------------------------------------------- #
# Profile overrides
# --------------------------------------------------------------------------- #
def get_profile_overrides(db: Session, user_id: int) -> dict:
    row = db.scalar(select(ProfileOverride).where(ProfileOverride.user_id == user_id))
    return dict(row.data) if row and row.data else {}


def set_profile_overrides(db: Session, user_id: int, fields: dict) -> dict:
    row = db.scalar(select(ProfileOverride).where(ProfileOverride.user_id == user_id))
    if row is None:
        row = ProfileOverride(user_id=user_id, data={})
        db.add(row)
    merged = dict(row.data or {})
    for k, v in fields.items():
        if v is not None:
            merged[k] = v
    row.data = merged
    db.commit()
    return merged


def reset_profile_overrides(db: Session, user_id: int) -> None:
    db.execute(delete(ProfileOverride).where(ProfileOverride.user_id == user_id))
    db.commit()


# --------------------------------------------------------------------------- #
# Documents + transactions
# --------------------------------------------------------------------------- #
def add_document(db: Session, user_id: int, filename: str, kind: str, chunks: int, txns: int) -> Document:
    doc = Document(
        user_id=user_id, filename=filename, kind=kind, chunks=chunks, transactions_count=txns
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)
    return doc


def list_documents(db: Session, user_id: int) -> list[Document]:
    return list(db.scalars(select(Document).where(Document.user_id == user_id).order_by(Document.id)))


def list_documents_dicts(db: Session, user_id: int) -> list[dict]:
    """Document records shaped for the frontend (transactions_count -> transactions)."""
    return [
        {
            "filename": d.filename,
            "kind": d.kind,
            "chunks": d.chunks,
            "transactions": d.transactions_count,
        }
        for d in list_documents(db, user_id)
    ]


def _month_of(date_str: str) -> str:
    d = (date_str or "").strip()
    if len(d) >= 7 and d[4] in "-/":
        return d[:7].replace("/", "-")
    if len(d) >= 10 and d[2] in "-/" and d[5] in "-/":  # DD-MM-YYYY / MM-DD-YYYY
        return f"{d[6:10]}-{d[3:5]}"
    return ""


def add_transactions(db: Session, user_id: int, txns: list[dict], source: str = "") -> int:
    rows = []
    for t in txns:
        date = str(t.get("date") or "")
        rows.append(
            Transaction(
                user_id=user_id,
                txn_date=date[:10],
                month=_month_of(date),
                description=str(t.get("description") or "")[:512],
                amount=float(t.get("amount") or 0.0),
                category=str(t.get("category") or "other").lower()[:80],
                kind=str(t.get("kind") or "expense"),
                source=source[:512],
            )
        )
    db.add_all(rows)
    db.commit()
    return len(rows)


def get_transactions(db: Session, user_id: int) -> list[dict]:
    rows = db.scalars(select(Transaction).where(Transaction.user_id == user_id).order_by(Transaction.txn_date))
    return [
        {
            "id": r.id,
            "date": r.txn_date,
            "month": r.month,
            "description": r.description,
            "amount": r.amount,
            "category": r.category,
            "kind": r.kind,
        }
        for r in rows
    ]


def update_transaction_category(db: Session, user_id: int, txn_id: int, category: str) -> bool:
    row = db.get(Transaction, txn_id)
    if not row or row.user_id != user_id:
        return False
    row.category = category.lower()[:80]
    db.commit()
    return True


# --------------------------------------------------------------------------- #
# Analytics (SQL aggregations)
# --------------------------------------------------------------------------- #
def analytics_summary(db: Session, user_id: int) -> dict:
    """Spending trends, category mix, and month-over-month deltas in SQL."""
    base = select(Transaction).where(Transaction.user_id == user_id)
    total_txns = db.scalar(select(func.count()).select_from(base.subquery())) or 0
    if not total_txns:
        return {"has_data": False}

    # Monthly income / expense series.
    monthly_rows = db.execute(
        select(
            Transaction.month,
            Transaction.kind,
            func.sum(Transaction.amount),
        )
        .where(Transaction.user_id == user_id, Transaction.month != "")
        .group_by(Transaction.month, Transaction.kind)
        .order_by(Transaction.month)
    ).all()
    monthly: dict[str, dict] = {}
    for month, kind, total in monthly_rows:
        m = monthly.setdefault(month, {"month": month, "income": 0.0, "expense": 0.0})
        m[kind] = round(float(total or 0.0), 2)
    series = sorted(monthly.values(), key=lambda x: x["month"])
    for m in series:
        m["net"] = round(m["income"] - m["expense"], 2)

    # Category breakdown (expenses only).
    cat_rows = db.execute(
        select(Transaction.category, func.sum(Transaction.amount), func.count())
        .where(Transaction.user_id == user_id, Transaction.kind == "expense")
        .group_by(Transaction.category)
        .order_by(func.sum(Transaction.amount).desc())
    ).all()
    by_category = [
        {"category": c, "total": round(float(t or 0.0), 2), "count": n} for c, t, n in cat_rows
    ]

    # Month-over-month spend delta.
    mom = None
    if len(series) >= 2:
        prev, last = series[-2], series[-1]
        delta = last["expense"] - prev["expense"]
        mom = {
            "prev_month": prev["month"],
            "last_month": last["month"],
            "delta": round(delta, 2),
            "pct": round((delta / prev["expense"] * 100) if prev["expense"] else 0.0, 1),
        }

    n_months = max(len(series), 1)
    avg_income = round(sum(m["income"] for m in series) / n_months, 2)
    avg_expense = round(sum(m["expense"] for m in series) / n_months, 2)
    return {
        "has_data": True,
        "transaction_count": total_txns,
        "months": n_months,
        "monthly_series": series,
        "by_category": by_category,
        "avg_monthly_income": avg_income,
        "avg_monthly_expense": avg_expense,
        "avg_monthly_savings": round(avg_income - avg_expense, 2),
        "month_over_month": mom,
        "top_category": by_category[0]["category"] if by_category else None,
    }


# --------------------------------------------------------------------------- #
# Goals
# --------------------------------------------------------------------------- #
def list_goals(db: Session, user_id: int) -> list[Goal]:
    return list(db.scalars(select(Goal).where(Goal.user_id == user_id).order_by(Goal.id)))


def create_goal(db: Session, user_id: int, **fields) -> Goal:
    goal = Goal(user_id=user_id, **fields)
    db.add(goal)
    db.commit()
    db.refresh(goal)
    return goal


def update_goal(db: Session, user_id: int, goal_id: int, **fields) -> Optional[Goal]:
    goal = db.get(Goal, goal_id)
    if not goal or goal.user_id != user_id:
        return None
    for k, v in fields.items():
        if v is not None:
            setattr(goal, k, v)
    db.commit()
    db.refresh(goal)
    return goal


def delete_goal(db: Session, user_id: int, goal_id: int) -> bool:
    goal = db.get(Goal, goal_id)
    if not goal or goal.user_id != user_id:
        return False
    db.delete(goal)
    db.commit()
    return True


# --------------------------------------------------------------------------- #
# Conversations + messages (memory)
# --------------------------------------------------------------------------- #
def get_or_create_conversation(db: Session, user_id: int, conversation_id: Optional[int]) -> Conversation:
    if conversation_id:
        conv = db.get(Conversation, conversation_id)
        if conv and conv.user_id == user_id:
            return conv
    conv = Conversation(user_id=user_id)
    db.add(conv)
    db.commit()
    db.refresh(conv)
    return conv


def add_message(db: Session, conversation_id: int, role: str, content: str) -> Message:
    msg = Message(conversation_id=conversation_id, role=role, content=content)
    db.add(msg)
    db.commit()
    db.refresh(msg)
    return msg


def recent_messages(db: Session, conversation_id: int, limit: int = 10) -> list[dict]:
    rows = db.scalars(
        select(Message)
        .where(Message.conversation_id == conversation_id)
        .order_by(Message.id.desc())
        .limit(limit)
    )
    msgs = [{"role": r.role, "content": r.content} for r in rows]
    msgs.reverse()
    return msgs


def list_conversations(db: Session, user_id: int) -> list[dict]:
    rows = db.scalars(
        select(Conversation).where(Conversation.user_id == user_id).order_by(Conversation.id.desc())
    )
    return [{"id": c.id, "title": c.title, "created_at": c.created_at.isoformat()} for c in rows]
