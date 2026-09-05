#!/bin/bash
set -e

echo "============================================"
echo " The Lenny Growth Assistant - Backend Startup"
echo "============================================"

# Step 1: Wait for PostgreSQL to be ready
echo "[1/4] Waiting for PostgreSQL..."
MAX_RETRIES=30
RETRY=0
until python -c "
import asyncio
from app.database import init_db
result = asyncio.run(init_db())
exit(0 if result else 1)
" 2>/dev/null; do
    RETRY=$((RETRY + 1))
    if [ $RETRY -ge $MAX_RETRIES ]; then
        echo "  WARNING: PostgreSQL not available after ${MAX_RETRIES} retries. Starting with local cache fallback."
        break
    fi
    echo "  Waiting for database... (attempt $RETRY/$MAX_RETRIES)"
    sleep 2
done
echo "  Database check complete."

# Step 2: Download transcripts if needed
TRANSCRIPT_DIR="/app/data/transcripts"
TRANSCRIPT_COUNT=$(find "$TRANSCRIPT_DIR" -name "*.md" 2>/dev/null | wc -l)
echo "[2/4] Transcript files on disk: $TRANSCRIPT_COUNT"

if [ "$TRANSCRIPT_COUNT" -lt 5 ]; then
    echo "  Downloading transcripts from GitHub..."
    python scripts/download_transcripts.py || echo "  WARNING: Transcript download encountered errors (some may have failed)."
    TRANSCRIPT_COUNT=$(find "$TRANSCRIPT_DIR" -name "*.md" 2>/dev/null | wc -l)
    echo "  Transcripts after download: $TRANSCRIPT_COUNT"
else
    echo "  Transcripts already present, skipping download."
fi

# Step 3: Run ingestion if cache is missing or empty
CACHE_FILE="/app/data/chunks_cache.json"
echo "[3/4] Checking vector cache..."

if [ ! -f "$CACHE_FILE" ] || [ ! -s "$CACHE_FILE" ] || [ "$(python -c "import json; print(len(json.load(open('$CACHE_FILE'))))" 2>/dev/null)" = "0" ]; then
    echo "  Running ingestion pipeline (this may take several minutes on first boot)..."
    python scripts/ingest.py || echo "  WARNING: Ingestion encountered errors."
else
    CHUNK_COUNT=$(python -c "import json; print(len(json.load(open('$CACHE_FILE'))))" 2>/dev/null || echo "0")
    echo "  Cache already exists with $CHUNK_COUNT chunks. Skipping ingestion."
    echo "  (To re-ingest, delete $CACHE_FILE and restart)"
fi

# Step 4: Start the FastAPI server
echo "[4/4] Starting FastAPI server on port 8000..."
echo "============================================"
exec uvicorn app.main:app --host 0.0.0.0 --port 8000
