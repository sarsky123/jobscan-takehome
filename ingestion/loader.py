"""Load job JSONs from a directory and produce text for embedding."""
from __future__ import annotations

import json
from pathlib import Path

from ingestion.config import JOB_MAPPING_FILENAME, MAX_TEXT_CHARS


def discover_job_files(data_dir: Path) -> list[Path]:
    out: list[Path] = []
    for p in sorted(data_dir.glob("*.json")):
        if p.name == JOB_MAPPING_FILENAME:
            continue
        out.append(p)
    return out


def load_jobs_from_path(path: Path) -> list[dict]:
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, list):
        raise ValueError(f"{path.name}: expected a JSON array of job objects")
    return data


def load_all_jobs(data_dir: Path) -> list[dict]:
    paths = discover_job_files(data_dir)
    if not paths:
        raise FileNotFoundError(f"No seed JSON files found in {data_dir}")
    jobs: list[dict] = []
    for p in paths:
        jobs.extend(load_jobs_from_path(p))
    return jobs


def text_to_embed(job: dict) -> str:
    title = job.get("title") or job.get("title_raw") or ""
    org = job.get("organization") or job.get("company") or ""
    desc = job.get("description_text") or job.get("description") or ""
    text = f"{title}\n\n{org}\n\n{desc}".strip()
    if len(text) > MAX_TEXT_CHARS:
        text = text[:MAX_TEXT_CHARS] + "\n[truncated]"
    return text
