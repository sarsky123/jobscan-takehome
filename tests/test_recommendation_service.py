"""Tests for get_recommendations with real JobVectorStore and mocked OpenAI."""
from __future__ import annotations

from typing import Any, Dict, List
from unittest.mock import AsyncMock, MagicMock

import numpy as np
import pytest

from backend.models.schemas import JobResponse
from backend.repositories.vector_store import JobVectorStore
from backend.services.recommendation import MAX_RESUME_CHARS, get_recommendations


class RecordingVectorStore:
    """Wraps a JobVectorStore and records the last query_vector passed to search."""

    def __init__(self, store: JobVectorStore) -> None:
        self._store = store
        self.last_query: np.ndarray | None = None

    def search(self, query_vector: np.ndarray, k: int) -> List[Dict[str, Any]]:
        self.last_query = query_vector.copy()
        return self._store.search(query_vector, k)


def _make_mock_client(
    embedding: List[float],
    capture_input: List[str] | None = None,
) -> MagicMock:
    """Build a mock AsyncOpenAI whose embeddings.create returns the given embedding."""
    mock_create = AsyncMock(return_value=MagicMock(
        data=[MagicMock(embedding=embedding)],
    ))
    if capture_input is not None:
        def side_effect(*args, **kwargs):
            inp = kwargs.get("input") or (args[1] if len(args) > 1 else [])
            if isinstance(inp, list) and inp:
                capture_input.append(inp[0])
            return mock_create.return_value
        mock_create.side_effect = side_effect
    client = MagicMock()
    client.embeddings.create = mock_create
    return client


@pytest.mark.asyncio
async def test_get_recommendations_returns_job_responses(
    test_vector_store: JobVectorStore,
) -> None:
    """get_recommendations returns a list of JobResponse with id, score, metadata."""
    # Fixed 1536-dim vector (will be L2-normalized by service)
    embedding = [0.0] * 1536
    embedding[0] = 1.0
    mock_client = _make_mock_client(embedding)

    result = await get_recommendations(
        resume_text="Experienced software engineer with Python and FastAPI.",
        k=2,
        vector_store=test_vector_store,
        client=mock_client,
    )

    assert isinstance(result, list)
    assert len(result) == 2
    for item in result:
        assert isinstance(item, JobResponse)
        assert item.id
        assert isinstance(item.score, float)
        assert "title" in item.metadata
        assert "company" in item.metadata
        assert "description" in item.metadata


@pytest.mark.asyncio
async def test_get_recommendations_truncates_resume_to_30k_chars(
    test_vector_store: JobVectorStore,
) -> None:
    """Resume text longer than 30k chars is truncated before embedding."""
    captured: List[str] = []
    embedding = [0.0] * 1536
    embedding[0] = 1.0
    mock_client = _make_mock_client(embedding, capture_input=captured)

    await get_recommendations(
        resume_text="x" * 35_000,
        k=1,
        vector_store=test_vector_store,
        client=mock_client,
    )

    assert len(captured) == 1
    assert len(captured[0]) == MAX_RESUME_CHARS


@pytest.mark.asyncio
async def test_get_recommendations_l2_normalizes_query(
    test_vector_store: JobVectorStore,
) -> None:
    """The query vector passed to vector_store.search is L2-normalized."""
    recording_store = RecordingVectorStore(test_vector_store)
    # Non-normalized embedding
    embedding = [1.0, 2.0, 3.0] + [0.0] * (1536 - 3)
    mock_client = _make_mock_client(embedding)

    await get_recommendations(
        resume_text="A realistic resume text here.",
        k=1,
        vector_store=recording_store,
        client=mock_client,
    )

    assert recording_store.last_query is not None
    norm = float(np.linalg.norm(recording_store.last_query, axis=1)[0])
    assert np.isclose(norm, 1.0, atol=1e-5)
