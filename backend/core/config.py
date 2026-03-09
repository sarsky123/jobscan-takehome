from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Backend configuration, mirroring ingestion defaults for storage paths."""

    # Default: repo root is parent of backend/
    _default_root: Path = Path(__file__).resolve().parents[2]
    _default_storage: Path = _default_root / "storage"
    _default_vectors: Path = _default_storage / "vectors"
    _default_documents: Path = _default_storage / "documents"

    faiss_index_path: Path = Field(
        default=_default_vectors / "faiss_index.bin",
        description="Path to the persisted FAISS index file.",
    )
    job_ids_path: Path = Field(
        default=_default_vectors / "job_ids.json",
        description="Path to JSON list mapping FAISS row index -> job_id.",
    )
    documents_path: Path = Field(
        default=_default_documents / "jobs.json",
        description="Path to JSON mapping job_id -> full job document.",
    )

    # OpenAI configuration (API key is normally read from environment by the SDK).
    openai_api_key: str | None = Field(
        default=None,
        description="Optional OpenAI API key override; if unset, the OpenAI client uses its defaults.",
    )

    model_config = {
        "env_prefix": "BACKEND_",
        "extra": "ignore",
    }


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return a cached Settings instance."""
    return Settings()

