"""Persistence layer: SQLAlchemy engine, ORM models, and repositories.

Defaults to a local SQLite file so the app runs with zero setup; point
``DATABASE_URL`` at a ``postgresql://`` instance to use Postgres-backed
multi-user persistence and financial analytics.
"""
