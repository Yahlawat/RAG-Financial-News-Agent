import os
import json
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import Document
import re
import unicodedata

def clean_chunk(text: str) -> str:
    text = unicodedata.normalize("NFKD", text)
    text = re.sub(r'[\x00-\x1F\x7F]', '', text)
    text = text.replace("“", '"').replace("”", '"').replace("’", "'")
    text = text.strip()
    text = re.sub(r'\s+', ' ', text)

    return text

def chunk_articles(articles: list[dict], max_characters=1000) -> list[Document]:
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=max_characters,
        chunk_overlap=400,
        separators=["\n\n", "\n", ". ", "! ", "? ", " ", ""]
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
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    with open(input_path, "r", encoding="utf-8") as f:
        articles = [json.loads(line) for line in f]

    chunked_docs = chunk_articles(articles)
    

    with open(output_path, "w", encoding="utf-8") as out_f:
        for doc in chunked_docs:
            out_f.write(json.dumps({
                "content": doc.page_content,
                "metadata": doc.metadata
            }) + "\n")

    print(f"Saved {len(chunked_docs)} chunks to {output_path}")

if __name__ == "__main__":
    process_jsonl(
        input_path="data/raw_news/articles.jsonl",
        output_path="data/processed_chunks/chunked_articles.jsonl"
    )