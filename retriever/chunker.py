# retriever/chunker.py

import os
import json
from typing import List

def chunk_text(text: str, max_tokens: int = 300) -> List[str]:
    words = text.split()
    return [' '.join(words[i:i + max_tokens]) for i in range(0, len(words), max_tokens)]

def process_articles(input_dir: str, output_dir: str):
    os.makedirs(output_dir, exist_ok=True)

    for filename in os.listdir(input_dir):
        if filename.endswith(".json"):
            with open(os.path.join(input_dir, filename), 'r', encoding='utf-8') as f:
                article = json.load(f)
            
            body = article.get("body", "")
            chunks = chunk_text(body)

            output_path = os.path.join(output_dir, filename.replace('.json', '.json'))
            with open(output_path, 'w', encoding='utf-8') as out_f:
                json.dump({
                    "ticker": article.get("ticker"),
                    "title": article.get("title"),
                    "chunks": chunks
                }, out_f, indent=2)

if __name__ == "__main__":
    process_articles("data/raw_news", "data/processed_chunks")
