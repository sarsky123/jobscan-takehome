"""Orchestrate load → embed → L2 normalize → build index → save."""
from __future__ import annotations

import numpy as np
from openai import OpenAI

from ingestion.config import get_config
from ingestion.embedding import embed_all, l2_normalize
from ingestion.index_builder import build_and_save
from ingestion.loader import load_all_jobs, text_to_embed


def run() -> None:
    cfg = get_config()
    jobs_input_dir = cfg["jobs_input_dir"]
    faiss_index_path = cfg["faiss_index_path"]
    job_ids_path = cfg["job_ids_path"]
    documents_path = cfg["documents_path"]

    jobs = load_all_jobs(jobs_input_dir)
    if not jobs:
        raise ValueError("No job objects found in seed JSON files")

    texts = [text_to_embed(j) for j in jobs]
    client = OpenAI()
    all_embeddings = embed_all(client, texts)
    matrix = np.array(all_embeddings, dtype=np.float32)
    normalized = l2_normalize(matrix)

    build_and_save(normalized, jobs, faiss_index_path, job_ids_path, documents_path)
    print(
        f"Ingested {len(jobs)} jobs. "
        f"Index: {faiss_index_path}, job_ids: {job_ids_path}, documents: {documents_path}"
    )


if __name__ == "__main__":
    run()
