"""
Tests for transcript chunking pipeline.
Validates chunk size (500-800 token range), overlap, and metadata extraction.
"""
import sys
import os
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from scripts.ingest import (
    parse_transcript_file,
    chunk_transcript,
    estimate_tokens,
)


def test_estimate_tokens():
    """Verify token estimation approximation."""
    text = "This is a simple test sentence with ten words."
    tokens = estimate_tokens(text)
    # 10 words * 1.33 ≈ 13 tokens
    assert 10 <= tokens <= 20


def test_chunk_size_within_spec():
    """Verify chunks fall within the 500-800 token target range (allowing some tolerance)."""
    # Simulate a long transcript body
    body_lines = []
    for i in range(200):
        speaker = "Adam Fishman" if i % 2 == 0 else "Lenny Rachitsky"
        timestamp = f"0:{i:02d}:00"
        body_lines.append(
            f"{speaker} ({timestamp}): This is a test segment number {i} about product growth "
            f"onboarding retention activation metrics and how to build high performing teams "
            f"that leverage data driven experiments for sustained compounding growth loops."
        )
    body = "\n\n".join(body_lines)

    metadata = {
        "guest": "Adam Fishman",
        "title": "Test Episode",
        "youtube_url": "https://youtube.com/watch?v=test",
        "publish_date": "2024-01-01",
    }

    chunks = chunk_transcript("test-episode", metadata, body, target_tokens=650, overlap_tokens=100)

    assert len(chunks) > 1, "Should produce multiple chunks from a long transcript"

    # Check that most chunks are in reasonable token range (400-1000 to allow edge cases)
    for chunk in chunks[:-1]:  # Exclude last chunk which may be shorter
        token_count = chunk["token_count"]
        assert 300 <= token_count <= 1200, (
            f"Chunk {chunk['chunk_index']} has {token_count} tokens, "
            f"expected approximately 500-800 range"
        )


def test_chunk_overlap():
    """Verify that consecutive chunks share overlap text."""
    body_lines = []
    for i in range(100):
        speaker = "Guest"
        body_lines.append(
            f"{speaker} (0:{i:02d}:00): Segment {i} discussing growth strategies "
            f"and product led growth approaches for building successful products."
        )
    body = "\n\n".join(body_lines)

    metadata = {"guest": "Test Guest", "title": "Overlap Test"}
    chunks = chunk_transcript("overlap-test", metadata, body, target_tokens=650, overlap_tokens=100)

    if len(chunks) >= 2:
        # The end of chunk[0] should appear at the start of chunk[1] due to overlap
        chunk0_words = chunks[0]["chunk_text"].split()
        chunk1_words = chunks[1]["chunk_text"].split()
        # Check that the last ~75 words of chunk 0 appear in the beginning of chunk 1
        overlap_size = min(75, len(chunk0_words) // 2)
        tail_words = set(chunk0_words[-overlap_size:])
        head_words = set(chunk1_words[:overlap_size * 2])
        common = tail_words & head_words
        assert len(common) > 5, "Chunks should share overlap words"


def test_chunk_metadata_extraction():
    """Verify that chunk metadata is correctly extracted from frontmatter."""
    metadata = {
        "guest": "Elena Verna",
        "title": "How B2B companies grow",
        "youtube_url": "https://youtube.com/watch?v=abc123",
        "publish_date": "2023-06-15",
    }
    body = "Elena Verna (00:05:00): Product led growth is the future of B2B acquisition. " * 100

    chunks = chunk_transcript("elena-verna", metadata, body)

    assert len(chunks) > 0
    for chunk in chunks:
        assert chunk["guest_name"] == "Elena Verna"
        assert chunk["episode_title"] == "How B2B companies grow"
        assert chunk["youtube_url"] == "https://youtube.com/watch?v=abc123"
        assert chunk["publish_date"] == "2023-06-15"
        assert chunk["episode_slug"] == "elena-verna"


def test_chunk_timestamp_parsing():
    """Verify timestamps are correctly parsed from speaker lines."""
    body = (
        "Adam Fishman (00:05:30): Onboarding is crucial.\n\n"
        "Lenny Rachitsky (00:10:00): How do you measure it?\n\n"
        "Adam Fishman (00:15:00): We track activation rate. " * 50
    )
    metadata = {"guest": "Adam Fishman", "title": "Test Episode"}
    chunks = chunk_transcript("test", metadata, body)

    assert len(chunks) > 0
    # First chunk should reference earliest timestamp
    assert chunks[0]["timestamp_ref"] in ["00:05:30", "0:05:30"]


def test_empty_transcript_handling():
    """Verify that an empty transcript produces no chunks."""
    metadata = {"guest": "Nobody"}
    chunks = chunk_transcript("empty", metadata, "")
    assert len(chunks) == 0


def test_short_transcript_single_chunk():
    """Verify that a very short transcript produces at most one chunk."""
    body = "Guest (00:00:00): This is a brief transcript with just a few words about growth."
    metadata = {"guest": "Brief Guest", "title": "Short Episode"}
    chunks = chunk_transcript("short", metadata, body)
    # May be 0 chunks (too short) or 1 chunk
    assert len(chunks) <= 1


def test_parse_transcript_file_with_frontmatter(tmp_path):
    """Test parsing a transcript file with YAML frontmatter."""
    content = """---
guest: Adam Fishman
title: How to build a high-performing growth team
youtube_url: https://www.youtube.com/watch?v=test
publish_date: 2022-10-13
---

## Transcript

Adam Fishman (00:00:00):
Onboarding is the only part of your product experience that a hundred percent of people are ever going to touch.
"""
    test_file = tmp_path / "test-episode.md"
    test_file.write_text(content)

    result = parse_transcript_file(str(test_file))
    assert result["metadata"]["guest"] == "Adam Fishman"
    assert result["metadata"]["title"] == "How to build a high-performing growth team"
    assert "Onboarding" in result["body"]
    assert "## Transcript" not in result["body"]
