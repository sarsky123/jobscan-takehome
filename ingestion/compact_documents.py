"""Create a compact documents mapping for low-memory backends.

This module avoids OpenAI calls. It converts an existing full documents mapping
(`storage/documents/jobs.json`) into a compact mapping (`jobs_compact.json`)
that contains only the fields needed by the demo UI.
"""

from __future__ import annotations

import json
from pathlib import Path


def _compact_job(job: dict) -> dict:
    title = job.get("title") or job.get("title_raw") or ""
    company = job.get("organization") or job.get("company") or ""
    description = job.get("description_text") or job.get("description") or ""
    if len(description) > 2_000:
        description = description[:2_000] + "…"
    return {
        "title": title,
        "organization": company,
        "company": company,
        "description": description,
    }


def build_compact_documents(*, full_documents_path: Path, compact_documents_path: Path) -> None:
    with full_documents_path.open(encoding="utf-8") as f:
        docs: dict[str, dict] = json.load(f)

    compact: dict[str, dict] = {job_id: _compact_job(job) for job_id, job in docs.items()}

    compact_documents_path.parent.mkdir(parents=True, exist_ok=True)
    with compact_documents_path.open("w", encoding="utf-8") as f:
        json.dump(compact, f, indent=2, ensure_ascii=False)


def main() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    docs_dir = repo_root / "storage" / "documents"
    full_path = docs_dir / "jobs.json"
    compact_path = docs_dir / "jobs_compact.json"
    if not full_path.is_file():
        raise FileNotFoundError(f"Full documents file not found at {full_path}")
    build_compact_documents(full_documents_path=full_path, compact_documents_path=compact_path)
    print(f"Wrote compact documents: {compact_path}")


if __name__ == "__main__":
    main()

