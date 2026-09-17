"""Central settings, loaded from environment / .env. Nothing else in the codebase
should call os.environ directly — import `settings` from here instead."""

from __future__ import annotations

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # Database
    database_url: str = "postgresql+psycopg://aegis:aegis@localhost:5432/aegis"
    database_url_async: str = "postgresql+asyncpg://aegis:aegis@localhost:5432/aegis"

    # LLM routing — provider-agnostic model identifiers, resolved by llm/router.py
    anthropic_api_key: str | None = None
    aegis_triage_model: str = "claude-haiku-4-5-20251001"
    aegis_diagnosis_model: str = "claude-sonnet-5"
    aegis_critic_model: str = "claude-sonnet-5"

    # RAG
    aegis_embedding_model: str = "BAAI/bge-small-en-v1.5"
    aegis_reranker_model: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"
    aegis_embedding_dim: int = 384

    # Ingestion
    aegis_poll_interval_minutes: int = Field(default=5, ge=1)

    # Observability
    langfuse_public_key: str | None = None
    langfuse_secret_key: str | None = None
    langfuse_host: str = "https://cloud.langfuse.com"

    # Critic loop
    aegis_max_critic_retries: int = 2
    aegis_groundedness_threshold: float = 0.75


settings = Settings()
