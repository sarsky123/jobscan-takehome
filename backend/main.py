from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.api.routes import router as api_router
from backend.core.config import get_settings
from backend.repositories.vector_store import JobVectorStore


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

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)

