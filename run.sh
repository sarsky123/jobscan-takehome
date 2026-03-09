#!/usr/bin/env bash
# Run backend and frontend from repo root. Ctrl+C stops both.

set -e
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT"

if [ -d ".venv" ]; then
  source .venv/bin/activate
elif [ -d "venv" ]; then
  source venv/bin/activate
fi

BACKEND_PID=""
cleanup() {
  if [ -n "$BACKEND_PID" ]; then
    kill "$BACKEND_PID" 2>/dev/null || true
  fi
  exit 0
}
trap cleanup INT TERM EXIT

uvicorn backend.main:app --reload &
BACKEND_PID=$!
sleep 2
cd frontend && npm run dev
