import os
import json
import logging
from tqdm import tqdm

from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain.schema import Document
from finnews.common.config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def load_chunks_from_file(file_path: str):
    documents = []
    ids = []

    with open(file_path, "r", encoding="utf-8") as f:
        for idx, line in enumerate(f):
            try:
                item = json.loads(line)
                chunk = item.get("content", "").strip()
                
                # Handle missing metadata gracefully
                item_metadata = item.get("metadata", {})
                metadata = {
                        "title": item_metadata.get("title", ""),
                        "url": item_metadata.get("url", ""),
                        "relevant_tickers": ", ".join(item_metadata.get("relevant_tickers", [])) if isinstance(item_metadata.get("relevant_tickers"), list) else item_metadata.get("relevant_tickers", ""),
                        "published_date": item_metadata.get("published_date", "")
                    }
            except (json.JSONDecodeError, KeyError) as e:
                logger.warning(f"Skipping invalid line {idx}: {e}")
                continue
            if not chunk:
                continue

            title = metadata.get("title", "").replace(" ", "_")[:80]
            doc_id = f"{title}_{idx}"

            documents.append(Document(page_content=chunk, metadata=metadata))
            ids.append(doc_id)

    return documents, ids


def batch(iterable: list, batch_size: int):
    for i in range(0, len(iterable), batch_size):
        yield iterable[i:i + batch_size]


<<<<<<< HEAD
def delete_old_articles_from_chroma(
    vectorstore: Chroma,
    cutoff_date: str,
) -> int:
    """
    Delete articles older than cutoff_date from ChromaDB.

    Args:
        vectorstore: ChromaDB vector store instance
        cutoff_date: ISO format date string (e.g., "2024-10-22")
                    Articles published before this date will be deleted

    Returns:
        Number of documents deleted
    """
    try:
        # Get all documents with metadata to find those older than cutoff
        all_docs = vectorstore.get(include=["metadatas"])

        # Find IDs of documents older than cutoff_date
        old_doc_ids = []
        for doc_id, metadata in zip(all_docs["ids"], all_docs["metadatas"]):
            published_date = metadata.get("published_date", "")
            if published_date and published_date < cutoff_date:
                old_doc_ids.append(doc_id)

        # Delete old documents
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


=======
>>>>>>> 7af5a402772857b0c388489419e38a01f18be89d
def build_chroma_index(
    input_file: str,
    output_path: str,
    model_name: str = "BAAI/bge-base-en-v1.5",
    batch_size: int = 32,
) -> Chroma:
    documents, ids = load_chunks_from_file(input_file)
    logger.info(f"Loaded {len(documents)} documents from file.")

    embedding_model = HuggingFaceEmbeddings(model_name=model_name)
    os.makedirs(output_path, exist_ok=True)

    vectorstore = Chroma(
        embedding_function=embedding_model,
        persist_directory=output_path,
    )

    try:
        existing_ids = set(vectorstore.get()["ids"])
    except Exception:
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

    for doc_batch, id_batch in tqdm(zip(batch(new_documents, batch_size), batch(new_ids, batch_size)),
                                    total=len(new_documents)//batch_size + 1,
                                    desc="Indexing in batches"):
        vectorstore.add_documents(documents=doc_batch, ids=id_batch)

<<<<<<< HEAD
    # Note: ChromaDB 0.4.24+ auto-persists changes, no need to call persist()
=======
    vectorstore.persist()
>>>>>>> 7af5a402772857b0c388489419e38a01f18be89d
    logger.info(f"Added {len(new_documents)} new documents to Chroma DB.")
    return vectorstore


def main() -> None:
    build_chroma_index(
        input_file=str(settings.processed_chunks),
        output_path=str(settings.chroma_store),
    )


if __name__ == "__main__":
    main()
