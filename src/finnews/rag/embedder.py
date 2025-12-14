import logging
import os
import re

from langchain_core.documents import Document
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from tqdm import tqdm

from finnews.common.config import settings
from finnews.common.io_utils import read_jsonl
from finnews.common.logging import setup_logging

setup_logging(component="rag", level=logging.INFO, console=True)
logger = logging.getLogger(__name__)


def get_embedding_model(model_name: str | None = None) -> HuggingFaceEmbeddings:
    """
    Get the configured embedding model.

    Args:
        model_name: Optional model name override. If not provided, uses settings.EMBEDDING_MODEL

    Returns:
        HuggingFaceEmbeddings instance
    """
    if model_name is None:
        model_name = settings.EMBEDDING_MODEL
    return HuggingFaceEmbeddings(model_name=model_name)


def load_chunks_from_file(file_path: str):
    documents = []
    ids = []

    for idx, item in enumerate(read_jsonl(file_path)):
        try:
            chunk = item.get("content", "").strip()

            item_metadata = item.get("metadata", {})
            metadata = {
                "title": item_metadata.get("title", ""),
                "url": item_metadata.get("url", ""),
                "relevant_tickers": ", ".join(item_metadata.get("relevant_tickers", []))
                if isinstance(item_metadata.get("relevant_tickers"), list)
                else item_metadata.get("relevant_tickers", ""),
                "published_date": item_metadata.get("published_date", ""),
            }

            if not chunk:
                continue

            # Sanitize title for use in document ID (remove special characters)
            title = metadata.get("title", "")
            title_clean = re.sub(r'[^a-zA-Z0-9_-]', '_', title)[:80]
            doc_id = f"{title_clean}_{idx}"

            documents.append(Document(page_content=chunk, metadata=metadata))
            ids.append(doc_id)
        except KeyError as e:
            logger.warning(f"Skipping item {idx} due to missing key: {e}")
            continue

    return documents, ids


def batch(iterable: list, batch_size: int):
    for i in range(0, len(iterable), batch_size):
        yield iterable[i : i + batch_size]


def delete_old_articles_from_chroma(vectorstore: Chroma, cutoff_date: str) -> int:
    """
    Delete articles older than cutoff_date from ChromaDB.

    Args:
        vectorstore: ChromaDB vector store instance
        cutoff_date: ISO format date string (e.g., "2024-10-22")

    Returns:
        Number of documents deleted
    """
    try:
        # Get all documents with metadata
        all_docs = vectorstore.get(include=["metadatas"])

        # Find IDs of documents older than cutoff_date
        old_doc_ids = []
        for doc_id, metadata in zip(all_docs["ids"], all_docs["metadatas"]):
            published_date = metadata.get("published_date", "")
            if published_date and published_date < cutoff_date:
                old_doc_ids.append(doc_id)

        if old_doc_ids:
            vectorstore.delete(ids=old_doc_ids)
            logger.info(f"Deleted {len(old_doc_ids)} old documents from ChromaDB")
            return len(old_doc_ids)
        else:
            logger.info("No old documents found to delete")
            return 0

    except Exception as e:
        logger.error(f"Error deleting old articles: {e}")
        return 0


def build_chroma_index(
    input_file: str,
    output_path: str,
    model_name: str | None = None,
    batch_size: int = 10,
) -> Chroma:
    documents, ids = load_chunks_from_file(input_file)
    logger.info(f"Loaded {len(documents)} documents from file.")

    embedding_model = get_embedding_model(model_name)
    os.makedirs(output_path, exist_ok=True)

    vectorstore = Chroma(
        embedding_function=embedding_model,
        persist_directory=output_path,
    )

    try:
        existing_ids = set(vectorstore.get()["ids"])
    except (KeyError, AttributeError, RuntimeError) as e:
        logger.warning(f"Could not load existing IDs: {e}")
        existing_ids = set()

    new_documents = []
    new_ids = []
    for doc, doc_id in zip(documents, ids):
        if doc_id not in existing_ids:
            new_documents.append(doc)
            new_ids.append(doc_id)

    if not new_documents:
        logger.info("No new documents to add. Vector DB is up to date.")
        return vectorstore

    logger.info(f"Adding {len(new_documents)} new documents to Chroma DB...")

    for doc_batch, id_batch in tqdm(
        zip(batch(new_documents, batch_size), batch(new_ids, batch_size)),
        total=len(new_documents) // batch_size + 1,
        desc="Indexing in batches",
    ):
        try:
            vectorstore.add_documents(documents=doc_batch, ids=id_batch)
        except Exception as e:
            logger.error(f"Error adding batch to ChromaDB: {e}")
            logger.error(f"Batch size: {len(doc_batch)}")
            logger.error(f"Sample IDs from failed batch: {id_batch[:5]}")
            raise

    logger.info(f"Added {len(new_documents)} new documents to Chroma DB.")
    return vectorstore


def main() -> None:
    build_chroma_index(
        input_file=str(settings.PROCESSED_CHUNKS_PATH),
        output_path=str(settings.CHROMA_DIR),
    )


if __name__ == "__main__":
    main()
