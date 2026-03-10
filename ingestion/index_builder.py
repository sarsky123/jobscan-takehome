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
    # Persist only lightweight document metadata to keep memory low at query time.
    job_ids: list[str] = []
    documents: dict[str, dict] = {}
    for i, job in enumerate(jobs):
        job_id = job.get("id") or f"_{i}"
        job_ids.append(job_id)
        title = job.get("title") or job.get("title_raw") or ""
        company = job.get("organization") or job.get("company") or ""
        description = job.get("description_text") or job.get("description") or ""
        # Keep descriptions compact so the backend can load documents on small instances (e.g. 512Mi).
        if len(description) > 2_000:
            description = description[:2_000] + "…"
        documents[job_id] = {
            "title": title,
            "organization": company,
            "company": company,
            "description": description,
        }

    faiss_index_path.parent.mkdir(parents=True, exist_ok=True)
    job_ids_path.parent.mkdir(parents=True, exist_ok=True)
    documents_path.parent.mkdir(parents=True, exist_ok=True)

    faiss.write_index(index, str(faiss_index_path))
    with open(job_ids_path, "w", encoding="utf-8") as f:
        json.dump(job_ids, f, indent=2, ensure_ascii=False)
    with open(documents_path, "w", encoding="utf-8") as f:
        json.dump(documents, f, indent=2, ensure_ascii=False)
