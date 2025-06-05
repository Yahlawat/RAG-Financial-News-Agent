from typing import Optional
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain.schema import Document
from datetime import datetime
import os

def load_article_vectorstore(
    persist_directory: str,
    model_name: str = "BAAI/bge-base-en-v1.5"
) -> Chroma:
    embedding_model = HuggingFaceEmbeddings(model_name=model_name)
    return Chroma(
        persist_directory=persist_directory,
        embedding_function=embedding_model
    )


def article_chunk_reranker(
    docs: list[Document],
    target_tickers: Optional[list[str]] = None
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
                days_old = (datetime.now() - pub_date).days
                s -= 0.1 * days_old
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

def load_chat_vectorstore(
    persist_directory: str,
    model_name: str = "BAAI/bge-base-en-v1.5"
) -> Chroma:
    os.makedirs(persist_directory, exist_ok=True)
    embedding_model = HuggingFaceEmbeddings(model_name=model_name)
    return Chroma(
        persist_directory=persist_directory,
        embedding_function=embedding_model
    )

def add_chat_memory(
    chat_store: Chroma,
    conversation_id: str,
    question: str,
    answer: str
) -> None:

    timestamp = datetime.now().isoformat()
    content = f"Q: {question}\nA: {answer}"
    metadata = {
        "timestamp": timestamp,
        "conversation_id": conversation_id
    }
    doc = Document(page_content=content, metadata=metadata)
    doc_id = f"{conversation_id}_{timestamp}"
    chat_store.add_documents(documents=[doc], ids=[doc_id])

def retrieve_chat_memory(
    chat_store: Chroma,
    conversation_id: str,
    query: str,
    k: int = 3
) -> list[Document]:

    metadata_filter = {"conversation_id": conversation_id}
    retriever = chat_store.as_retriever(search_kwargs={"k": k, "filter": metadata_filter})
    return retriever.invoke(query)
