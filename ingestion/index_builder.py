"""Build FAISS index and persist vectors + documents (scaling-ready)."""
from __future__ import annotations

import json
from pathlib import Path

import faiss
import numpy as np

from ingestion.config import EMBEDDING_DIM


def build_and_save(
    vectors: np.ndarray,
    jobs: list[dict],
    faiss_index_path: Path,
    job_ids_path: Path,
    documents_path: Path,
) -> None:
    index = faiss.IndexFlatIP(EMBEDDING_DIM)
    index.add(vectors)

    # Vector store should only contain vectors + a lightweight ID mapping.
    job_ids: list[str] = []
    documents: dict[str, dict] = {}
    for i, job in enumerate(jobs):
        job_id = job.get("id") or f"_{i}"
        job_ids.append(job_id)
        documents[job_id] = job

    faiss_index_path.parent.mkdir(parents=True, exist_ok=True)
    job_ids_path.parent.mkdir(parents=True, exist_ok=True)
    documents_path.parent.mkdir(parents=True, exist_ok=True)

    faiss.write_index(index, str(faiss_index_path))
    with open(job_ids_path, "w", encoding="utf-8") as f:
        json.dump(job_ids, f, indent=2, ensure_ascii=False)
    with open(documents_path, "w", encoding="utf-8") as f:
        json.dump(documents, f, indent=2, ensure_ascii=False)
