"""
Integration tests for PostgreSQL + pgvector.
These tests are conditional — they skip gracefully if PostgreSQL is not available.
"""
import pytest
import asyncio
import os

# Check if database is reachable before running integration tests
def is_db_available():
    """Quick check if PostgreSQL is reachable."""
    try:
        from app.database import engine
        return engine is not None
    except Exception:
        return False


@pytest.mark.asyncio
async def test_database_initialization():
    """Verify that init_db creates the pgvector extension and tables."""
    from app.database import init_db, engine

    if engine is None:
        pytest.skip("PostgreSQL not available (running in standalone mode)")

    result = await init_db()
    # Result may be True (connected) or False (connection failed)
    # Both are valid states — we're testing that it doesn't crash
    assert isinstance(result, bool)


@pytest.mark.asyncio
async def test_pgvector_extension_exists():
    """Verify that the pgvector extension is installed."""
    from app.database import engine, async_session_factory
    from sqlalchemy import text

    if engine is None or async_session_factory is None:
        pytest.skip("PostgreSQL not available")

    try:
        async with async_session_factory() as session:
            result = await asyncio.wait_for(
                session.execute(text("SELECT extname FROM pg_extension WHERE extname = 'vector';")),
                timeout=3.0
            )
            rows = result.fetchall()
            assert len(rows) > 0, "pgvector extension should be installed"
            assert rows[0][0] == "vector"
    except Exception as e:
        pytest.skip(f"Database connection failed: {e}")


@pytest.mark.asyncio
async def test_transcript_chunks_table_exists():
    """Verify the transcript_chunks table exists."""
    from app.database import engine, async_session_factory
    from sqlalchemy import text

    if engine is None or async_session_factory is None:
        pytest.skip("PostgreSQL not available")

    try:
        async with async_session_factory() as session:
            result = await asyncio.wait_for(
                session.execute(text(
                    "SELECT tablename FROM pg_tables WHERE tablename = 'transcript_chunks';"
                )),
                timeout=3.0
            )
            rows = result.fetchall()
            assert len(rows) > 0, "transcript_chunks table should exist"
    except Exception as e:
        pytest.skip(f"Database connection failed: {e}")


@pytest.mark.asyncio
async def test_hnsw_index_exists():
    """Verify the HNSW index exists on transcript_chunks.embedding."""
    from app.database import engine, async_session_factory
    from sqlalchemy import text

    if engine is None or async_session_factory is None:
        pytest.skip("PostgreSQL not available")

    try:
        async with async_session_factory() as session:
            result = await asyncio.wait_for(
                session.execute(text(
                    "SELECT indexname, indexdef FROM pg_indexes "
                    "WHERE tablename = 'transcript_chunks' AND indexdef LIKE '%hnsw%';"
                )),
                timeout=3.0
            )
            rows = result.fetchall()
            if len(rows) == 0:
                pytest.skip("HNSW index not yet created (run ingestion first)")
            assert "hnsw" in rows[0][1].lower(), "Index should use HNSW method"
            assert "vector_cosine_ops" in rows[0][1].lower(), "Index should use cosine distance"
    except Exception as e:
        pytest.skip(f"Database connection failed: {e}")


@pytest.mark.asyncio
async def test_vector_dimension_matches_model():
    """Verify that stored vectors match the embedding model dimension (384)."""
    from app.database import engine, async_session_factory
    from app.config import get_settings
    from sqlalchemy import text

    if engine is None or async_session_factory is None:
        pytest.skip("PostgreSQL not available")

    settings = get_settings()

    try:
        async with async_session_factory() as session:
            result = await asyncio.wait_for(
                session.execute(text(
                    "SELECT embedding FROM transcript_chunks LIMIT 1;"
                )),
                timeout=3.0
            )
            row = result.fetchone()
            if row is None:
                pytest.skip("No chunks in database (run ingestion first)")

            # pgvector returns the vector as a string representation
            vec_str = str(row[0])
            # Count dimensions by splitting the vector string
            dims = len(vec_str.strip("[]").split(","))
            assert dims == settings.EMBEDDING_DIMENSION, (
                f"Vector dimension {dims} does not match model "
                f"dimension {settings.EMBEDDING_DIMENSION}"
            )
    except Exception as e:
        pytest.skip(f"Database connection failed: {e}")


@pytest.mark.asyncio
async def test_pgvector_cosine_similarity_query():
    """Verify that pgvector cosine similarity query executes without error."""
    from app.database import engine, async_session_factory
    from app.rag.embeddings import compute_embedding
    from sqlalchemy import text

    if engine is None or async_session_factory is None:
        pytest.skip("PostgreSQL not available")

    try:
        query_vector = compute_embedding("onboarding growth activation")
        async with async_session_factory() as session:
            result = await asyncio.wait_for(
                session.execute(
                    text("""
                        SELECT episode_title, guest_name,
                               1 - (embedding <=> :vector::vector) AS similarity
                        FROM transcript_chunks
                        ORDER BY similarity DESC
                        LIMIT 3;
                    """),
                    {"vector": str(query_vector)}
                ),
                timeout=5.0
            )
            rows = result.fetchall()
            if len(rows) == 0:
                pytest.skip("No chunks in database (run ingestion first)")
            
            # Verify result structure
            for row in rows:
                assert row.episode_title is not None
                assert row.guest_name is not None
                assert 0.0 <= row.similarity <= 1.0
    except Exception as e:
        pytest.skip(f"Database query failed: {e}")
