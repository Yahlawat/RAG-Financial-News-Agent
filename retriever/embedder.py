# retriever/embedder.py

import json
import os
from sentence_transformers import SentenceTransformer
import faiss
import numpy as np

def build_faiss_index(input_dir: str, output_path: str, model_name: str = "all-MiniLM-L6-v2"):
    model = SentenceTransformer(model_name)
    index = faiss.IndexFlatL2(384)  # for MiniLM output dim

    metadata = []
    all_embeddings = []

    for filename in os.listdir(input_dir):
        with open(os.path.join(input_dir, filename), 'r', encoding='utf-8') as f:
            data = json.load(f)
            chunks = data["chunks"]
            embeddings = model.encode(chunks)

            all_embeddings.append(embeddings)
            metadata.extend([{
                "ticker": data["ticker"],
                "title": data["title"],
                "chunk": chunk
            } for chunk in chunks])

    vectors = np.vstack(all_embeddings)
    index.add(vectors)

    # Save FAISS index
    faiss.write_index(index, os.path.join(output_path, "news_index.faiss"))

    # Save metadata
    with open(os.path.join(output_path, "metadata.json"), "w") as f:
        json.dump(metadata, f, indent=2)

if __name__ == "__main__":
    os.makedirs("data/embeddings", exist_ok=True)
    build_faiss_index("data/processed_chunks", "data/embeddings")
