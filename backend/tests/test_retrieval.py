import pytest
import numpy as np
from app.rag.retriever import TranscriptRetriever
from app.rag.embeddings import compute_embedding
from app.config import get_settings

settings = get_settings()

@pytest.mark.asyncio
async def test_compute_embedding_shape_and_norm():
    """Verify that embedding vector is 384-dimensional and normalized."""
    text = "Onboarding is the only part of your product experience that 100% of people touch."
    embedding = compute_embedding(text)
    assert len(embedding) == 384
    arr = np.array(embedding, dtype=np.float32)
    norm = np.linalg.norm(arr)
    assert np.isclose(norm, 1.0, atol=1e-2)

@pytest.mark.asyncio
async def test_retriever_local_cache_scoring():
    """Test in-memory fallback similarity search and ranking."""
    retriever = TranscriptRetriever(session=None)

    # Inject mock chunks into retriever's internal cache
    target_query = "Onboarding and customer activation strategies at Lyft and Patreon."
    sample_emb1 = compute_embedding(target_query)
    sample_emb2 = compute_embedding("Enterprise sales cycles, contract negotiation, and procurement.")

    retriever._local_cache = [
        {
            "id": "1",
            "episode_slug": "adam-fishman",
            "episode_title": "How to build a high-performing growth team",
            "guest_name": "Adam Fishman",
            "youtube_url": "https://youtube.com/watch?v=123",
            "timestamp_ref": "00:05:30",
            "chunk_text": "Onboarding is the only part of your product experience that a hundred percent of people are ever going to touch.",
            "embedding": sample_emb1
        },
        {
            "id": "2",
            "episode_slug": "sales-special",
            "episode_title": "Enterprise B2B Sales",
            "guest_name": "Sales Leader",
            "youtube_url": "https://youtube.com/watch?v=456",
            "timestamp_ref": "00:10:00",
            "chunk_text": "Enterprise procurement involves lengthy security reviews and legal redlines.",
            "embedding": sample_emb2
        }
    ]

    # Query closely matching chunk 1
    results = await retriever.retrieve_relevant_chunks(target_query, top_k=2, similarity_threshold=0.20)

    assert len(results) > 0
    top = results[0]
    assert top["guest"] == "Adam Fishman"
    assert "Onboarding" in top["text"]
    assert top["score"] > 0.20
    assert "timestamp" in top

@pytest.mark.asyncio
async def test_retriever_out_of_domain_threshold():
    """Verify that irrelevant queries return no results when threshold is not met."""
    retriever = TranscriptRetriever(session=None)
    retriever._local_cache = [
        {
            "id": "1",
            "episode_title": "Growth Podcasting",
            "guest_name": "Growth Guest",
            "timestamp_ref": "00:00:00",
            "chunk_text": "Retention curves flatten when product market fit is achieved.",
            "embedding": compute_embedding("Retention curves flatten when product market fit is achieved.")
        }
    ]

    # Out of domain query with high threshold
    results = await retriever.retrieve_relevant_chunks("Recipe for chocolate chip cookies", top_k=1, similarity_threshold=0.95)
    assert len(results) == 0


@pytest.mark.asyncio
async def test_retriever_empty_cache():
    """Verify retriever returns empty list when cache is empty."""
    retriever = TranscriptRetriever(session=None)
    retriever._local_cache = []
    results = await retriever.retrieve_relevant_chunks("onboarding activation", top_k=5)
    assert results == []


@pytest.mark.asyncio
async def test_retriever_multiple_sources():
    """Verify retriever returns chunks from multiple episodes."""
    retriever = TranscriptRetriever(session=None)

    retriever._local_cache = [
        {
            "id": "1",
            "episode_title": "Growth at Lyft",
            "guest_name": "Adam Fishman",
            "timestamp_ref": "00:05:00",
            "chunk_text": "Onboarding is a hundred percent growth lever for activation and retention.",
            "embedding": compute_embedding("Onboarding is a hundred percent growth lever for activation and retention.")
        },
        {
            "id": "2",
            "episode_title": "PLG at Scale",
            "guest_name": "Elena Verna",
            "timestamp_ref": "00:10:00",
            "chunk_text": "Product led growth requires strong onboarding flows to drive activation.",
            "embedding": compute_embedding("Product led growth requires strong onboarding flows to drive activation.")
        },
        {
            "id": "3",
            "episode_title": "Unrelated Topic",
            "guest_name": "Random Guest",
            "timestamp_ref": "00:00:00",
            "chunk_text": "The history of ancient Roman architecture is fascinating.",
            "embedding": compute_embedding("The history of ancient Roman architecture is fascinating.")
        }
    ]

    results = await retriever.retrieve_relevant_chunks(
        "How does onboarding improve growth and activation?",
        top_k=3,
        similarity_threshold=0.20
    )

    assert len(results) >= 2
    guests = [r["guest"] for r in results]
    # Both growth-related chunks should score higher
    assert "Adam Fishman" in guests or "Elena Verna" in guests


@pytest.mark.asyncio
async def test_retriever_citation_format():
    """Verify that retriever results contain all required citation fields."""
    retriever = TranscriptRetriever(session=None)

    retriever._local_cache = [
        {
            "id": "1",
            "episode_title": "Growth Strategies",
            "guest_name": "Test Guest",
            "youtube_url": "https://youtube.com/watch?v=test123",
            "timestamp_ref": "00:12:30",
            "chunk_text": "Important growth insight about onboarding and activation.",
            "embedding": compute_embedding("Important growth insight about onboarding and activation.")
        }
    ]

    results = await retriever.retrieve_relevant_chunks(
        "growth onboarding activation",
        top_k=1,
        similarity_threshold=0.10
    )

    assert len(results) > 0
    result = results[0]
    # Verify all citation fields
    assert "episode" in result
    assert "guest" in result
    assert "timestamp" in result
    assert "text" in result
    assert "score" in result
    assert "youtube_url" in result
    assert isinstance(result["score"], float)
    assert result["guest"] == "Test Guest"
    assert result["timestamp"] == "00:12:30"


@pytest.mark.asyncio
async def test_retriever_low_similarity_threshold():
    """Verify that the similarity threshold correctly filters results."""
    retriever = TranscriptRetriever(session=None)

    retriever._local_cache = [
        {
            "id": "1",
            "episode_title": "Retention Deep Dive",
            "guest_name": "Retention Expert",
            "timestamp_ref": "00:00:00",
            "chunk_text": "User retention is about habit formation and value delivery.",
            "embedding": compute_embedding("User retention is about habit formation and value delivery.")
        }
    ]

    # Very high threshold should filter out marginal matches
    results_high = await retriever.retrieve_relevant_chunks(
        "What is the recipe for pizza?",
        top_k=5,
        similarity_threshold=0.90
    )
    assert len(results_high) == 0

    # Very low threshold should include more matches
    results_low = await retriever.retrieve_relevant_chunks(
        "retention and habit formation",
        top_k=5,
        similarity_threshold=0.10
    )
    assert len(results_low) > 0


@pytest.mark.asyncio
async def test_embedding_dimension_matches_config():
    """Verify that embedding dimension matches the configured value."""
    embedding = compute_embedding("test text")
    assert len(embedding) == settings.EMBEDDING_DIMENSION
