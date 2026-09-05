from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, ConfigDict

class SourceCitation(BaseModel):
    episode: str
    guest: str
    timestamp: str = "00:00:00"
    youtube_url: Optional[str] = None
    score: float
    text: str

class ArtifactBase(BaseModel):
    artifact_type: str = Field(description="'markdown' or 'html'")
    title: str
    content: str

class ArtifactSchema(ArtifactBase):
    id: str
    message_id: str
    session_id: str
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

class MessageSchema(BaseModel):
    id: str
    session_id: str
    role: str
    content: str
    sources: List[Dict[str, Any]] = []
    mode: str = "default"
    provider: str = "ollama"
    created_at: datetime
    artifacts: List[ArtifactSchema] = []
    model_config = ConfigDict(from_attributes=True)

class SessionCreate(BaseModel):
    title: Optional[str] = "New Growth Session"

class SessionResponse(BaseModel):
    id: str
    title: str
    created_at: datetime
    updated_at: datetime
    message_count: int = 0
    model_config = ConfigDict(from_attributes=True)

class SessionDetailResponse(BaseModel):
    id: str
    title: str
    created_at: datetime
    updated_at: datetime
    messages: List[MessageSchema] = []
    model_config = ConfigDict(from_attributes=True)

class ChatRequest(BaseModel):
    session_id: str
    message: str
    mode: Optional[str] = "default"  # 'default' or 'ship30'
    provider: Optional[str] = "ollama"  # 'ollama', 'claude', or 'openai'

class HealthResponse(BaseModel):
    status: str
    database: bool
    ollama: bool
    ollama_model: str
    total_chunks: int
    cloud_providers: Dict[str, bool]
    vector_index: bool = False
    retrieval_source: str = "none"  # 'pgvector', 'local_cache', or 'none'
