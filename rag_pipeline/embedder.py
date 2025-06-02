import os
import json
import logging
from tqdm import tqdm 

from langchain_community.vectorstores import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain.schema import Document

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def load_chunks_from_file(file_path: str):
    documents = []
    ids = []

    with open(file_path, "r", encoding="utf-8") as f:
        for idx, line in enumerate(f):

            item = json.loads(line)
            chunk = item.get("content", "").strip()
            metadata = {
                    "title": item["metadata"].get("title", ""),
                    "url": item["metadata"].get("url", ""),
                    "relevant_tickers": ", ".join(item["metadata"].get("relevant_tickers", [])),
                    "published_date": item["metadata"].get("published_date", "")
                }
            if not chunk:
                continue

            title = metadata.get("title", "").replace(" ", "_")[:80]
            doc_id = f"{title}_{idx}"

            documents.append(Document(page_content=chunk, metadata=metadata))
            ids.append(doc_id)

    return documents, ids


def build_chroma_index(
    input_file: str,
    output_path: str,
    model_name: str = "BAAI/bge-base-en-v1.5",
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

    texts = [doc.page_content for doc in new_documents]
    metadatas = [doc.metadata for doc in new_documents]

    logger.info(f"Embedding {len(new_documents)} new documents...")
    embeddings = [
        embedding_model.embed_query(text)
        for text in tqdm(texts, desc="Embedding new docs")
    ]

    vectorstore.add_embeddings(
        texts=texts,
        embeddings=embeddings,
        metadatas=metadatas,
        ids=new_ids
    )
    vectorstore.persist()
    logger.info(f"Added {len(new_documents)} new documents to Chroma DB.")

    return vectorstore


if __name__ == "__main__":
    build_chroma_index(
        input_file="data/processed_chunks/chunked_articles.jsonl",
        output_path="data/chroma_store",
    )
