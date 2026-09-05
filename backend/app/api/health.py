import logging
import httpx
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text, select, func

from app.database import get_db
from app.config import get_settings
from app.models.db_models import TranscriptChunkModel
from app.models.schemas import HealthResponse
from app.rag.retriever import LOCAL_CACHE_PATH
import os
import json

logger = logging.getLogger(__name__)
settings = get_settings()
router = APIRouter(prefix="/api/health", tags=["Health"])

@router.get("", response_model=HealthResponse)
async def check_health(db: AsyncSession = Depends(get_db)):
    """Comprehensive healthcheck probe reporting Database, Ollama, Vector Index, and retrieval source status."""
    db_ok = False
    total_chunks = 0
    vector_index = False
    retrieval_source = "none"

    # 1. Check PostgreSQL & Vector Index
    if db is not None:
        try:
            import asyncio
            stmt = select(func.count(TranscriptChunkModel.id))
            result = await asyncio.wait_for(db.execute(stmt), timeout=2.0)
            total_chunks = result.scalar() or 0
            db_ok = True

            if total_chunks > 0:
                retrieval_source = "pgvector"

            # Verify HNSW index existence
            try:
                idx_result = await asyncio.wait_for(
                    db.execute(text(
                        "SELECT indexname FROM pg_indexes WHERE tablename = 'transcript_chunks' AND indexdef LIKE '%hnsw%';"
                    )),
                    timeout=2.0
                )
                idx_rows = idx_result.fetchall()
                vector_index = len(idx_rows) > 0
            except Exception as idx_err:
                logger.debug(f"HNSW index check failed: {idx_err}")

        except Exception as e:
            logger.debug(f"DB health probe failed ({e}). Checking local cache file.")
            if os.path.exists(LOCAL_CACHE_PATH):
                try:
                    with open(LOCAL_CACHE_PATH, "r", encoding="utf-8") as f:
                        cached = json.load(f)
                        total_chunks = len(cached)
                        retrieval_source = "local_cache"
                except Exception:
                    pass
    else:
        if os.path.exists(LOCAL_CACHE_PATH):
            try:
                with open(LOCAL_CACHE_PATH, "r", encoding="utf-8") as f:
                    cached = json.load(f)
                    total_chunks = len(cached)
                    retrieval_source = "local_cache"
            except Exception:
                pass

    # 2. Check Ollama Connectivity
    ollama_ok = False
    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            resp = await client.get(f"{settings.OLLAMA_BASE_URL}/api/tags")
            if resp.status_code == 200:
                ollama_ok = True
    except Exception:
        ollama_ok = False

    # 3. Check Cloud Providers configuration
    cloud_status = {
        "anthropic": bool(settings.ANTHROPIC_API_KEY),
        "openai": bool(settings.OPENAI_API_KEY)
    }

    overall_status = "healthy" if (db_ok or total_chunks > 0) and (ollama_ok or any(cloud_status.values())) else "degraded"

    return HealthResponse(
        status=overall_status,
        database=db_ok,
        ollama=ollama_ok,
        ollama_model=settings.OLLAMA_MODEL,
        total_chunks=total_chunks,
        cloud_providers=cloud_status,
        vector_index=vector_index,
        retrieval_source=retrieval_source
    )
