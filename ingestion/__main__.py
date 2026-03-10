"""Run as: python -m ingestion

Note: Ingestion uses the OpenAI SDK, which reads API keys from environment variables.
For local convenience, we load repo-root `.env` (if present) so `OPENAI_API_KEY` works
without having to prefix the command. In hosted environments (e.g. Render), env vars
should be provided by the platform and `.env` should not be relied on.
"""

from __future__ import annotations

from dotenv import load_dotenv

from ingestion.run import run


if __name__ == "__main__":
    # Load repo-root `.env` if present (no override).
    load_dotenv(override=False)
    run()
