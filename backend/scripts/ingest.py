"""
Transcript Ingestion Pipeline for The Lenny Growth Assistant.

Parses downloaded Markdown transcript files, chunks them into 500-800 token segments
with ~100-token overlap, computes dense vector embeddings, saves to local JSON cache,
and ingests into PostgreSQL pgvector when available.
"""
import sys
import os
import re
import json
import uuid
import yaml
import asyncio
import logging
from typing import List, Dict, Any

# Ensure backend root is in sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.config import get_settings
from app.rag.embeddings import compute_batch_embeddings
from app.database import engine, Base, init_db
from app.models.db_models import TranscriptChunkModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("transcript-ingest")
settings = get_settings()

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TRANSCRIPTS_DIR = os.path.join(BASE_DIR, "data", "transcripts")
CACHE_FILE = os.path.join(BASE_DIR, "data", "chunks_cache.json")

TIMESTAMP_PATTERN = re.compile(r'^(.*?)\s*\(((?:\d{1,3}:)?\d{1,2}:\d{2})\):', re.MULTILINE)


def estimate_tokens(text: str) -> int:
    """Estimate token count. Standard approximation: 1 token ≈ 0.75 words (or ~4 chars)."""
    # Use word-based estimation: ~1.33 tokens per word is a standard heuristic
    words = len(text.split())
    return int(words * 1.33)


def parse_transcript_file(file_path: str) -> Dict[str, Any]:
    """Extract YAML frontmatter and transcript dialogue from markdown file."""
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    metadata = {}
    body = content

    if content.startswith("---"):
        parts = content.split("---", 2)
        if len(parts) >= 3:
            try:
                metadata = yaml.safe_load(parts[1]) or {}
                body = parts[2].strip()
            except Exception as e:
                logger.warning(f"Error parsing frontmatter in {file_path}: {e}")

    # Remove ## Transcript header if present
    body = re.sub(r'^##\s*Transcript\s*', '', body, flags=re.IGNORECASE | re.MULTILINE)
    return {"metadata": metadata, "body": body}


def chunk_transcript(
    slug: str,
    metadata: Dict[str, Any],
    body: str,
    target_tokens: int = 650,
    overlap_tokens: int = 100
) -> List[Dict[str, Any]]:
    """
    Chunk transcript dialogue into 500-800 token segments with ~100-token overlap.

    Strategy:
    - Parse speaker/timestamp segments from the transcript
    - Accumulate segments until reaching target_tokens (~650, midpoint of 500-800)
    - Retain overlap_tokens (~100) worth of words from the end of each chunk
    - Preserve speaker attribution and timestamp reference for every chunk

    Token estimation: ~1.33 tokens per word (standard GPT tokenizer approximation).
    This means target_tokens=650 ≈ 488 words, overlap_tokens=100 ≈ 75 words.
    """
    # Convert token targets to word targets using the 1.33 ratio
    target_words = int(target_tokens / 1.33)  # ~488 words for 650 tokens
    overlap_words = int(overlap_tokens / 1.33)  # ~75 words for 100 tokens

    guest_name = metadata.get("guest") or slug.replace("-", " ").title()
    title = metadata.get("title") or f"Lenny's Podcast: {guest_name}"
    youtube_url = metadata.get("youtube_url") or ""
    publish_date = str(metadata.get("publish_date") or "")

    # Split into sections by timestamp/speaker markers
    matches = list(TIMESTAMP_PATTERN.finditer(body))
    segments = []

    if not matches:
        # Fallback to simple paragraph splitting if no timestamp markers found
        paragraphs = [p.strip() for p in body.split("\n\n") if p.strip()]
        for p in paragraphs:
            segments.append(("Lenny & Guest", "00:00:00", p))
    else:
        for i, match in enumerate(matches):
            speaker = match.group(1).strip()
            timestamp = match.group(2).strip()
            # Normalize timestamp to HH:MM:SS
            if timestamp.count(":") == 1:
                timestamp = "0:" + timestamp
            start_pos = match.end()
            end_pos = matches[i + 1].start() if i + 1 < len(matches) else len(body)
            speech = body[start_pos:end_pos].strip()
            if speech:
                segments.append((speaker, timestamp, speech))

    chunks = []
    current_words = []
    current_timestamp = "00:00:00"
    chunk_index = 0

    for speaker, timestamp, speech in segments:
        words = speech.split()
        if not current_words:
            current_timestamp = timestamp

        current_words.extend([f"{speaker}: "] + words)

        while len(current_words) >= target_words:
            chunk_slice = current_words[:target_words]
            chunk_text = " ".join(chunk_slice)
            token_count = estimate_tokens(chunk_text)
            chunks.append({
                "id": str(uuid.uuid4()),
                "episode_slug": slug,
                "episode_title": title,
                "guest_name": guest_name,
                "youtube_url": youtube_url,
                "publish_date": publish_date,
                "timestamp_ref": current_timestamp,
                "chunk_index": chunk_index,
                "chunk_text": chunk_text,
                "token_count": token_count
            })
            chunk_index += 1
            # Advance sliding window by (target_words - overlap_words)
            step = max(1, target_words - overlap_words)
            current_words = current_words[step:]

    # Handle remaining words (minimum 30 words to avoid tiny fragments)
    if current_words and len(current_words) > 30:
        chunk_text = " ".join(current_words)
        token_count = estimate_tokens(chunk_text)
        chunks.append({
            "id": str(uuid.uuid4()),
            "episode_slug": slug,
            "episode_title": title,
            "guest_name": guest_name,
            "youtube_url": youtube_url,
            "publish_date": publish_date,
            "timestamp_ref": current_timestamp,
            "chunk_index": chunk_index,
            "chunk_text": chunk_text,
            "token_count": token_count
        })

    return chunks


