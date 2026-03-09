"""Tests for JobVectorStore using a real FAISS index and job documents."""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest

from backend.repositories.vector_store import JobVectorStore


def test_search_returns_hits_with_correct_ids_and_metadata(
    test_vector_store: JobVectorStore,
) -> None:
    """Search returns hits with id, score, and metadata (title, company, description)."""
    # Query aligned with first indexed vector (job-1) so it scores highest.
    query = np.zeros((1, 1536), dtype=np.float32)
    query[0, 0] = 1.0
    norm = np.linalg.norm(query)
    query = (query / norm).astype(np.float32)

    hits = test_vector_store.search(query, k=3)

    assert len(hits) == 3
    assert hits[0]["id"] == "job-1"
    # job-2 and job-3 have score 0 (orthogonal to query); order between them is undefined
    by_id = {h["id"]: h for h in hits}

    # job-1: organization -> company, description_text -> description
    m1 = by_id["job-1"]["metadata"]
    assert m1["title"] == "Software Engineer"
    assert m1["company"] == "Acme Inc"
    assert "backend" in m1["description"].lower()

    # job-2: company and description already present
    m2 = by_id["job-2"]["metadata"]
    assert m2["title"] == "Product Manager"
    assert m2["company"] == "Beta Corp"
    assert "roadmap" in m2["description"].lower()

    # job-3: title_raw -> title
    m3 = by_id["job-3"]["metadata"]
    assert m3["title"] == "Data Analyst"
    assert m3["company"] == "Gamma LLC"
    assert "dashboards" in m3["description"].lower()


def test_search_handles_k_larger_than_index(test_vector_store: JobVectorStore) -> None:
    """Requesting k=10 with only 3 vectors returns 3 hits, no duplicates."""
    query = np.zeros((1, 1536), dtype=np.float32)
    query[0, 0] = 1.0
    query = (query / np.linalg.norm(query)).astype(np.float32)

    hits = test_vector_store.search(query, k=10)

    assert len(hits) == 3
    ids = [h["id"] for h in hits]
    assert len(ids) == len(set(ids))
    assert set(ids) == {"job-1", "job-2", "job-3"}


def test_init_fails_when_index_missing(tmp_path: Path) -> None:
    """JobVectorStore raises FileNotFoundError when FAISS index path does not exist."""
    missing_index = tmp_path / "missing.bin"
    job_ids_path = tmp_path / "job_ids.json"
    documents_path = tmp_path / "jobs.json"
    job_ids_path.write_text("[]")
    documents_path.write_text("{}")

    with pytest.raises(FileNotFoundError, match="FAISS index not found"):
        JobVectorStore(missing_index, job_ids_path, documents_path)
