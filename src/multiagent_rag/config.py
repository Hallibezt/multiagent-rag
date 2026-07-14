"""Application settings.

The data sources are INJECTED here — CLAUDE.md Rule 4, seam #1. Nothing
downstream hardcodes a connection string or a corpus: swap the env vars and the
same code runs against local Docker, a hosted Supabase, or a second domain.

pydantic-settings reads each field from the environment (or a `.env` file),
validates its type, and fails loudly if something is malformed.
"""

from __future__ import annotations

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # --- Injected data sources (Rule 4, seam #1) ---
    doc_store_dsn: str = Field(
        default="postgresql://rag:rag@localhost:5432/docs",
        description="Postgres + pgvector store for embedded documents (the RAG agent's data).",
    )
    sql_store_dsn: str = Field(
        default="postgresql://rag:rag@localhost:5433/guestpad",
        description="Postgres store for the structured GuestPad tables (the SQL agent's data).",
    )

    # --- Embedding (fastembed: local, no API key) ---
    embedding_model: str = Field(
        default="BAAI/bge-small-en-v1.5",
        description="fastembed model name (see TextEmbedding.list_supported_models()).",
    )
    embedding_dim: int = Field(
        default=384,
        description="Vector dimension of embedding_model; MUST match the pgvector column size.",
    )

    # --- LLM (Claude via Anthropic; model-agnostic seam) ---
    anthropic_api_key: str | None = Field(
        default=None,
        description="Claude API key (Phase 1+ agents). Loaded from .env; never committed.",
    )
    llm_model: str = Field(
        default="claude-opus-4-8",
        description="Claude model for answer synthesis and text-to-SQL.",
    )
    router_model: str = Field(
        default="claude-opus-4-8",
        description="Claude model for the supervisor classifier (claude-haiku-4-5 is a cheaper, faster option).",
    )


# Import this singleton everywhere: `from multiagent_rag.config import settings`.
settings = Settings()
