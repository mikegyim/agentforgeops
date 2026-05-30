"""Application configuration loaded from environment."""
from __future__ import annotations

from functools import lru_cache
from typing import List, Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    env: Literal["dev", "staging", "prod"] = "dev"

    # Database
    postgres_url: str = "postgresql+asyncpg://agentforge:agentforge@postgres:5432/agentforge"

    # Vector store
    vector_backend: Literal["qdrant", "chroma"] = "qdrant"
    qdrant_url: str = "http://qdrant:6333"
    qdrant_collection: str = "agentforge"
    chroma_path: str = "/data/chroma"

    # LLM
    llm_provider: Literal["openai", "anthropic", "bedrock", "mock"] = "mock"
    llm_model: str = "claude-opus-4-6"
    openai_api_key: str = ""
    anthropic_api_key: str = ""
    aws_region: str = "us-east-1"

    # Embeddings
    embedding_provider: Literal["openai", "anthropic", "local"] = "local"
    embedding_model: str = "all-MiniLM-L6-v2"
    embedding_dim: int = 384

    # GitHub integration
    github_token: str = ""
    github_webhook_secret: str = ""

    # Misc
    cors_origins: List[str] = Field(default_factory=lambda: ["http://localhost:3000"])
    upload_dir: str = "/data/uploads"
    max_upload_mb: int = 50


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
