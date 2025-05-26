# retriever/embedder.py
import os
import json
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain.schema import Document

def load_chunks_from_file(file_path: str):
    documents = []
    with open(file_path, "r", encoding="utf-8") as f:
        for line in f:
            item = json.loads(line)
            chunks = item["content"]
            for i, chunk in enumerate(chunks):
                metadata = {
                    "title": item.get("title", ""),
                    "url": item.get("url", ""),
                    "relevant_tickers": ", ".join(item.get("relevant_tickers", [])),
                    "published_date": item.get("published_date", ""),
                    "chunk_index": i,
                }
                documents.append(Document(page_content=chunk, metadata=metadata))
    return documents

def build_chroma_index(input_file: str, output_path: str, model_name: str = "BAAI/bge-base-en-v1.5"):
    embedding_model = HuggingFaceEmbeddings(model_name=model_name)
    documents = load_chunks_from_file(input_file)
    os.makedirs(output_path, exist_ok=True)

    vectorstore = Chroma.from_documents(
        documents=documents,
        embedding=embedding_model,
        persist_directory=output_path
    )
    vectorstore.persist()
    return vectorstore


if __name__ == "__main__":
    build_chroma_index("data/processed_chunks/chunked_articles.jsonl", "data/chroma_store")
