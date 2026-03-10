"""Entrypoint for running the API. Uses PORT env (default 8000) and binds to 0.0.0.0 for Render."""
from __future__ import annotations

import os

import uvicorn

if __name__ == "__main__":
    port = int(os.environ.get("PORT", "8000"))
    uvicorn.run(
        "backend.main:app",
        host="0.0.0.0",
        port=port,
    )
