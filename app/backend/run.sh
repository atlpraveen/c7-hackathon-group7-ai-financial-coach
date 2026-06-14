#!/usr/bin/env bash
# Start the AI Financial Coach backend.
set -euo pipefail
cd "$(dirname "$0")"

if [ ! -d ".venv" ]; then
  echo "Creating virtual environment..."
  python3 -m venv .venv
fi
source .venv/bin/activate

pip install --quiet --upgrade pip
pip install --quiet -r requirements.txt

[ -f .env ] || cp .env.example .env

echo "Starting API on http://localhost:8000  (docs at /docs)"
uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000
