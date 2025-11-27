# app.py
import logging
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from finnews.api.scraper_endpoints import router as scraper_router
from finnews.common.config import settings
from finnews.common.logging import setup_logging
from finnews.rag.rag_chain import rag_chat
from finnews.rag.retriever import load_vectorstore
from finnews.ui.user_profile import get_portfolio_tickers

# Setup logging for API component
setup_logging(component="api", level=logging.INFO, console=True, unified=True)
logger = logging.getLogger(__name__)

# Vector stores loaded at startup
article_store = None
chat_store = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown events."""
    # Startup: Initialize vector stores
    global article_store, chat_store
    logger.info("Initializing vector stores")
    article_store = load_vectorstore(str(settings.CHROMA_DIR))
    chat_store = load_vectorstore(str(settings.CHAT_MEMORY_DIR))
    logger.info("Vector stores initialized")

    # Startup: Initialize automated scraping scheduler
    from finnews.scraper.scheduler import start_scheduler, stop_scheduler

    logger.info("Starting automated scraping scheduler")
    start_scheduler()
    logger.info("Scheduler started")

    yield

    # Shutdown: Stop scheduler and cleanup
    logger.info("Shutting down scheduler")
    stop_scheduler()
    logger.info("Shutdown complete")


app = FastAPI(lifespan=lifespan)

# Include scraper endpoints router
app.include_router(scraper_router)


@app.get("/health")
def health_check():
    """Health check endpoint to verify API and vector stores are ready."""
    return {
        "status": "healthy",
        "article_store_loaded": article_store is not None,
        "chat_store_loaded": chat_store is not None,
    }


class ChatRequest(BaseModel):
    question: str
    user_id: str
    conversation_id: str
    tickers: list[str] | None = None
    top_k: int | None = 5
    chat_k: int | None = 3


@app.post("/chat")
def chat_endpoint(req: ChatRequest):
    logger.info("Chat request from user %s in conversation %s", req.user_id, req.conversation_id)

    # Auto-load user's portfolio tickers if not explicitly provided
    target_tickers = req.tickers
    if not target_tickers:
        target_tickers = get_portfolio_tickers(req.user_id)
        if target_tickers:
            logger.info(f"Using portfolio tickers for user {req.user_id}: {target_tickers}")

    try:
        response = rag_chat(
            question=req.question,
            conversation_id=req.conversation_id,
            user_id=req.user_id,
            target_tickers=target_tickers,
            top_k=req.top_k,
            chat_k=req.chat_k,
            article_store=article_store,
            chat_store=chat_store,
        )
    except Exception as e:
        logger.exception("RAG pipeline failed: %s", e)
        raise HTTPException(status_code=500, detail="Internal server error")

    return response


def run(
    host: str = settings.API_HOST,
    port: int = settings.API_PORT,
    reload: bool = False,
    workers: int = 1,
):
    """Run the FastAPI app with uvicorn.

    Args:
        host: Host to bind to
        port: Port to bind to
        reload: Enable auto-reload for development
        workers: Number of worker processes (production)
    """
    uvicorn.run(
        "finnews.api.main:app",  # String import for reload support
        host=host,
        port=port,
        reload=reload,
        workers=workers,
        log_level=settings.LOG_LEVEL.lower(),
        access_log=True,
    )
