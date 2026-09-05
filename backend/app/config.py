import os
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache

class Settings(BaseSettings):
    APP_NAME: str = "The Lenny Growth Assistant"
    APP_ENV: str = "development"
    DEBUG: bool = True
    
    # Database configuration
    DATABASE_URL: str = "postgresql+asyncpg://postgres:password123@localhost:5432/lenny_assistant"
    DB_ECHO: bool = False
    
    # Local LLM (Ollama)
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "llama3.1:8b"
    
    # Cloud LLMs
    ANTHROPIC_API_KEY: Optional[str] = None
    CLAUDE_MODEL: str = "claude-3-5-sonnet-20241022"
    OPENAI_API_KEY: Optional[str] = None
    OPENAI_MODEL: str = "gpt-4o"
    
    # Retrieval Configuration
    DEFAULT_PROVIDER: str = "ollama"  # 'ollama', 'claude', or 'openai'
    SIMILARITY_THRESHOLD: float = 0.45
    TOP_K_RETRIEVAL: int = 5
    EMBEDDING_MODEL_NAME: str = "all-MiniLM-L6-v2"
    EMBEDDING_DIMENSION: int = 384
    
    # CORS
    CORS_ORIGINS: list[str] = ["http://localhost:3000", "http://127.0.0.1:3000"]
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

@lru_cache()
def get_settings() -> Settings:
    return Settings()
