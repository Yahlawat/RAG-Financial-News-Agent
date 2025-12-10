import logging
import os
from typing import Optional

from langchain_chroma import Chroma
from langchain_core.prompts import PromptTemplate
from langchain_core.runnables import RunnablePassthrough

from finnews.common.config import settings
from finnews.common.logging import setup_logging
from finnews.rag.retriever import (
    add_chat_memory,
    article_chunk_retriever,
    load_vectorstore,
    retrieve_chat_memory,
)

# Setup logging for RAG component
setup_logging(component="rag", level=logging.INFO, console=True)
logger = logging.getLogger(__name__)


def format_doc_with_metadata(doc, doc_type: str = "news") -> str:
    """
    Format a document with its metadata for better LLM context awareness.

    Args:
        doc: Document object with page_content and metadata
        doc_type: Either "chat" or "news"

    Returns:
        Formatted string with metadata headers
    """
    if doc_type == "chat":
        role = doc.metadata.get("role", "unknown").upper()
        return f"[{role}]: {doc.page_content}"
    else:  # news
        title = doc.metadata.get("title", "Unknown Article")
        date = doc.metadata.get("published_date", "Unknown date")
        tickers = doc.metadata.get("relevant_tickers", "")

        # Parse tickers from comma-separated string
        ticker_list = [t.strip() for t in tickers.split(",") if t.strip()]
        ticker_str = f" ({', '.join(ticker_list)})" if ticker_list else ""

        return f"[Article: {title}{ticker_str} - {date}]\n{doc.page_content}"


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

    # Format chat history with metadata
    if past_qas:
        formatted_chat = "\n\n".join(
            format_doc_with_metadata(doc, doc_type="chat") for doc in past_qas
        )
        chat_context = f"=== CONVERSATION HISTORY ===\n(Previous exchanges in this conversation)\n\n{formatted_chat}"
    else:
        chat_context = ""

    # Retrieve and format news articles with metadata
    news_docs = article_chunk_retriever(
        article_store, query=question, target_tickers=target_tickers, top_n=top_k
    )
    formatted_news = "\n\n".join(
        format_doc_with_metadata(doc, doc_type="news") for doc in news_docs
    )
    news_context = f"=== RELEVANT NEWS ARTICLES ===\n(Recent financial news excerpts)\n\n{formatted_news}"

    # Combine contexts
    if chat_context:
        combined_context = f"{chat_context}\n\n{news_context}"
    else:
        combined_context = news_context

    prompt_template = PromptTemplate.from_template(
        """You are a financial news assistant specializing in company news and market developments. Your role is to provide factual, well-structured summaries based on the information provided.

GUIDELINES:
- Answer using ONLY the information in the context below
- Structure your response with clear paragraphs or bullet points for readability
- When discussing specific financial data (earnings, stock prices, percentages), include the exact figures mentioned
- Note publication dates when timing is relevant to the question (e.g., "most recent", "this week")
- Distinguish between factual reporting and opinion/analysis from source articles
- If multiple sources present different perspectives or information, acknowledge both viewpoints
- If the context lacks sufficient information to fully answer the question, clearly state what information is missing
- Use conversation history to understand follow-up questions and maintain context
- Important: This information reflects article publication dates and may not represent current conditions
- Do NOT provide investment advice or buy/sell recommendations
- Do NOT include article URLs or source links (these are provided separately)

Context:
{combined_context}

Question: {question}

Response:"""
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
