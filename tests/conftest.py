"""Shared test fixtures: production-like FAISS index and job documents."""
from __future__ import annotations

import json
import os
from pathlib import Path

import faiss
import numpy as np
import pytest

from backend.core.config import get_settings
from backend.repositories.vector_store import JobVectorStore

EMBEDDING_DIM = 1536


def _l2_normalize(vectors: np.ndarray) -> np.ndarray:
    """Match ingestion: divide by L2 norm, zeros -> 1."""
    norms = np.linalg.norm(vectors, axis=1, keepdims=True)
    norms = np.where(norms == 0, 1.0, norms)
    return (vectors / norms).astype(np.float32)


@pytest.fixture(scope="session")
def test_storage_path(tmp_path_factory: pytest.TempPathFactory) -> Path:
    """Build a real FAISS index and job metadata files; return the directory path."""
    root = tmp_path_factory.mktemp("backend_test_storage")

    # Three L2-normalized vectors (canonical basis-like, then normalized)
    vectors = np.zeros((3, EMBEDDING_DIM), dtype=np.float32)
    vectors[0, 0] = 1.0
    vectors[1, 1] = 1.0
    vectors[2, 2] = 1.0
    vectors = _l2_normalize(vectors)

    index = faiss.IndexFlatIP(EMBEDDING_DIM)
    index.add(vectors)

    vectors_dir = root / "vectors"
    vectors_dir.mkdir()
    docs_dir = root / "documents"
    docs_dir.mkdir()

    faiss_index_path = vectors_dir / "faiss_index.bin"
    job_ids_path = vectors_dir / "job_ids.json"
    documents_path = docs_dir / "jobs.json"

    faiss.write_index(index, str(faiss_index_path))

    job_ids = ["job-1", "job-2", "job-3"]
    # Mix organization/company and description_text/description like production.
    documents = {
        "job-1": {
            "id": "job-1",
            "title": "Software Engineer",
            "organization": "Acme Inc",
            "description_text": "Build and maintain backend services.",
        },
        "job-2": {
            "id": "job-2",
            "title": "Product Manager",
            "company": "Beta Corp",
            "description": "Own the roadmap and work with engineering.",
        },
        "job-3": {
            "id": "job-3",
            "title_raw": "Data Analyst",
            "organization": "Gamma LLC",
            "description_text": "Analyze data and build dashboards.",
        },
    }

    job_ids_path.write_text(json.dumps(job_ids), encoding="utf-8")
    documents_path.write_text(json.dumps(documents), encoding="utf-8")

    return root


@pytest.fixture(scope="session")
def test_vector_store(test_storage_path: Path) -> JobVectorStore:
    """Session-scoped JobVectorStore loaded from test_storage_path."""
    vectors_dir = test_storage_path / "vectors"
    docs_dir = test_storage_path / "documents"
    return JobVectorStore(
        faiss_index_path=vectors_dir / "faiss_index.bin",
        job_ids_path=vectors_dir / "job_ids.json",
        documents_path=docs_dir / "jobs.json",
    )


@pytest.fixture
def api_client_env(test_storage_path: Path) -> None:
    """Set BACKEND_* env vars and clear settings cache so app lifespan uses test data."""
    vectors_dir = test_storage_path / "vectors"
    docs_dir = test_storage_path / "documents"
    os.environ["BACKEND_FAISS_INDEX_PATH"] = str(vectors_dir / "faiss_index.bin")
    os.environ["BACKEND_JOB_IDS_PATH"] = str(vectors_dir / "job_ids.json")
    os.environ["BACKEND_DOCUMENTS_PATH"] = str(docs_dir / "jobs.json")
    get_settings.cache_clear()
    try:
        yield
    finally:
        get_settings.cache_clear()
        for key in ("BACKEND_FAISS_INDEX_PATH", "BACKEND_JOB_IDS_PATH", "BACKEND_DOCUMENTS_PATH"):
            os.environ.pop(key, None)
