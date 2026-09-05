import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app

@pytest.mark.asyncio
async def test_root_endpoint():
    """Verify root endpoint health and info."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "online"
        assert "docs_url" in data

@pytest.mark.asyncio
async def test_health_endpoint():
    """Verify healthcheck probe returns all expected diagnostic fields."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get("/api/health")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "ollama" in data
        assert "database" in data
        assert "total_chunks" in data
        assert "cloud_providers" in data
        assert "vector_index" in data
        assert "retrieval_source" in data
        assert data["status"] in ["healthy", "degraded"]

@pytest.mark.asyncio
async def test_session_lifecycle():
    """Verify session creation, retrieval, listing, and deletion."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # Create session
        create_resp = await ac.post("/api/sessions", json={"title": "Test Growth Session"})
        assert create_resp.status_code == 201
        session_data = create_resp.json()
        session_id = session_data["id"]
        assert session_data["title"] == "Test Growth Session"

        # Retrieve session
        get_resp = await ac.get(f"/api/sessions/{session_id}")
        assert get_resp.status_code == 200
        detail = get_resp.json()
        assert detail["id"] == session_id
        assert isinstance(detail["messages"], list)

        # List sessions
        list_resp = await ac.get("/api/sessions")
        assert list_resp.status_code == 200
        sessions = list_resp.json()
        assert any(s["id"] == session_id for s in sessions)

        # Delete session
        del_resp = await ac.delete(f"/api/sessions/{session_id}")
        assert del_resp.status_code == 204


@pytest.mark.asyncio
async def test_session_not_found():
    """Verify 404 for non-existent session."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.get("/api/sessions/non-existent-id-12345")
        assert resp.status_code == 404


@pytest.mark.asyncio
async def test_session_default_title():
    """Verify session created without title gets default."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.post("/api/sessions", json={})
        assert resp.status_code == 201
        data = resp.json()
        assert data["title"] == "New Growth Session"
        # Cleanup
        await ac.delete(f"/api/sessions/{data['id']}")


@pytest.mark.asyncio
async def test_chat_endpoint_returns_sse(monkeypatch):
    """Verify chat endpoint returns SSE stream."""
    class MockProvider:
        async def generate_response(self, messages, system_prompt, temperature=0.3):
            yield "Onboarding is the first impression. "
            yield "[Adam Fishman, 00:00:00]"

    async def mock_retrieve(*args, **kwargs):
        return [{"episode": "Test Ep", "guest": "Adam", "text": "sample", "timestamp": "00:00:00", "score": 0.9, "youtube_url": ""}]

    monkeypatch.setattr("app.api.chat.get_llm_provider", lambda _: MockProvider())
    monkeypatch.setattr("app.api.chat.TranscriptRetriever.retrieve_relevant_chunks", mock_retrieve)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test", timeout=10.0) as ac:
        # Create session first
        sess_resp = await ac.post("/api/sessions", json={"title": "Chat Test"})
        session_id = sess_resp.json()["id"]

        # Send chat request via stream
        async with ac.stream("POST", "/api/chat", json={
            "session_id": session_id,
            "message": "What is onboarding?",
            "mode": "default",
            "provider": "ollama"
        }) as chat_resp:
            assert chat_resp.status_code == 200
            assert "text/event-stream" in chat_resp.headers.get("content-type", "")

            lines = []
            async for line in chat_resp.aiter_lines():
                if line.strip():
                    lines.append(line.strip())
                if len(lines) >= 3:
                    break

            assert any("data:" in l for l in lines)

        # Cleanup
        await ac.delete(f"/api/sessions/{session_id}")


@pytest.mark.asyncio
async def test_session_delete_removes_from_list():
    """Verify deleted session no longer appears in list."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # Create
        resp = await ac.post("/api/sessions", json={"title": "Delete Me"})
        session_id = resp.json()["id"]

        # Delete
        await ac.delete(f"/api/sessions/{session_id}")

        # Verify not in list
        list_resp = await ac.get("/api/sessions")
        sessions = list_resp.json()
        assert not any(s["id"] == session_id for s in sessions)
