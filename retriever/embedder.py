from typing import List, Dict
import os
from sentence_transformers import SentenceTransformer
import chromadb
from chromadb.config import Settings

class NewsEmbedder:
    def __init__(self, model_name: str = "sentence-transformers/all-MiniLM-L6-v2"):
        self.model = SentenceTransformer(model_name)
        self.client = chromadb.Client(Settings(
            persist_directory="data/embeddings/chroma"
        ))
        self.collection = self.client.get_or_create_collection("financial_news")
    
    def create_embeddings(self, chunks: List[Dict]) -> None:
        """
        Create embeddings for text chunks and store them in ChromaDB.
        
        Args:
            chunks: List of dictionaries containing text chunks and metadata
        """
        texts = [chunk["text"] for chunk in chunks]
        metadatas = [chunk["metadata"] for chunk in chunks]
        ids = [chunk["chunk_id"] for chunk in chunks]
        
        # Create embeddings
        embeddings = self.model.encode(texts)
        
        # Store in ChromaDB
        self.collection.add(
            embeddings=embeddings.tolist(),
            documents=texts,
            metadatas=metadatas,
            ids=ids
        )
    
    def search_similar(self, query: str, n_results: int = 5) -> List[Dict]:
        """
        Search for similar chunks using a query.
        
        Args:
            query: Search query
            n_results: Number of results to return
            
        Returns:
            List of dictionaries containing similar chunks and their metadata
        """
        # Create query embedding
        query_embedding = self.model.encode(query)
        
        # Search in ChromaDB
        results = self.collection.query(
            query_embeddings=[query_embedding.tolist()],
            n_results=n_results
        )
        
        # Format results
        similar_chunks = []
        for i in range(len(results["documents"][0])):
            chunk = {
                "text": results["documents"][0][i],
                "metadata": results["metadatas"][0][i],
                "distance": results["distances"][0][i]
            }
            similar_chunks.append(chunk)
            
        return similar_chunks 