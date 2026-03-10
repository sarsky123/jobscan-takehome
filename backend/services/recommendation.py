from __future__ import annotations

import asyncio
import hashlib
import logging
import os
from collections import OrderedDict
from typing import List

import numpy as np
from openai import AsyncOpenAI, OpenAIError
from tenacity import (
    AsyncRetrying,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

logger = logging.getLogger(__name__)
from backend.core.config import get_settings
from backend.models.schemas import JobResponse
from backend.repositories.vector_store import JobVectorStore

MAX_RESUME_CHARS = 30_000
EMBEDDING_MODEL = "text-embedding-3-small"
EMBED_CACHE_MAXSIZE = 500


class _EmbeddingLRUCache:
    """LRU cache for resume text -> embedding. Not thread-safe; use with a lock."""

    def __init__(self, maxsize: int) -> None:
        self._cache: OrderedDict[str, list[float]] = OrderedDict()
        self._maxsize = maxsize

    def get(self, key: str) -> list[float] | None:
        if key not in self._cache:
            return None
        self._cache.move_to_end(key)
        return self._cache[key]

    def set(self, key: str, value: list[float]) -> None:
        if key in self._cache:
            self._cache.move_to_end(key)
        self._cache[key] = value
        while len(self._cache) > self._maxsize:
            self._cache.popitem(last=False)


_embed_cache = _EmbeddingLRUCache(maxsize=EMBED_CACHE_MAXSIZE)
_embed_cache_lock = asyncio.Lock()


def _embed_cache_key(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _log_embed_retry(retry_state) -> None:
    if retry_state.outcome and retry_state.outcome.failed:
        exc = retry_state.outcome.exception()
        logger.warning(
            "OpenAI embedding attempt %s failed, retrying: %s",
            retry_state.attempt_number,
            exc,
        )


async def _embed_resume(client: AsyncOpenAI, text: str) -> list[float]:
    async for attempt in AsyncRetrying(
        retry=retry_if_exception_type(OpenAIError),
        stop=stop_after_attempt(5),
        wait=wait_exponential(multiplier=1, min=2, max=60),
        reraise=True,
        before_sleep=_log_embed_retry,
    ):
        with attempt:
            logger.info("Calling OpenAI embeddings API (model=%s, input_len=%d)", EMBEDDING_MODEL, len(text))
            resp = await client.embeddings.create(model=EMBEDDING_MODEL, input=[text])
            logger.debug("OpenAI embeddings API succeeded")
            return resp.data[0].embedding

    # Unreachable, but satisfies type-checkers.
    raise RuntimeError("Failed to obtain embedding for resume text")


def _l2_normalize_single(vector: np.ndarray) -> np.ndarray:
    if vector.ndim != 2 or vector.shape[0] != 1:
        raise ValueError(f"Expected vector shape (1, dim); got {vector.shape}")
    norms = np.linalg.norm(vector, axis=1, keepdims=True)
    norms = np.where(norms == 0, 1.0, norms)
    return (vector / norms).astype(np.float32)


async def get_recommendations(
    resume_text: str,
    k: int,
    vector_store: JobVectorStore,
    client: AsyncOpenAI | None = None,
) -> List[JobResponse]:
    """Embed resume text, search the vector store, and return job recommendations."""
    truncated = resume_text[:MAX_RESUME_CHARS]
    cache_key = _embed_cache_key(truncated)

    async with _embed_cache_lock:
        embedding = _embed_cache.get(cache_key)
    if embedding is None:
        logger.info("Embedding resume text (truncated to %d chars)", len(truncated))
        settings = get_settings()
        api_key = (settings.openai_api_key or os.environ.get("OPENAI_API_KEY")) if client is None else None
        openai_client = client or AsyncOpenAI(api_key=api_key)
        try:
            embedding = await _embed_resume(openai_client, truncated)
        except OpenAIError as e:
            logger.error("OpenAI error while embedding resume: %s", e, exc_info=True)
            raise
        async with _embed_cache_lock:
            _embed_cache.set(cache_key, embedding)
    else:
        logger.debug("Resume embedding cache hit")

    vec = np.array(embedding, dtype=np.float32).reshape(1, -1)
    normalized = _l2_normalize_single(vec)

    hits = vector_store.search(normalized, k)
    return [JobResponse(**hit) for hit in hits]

