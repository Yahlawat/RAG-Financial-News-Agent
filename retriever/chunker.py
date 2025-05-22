from typing import List, Dict
import re
from langchain.text_splitter import RecursiveCharacterTextSplitter

class NewsChunker:
    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 200):
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=len,
            separators=["\n\n", "\n", ".", "!", "?", ",", " ", ""]
        )
    
    def chunk_article(self, article: Dict) -> List[Dict]:
        """
        Split a news article into chunks while preserving metadata.
        
        Args:
            article: Dictionary containing article data (title, content, metadata)
            
        Returns:
            List of dictionaries, each containing a chunk and its metadata
        """
        # Combine title and content for chunking
        full_text = f"{article['title']}\n\n{article['content']}"
        chunks = self.text_splitter.split_text(full_text)
        
        # Create chunk documents with metadata
        chunk_docs = []
        for i, chunk in enumerate(chunks):
            chunk_doc = {
                "chunk_id": f"{article['url']}_{i}",
                "text": chunk,
                "metadata": {
                    "title": article["title"],
                    "url": article["url"],
                    "source": article["source"],
                    "published_date": article["published_date"],
                    "chunk_index": i,
                    "total_chunks": len(chunks)
                }
            }
            chunk_docs.append(chunk_doc)
            
        return chunk_docs 