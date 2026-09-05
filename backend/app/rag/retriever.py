import os
import re
import json
import logging
from typing import List, Dict, Any, Optional
import numpy as np
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from app.rag.embeddings import compute_embedding
from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

# Path for local serialized chunks fallback
LOCAL_CACHE_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data", "chunks_cache.json")

class TranscriptRetriever:
    def __init__(self, session: Optional[AsyncSession] = None):
        self.session = session
        self._local_cache: Optional[List[Dict[str, Any]]] = None

    def _load_local_cache(self) -> List[Dict[str, Any]]:
        """Load pre-indexed chunks from local disk if database is offline."""
        if self._local_cache is not None:
            return self._local_cache
        if os.path.exists(LOCAL_CACHE_PATH):
            try:
                with open(LOCAL_CACHE_PATH, "r", encoding="utf-8") as f:
                    self._local_cache = json.load(f)
                    logger.info(f"Loaded {len(self._local_cache)} chunks from local cache.")
                    return self._local_cache
            except Exception as e:
                logger.error(f"Error loading local cache: {e}")
        return []

    async def retrieve_relevant_chunks(
        self,
        query: str,
        top_k: int = 5,
        similarity_threshold: float = 0.45
    ) -> List[Dict[str, Any]]:
        """
        Compute query vector and execute pgvector cosine similarity search.
        Falls back to in-memory vector search if database connection is unavailable.
        """
        query_vector = compute_embedding(query)

        # 1. Attempt PostgreSQL pgvector execution if database is online
        from app.database import DB_ONLINE
        if self.session is not None and DB_ONLINE:
            try:
                import asyncio
                query_stmt = text("""
                    SELECT
                        episode_title,
                        guest_name,
                        chunk_text,
                        timestamp_ref,
                        youtube_url,
                        1 - (embedding <=> :vector::vector) AS similarity_score
                    FROM transcript_chunks
                    WHERE 1 - (embedding <=> :vector::vector) >= :threshold
                    ORDER BY similarity_score DESC
                    LIMIT :limit;
                """)

                result = await asyncio.wait_for(
                    self.session.execute(
                        query_stmt,
                        {
                            "vector": str(query_vector),
                            "threshold": similarity_threshold,
                            "limit": top_k
                        }
                    ),
                    timeout=1.0
                )

                rows = result.fetchall()
                if rows:
                    return [
                        {
                            "episode": r.episode_title,
                            "guest": r.guest_name,
                            "text": r.chunk_text,
                            "timestamp": r.timestamp_ref,
                            "youtube_url": r.youtube_url or "",
                            "score": round(float(r.similarity_score), 4)
                        }
                        for r in rows
                    ]
            except Exception as e:
                logger.warning(f"pgvector query failed or DB offline ({e}). Using local in-memory fallback.")

        # 2. Resilient In-Memory Hybrid Vector + Keyword Search Fallback
        cached_chunks = self._load_local_cache()
        if not cached_chunks:
            return []

        q_vec = np.array(query_vector, dtype=np.float32)
        q_norm = np.linalg.norm(q_vec)
        if q_norm > 0:
            q_vec = q_vec / q_norm

        query_terms = set(re.findall(r'\w+', query.lower()))
        stopwords = {"the", "a", "an", "and", "or", "in", "on", "at", "to", "for", "of", "with", "is", "are", "what", "how", "why", "who", "view", "it"}
        filtered_terms = query_terms - stopwords

        scored_chunks = []
        for chunk in cached_chunks:
            c_vec = np.array(chunk.get("embedding", []), dtype=np.float32)
            vector_score = 0.0
            if len(c_vec) > 0:
                c_norm = np.linalg.norm(c_vec)
                if c_norm > 0:
                    c_vec = c_vec / c_norm
                vector_score = float(np.dot(q_vec, c_vec))

            # Keyword lexical overlap
            chunk_content = (
                chunk.get("guest_name", "") + " " +
                chunk.get("episode_title", "") + " " +
                chunk.get("chunk_text", "")
            ).lower()

            if filtered_terms:
                term_matches = sum(1 for t in filtered_terms if t in chunk_content)
                lexical_score = term_matches / len(filtered_terms)
            else:
                lexical_score = 0.0

            # Hybrid score: combines dense vector alignment and lexical accuracy
            final_score = round(max(vector_score, 0.4 * vector_score + 0.6 * lexical_score), 4)

            if final_score >= similarity_threshold:
                scored_chunks.append({
                    "episode": chunk.get("episode_title", "Lenny's Podcast"),
                    "guest": chunk.get("guest_name", "Lenny Rachitsky"),
                    "text": chunk.get("chunk_text", ""),
                    "timestamp": chunk.get("timestamp_ref", "00:00:00"),
                    "youtube_url": chunk.get("youtube_url", ""),
                    "score": final_score
                })

        scored_chunks.sort(key=lambda x: x["score"], reverse=True)
        return scored_chunks[:top_k]