async def ingest_all():
    os.makedirs(os.path.dirname(CACHE_FILE), exist_ok=True)
    if not os.path.exists(TRANSCRIPTS_DIR):
        logger.error(f"Transcripts directory {TRANSCRIPTS_DIR} does not exist. Run download_transcripts.py first.")
        return

    files = [f for f in os.listdir(TRANSCRIPTS_DIR) if f.endswith(".md")]
    if not files:
        logger.warning(f"No markdown files found in {TRANSCRIPTS_DIR}.")
        return

    all_chunks = []
    for f in files:
        slug = f[:-3]
        file_path = os.path.join(TRANSCRIPTS_DIR, f)
        parsed = parse_transcript_file(file_path)
        chunks = chunk_transcript(slug, parsed["metadata"], parsed["body"])
        logger.info(f"Generated {len(chunks)} chunks for episode '{slug}' "
                     f"(avg ~{sum(c['token_count'] for c in chunks) // max(len(chunks), 1)} tokens/chunk)")
        all_chunks.extend(chunks)

    logger.info(f"Total chunks across {len(files)} episodes: {len(all_chunks)}. Computing vector embeddings...")

    # Compute dense embeddings in batches
    texts_to_embed = [c["chunk_text"] for c in all_chunks]
    embeddings = compute_batch_embeddings(texts_to_embed)

    for c, emb in zip(all_chunks, embeddings):
        c["embedding"] = emb

    # Save to local JSON cache for instant offline fallback
    with open(CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(all_chunks, f)
    logger.info(f"Saved {len(all_chunks)} chunks with embeddings to {CACHE_FILE}")

    # Compute corpus statistics
    total_tokens = sum(c["token_count"] for c in all_chunks)
    avg_tokens = total_tokens // max(len(all_chunks), 1)
    logger.info(f"Corpus stats: {len(files)} episodes, {len(all_chunks)} chunks, "
                f"~{total_tokens:,} total tokens, ~{avg_tokens} avg tokens/chunk")

    # Attempt PostgreSQL ingestion if database is available
    logger.info("Attempting PostgreSQL pgvector ingestion...")
    if engine is not None:
        try:
            await init_db()
            async with AsyncSession(engine) as session:
                # Clear existing chunks
                await session.execute(text("DELETE FROM transcript_chunks;"))

                # Insert in batches for better performance
                batch_size = 100
                for batch_start in range(0, len(all_chunks), batch_size):
                    batch = all_chunks[batch_start:batch_start + batch_size]
                    for c in batch:
                        db_chunk = TranscriptChunkModel(
                            id=c["id"],
                            episode_slug=c["episode_slug"],
                            episode_title=c["episode_title"],
                            guest_name=c["guest_name"],
                            youtube_url=c["youtube_url"],
                            publish_date=c["publish_date"],
                            timestamp_ref=c["timestamp_ref"],
                            chunk_index=c["chunk_index"],
                            chunk_text=c["chunk_text"],
                            token_count=c["token_count"],
                            embedding=c["embedding"]
                        )
                        session.add(db_chunk)
                    await session.commit()
                    logger.info(f"  Inserted batch {batch_start // batch_size + 1} "
                                f"({batch_start + len(batch)}/{len(all_chunks)} chunks)")

                logger.info("Successfully loaded all chunks into PostgreSQL transcript_chunks table!")

                # Create HNSW Index
                try:
                    await session.execute(text("""
                        CREATE INDEX IF NOT EXISTS idx_transcript_chunks_hnsw 
                        ON transcript_chunks 
                        USING hnsw (embedding vector_cosine_ops)
                        WITH (m = 16, ef_construction = 64);
                    """))
                    await session.commit()
                    logger.info("HNSW index created/verified on transcript_chunks.embedding.")
                except Exception as idx_err:
                    logger.warning(f"Could not create HNSW index: {idx_err}")

                # Verify ingestion
                result = await session.execute(text("SELECT COUNT(*) FROM transcript_chunks;"))
                count = result.scalar()
                logger.info(f"Verification: {count} chunks in PostgreSQL transcript_chunks table.")

        except Exception as db_err:
            logger.warning(f"PostgreSQL ingestion skipped or DB offline ({db_err}). Offline cache is fully ready.")
    else:
        logger.info("Database engine not active; offline cache is ready.")


if __name__ == "__main__":
    asyncio.run(ingest_all())
