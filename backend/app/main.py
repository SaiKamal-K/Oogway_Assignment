import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import get_settings
from app.database import init_db
from app.api.health import router as health_router
from app.api.sessions import router as sessions_router
from app.api.chat import router as chat_router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("lenny-growth-assistant")
settings = get_settings()

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Initializing The Lenny Growth Assistant backend...")
    # Initialize DB & pgvector extension asynchronously
    db_initialized = await init_db()
    if db_initialized:
        logger.info("Database & pgvector ready.")
    else:
        logger.warning("Database offline or initializing; local cache fallback active.")
    yield
    logger.info("Shutting down The Lenny Growth Assistant backend.")

app = FastAPI(
    title=settings.APP_NAME,
    description="Enterprise-grade RAG and Ship 30 for 30 Content Engine grounded in Lenny's Podcast transcripts.",
    version="1.0.0",
    lifespan=lifespan
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Permits local dev and containerized communication
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global exception handler for resilience
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Global unhandled exception on {request.url}: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal Server Error", "error": str(exc)}
    )

# Include API Routers
app.include_router(health_router)
app.include_router(sessions_router)
app.include_router(chat_router)

@app.get("/")
async def root():
    return {
        "app": settings.APP_NAME,
        "status": "online",
        "docs_url": "/docs",
        "health_url": "/api/health"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
