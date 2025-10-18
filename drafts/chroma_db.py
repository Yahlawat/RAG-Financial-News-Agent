from langchain_community.vectorstores import Chroma
from langchain_huggingface import HuggingFaceEmbeddings

# Load the existing Chroma store
embedding_model = HuggingFaceEmbeddings(model_name="BAAI/bge-base-en-v1.5")
vectorstore = Chroma(
    persist_directory="../data/chroma_store",
    embedding_function=embedding_model
)

# Fetch document IDs and count them
db_contents = vectorstore.get()
num_chunks = len(db_contents["ids"])
print(f"Total article chunks in Chroma DB: {num_chunks}")

matches = [
    metadata for metadata in db_contents["metadatas"]
    if "AMZN" in metadata.get("relevant_tickers", "")
]

db_contents = vectorstore.get()

matched = []
for doc_id, doc, metadata in zip(db_contents["ids"], db_contents["documents"], db_contents["metadatas"]):
    tickers = metadata.get("relevant_tickers", "")
    
    if isinstance(tickers, str):
        if "NVDA" in tickers:
            matched.append((doc_id, doc, metadata))
    elif isinstance(tickers, list):
        if "NVDA" in tickers:
            matched.append((doc_id, doc, metadata))

print(f"Found {len(matched)} chunks related to 'NVDA'.")

# Print up to 5 examples
for i, (doc_id, doc, meta) in enumerate(matched[:5]):
    print(f"\nExample {i+1}")
    print(f"ID: {doc_id}")
    print(f"Title: {meta.get('title', '')}")
    print(f"URL: {meta.get('url', '')}")
    print(f"Tickers: {meta.get('relevant_tickers', '')}")
    print(f"Published: {meta.get('published_date', '')}")
    print(f"Content: {doc[:300]}...")  # Truncate for readability
