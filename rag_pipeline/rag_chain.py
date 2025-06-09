import os
import json
import uuid
from datetime import datetime
from typing import Optional
from langchain_chroma import Chroma

from langchain_core.prompts import PromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_ollama import OllamaLLM

from rag_pipeline.retriever import (
    load_vectorstore,
    article_chunk_retriever,
    retrieve_chat_memory,
    add_chat_memory
)

def rag_chat(
    question: str,
    conversation_id: str,
    user_id: str,
    target_tickers: Optional[list[str]] = None,
    top_k: int = 5,   
    chat_k: int = 3,
    article_store: Optional[Chroma] = None,
    chat_store: Optional[Chroma] = None
) -> dict:

    if article_store is None:
        article_store = load_vectorstore("data/chroma_store")
    if chat_store is None:
        chat_store = load_vectorstore("data/chat_memory")

    past_qas = retrieve_chat_memory(chat_store, conversation_id, query=question, k=chat_k)
    chat_context = ""
    if past_qas:
        chat_context = "\n\n".join(doc.page_content for doc in past_qas)

    news_docs = article_chunk_retriever(article_store, query=question, target_tickers=target_tickers, top_n=top_k)    
    news_context = "\n\n".join(doc.page_content for doc in news_docs)

    if chat_context:
        combined_context = (
            f"Previous Q&A (same conversation):\n\n{chat_context}\n\n"
            f"News excerpts:\n\n{news_context}"
        )
    else:
        combined_context = f"News excerpts:\n\n{news_context}"

    prompt_template = PromptTemplate.from_template(
        """You're a helpful assistant with deep expertise in financial news. Using the information provided below, answer the user's question in a clear, structured way:
    
        Don’t include source links here — they’ll be shared separately.

        Here’s what you’ve got to work with:
        {combined_context}

        User’s question: {question}

        Your response (use the structure above):"""
    )


    llm = OllamaLLM(model="gemma3:4b", temperature=0.0)

    chain = (
        {
            "combined_context": RunnablePassthrough() | (lambda _: combined_context),
            "question": RunnablePassthrough()
        }
        | prompt_template
        | llm
    )

    answer_output = chain.invoke(question).strip()

    add_chat_memory(chat_store, conversation_id=conversation_id, user_id=user_id, question=question, answer=answer_output)

    sources = []
    for doc in news_docs:
        title = str(doc.metadata.get("title", "")).strip()
        url = str(doc.metadata.get("url", "")).strip()
        published_str = str(doc.metadata.get("published_date", ""))
        published_str = published_str.strip() if published_str else ""

        published_date = None
        if published_str:
            try:
                published_date = datetime.fromisoformat(published_str).date().isoformat()
            except ValueError:
                pass

        if title and url and published_date:
            sources.append({"title": title, "url": url, "published_date": published_date})
        elif title and url:
            sources.append({"title": title, "url": url, "published_date": "(published_date not available)"})

    return {
        "conversation_id": conversation_id,
        "user_id": user_id,
        "question": question,
        "answer": answer_output,
        "sources": sources
    }