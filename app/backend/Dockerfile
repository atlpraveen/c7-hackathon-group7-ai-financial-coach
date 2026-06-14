# ---------------------------------------------------------------------------
# AI Financial Coach — backend (FastAPI + Uvicorn)
# Self-contained image: all Python deps baked in, runs as a non-root user.
# ---------------------------------------------------------------------------
FROM python:3.11-slim AS base

# - PYTHONUNBUFFERED: stream logs straight to stdout (good for `docker logs`)
# - PIP_NO_CACHE_DIR: keep the image small
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# System libs:
#  - libgomp1: required by onnxruntime (pulled in by fastembed)
#  - curl: used by the container HEALTHCHECK
#  - build-essential: compiler for source-only wheels (e.g. PyStemmer on ARM64)
RUN apt-get update \
    && apt-get install -y --no-install-recommends libgomp1 curl build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies first so this layer is cached across code edits.
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copy application source.
COPY . .

# Writable data dir (SQLite db / embedded Qdrant / uploads) owned by app user.
RUN useradd --create-home --uid 10001 appuser \
    && mkdir -p /app/data \
    && chown -R appuser:appuser /app
USER appuser

EXPOSE 8000

# Container-level health probe hits the FastAPI /health endpoint.
HEALTHCHECK --interval=15s --timeout=5s --start-period=40s --retries=5 \
    CMD curl -fsS http://localhost:8000/health || exit 1

CMD ["uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
