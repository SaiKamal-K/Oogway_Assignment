import json
import uuid
import logging
from typing import Optional
from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from datetime import datetime, timezone

from app.database import get_db
from app.config import get_settings
from app.models.schemas import ChatRequest
from app.models.db_models import SessionModel, MessageModel, ArtifactModel
from app.rag.retriever import TranscriptRetriever
from app.providers.cloud_provider import get_llm_provider
from app.skills.ship30_writer import SHIP_30_SYSTEM_PROMPT, build_ship30_prompt
from app.skills.artifact_generator import extract_artifacts
from app.api.sessions import IN_MEMORY_SESSIONS

logger = logging.getLogger(__name__)
settings = get_settings()
router = APIRouter(prefix="/api/chat", tags=["Chat"])

GROUNDED_QA_SYSTEM_PROMPT = """You are The Lenny Growth Assistant—an elite AI partner for Product Managers and Growth Leaders.
Your knowledge base consists of transcripts from Lenny's Podcast.

### Grounding Rules:
1. STRICT GROUNDING: Ground every factual assertion strictly in the provided podcast transcript excerpts.
2. CITATIONS: Include concise citation brackets referencing the speaker and timestamp, e.g., `[Adam Fishman, 00:00:00]`.
3. UNCERTAINTY / OUT-OF-DOMAIN: If the provided transcript context does not contain sufficient information to answer the question, state:
   "I do not have sufficient information in Lenny's podcast archive to answer this question. Please ask a product, growth, or leadership question covered in the podcast."
   Do NOT hallucinate or speculate from general training data.
4. TACTICAL & ACTIONABLE: Deliver concise, high-density answers highlighting concrete metrics, benchmarks, and operational tactics.
"""

