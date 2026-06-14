"""Application configuration.

Every setting is optional so the app boots and works with zero setup. When the
relevant keys/URLs are present, richer backends light up automatically:

  * OPENROUTER_API_KEY  -> LLM routing, narration, categorization, streaming
  * DATABASE_URL        -> PostgreSQL persistence (defaults to local SQLite)
  * QDRANT_URL          -> Qdrant vector search (defaults to in-process TF-IDF)
  * GOOGLE_CLIENT_ID/SECRET -> Google OAuth login (JWT email/password always on)
"""
from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    APP_NAME: str = "AI Financial Coach"
    CURRENCY: str = "INR"  # all user-facing money is rendered in Indian Rupees

    # ---- LLM (OpenRouter, OpenAI-compatible) --------------------------------
    OPENROUTER_API_KEY: str = ""
    OPENROUTER_BASE_URL: str = "https://openrouter.ai/api/v1"
    # A strong default available on OpenRouter; override via .env if you like.
    COACH_MODEL: str = "anthropic/claude-opus-4-8"
    ROUTER_MODEL: str = "anthropic/claude-3.5-haiku"  # cheap/fast for routing + categorization
    # Legacy direct-Anthropic key (still honoured as a fallback narrator).
    ANTHROPIC_API_KEY: str = ""

    # ---- Persistence --------------------------------------------------------
    # Defaults to a local SQLite file; set a postgresql:// URL for Postgres.
    DATABASE_URL: str = "sqlite:///./financial_coach.db"

    # ---- Vector store -------------------------------------------------------
    # ":memory:" -> embedded Qdrant in RAM; a path -> embedded on disk;
    # an http(s) URL -> remote Qdrant server. Empty -> pure-Python TF-IDF.
    QDRANT_URL: str = ":memory:"
    QDRANT_API_KEY: str = ""
    QDRANT_COLLECTION: str = "financial_docs"
    EMBEDDING_MODEL: str = "BAAI/bge-small-en-v1.5"  # fastembed model id

    # ---- Auth ---------------------------------------------------------------
    JWT_SECRET: str = "dev-insecure-change-me"  # override in production!
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days
    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""
    OAUTH_REDIRECT_URL: str = "http://localhost:8000/auth/google/callback"
    FRONTEND_URL: str = "http://localhost:5173"

    # ---- CORS ---------------------------------------------------------------
    CORS_ORIGINS: str = "http://localhost:5173,http://127.0.0.1:5173"

    @property
    def cors_origins(self) -> list[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]

    # ---- Capability flags (used by /health and graceful fallbacks) ----------
    @property
    def llm_enabled(self) -> bool:
        return bool(self.OPENROUTER_API_KEY.strip() or self.ANTHROPIC_API_KEY.strip())

    @property
    def openrouter_enabled(self) -> bool:
        return bool(self.OPENROUTER_API_KEY.strip())

    @property
    def google_oauth_enabled(self) -> bool:
        return bool(self.GOOGLE_CLIENT_ID.strip() and self.GOOGLE_CLIENT_SECRET.strip())

    @property
    def is_postgres(self) -> bool:
        return self.DATABASE_URL.strip().lower().startswith(("postgres://", "postgresql://"))


settings = Settings()
