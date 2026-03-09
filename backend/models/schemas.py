from __future__ import annotations

from typing import Any, Dict, List

from pydantic import BaseModel, Field


class RecommendationRequest(BaseModel):
    resume_text: str = Field(
        alias="resumeText",
        min_length=10,
        description="Raw resume text provided by the user.",
    )
    k: int = Field(
        default=5,
        ge=1,
        le=20,
        description="Number of top job recommendations to return.",
    )

    model_config = {
        "populate_by_name": True,
        "extra": "ignore",
    }


class JobResponse(BaseModel):
    id: str
    score: float
    metadata: Dict[str, Any]


JobResponseList = List[JobResponse]

