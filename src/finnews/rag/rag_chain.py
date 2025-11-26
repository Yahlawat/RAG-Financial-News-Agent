import logging
import os
from typing import Optional

from langchain_chroma import Chroma
from langchain_core.prompts import PromptTemplate
from langchain_core.runnables import RunnablePassthrough

from finnews.common.config import settings
from finnews.rag.retriever import (
    add_chat_memory,
    article_chunk_retriever,
    load_vectorstore,
    retrieve_chat_memory,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def rag_chat(
    question: str,
    conversation_id: str,
    user_id: str,
    target_tickers: Optional[list[str]] = None,
    top_k: int = 5,
    chat_k: int = 3,
    article_store: Optional[Chroma] = None,
    chat_store: Optional[Chroma] = None,
) -> dict:
    logger.info("Processing question for conversation %s", conversation_id)
    if article_store is None:
        article_store = load_vectorstore(str(settings.CHROMA_DIR))
    if chat_store is None:
        chat_store = load_vectorstore(str(settings.CHAT_MEMORY_DIR))

    past_qas = retrieve_chat_memory(chat_store, conversation_id, query=question, k=chat_k)
    chat_context = "\n\n".join(doc.page_content for doc in past_qas) if past_qas else ""

    news_docs = article_chunk_retriever(
        article_store, query=question, target_tickers=target_tickers, top_n=top_k
    )
    news_context = "\n\n".join(doc.page_content for doc in news_docs)

    if chat_context:
        combined_context = (
            f"Previous Q&A (same conversation):\n\n{chat_context}\n\n"
            f"News excerpts:\n\n{news_context}"
        )
    else:
        combined_context = f"News excerpts:\n\n{news_context}"

    prompt_template = PromptTemplate.from_template(
        """You're a helpful assistant with deep expertise in financial news. Using the information provided below, answer the user's question in a clear, structured way.

        Do not include source links here — they will be shared separately.

        Context:
        {combined_context}

        User question: {question}

        Your response:"""
    )

    api_key = settings.OPENAI_API_KEY or os.getenv("OPENAI_API_KEY")

    if not api_key:
        raise ValueError("OPENAI_API_KEY is required but not set in config or environment")

    from langchain_openai import ChatOpenAI  # type: ignore

    llm = ChatOpenAI(model=settings.LLM_MODEL, temperature=0.0, api_key=api_key)

    chain = (
        {
            "combined_context": RunnablePassthrough() | (lambda _: combined_context),
            "question": RunnablePassthrough(),
        }
        | prompt_template
        | llm
    )

    try:
        answer_output = chain.invoke(
            {"combined_context": combined_context, "question": question}
        ).content.strip()

    except Exception as e:
        logger.exception("LLM chain failed: %s", e)
        raise

    add_chat_memory(
        chat_store,
        conversation_id=conversation_id,
        user_id=user_id,
        question=question,
        answer=answer_output,
    )

    logger.info("Answer generated for conversation %s", conversation_id)

    sources = []
    for doc in news_docs:
        source = {
            "title": doc.metadata.get("title", ""),
            "url": doc.metadata.get("url", ""),
        }
        if pub_date := doc.metadata.get("published_date"):
            source["published_date"] = pub_date
        if source["title"] and source["url"]:
            sources.append(source)

    return {
        "conversation_id": conversation_id,
        "user_id": user_id,
        "question": question,
        "answer": answer_output,
        "sources": sources,
    }
