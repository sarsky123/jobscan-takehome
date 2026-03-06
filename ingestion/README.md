# Ingestion Service

Offline ingestion: load job JSONs from storage, embed via OpenAI, L2-normalize, build FAISS index, persist. Runs as an isolated service (`python -m ingestion`).

---

## Storage layout (scaling-ready)

This repo uses a **local storage layout that mimics the future scaled architecture** (S3 + Vector DB + Document DB), while using **FAISS locally** as a stand-in for the vector database.

- **Feed (future: S3):** `storage/feed/` contains raw job JSON files (each file is an array of job objects).
- **Vector store (future: Pinecone/Milvus):** `storage/vectors/`
  - `faiss_index.bin` — FAISS `IndexFlatIP` over L2-normalized embeddings (cosine similarity).
  - `job_ids.json` — FAISS row index → `job_id` mapping (lightweight).
- **Document store (future: DynamoDB/MongoDB):** `storage/documents/jobs.json` contains `{job_id: job_object}` for full payload retrieval.

At query time (in the future API): embed resume → FAISS search → indices → `job_ids.json` → fetch job payloads from `documents/jobs.json`.

---

## Scaling to Millions of Documents: What Breaks & How to Fix It

### What breaks first

**Ingestion:** A single script will fail on network errors/rate limits. Resuming from a 500k-record failure is impossible without checkpointing.

**Memory & Compute:** In-memory FAISS (IndexFlatIP) scales at \(O(N)\). Millions of 1536-d vectors will exhaust RAM and spike query latency.

### Concrete strategy

**Decoupled ingestion pipeline:** Move from a synchronous script to an event-driven architecture. Raw jobs land in S3 → publish to Kafka/SQS → consumed by a pool of Embedding Workers. These workers handle rate-limiting, batching, and fault tolerance via message retries.

**Dedicated vector database:** Replace local FAISS with a managed Vector DB (e.g., Pinecone, Milvus). Use ANN (Approximate Nearest Neighbors, like HNSW) indexes to reduce search complexity from \(O(N)\) to \(O(\log N)\).

**Database segregation:** Store only vectors and Job IDs in the Vector DB for fast retrieval. Store the heavy text payloads (full job descriptions) in a Document DB (e.g., DynamoDB/MongoDB) to optimize storage costs and allow traditional keyword filtering.
