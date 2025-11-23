# app.py
from typing import List, Optional
import logging
import uvicorn
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from finnews.rag.retriever import load_vectorstore
from finnews.rag.rag_chain import rag_chat
from finnews.common.config import settings
from finnews.api.scraper_endpoints import router as scraper_router
from finnews.ui.user_profile import get_portfolio_tickers

logging.basicConfig(level=logging.INFO)
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
    article_store = load_vectorstore(str(settings.chroma_store))
    chat_store = load_vectorstore(str(settings.chat_memory))
    logger.info("Vector stores initialized")

    yield

    # Shutdown: cleanup if needed
    logger.info("Shutting down")


app = FastAPI(lifespan=lifespan)

# Include scraper endpoints router
app.include_router(scraper_router)


@app.get("/health")
async def health_check():
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
    tickers: Optional[List[str]] = None
    top_k: Optional[int] = 5
    chat_k: Optional[int] = 3

@app.post("/chat")
async def chat_endpoint(req: ChatRequest):
    logger.info(
        "Chat request from user %s in conversation %s", req.user_id, req.conversation_id
    )

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


def run(host: str = settings.api_host, port: int = settings.api_port):
    """Run the FastAPI app with uvicorn."""
    uvicorn.run(app, host=host, port=port)
