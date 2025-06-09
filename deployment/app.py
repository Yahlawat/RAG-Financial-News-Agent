# app.py
from typing import List, Optional
from uuid import uuid4

from fastapi import FastAPI
from pydantic import BaseModel

from rag_pipeline.retriever import load_vectorstore
from rag_pipeline.rag_chain import rag_chat

app = FastAPI()

# Vector stores loaded at startup
article_store = None
chat_store = None

@app.on_event("startup")
def init_vectorstores() -> None:
    global article_store, chat_store
    article_store = load_vectorstore("data/chroma_store")
    chat_store = load_vectorstore("data/chat_memory")

class ChatRequest(BaseModel):
    question: str
    user_id: str
    conversation_id: str
    tickers: Optional[List[str]] = None
    top_k: Optional[int] = 5
    chat_k: Optional[int] = 3

@app.post("/chat")
async def chat_endpoint(req: ChatRequest):
    response = rag_chat(
        question=req.question,
        conversation_id=req.conversation_id,
        user_id=req.user_id,
        target_tickers=req.tickers,
        top_k=req.top_k,
        chat_k=req.chat_k,
        article_store=article_store,
        chat_store=chat_store,
    )

    return response
