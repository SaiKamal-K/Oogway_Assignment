import logging
import uuid
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete, desc
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models.db_models import SessionModel, MessageModel, ArtifactModel
from app.models.schemas import SessionCreate, SessionResponse, SessionDetailResponse, MessageSchema, ArtifactSchema

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/sessions", tags=["Sessions"])

# In-memory fallback sessions store if DB is offline
IN_MEMORY_SESSIONS: dict[str, dict] = {}

@router.post("", response_model=SessionResponse, status_code=status.HTTP_201_CREATED)
async def create_session(
    payload: SessionCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create a new chat session."""
    session_id = str(uuid.uuid4())
    title = payload.title or "New Growth Session"

    from app.database import DB_ONLINE
    if DB_ONLINE and db is not None:
        try:
            new_session = SessionModel(id=session_id, title=title)
            db.add(new_session)
            await db.commit()
            await db.refresh(new_session)
            return SessionResponse(
                id=new_session.id,
                title=new_session.title,
                created_at=new_session.created_at,
                updated_at=new_session.updated_at,
                message_count=0
            )
        except Exception as e:
            logger.warning(f"Database session creation failed ({e}). Storing in-memory.")

    from datetime import datetime, timezone
    now = datetime.now(timezone.utc)
    IN_MEMORY_SESSIONS[session_id] = {
        "id": session_id,
        "title": title,
        "created_at": now,
        "updated_at": now,
        "messages": []
    }
    return SessionResponse(
        id=session_id,
        title=title,
        created_at=now,
        updated_at=now,
        message_count=0
    )

@router.get("", response_model=List[SessionResponse])
async def list_sessions(db: AsyncSession = Depends(get_db)):
    """List all chat sessions."""
    from app.database import DB_ONLINE
    if DB_ONLINE and db is not None:
        try:
            stmt = select(SessionModel).options(selectinload(SessionModel.messages)).order_by(desc(SessionModel.updated_at))
            result = await db.execute(stmt)
            sessions = result.scalars().all()
            return [
                SessionResponse(
                    id=s.id,
                    title=s.title,
                    created_at=s.created_at,
                    updated_at=s.updated_at,
                    message_count=len(s.messages)
                )
                for s in sessions
            ]
        except Exception as e:
            logger.warning(f"DB list sessions failed ({e}). Returning in-memory sessions.")

    return [
        SessionResponse(
            id=s["id"],
            title=s["title"],
            created_at=s["created_at"],
            updated_at=s["updated_at"],
            message_count=len(s.get("messages", []))
        )
        for s in IN_MEMORY_SESSIONS.values()
    ]

@router.get("/{session_id}", response_model=SessionDetailResponse)
async def get_session(session_id: str, db: AsyncSession = Depends(get_db)):
    """Retrieve complete message history and artifacts for a session."""
    from app.database import DB_ONLINE
    if DB_ONLINE and db is not None:
        try:
            stmt = (
                select(SessionModel)
                .where(SessionModel.id == session_id)
                .options(
                    selectinload(SessionModel.messages).selectinload(MessageModel.artifacts)
                )
            )
            result = await db.execute(stmt)
            sess = result.scalar_one_or_none()
            if sess:
                formatted_messages = []
                for m in sess.messages:
                    formatted_messages.append(
                        MessageSchema(
                            id=m.id,
                            session_id=m.session_id,
                            role=m.role,
                            content=m.content,
                            sources=m.sources or [],
                            mode=m.mode or "default",
                            provider=m.provider or "ollama",
                            created_at=m.created_at,
                            artifacts=[
                                ArtifactSchema(
                                    id=a.id,
                                    message_id=a.message_id,
                                    session_id=a.session_id,
                                    artifact_type=a.artifact_type,
                                    title=a.title,
                                    content=a.content,
                                    created_at=a.created_at
                                )
                                for a in m.artifacts
                            ]
                        )
                    )
                return SessionDetailResponse(
                    id=sess.id,
                    title=sess.title,
                    created_at=sess.created_at,
                    updated_at=sess.updated_at,
                    messages=formatted_messages
                )
        except Exception as e:
            logger.warning(f"DB get session failed ({e}). Checking in-memory.")

    if session_id in IN_MEMORY_SESSIONS:
        s = IN_MEMORY_SESSIONS[session_id]
        return SessionDetailResponse(
            id=s["id"],
            title=s["title"],
            created_at=s["created_at"],
            updated_at=s["updated_at"],
            messages=s.get("messages", [])
        )
    raise HTTPException(status_code=404, detail="Session not found")

@router.delete("/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_session(session_id: str, db: AsyncSession = Depends(get_db)):
    """Delete a chat session."""
    from app.database import DB_ONLINE
    if DB_ONLINE and db is not None:
        try:
            stmt = delete(SessionModel).where(SessionModel.id == session_id)
            await db.execute(stmt)
            await db.commit()
        except Exception as e:
            logger.warning(f"DB delete session failed: {e}")

    if session_id in IN_MEMORY_SESSIONS:
        del IN_MEMORY_SESSIONS[session_id]
    return None
