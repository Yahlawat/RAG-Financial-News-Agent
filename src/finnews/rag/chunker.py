import json
import logging
import re
import unicodedata

from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

from finnews.common.config import settings
from finnews.common.io_utils import ensure_file_dir, read_jsonl
from finnews.common.logging import get_logger, setup_logging

setup_logging(component="rag", level=logging.INFO, console=True)
logger = get_logger(__name__)


def clean_chunk(text: str) -> str:
    """
    Clean and normalize text by removing control characters and fixing encoding issues.

    Args:
        text: Raw text string to clean

    Returns:
        Cleaned and normalized text string
    """
    text = unicodedata.normalize("NFKD", text)
    text = re.sub(r"[\x00-\x1F\x7F]", "", text)
    text = text.replace("�?o", '"').replace("�??", '"').replace("�?T", "'")
    text = text.strip()
    text = re.sub(r"\s+", " ", text)

    return text


def chunk_articles(articles: list[dict], max_characters=800) -> list[Document]:
    """
    Split news articles into smaller chunks while preserving metadata.

    Args:
        articles: List of article dictionaries with 'body', 'title', 'url', etc.
        max_characters: Maximum characters per chunk (default: 800)

    Returns:
        List of LangChain Document objects with chunked content and metadata
    """
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=max_characters,
        chunk_overlap=200,
        separators=["\n\n", "\n", ". ", "! ", "? ", " ", ""],
    )

    docs = []

    for article in articles:
        body = article.get("body", "")
        if not body.strip():
            continue

        metadata = {
            "title": article.get("title"),
            "url": article.get("url"),
            "relevant_tickers": article.get("relevant_tickers", []),
            "published_date": article.get("published_date"),
        }

        body = clean_chunk(body)
        chunks = splitter.create_documents([body], metadatas=[metadata])
        docs.extend(chunks)

    return docs


def process_jsonl(input_path: str, output_path: str):
    """
    Process a JSONL file of articles into chunked documents.

    Args:
        input_path: Path to input JSONL file containing raw articles
        output_path: Path to output JSONL file for chunked documents
    """
    ensure_file_dir(output_path)

    articles = list(read_jsonl(input_path))

    chunked_docs = chunk_articles(articles)

    with open(output_path, "w", encoding="utf-8") as out_f:
        for doc in chunked_docs:
            out_f.write(
                json.dumps(
                    {"content": doc.page_content, "metadata": doc.metadata}, ensure_ascii=False
                )
                + "\n"
            )

    logger.info(f"Saved {len(chunked_docs)} chunks to {output_path}")


def main() -> None:
    process_jsonl(
        input_path=str(settings.RAW_NEWS_PATH),
        output_path=str(settings.PROCESSED_CHUNKS_PATH),
    )


if __name__ == "__main__":
    main()
