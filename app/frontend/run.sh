#!/usr/bin/env bash
# Start the AI Financial Coach frontend (Vite dev server on :5173).
set -euo pipefail
cd "$(dirname "$0")"

if ! command -v npm >/dev/null 2>&1; then
  echo "Node.js / npm is required. Install Node 18+ from https://nodejs.org and re-run."
  exit 1
fi

[ -d node_modules ] || npm install
echo "Starting frontend on http://localhost:5173 (proxying /api → http://localhost:8000)"
npm run dev
