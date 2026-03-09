from __future__ import annotations

from typing import List

from fastapi import APIRouter, HTTPException, Request
from openai import OpenAIError

from backend.core.rate_limit import limiter
from backend.models.schemas import JobResponse, RecommendationRequest
from backend.services.recommendation import get_recommendations


router = APIRouter()


@router.get("/health")
@limiter.limit("30/minute")
async def health(request: Request) -> dict:
    return {"status": "ok"}


@router.post("/recommendations", response_model=List[JobResponse])
@limiter.limit("30/minute")
async def recommendations_endpoint(
    request: Request,
    body: RecommendationRequest,
) -> List[JobResponse]:
    vector_store = getattr(request.app.state, "vector_store", None)
    if vector_store is None:
        raise HTTPException(status_code=500, detail="Vector store not initialized")

    try:
        return await get_recommendations(
            resume_text=body.resume_text,
            k=body.k,
            vector_store=vector_store,
        )
    except OpenAIError as exc:
        raise HTTPException(status_code=502, detail="Upstream OpenAI error") from exc

