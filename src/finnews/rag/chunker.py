import json
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import Document
from finnews.common.config import settings
from finnews.common.io_utils import ensure_file_dir, read_jsonl
import re
import unicodedata

def clean_chunk(text: str) -> str:
    text = unicodedata.normalize("NFKD", text)
    text = re.sub(r'[\x00-\x1F\x7F]', '', text)
    text = text.replace("�?o", '"').replace("�??", '"').replace("�?T", "'")
    text = text.strip()
    text = re.sub(r'\s+', ' ', text)

    return text

def chunk_articles(articles: list[dict], max_characters=800) -> list[Document]:
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=max_characters,
        chunk_overlap=200,
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
    ensure_file_dir(output_path)

    # Load articles using utility function
    articles = list(read_jsonl(input_path))

    chunked_docs = chunk_articles(articles)

    # Write chunks to output file
    with open(output_path, "w", encoding="utf-8") as out_f:
        for doc in chunked_docs:
            out_f.write(json.dumps({
                "content": doc.page_content,
                "metadata": doc.metadata
            }, ensure_ascii=False) + "\n")

    print(f"Saved {len(chunked_docs)} chunks to {output_path}")

def main() -> None:
    process_jsonl(
        input_path=str(settings.RAW_NEWS_PATH),
        output_path=str(settings.PROCESSED_CHUNKS_PATH),
    )


if __name__ == "__main__":
    main()
 