import os
import json
import uuid
from datetime import datetime
from typing import Optional

from langchain_core.prompts import PromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_ollama import OllamaLLM

from rag_pipeline.retriever import (
    load_article_vectorstore,
    article_chunk_retriever,
    load_chat_vectorstore,
    retrieve_chat_memory,
    add_chat_memory
)



def rag_chat(
    question: str,
    conversation_id: str,
    target_tickers: Optional[list[str]] = None,
    top_k: int = 5,   
    chat_k: int = 3    
) -> dict:

    news_store = load_article_vectorstore("data/chroma_store")
    chat_store = load_chat_vectorstore("data/chat_memory")

    past_qas = retrieve_chat_memory(chat_store, conversation_id, query=question, k=chat_k)
    chat_context = ""
    if past_qas:
        chat_context = "\n\n".join(doc.page_content for doc in past_qas)

    news_docs = article_chunk_retriever(news_store, query=question, target_tickers=target_tickers, top_n=top_k)    
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

        1. Start with a one- or two-sentence summary that gets straight to the point.
        2. Share 2–3 key insights or facts that stand out.
        3. Explain your reasoning or provide helpful context behind the insights.
        4. If it makes sense, suggest what the user should keep an eye on or consider doing next.

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

    add_chat_memory(chat_store, conversation_id=conversation_id, question=question, answer=answer_output)

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
        "question": question,
        "answer": answer_output,
        "sources": sources
    }