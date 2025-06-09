from typing import Optional
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain.schema import Document
from datetime import datetime
from uuid import uuid4
import math
import os

def load_vectorstore(
    persist_directory: str,
    model_name: str = "BAAI/bge-base-en-v1.5"
) -> Chroma:
    os.makedirs(persist_directory, exist_ok=True)
    embedding_model = HuggingFaceEmbeddings(model_name=model_name)
    return Chroma(
        persist_directory=persist_directory,
        embedding_function=embedding_model
    )


def article_chunk_reranker(
    docs: list[Document],
    target_tickers: Optional[list[str]] = None,
) -> list[Document]:

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
        except:
            pass

        # Ticker-match boost
        if target_tickers:
            tickers_in_doc = metadata.get("relevant_tickers", "").split(", ")
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

    search_kwargs = {"k": 15}
    retriever = vectorstore.as_retriever(search_kwargs=search_kwargs)
    docs = retriever.invoke(query)
    
    reranked_docs = article_chunk_reranker(docs, target_tickers=target_tickers)
    return reranked_docs[:top_n]

def add_chat_memory(
    chat_store: Chroma,
    conversation_id: str,
    user_id: str,
    question: str,
    answer: str,
    model_name: str = "BAAI/bge-base-en-v1.5"
) -> None:
    timestamp = datetime.now().isoformat()

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
            f"{conversation_id}_{timestamp}_user",
            f"{conversation_id}_{timestamp}_assistant"
        ]
    )


def retrieve_chat_memory(
    chat_store: Chroma,
    conversation_id: str,
    query: str,
    k: int = 3
) -> list[Document]:

    metadata_filter = {"conversation_id": conversation_id}
    retriever = chat_store.as_retriever(search_kwargs={"k": k, "filter": metadata_filter})
    return retriever.invoke(query)

def get_full_chat_history(
    chat_store: Chroma, 
    conversation_id: str, 
    user_id: Optional[str] = None
    ) -> list[Document]:

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

