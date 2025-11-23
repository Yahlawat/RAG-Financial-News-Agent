from typing import Optional
from langchain_chroma import Chroma
from langchain.schema import Document
from datetime import datetime, timezone
from uuid import uuid4
import math

from dotenv import load_dotenv
from finnews.common.logging import get_logger
from finnews.common.io_utils import ensure_file_dir
from finnews.rag.embedder import get_embedding_model

load_dotenv()

logger = get_logger(__name__)

def load_vectorstore(
    persist_directory: str,
    model_name: str | None = None
) -> Chroma:
    logger.info(f"Loading vectorstore from {persist_directory}")
    from pathlib import Path
    Path(persist_directory).mkdir(parents=True, exist_ok=True)
    embedding_model = get_embedding_model(model_name)
    store = Chroma(
        persist_directory=persist_directory,
        embedding_function=embedding_model
    )
    logger.info("Vectorstore loaded")
    return store

def article_chunk_reranker(
    docs: list[Document],
    target_tickers: Optional[list[str]] = None,
) -> list[Document]:
    logger.debug("Reranking %d documents for tickers: %s", len(docs), target_tickers)

    def score(doc: Document) -> float:
        s = 0
        metadata = doc.metadata
        content = doc.page_content.strip()

        # Recency boost
        try:
            pub_date_str = metadata.get("published_date", "")
            if pub_date_str:
                pub_date = datetime.fromisoformat(pub_date_str)
                days_old = max((datetime.now() - pub_date).days, 1)
                s -= 0.5 * math.log(days_old)
        except Exception as e:
            logger.warning("Failed to parse publication date: %s", e)

        # Ticker-match boost
        if target_tickers:
            tickers_in_doc = [t.strip() for t in metadata.get("relevant_tickers", "").split(",")]
            if any(t in tickers_in_doc for t in target_tickers):
                s += 5

        # Short-chunk penalty
        length = len(content)
        if length < 100:
            s -= 5
        elif length < 300:
            s -= 2

        return s

    return sorted(docs, key=score, reverse=True)

def article_chunk_retriever(
    vectorstore: Chroma,
    query: str,
    target_tickers: Optional[list[str]] = None,
    top_n: int = 5
) -> list[Document]:
    logger.info("Retrieving articles for query: %s", query)
    
    if not query or not query.strip():
        logger.warning("Empty query provided")
        return []
    
    try:
        search_kwargs = {"k": 15}
        retriever = vectorstore.as_retriever(search_kwargs=search_kwargs)
        docs = retriever.invoke(query)
        logger.debug("Retrieved %d documents", len(docs))
        
        if not docs:
            logger.warning("No documents retrieved for query: %s", query)
            return []

        reranked_docs = article_chunk_reranker(docs, target_tickers=target_tickers)
        logger.info("Returning top %d documents", top_n)
        return reranked_docs[:top_n]
    except Exception as e:
        logger.error("Error retrieving documents: %s", e)
        return []

def add_chat_memory(
    chat_store: Chroma,
    conversation_id: str,
    user_id: str,
    question: str,
    answer: str
) -> None:
    timestamp = datetime.now(timezone.utc).isoformat()
    suffix = str(uuid4()).split("-")[0] 

    if not isinstance(answer, str):
        answer = getattr(answer, "content", str(answer))

    user_doc = Document(
        page_content=question,
        metadata={
            "timestamp": timestamp,
            "role": "user",
            "user_id": user_id,
            "conversation_id": conversation_id,
            "doc_type": "chat",
        }
    )

    assistant_doc = Document(
        page_content=answer,
        metadata={
            "timestamp": timestamp,
            "role": "assistant",
            "user_id": user_id,
            "conversation_id": conversation_id,
            "doc_type": "chat",
        }
    )

    chat_store.add_documents(
        documents=[user_doc, assistant_doc],
        ids=[
            f"{conversation_id}_{timestamp}_user_{suffix}",
            f"{conversation_id}_{timestamp}_assistant_{suffix}"
        ]
    )
    logger.info("Stored chat messages for conversation %s", conversation_id)

def retrieve_chat_memory(
    chat_store: Chroma,
    conversation_id: str,
    query: str,
    k: int = 3
) -> list[Document]:
    logger.debug("Retrieving relevant chat messages for conversation %s", conversation_id)
    metadata_filter = {"conversation_id": conversation_id}
    retriever = chat_store.as_retriever(search_kwargs={"k": k, "filter": metadata_filter})
    return retriever.invoke(query)

def get_full_chat_history(
    chat_store: Chroma,
    conversation_id: str,
    user_id: Optional[str] = None
) -> list[Document]:
    logger.debug("Fetching full chat history for conversation %s", conversation_id)
    if user_id:
        filters = {
            "$and": [
                {"conversation_id": conversation_id},
                {"user_id": user_id}
            ]
        }
    else:
        filters = {"conversation_id": conversation_id}

    results = chat_store.get(where=filters, include=["documents", "metadatas"])
    docs = [
        Document(page_content=content, metadata=metadata)
        for content, metadata in zip(results["documents"], results["metadatas"])
    ]
    return sorted(docs, key=lambda doc: doc.metadata.get("timestamp", ""))

