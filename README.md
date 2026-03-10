# Jobscan Take-Home — Resume-to-Job Recommendation

Minimal, embedding-based resume-to-job recommendation app: backend API (FastAPI) and frontend (Vite + React). Paste a resume to get job recommendations.

## Prerequisites

- **Python 3.11+** (backend)
- **Node.js and npm** (frontend)
- **OpenAI API key**: set `OPENAI_API_KEY` or `BACKEND_OPENAI_API_KEY` in the environment, or use a `.env` file at the repo root (see [Configuration](#configuration) and [First-time setup](#first-time-setup-job-data)).
- **Job data**: Run the ingestion service once so `storage/vectors/` and `storage/documents/` are populated. See [ingestion/README.md](ingestion/README.md) for storage layout and ingestion commands.

## Configuration

Do not commit `.env`; it may contain secrets. Copy `.env.example` to `.env` and fill in values. The app reads from the environment (or `.env` at repo root when using a loader that supports it).

| Variable | Default | Notes |
|----------|---------|--------|
| **Backend** | `BACKEND_FAISS_INDEX_PATH` | `storage/vectors/faiss_index.bin` | Path to FAISS index file |
| | `BACKEND_JOB_IDS_PATH` | `storage/vectors/job_ids.json` | FAISS row index → job_id |
| | `BACKEND_DOCUMENTS_PATH` | `storage/documents/jobs.json` | job_id → job document |
| | `BACKEND_OPENAI_API_KEY` | — | Optional override; else `OPENAI_API_KEY` |
| **Ingestion** | `JOBS_INPUT_DIR` | `storage/feed/` | Directory of job JSON files |
| | `FAISS_INDEX_PATH` | `storage/vectors/faiss_index.bin` | Output FAISS index path |
| | `JOB_IDS_PATH` | `storage/vectors/job_ids.json` | Output job IDs list path |
| | `DOCUMENTS_PATH` | `storage/documents/jobs.json` | Output documents path |
| | `OPENAI_API_KEY` | — | **Required** for ingestion (embedding calls) |

Example for custom storage paths (ingestion):

```bash
export JOBS_INPUT_DIR=/data/feed
export FAISS_INDEX_PATH=/data/vectors/faiss_index.bin
export JOB_IDS_PATH=/data/vectors/job_ids.json
export DOCUMENTS_PATH=/data/documents/jobs.json
```

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

## API

- **GET /health** — Liveness check.
- **POST /recommendations** — Request body: `{ "resumeText": "…", "k": 5 }`. Validation: `resumeText` min length 10, `k` in 1–20. Returns a list of job recommendations with `id`, `score`, and metadata (title, company, description snippet, link). Score is cosine similarity (L2-normalized vectors, IndexFlatIP).

Rate limit: 30 requests per minute per client IP. Errors: 422 validation, 429 rate limit, 502 on upstream OpenAI failure.

## Testing / Verification

From the repo root with the backend venv activated:

```bash
pip install -r backend/requirements.txt
pytest
```

Tests cover: L2 normalization and truncation in the recommendation service, FAISS index ↔ job_id mapping and search in the vector store, and API validation and error handling.

## Evaluation plan

- **Labeled set:** Build a small set of (resume, set of relevant job_ids), e.g. 20–50 resumes with 1–5 relevant jobs each.
- **Metrics:** Recall@K and MRR@K for K = 5, 10, 20; optional human rubric (relevance, seniority/domain match) on a sample.
- **Baselines:** Compare embedding cosine vs a simple keyword baseline (e.g. BM25-lite); ablation without L2 normalization to confirm correctness.
- **Cost/latency:** Track embedding call latency and token/character usage under the current truncation policy.

## Scaling

For large corpora (e.g. 10k–1M jobs), the current in-memory FAISS and single-run ingestion become bottlenecks. See [ingestion/README.md](ingestion/README.md) for a concrete scaling strategy: decoupled ingestion (event-driven, checkpointing), dedicated vector DB with ANN indexes, and document store segregation.

## Troubleshooting

- **Missing `storage/vectors/faiss_index.bin` or `storage/documents/jobs.json`** — Run ingestion once: `OPENAI_API_KEY=your_key python -m ingestion`.
- **502 or "Upstream OpenAI error"** — Check `OPENAI_API_KEY` (or `BACKEND_OPENAI_API_KEY`) and network; possible rate limit from OpenAI.
- **429 from API** — Client rate limit (30/min per IP); back off or adjust rate limit in backend config.
- **CORS errors in browser** — Backend allows `http://localhost:5173` and `http://127.0.0.1:5173`. If using another origin (e.g. deployed frontend), add it to `CORS_ORIGINS` in `backend/main.py`.
