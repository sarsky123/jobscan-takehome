from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from backend.api.routes import router as api_router
from backend.core.config import get_settings
from backend.core.rate_limit import limiter
from backend.repositories.vector_store import JobVectorStore


def _cors_origins() -> list[str]:
    """Localhost origins plus any from BACKEND_CORS_ORIGINS (comma-separated)."""
    base = ["http://localhost:5173", "http://127.0.0.1:5173"]
    settings = get_settings()
    if not settings.cors_origins or not settings.cors_origins.strip():
        return base
    extra = [o.strip() for o in settings.cors_origins.split(",") if o.strip()]
    return base + extra


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    settings = get_settings()
    app.state.vector_store = JobVectorStore(
        faiss_index_path=settings.faiss_index_path,
        job_ids_path=settings.job_ids_path,
        documents_path=settings.documents_path,
    )
    try:
        yield
    finally:
        # No explicit cleanup required for in-memory FAISS index.
        app.state.vector_store = None


app = FastAPI(lifespan=lifespan)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Explicit origins so credentials work; localhost + BACKEND_CORS_ORIGINS for deployed frontend.
app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)

