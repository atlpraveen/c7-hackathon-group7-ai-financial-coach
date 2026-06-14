"""Database engine + session factory.

One SQLAlchemy engine is created from ``settings.DATABASE_URL``. SQLite (the
default) needs ``check_same_thread=False`` to be shared across FastAPI's thread
pool; Postgres uses a normal pooled connection.
"""
from __future__ import annotations

from collections.abc import Iterator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from src.core.config import settings
from src.core.logger import logger


class Base(DeclarativeBase):
    pass


def _make_engine():
    url = settings.DATABASE_URL
    if url.startswith("sqlite"):
        return create_engine(
            url, connect_args={"check_same_thread": False}, future=True
        )
    return create_engine(url, pool_pre_ping=True, future=True)


engine = _make_engine()
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False, future=True)


def init_db() -> None:
    """Create tables if they don't exist (demo-friendly; use Alembic in prod)."""
    # Import models so they're registered on Base.metadata before create_all.
    from src.db import models  # noqa: F401

    Base.metadata.create_all(bind=engine)
    logger.info("Database ready (%s).", "postgres" if settings.is_postgres else "sqlite")


def get_db() -> Iterator[Session]:
    """FastAPI dependency yielding a scoped session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
