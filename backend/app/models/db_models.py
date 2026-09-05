import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Text, Integer, DateTime, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import UUID as PG_UUID, JSONB
from sqlalchemy.orm import relationship
from pgvector.sqlalchemy import Vector
from app.database import Base

def utcnow():
    return datetime.now(timezone.utc)

class SessionModel(Base):
    __tablename__ = "sessions"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    title = Column(String(255), nullable=False, default="New Growth Session")
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)

    messages = relationship("MessageModel", back_populates="session", cascade="all, delete-orphan", order_by="MessageModel.created_at")
    artifacts = relationship("ArtifactModel", back_populates="session", cascade="all, delete-orphan")

class MessageModel(Base):
    __tablename__ = "messages"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id = Column(String(36), ForeignKey("sessions.id", ondelete="CASCADE"), nullable=False)
    role = Column(String(50), nullable=False)  # 'user', 'assistant', 'system'
    content = Column(Text, nullable=False)
    sources = Column(JSON, default=list)  # list of retrieved chunks
    mode = Column(String(50), default="default")  # 'default' or 'ship30'
    provider = Column(String(50), default="ollama")  # 'ollama', 'claude', 'openai'
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)

    session = relationship("SessionModel", back_populates="messages")
    artifacts = relationship("ArtifactModel", back_populates="message", cascade="all, delete-orphan")

class ArtifactModel(Base):
    __tablename__ = "artifacts"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    message_id = Column(String(36), ForeignKey("messages.id", ondelete="CASCADE"), nullable=False)
    session_id = Column(String(36), ForeignKey("sessions.id", ondelete="CASCADE"), nullable=False)
    artifact_type = Column(String(50), nullable=False)  # 'markdown' or 'html'
    title = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)

    session = relationship("SessionModel", back_populates="artifacts")
    message = relationship("MessageModel", back_populates="artifacts")

class TranscriptChunkModel(Base):
    __tablename__ = "transcript_chunks"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    episode_slug = Column(String(120), nullable=False, index=True)
    episode_title = Column(String(255), nullable=False)
    guest_name = Column(String(120), nullable=False, index=True)
    youtube_url = Column(String(255), nullable=True)
    publish_date = Column(String(50), nullable=True)
    timestamp_ref = Column(String(50), nullable=False, default="00:00:00")
    chunk_index = Column(Integer, nullable=False)
    chunk_text = Column(Text, nullable=False)
    token_count = Column(Integer, nullable=False, default=0)
    embedding = Column(Vector(384), nullable=False)
