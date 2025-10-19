from langchain_community.vectorstores import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
import os

# Load the existing Chroma store
embedding_model = HuggingFaceEmbeddings(model_name="BAAI/bge-base-en-v1.5")
persist_dir = "../data/chroma_store"

# Verify the directory exists
if not os.path.exists(persist_dir):
    raise FileNotFoundError(f"Chroma store directory not found: {persist_dir}")

vectorstore = Chroma(
    persist_directory=persist_dir,
    embedding_function=embedding_model
)

# Fetch document IDs and count them
try:
    db_contents = vectorstore.get()
    num_chunks = len(db_contents["ids"])
    print(f"Total article chunks in Chroma DB: {num_chunks}")
except Exception as e:
    print(f"Error accessing Chroma DB: {str(e)}")

matches = [
    metadata for metadata in db_contents["metadatas"]
    if "AMZN" in metadata.get("relevant_tickers", "")
]

db_contents = vectorstore.get()

matched = []
for doc_id, doc, metadata in zip(db_contents["ids"], db_contents["documents"], db_contents["metadatas"]):
    tickers = metadata.get("relevant_tickers", "")
    
    if isinstance(tickers, str):
        if "TSLA" in tickers:
            matched.append((doc_id, doc, metadata))
    elif isinstance(tickers, list):
        if "TSLA" in tickers:
            matched.append((doc_id, doc, metadata))

print(f"Found {len(matched)} chunks related to 'TSLA'.")

# Print up to 5 examples
for i, (doc_id, doc, meta) in enumerate(matched[:5]):
    print(f"\nExample {i+1}")
    print(f"ID: {doc_id}")
    print(f"Title: {meta.get('title', '')}")
    print(f"URL: {meta.get('url', '')}")
    print(f"Tickers: {meta.get('relevant_tickers', '')}")
    print(f"Published: {meta.get('published_date', '')}")
    print(f"Content: {doc[:300]}...")  # Truncate for readability
