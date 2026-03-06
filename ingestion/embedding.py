"""OpenAI embeddings with batching and retry; L2 normalization."""
from __future__ import annotations

import numpy as np
from openai import OpenAI
from openai import RateLimitError as OpenAIRateLimitError
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from ingestion.config import BATCH_SIZE, EMBEDDING_MODEL


@retry(
    retry=retry_if_exception_type(OpenAIRateLimitError),
    stop=stop_after_attempt(5),
    wait=wait_exponential(multiplier=1, min=2, max=60),
    reraise=True,
)
def embed_batch(client: OpenAI, texts: list[str]) -> list[list[float]]:
    resp = client.embeddings.create(model=EMBEDDING_MODEL, input=texts)
    return [e.embedding for e in resp.data]


def embed_all(client: OpenAI, texts: list[str], batch_size: int = BATCH_SIZE) -> list[list[float]]:
    all_embeddings: list[list[float]] = []
    for i in range(0, len(texts), batch_size):
        batch = texts[i : i + batch_size]
        all_embeddings.extend(embed_batch(client, batch))
    return all_embeddings


def l2_normalize(vectors: np.ndarray) -> np.ndarray:
    norms = np.linalg.norm(vectors, axis=1, keepdims=True)
    norms = np.where(norms == 0, 1.0, norms)
    return (vectors / norms).astype(np.float32)
