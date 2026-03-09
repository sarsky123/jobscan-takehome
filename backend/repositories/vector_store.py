from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List

import faiss
import numpy as np


class JobVectorStore:
    """Thin wrapper around a FAISS index plus job metadata."""

    def __init__(self, faiss_index_path: Path, job_ids_path: Path, documents_path: Path) -> None:
        if not faiss_index_path.is_file():
            raise FileNotFoundError(f"FAISS index not found at {faiss_index_path}")
        if not job_ids_path.is_file():
            raise FileNotFoundError(f"Job IDs mapping not found at {job_ids_path}")
        if not documents_path.is_file():
            raise FileNotFoundError(f"Documents mapping not found at {documents_path}")

        self.index = faiss.read_index(str(faiss_index_path))

        with job_ids_path.open(encoding="utf-8") as f:
            self.job_ids: List[str] = json.load(f)

        with documents_path.open(encoding="utf-8") as f:
            self.documents: Dict[str, Dict[str, Any]] = json.load(f)

        if self.index.ntotal != len(self.job_ids):
            raise ValueError(
                f"FAISS index size ({self.index.ntotal}) does not match number of job IDs ({len(self.job_ids)})"
            )

    def _build_metadata(self, job: Dict[str, Any]) -> Dict[str, Any]:
        title = job.get("title") or job.get("title_raw") or ""
        company = job.get("organization") or job.get("company") or ""
        description = job.get("description_text") or job.get("description") or ""
        return {
            "title": title,
            "company": company,
            "description": description,
        }

    def search(self, query_vector: np.ndarray, k: int) -> List[Dict[str, Any]]:
        """Search the FAISS index and return job hits with mapped metadata.

        Assumes query_vector is already L2-normalized and shaped as (1, dim).
        """
        if query_vector.ndim != 2 or query_vector.shape[0] != 1:
            raise ValueError(f"query_vector must have shape (1, dim); got {query_vector.shape}")

        if query_vector.dtype != np.float32:
            query_vector = query_vector.astype(np.float32)

        scores, indices = self.index.search(query_vector, k)
        hits: List[Dict[str, Any]] = []

        for score, idx in zip(scores[0], indices[0]):
            if idx < 0:
                continue
            try:
                job_id = self.job_ids[idx]
            except IndexError:
                continue

            job = self.documents.get(job_id)
            if job is None:
                continue

            hits.append(
                {
                    "id": job_id,
                    "score": float(score),
                    "metadata": self._build_metadata(job),
                }
            )

        return hits

