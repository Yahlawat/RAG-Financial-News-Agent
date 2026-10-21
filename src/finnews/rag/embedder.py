import hashlib
import json
import logging
import math
import os

from langchain_core.documents import Document
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from tqdm import tqdm

from finnews.common.config import settings
from finnews.common.io_utils import read_jsonl

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


def chunk_id(content: str, metadata: dict) -> str:
    """Build a content-based ID for a chunk.

    The ID stays the same however the chunks file is reordered (e.g. after cleanup),
    and changes whenever the chunk's text or metadata does.
    """
    payload = json.dumps({"content": content, "metadata": metadata}, sort_keys=True)
    return hashlib.sha1(payload.encode("utf-8")).hexdigest()


def load_chunks_from_file(file_path: str):
    documents = []
    ids = []
    seen_ids = set()

    for idx, item in enumerate(read_jsonl(file_path)):
        try:
            chunk = item.get("content", "").strip()

            item_metadata = item.get("metadata", {})
            metadata = {
                "title": item_metadata.get("title") or "",
                "url": item_metadata.get("url") or "",
                "relevant_tickers": ", ".join(item_metadata.get("relevant_tickers", []))
                if isinstance(item_metadata.get("relevant_tickers"), list)
                else item_metadata.get("relevant_tickers", ""),
                "published_date": item_metadata.get("published_date") or "",
            }

            if not chunk:
                continue

            # Identical chunks (same text and metadata) are stored once
            doc_id = chunk_id(chunk, metadata)
            if doc_id in seen_ids:
                continue
            seen_ids.add(doc_id)

            documents.append(Document(page_content=chunk, metadata=metadata))
            ids.append(doc_id)
        except KeyError as e:
            logger.warning(f"Skipping item {idx} due to missing key: {e}")
            continue

    return documents, ids


def batch(iterable: list, batch_size: int):
    for i in range(0, len(iterable), batch_size):
        yield iterable[i : i + batch_size]


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
        existing_ids = set(vectorstore.get(include=[])["ids"])
    except (KeyError, AttributeError, RuntimeError) as e:
        logger.warning(f"Could not load existing IDs: {e}")
        existing_ids = set()

    # Keep the index in sync with the chunks file: drop documents that are no longer
    # in it (removed by cleanup, or replaced because their text or metadata changed)
    stale_ids = list(existing_ids - set(ids))
    if stale_ids and not documents:
        logger.warning(
            "Chunks file is empty; keeping %d existing documents instead of deleting them",
            len(stale_ids),
        )
    elif stale_ids:
        logger.info(f"Removing {len(stale_ids)} documents no longer in the chunks file...")
        for id_batch in batch(stale_ids, 5000):
            vectorstore.delete(ids=id_batch)

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
        total=math.ceil(len(new_documents) / batch_size),
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