@router.post("")
async def stream_chat(
    req: ChatRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Stream grounded RAG responses or Ship 30 for 30 essays using Server-Sent Events (SSE).
    """
    user_msg_id = str(uuid.uuid4())
    assistant_msg_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc)

    # 1. Save user message to database or in-memory
    from app.database import DB_ONLINE
    if DB_ONLINE and db is not None:
        try:
            user_msg = MessageModel(
                id=user_msg_id,
                session_id=req.session_id,
                role="user",
                content=req.message,
                mode=req.mode or "default",
                provider=req.provider or "ollama"
            )
            db.add(user_msg)
            await db.commit()
        except Exception as e:
            logger.warning(f"Could not persist user message to DB ({e}). Updating in-memory.")
    else:
        if req.session_id in IN_MEMORY_SESSIONS:
            IN_MEMORY_SESSIONS[req.session_id]["messages"].append({
                "id": user_msg_id,
                "session_id": req.session_id,
                "role": "user",
                "content": req.message,
                "sources": [],
                "mode": req.mode or "default",
                "provider": req.provider or "ollama",
                "created_at": now,
                "artifacts": []
            })

    async def event_generator():
        # Step A: Status notification
        status_payload = json.dumps({"type": "status", "content": "Searching Lenny's Podcast archive..."})
        yield f"data: {status_payload}\n\n"

        # Step B: Retrieval
        retriever = TranscriptRetriever(session=db)
        retrieved_chunks = await retriever.retrieve_relevant_chunks(
            query=req.message,
            top_k=settings.TOP_K_RETRIEVAL,
            similarity_threshold=settings.SIMILARITY_THRESHOLD
        )

        # Step C: Yield citations
        sources_payload = json.dumps({"type": "sources", "sources": retrieved_chunks})
        yield f"data: {sources_payload}\n\n"

        # Step D: Construct Prompts
        is_ship30 = (req.mode == "ship30")
        max_score = max([c["score"] for c in retrieved_chunks]) if retrieved_chunks else 0.0

        if not retrieved_chunks or max_score < settings.SIMILARITY_THRESHOLD:
            # Query is out of domain or lacks grounding
            system_prompt = GROUNDED_QA_SYSTEM_PROMPT
            conversation_messages = [
                {"role": "user", "content": f"Context: [NO RELEVANT PODCAST DATA FOUND]\nQuestion: {req.message}"}
            ]
        elif is_ship30:
            system_prompt = SHIP_30_SYSTEM_PROMPT
            essay_prompt = build_ship30_prompt(req.message, retrieved_chunks)
            conversation_messages = [
                {"role": "user", "content": essay_prompt}
            ]
        else:
            system_prompt = GROUNDED_QA_SYSTEM_PROMPT
            formatted_context = "\n\n".join([
                f"--- Episode: '{c['episode']}' | Guest: {c['guest']} | Timestamp: {c['timestamp']} ---\n{c['text']}"
                for c in retrieved_chunks
            ])
            user_content = f"Podcast Transcript Context:\n{formatted_context}\n\nUser Question:\n{req.message}"
            conversation_messages = [
                {"role": "user", "content": user_content}
            ]

        # Step E: Instantiate Provider
        provider_name = req.provider or settings.DEFAULT_PROVIDER
        llm = get_llm_provider(provider_name)
        yield f"data: {json.dumps({'type': 'status', 'content': f'Generating response with {provider_name}...'})}\n\n"

        # Step F: Stream Tokens & Buffer for Artifact Detection
        accumulated_text = ""
        emitted_artifacts = set()

        async for token in llm.generate_response(conversation_messages, system_prompt, temperature=0.3):
            accumulated_text += token
            yield f"data: {json.dumps({'type': 'token', 'content': token})}\n\n"

            # Check if artifact completed during stream
            artifacts = extract_artifacts(accumulated_text)
            for art in artifacts:
                art_key = f"{art['type']}:{art['title']}"
                if art_key not in emitted_artifacts:
                    emitted_artifacts.add(art_key)
                    yield f"data: {json.dumps({'type': 'artifact', 'artifact': art})}\n\n"

        # Final artifact check in case tags closed at the end
        final_artifacts = extract_artifacts(accumulated_text)
        for art in final_artifacts:
            art_key = f"{art['type']}:{art['title']}"
            if art_key not in emitted_artifacts:
                emitted_artifacts.add(art_key)
                yield f"data: {json.dumps({'type': 'artifact', 'artifact': art})}\n\n"

        # Step G: Persist Assistant Message & Artifacts to DB / Memory
        from app.database import DB_ONLINE
        if DB_ONLINE and db is not None:
            try:
                asst_msg = MessageModel(
                    id=assistant_msg_id,
                    session_id=req.session_id,
                    role="assistant",
                    content=accumulated_text,
                    sources=retrieved_chunks,
                    mode=req.mode or "default",
                    provider=provider_name
                )
                db.add(asst_msg)

                for art in final_artifacts:
                    art_record = ArtifactModel(
                        id=str(uuid.uuid4()),
                        message_id=assistant_msg_id,
                        session_id=req.session_id,
                        artifact_type=art["type"],
                        title=art["title"],
                        content=art["content"]
                    )
                    db.add(art_record)

                # Auto-title session based on first query if title is default
                sess_stmt = select(SessionModel).where(SessionModel.id == req.session_id)
                sess_res = await db.execute(sess_stmt)
                curr_sess = sess_res.scalar_one_or_none()
                if curr_sess and (curr_sess.title == "New Growth Session" or not curr_sess.title):
                    clean_title = req.message[:45].strip()
                    if len(req.message) > 45:
                        clean_title += "..."
                    curr_sess.title = clean_title

                await db.commit()
            except Exception as e:
                logger.warning(f"Could not persist assistant message to DB ({e}). Updating in-memory.")
        else:
            if req.session_id in IN_MEMORY_SESSIONS:
                IN_MEMORY_SESSIONS[req.session_id]["messages"].append({
                    "id": assistant_msg_id,
                    "session_id": req.session_id,
                    "role": "assistant",
                    "content": accumulated_text,
                    "sources": retrieved_chunks,
                    "mode": req.mode or "default",
                    "provider": provider_name,
                    "created_at": datetime.now(timezone.utc),
                    "artifacts": [
                        {
                            "id": str(uuid.uuid4()),
                            "message_id": assistant_msg_id,
                            "session_id": req.session_id,
                            "artifact_type": a["type"],
                            "title": a["title"],
                            "content": a["content"],
                            "created_at": datetime.now(timezone.utc)
                        }
                        for a in final_artifacts
                    ]
                })

        yield f"data: {json.dumps({'type': 'done', 'session_id': req.session_id, 'message_id': assistant_msg_id})}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )
