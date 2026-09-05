import logging
from typing import AsyncGenerator, Optional
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from sqlalchemy import text
from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

Base = declarative_base()

engine = None
async_session_factory = None

try:
    engine = create_async_engine(
        settings.DATABASE_URL,
        echo=settings.DB_ECHO,
        future=True,
        pool_pre_ping=True,
        connect_args={"timeout": 2, "command_timeout": 2}
    )
    async_session_factory = async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autocommit=False,
        autoflush=False
    )
except Exception as e:
    logger.warning(f"Async database engine could not be created ({e}). Local in-memory fallback will be used.")

async def get_db() -> AsyncGenerator[Optional[AsyncSession], None]:
    global DB_ONLINE
    if not DB_ONLINE or async_session_factory is None:
        yield None
        return

    async with async_session_factory() as session:
        yield session

DB_ONLINE = False

async def init_db() -> bool:
    """Initialize database extensions and schema tables if reachable."""
    global DB_ONLINE
    if engine is None:
        logger.info("Database engine not configured; running in standalone cached mode.")
        DB_ONLINE = False
        return False

    try:
        async with engine.begin() as conn:
            # Enable vector extension for pgvector
            try:
                await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))
                logger.info("pgvector extension verified or created.")
            except Exception as e:
                logger.warning(f"Could not initialize vector extension: {e}")

            # Create tables
            await conn.run_sync(Base.metadata.create_all)
            logger.info("Database tables verified or created successfully.")
        DB_ONLINE = True
        return True
    except Exception as e:
        logger.warning(f"Database initialization failed ({e}). Resilient local cache is active.")
        DB_ONLINE = False
        return False
