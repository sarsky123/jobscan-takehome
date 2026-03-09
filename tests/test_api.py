"""API route tests using TestClient, test index via env, and mocked OpenAI."""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient
from openai import OpenAIError

from backend.main import app


@pytest.fixture
def api_client(api_client_env: None) -> TestClient:
    """TestClient with app that loads vector store from test paths; OpenAI mocked."""
    fake_embedding = [0.0] * 1536
    fake_embedding[0] = 1.0
    mock_instance = MagicMock()
    mock_instance.embeddings.create = AsyncMock(
        return_value=MagicMock(data=[MagicMock(embedding=fake_embedding)])
    )
    with patch("backend.services.recommendation.AsyncOpenAI") as MockOpenAI:
        MockOpenAI.return_value = mock_instance
        with TestClient(app) as client:
            client.get("/health")  # trigger lifespan so vector_store is set
            yield client


def test_health_returns_ok(api_client: TestClient) -> None:
    """GET /health returns 200 and {\"status\": \"ok\"}."""
    resp = api_client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


def test_recommendations_returns_list_of_jobs(api_client: TestClient) -> None:
    """POST /recommendations returns 200 and a list of jobs with id, score, metadata."""
    resp = api_client.post(
        "/recommendations",
        json={
            "resumeText": "Experienced software engineer with Python and FastAPI.",
            "k": 5,
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    assert len(data) >= 1
    for item in data:
        assert "id" in item
        assert "score" in item
        assert "metadata" in item
        assert "title" in item["metadata"]
        assert "company" in item["metadata"]
        assert "description" in item["metadata"]


def test_recommendations_openai_error_returns_502(api_client: TestClient) -> None:
    """When get_recommendations raises OpenAIError, response is 502."""
    async def raise_openai_error(*args, **kwargs):
        raise OpenAIError("simulated error")

    with patch("backend.api.routes.get_recommendations", side_effect=raise_openai_error):
        resp = api_client.post(
            "/recommendations",
            json={
                "resumeText": "Experienced software engineer with Python and FastAPI.",
                "k": 3,
            },
        )
    assert resp.status_code == 502
    assert resp.json()["detail"] == "Upstream OpenAI error"


def test_recommendations_validation_resume_text_too_short(
    api_client: TestClient,
) -> None:
    """POST with resumeText shorter than 10 chars returns 422."""
    resp = api_client.post(
        "/recommendations",
        json={"resumeText": "short", "k": 5},
    )
    assert resp.status_code == 422


def test_recommendations_validation_k_out_of_range(api_client: TestClient) -> None:
    """POST with k > 20 returns 422."""
    resp = api_client.post(
        "/recommendations",
        json={
            "resumeText": "A valid resume with at least ten characters here.",
            "k": 25,
        },
    )
    assert resp.status_code == 422
