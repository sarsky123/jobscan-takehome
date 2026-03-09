# Jobscan Take-Home — Resume-to-Job Recommendation

Minimal, embedding-based resume-to-job recommendation app: backend API (FastAPI) and frontend (Vite + React). Paste a resume to get job recommendations.

## Prerequisites

- **Python 3.11+** (backend)
- **Node.js and npm** (frontend)
- **OpenAI API key**: set `OPENAI_API_KEY` or `BACKEND_OPENAI_API_KEY` in the environment, or use a `.env` file at the repo root (see [First-time setup](#first-time-setup-job-data)).
- **Job data**: Run the ingestion service once so `storage/vectors/` and `storage/documents/` are populated. See [ingestion/README.md](ingestion/README.md) for storage layout and ingestion commands.

## Run backend only

From the repo root:

```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r backend/requirements.txt
uvicorn backend.main:app --reload
```

API: **http://localhost:8000**

## Run frontend only

```bash
cd frontend
npm install
npm run dev
```

App: **http://localhost:5173** (requires the backend to be running for recommendations).

## Run both (backend + frontend)

**Option A — one command (macOS/Linux):**

From the repo root (with a venv at `.venv` or `venv`):

```bash
./run.sh
```

This starts the backend in the background and the frontend in the foreground. Use Ctrl+C to stop both.

**Option B — two terminals:**

1. Terminal 1: activate venv, then `uvicorn backend.main:app --reload` from repo root.
2. Terminal 2: `cd frontend && npm run dev`.

On Windows, use Option B (two terminals) if you are not using WSL for `run.sh`.

## First-time setup: job data

To populate job data before using the app, run the ingestion service from the repo root (see [ingestion/README.md](ingestion/README.md)):

```bash
OPENAI_API_KEY=your_key python -m ingestion
```

Then run the backend and frontend as above.
