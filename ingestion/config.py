"""Env-based config so the service can be pointed at different paths when scaled."""
from __future__ import annotations

import os
from pathlib import Path


def _str_path(value: str | None) -> Path | None:
    if value is None or value.strip() == "":
        return None
    return Path(value).resolve()


def get_config() -> dict:
    """Paths for input (job JSONs) and outputs (FAISS index, job ids, documents)."""
    # Default: repo root is parent of ingestion/
    _default_root = Path(__file__).resolve().parents[1]
    _default_storage = _default_root / "storage"
    _default_feed = _default_storage / "feed"
    _default_vectors = _default_storage / "vectors"
    _default_documents = _default_storage / "documents"

    jobs_input_dir = _str_path(os.environ.get("JOBS_INPUT_DIR")) or _default_feed
    faiss_index_path = _str_path(os.environ.get("FAISS_INDEX_PATH")) or (
        _default_vectors / "faiss_index.bin"
    )
    job_ids_path = _str_path(os.environ.get("JOB_IDS_PATH")) or (_default_vectors / "job_ids.json")
    documents_path = _str_path(os.environ.get("DOCUMENTS_PATH")) or (
        _default_documents / "jobs.json"
    )

    return {
        "jobs_input_dir": jobs_input_dir,
        "faiss_index_path": faiss_index_path,
        "job_ids_path": job_ids_path,
        "documents_path": documents_path,
    }


EMBEDDING_MODEL = "text-embedding-3-small"
EMBEDDING_DIM = 1536
BATCH_SIZE = 100
MAX_TEXT_CHARS = 30_000
JOB_MAPPING_FILENAME = "job_mapping.json"  # legacy; no longer written by the service
