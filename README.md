# Jobscan Take-Home — Resume-to-Job Recommendation

Minimal, embedding-based resume-to-job recommendation app: backend API (FastAPI) and frontend (Vite + React). Paste a resume to get job recommendations.

## Prerequisites

- **Python 3.11+** (backend)
- **Node.js and npm** (frontend)
- **OpenAI API key**: set `OPENAI_API_KEY` or `BACKEND_OPENAI_API_KEY` in the environment, or use a `.env` file at the repo root (see [Configuration](#configuration) and [First-time setup](#first-time-setup-job-data)).
- **Job data**: Run the ingestion service once so `storage/vectors/` and `storage/documents/` are populated. See [ingestion/README.md](ingestion/README.md) for storage layout and ingestion commands.

## Configuration

Do not commit `.env`; it may contain secrets. Copy `.env.example` to `.env` and fill in values. The app reads from the environment (or `.env` at repo root when using a loader that supports it).

| Section | Variable | Default | Notes |
| --- | --- | --- | --- |
| Backend | `BACKEND_FAISS_INDEX_PATH` | `storage/vectors/faiss_index.bin` | Path to FAISS index file |
| Backend | `BACKEND_JOB_IDS_PATH` | `storage/vectors/job_ids.json` | FAISS row index → job_id |
| Backend | `BACKEND_DOCUMENTS_PATH` | `storage/documents/jobs_compact.json` | job_id → job metadata (compact) |
| Backend | `BACKEND_OPENAI_API_KEY` | — | Optional override; else `OPENAI_API_KEY` |
| Ingestion | `JOBS_INPUT_DIR` | `storage/feed/` | Directory of job JSON files |
| Ingestion | `FAISS_INDEX_PATH` | `storage/vectors/faiss_index.bin` | Output FAISS index path |
| Ingestion | `JOB_IDS_PATH` | `storage/vectors/job_ids.json` | Output job IDs list path |
| Ingestion | `DOCUMENTS_PATH` | `storage/documents/jobs_compact.json` | Output documents path (compact) |
| Ingestion | `OPENAI_API_KEY` | — | Required for ingestion (embedding calls) |
| Render | `BACKEND_CORS_ORIGINS` | — | Comma-separated extra CORS origins (e.g. frontend URL) |
| Render | `VITE_API_URL` | — | Backend public URL (set at build time for static site) |

Example for custom storage paths (ingestion):

```bash
export JOBS_INPUT_DIR=/data/feed
export FAISS_INDEX_PATH=/data/vectors/faiss_index.bin
export JOB_IDS_PATH=/data/vectors/job_ids.json
export DOCUMENTS_PATH=/data/documents/jobs_compact.json
```

## Run backend only

From the repo root:

```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r backend/requirements.txt
uvicorn backend.main:app --reload
```

API: `http://localhost:8000`

## Run frontend only

```bash
cd frontend
npm install
npm run dev
```

App: `http://localhost:5173` (requires the backend to be running for recommendations).

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

## Quality Evaluation

**How would you evaluate recommendation quality?**

To ensure the recommendation system is both algorithmically accurate and valuable to users, I would evaluate quality across three dimensions:

**Engineering Sanity (Consistency & Determinism):** As a baseline, the system must be strictly deterministic. I would implement automated regression tests to ensure that feeding the exact same resume text consistently yields the exact same ordering of job results and similarity scores. This validates that the vector L2 normalization and ID mappings are stable.

**Offline Evaluation (Benchmark Testing):** Before deployment, I would build a "Golden Dataset"—a benchmark set of curated resumes categorized by specific dimensions (e.g., Seniority, Frontend vs. Backend, Industry). By running these through the system, we can measure Information Retrieval (IR) metrics like Recall@K and NDCG (Normalized Discounted Cumulative Gain) to objectively score how well the model differentiates between specialized skill sets and seniorities.

**Online Evaluation (User Interaction & Product Metrics):** Algorithmic accuracy must translate to user engagement. Post-deployment, I would use A/B testing to track real-world interaction metrics. The primary indicators of success would be the Click-Through Rate (CTR) on the recommended job cards, and ultimately, the Conversion Rate (how many users actually hit "Apply" after clicking).

## Improving Accuracy

**How would you further improve accuracy? Name 3 improvements and describe when you would use each.**

To move beyond the limitations of a naive dense vector index, I would implement the following concrete architectural upgrades:

### Query Expansion via LLM (HyDE - Hypothetical Document Embeddings)

**What:** Instead of directly embedding the user's raw resume, the system first passes the resume to a lightweight LLM with a prompt to generate a "perfect hypothetical job description" for this candidate. We then embed this hypothetical job description and use it to search the actual job corpus.

**When to use:** When there is a severe "Vocabulary Mismatch." For instance, a candidate might write "built a website," while the HR job description asks for "frontend web architecture experience." Expanding the query bridges the gap between candidate phrasing and standard industry jargon, drastically improving semantic recall.

### Metadata Pre-filtering (Hard-filtering)

**What:** Extract key structured data (e.g., years of experience required, location, remote status) from job descriptions during ingestion and store them as payload metadata in the vector database.

**When to use:** When there are absolute deal-breakers in the job requirements. Filtering the dataset with a SQL-like query (e.g., experience <= 5 AND is_remote = true) before performing the cosine similarity search prevents the system from recommending highly semantic-matched but fundamentally unqualified roles (like a Director role for a Junior candidate).

### Structural Chunking & Multi-Vector Matching

**What:** Instead of embedding an entire resume or job description into a single dense vector (which dilutes critical keywords and averages out the semantic meaning), I would chunk the documents into distinct structural sections (e.g., "Skills", "Experience", "Education"). The system would then generate separate embeddings for each chunk and perform a multi-vector weighted search (e.g., heavily weighting the match between Resume_Skills and JD_Requirements).

**When to use:** When the corpus contains very long, multi-faceted documents. This prevents "noise matching"—for example, ensuring a candidate's hobby mentioned in the resume doesn't falsely trigger a highly-scored match with an unrelated job's core requirement. It maintains the signal-to-noise ratio in high-dimensional space.

## Scaling

For large corpora (e.g. 10k–1M jobs), the current in-memory FAISS and single-run ingestion become bottlenecks. See [ingestion/README.md](ingestion/README.md) for a concrete scaling strategy: decoupled ingestion (event-driven, checkpointing), dedicated vector DB with ANN indexes, and document store segregation.

## Troubleshooting

- **Missing `storage/vectors/faiss_index.bin` or `storage/documents/jobs.json`** — Run ingestion once: `OPENAI_API_KEY=your_key python -m ingestion`.
- **Missing `storage/documents/jobs_compact.json`** — Build compact docs from an existing `jobs.json`: `python -m ingestion.compact_documents` (recommended for large feeds to avoid re-embedding).
- **502 or "Upstream OpenAI error"** — Check `OPENAI_API_KEY` (or `BACKEND_OPENAI_API_KEY`) and network; possible rate limit from OpenAI.
- **429 from API** — Client rate limit (30/min per IP); back off or adjust rate limit in backend config.
- **CORS errors in browser** — Backend allows `http://localhost:5173` and `http://127.0.0.1:5173`. For a deployed frontend, set `BACKEND_CORS_ORIGINS` to the frontend URL (e.g. `https://your-frontend.onrender.com`).

## Deployment (Render)

You can deploy the backend as a **Web Service** and the frontend as a **Static Site** on [Render](https://render.com). The app binds to `PORT` (default 10000 on Render) and `0.0.0.0`.

### Backend (Web Service)

- **Pre-built index:** For Render (especially free-tier 512MB), the FAISS index must be pre-built and committed. Also commit the compact documents file to avoid startup OOM. Do not run ingestion on Render’s build environment. Run ingestion locally: `python -m ingestion` (uses repo-root `.env` if present), then commit `storage/vectors/` and `storage/documents/jobs_compact.json`. For large feeds, you can create `jobs_compact.json` from an existing `jobs.json` without re-embedding: `python -m ingestion.compact_documents`.
- **Build command:** `pip install --no-cache-dir -r backend/requirements.txt`
- **Start command:** `python -m backend.run` (listens on `0.0.0.0` and `PORT`).
- **Environment variables:** Set `OPENAI_API_KEY` (required for recommendation embedding at runtime). After the frontend is deployed, set `BACKEND_CORS_ORIGINS` to the frontend URL (e.g. `https://your-frontend.onrender.com`).
- **Health check path:** `/health` (optional).

### Frontend (Static Site)

- **Root directory:** `frontend`.
- **Build command:** `npm install && npm run build`.
- **Publish directory:** `dist`.
- **Environment variables:** Set `VITE_API_URL` to the backend’s public URL at build time (e.g. `https://your-backend.onrender.com`, no trailing slash).

**Order:** Deploy the backend first, then set `VITE_API_URL` on the frontend and `BACKEND_CORS_ORIGINS` on the backend to the two service URLs. Alternatively, use the [render.yaml](render.yaml) Blueprint (New → Blueprint), then fill in `OPENAI_API_KEY`, `BACKEND_CORS_ORIGINS`, and `VITE_API_URL` in the dashboard.
