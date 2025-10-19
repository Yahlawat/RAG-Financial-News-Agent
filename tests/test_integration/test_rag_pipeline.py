"""Integration tests for the RAG pipeline."""
import json
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from finnews.rag.chunker import chunk_articles, process_jsonl
from finnews.rag.embedder import build_chroma_index, load_chunks_from_file
from finnews.rag.retriever import article_chunk_retriever, article_chunk_reranker
from finnews.rag.rag_chain import rag_chat


class TestRAGPipelineIntegration:
    """Integration tests for the complete RAG pipeline."""

    def test_end_to_end_pipeline(self):
        """Test the complete RAG pipeline from articles to chat."""
        # Create test articles
        test_articles = [
            {
                "title": "Apple Reports Strong Q4 Earnings",
                "url": "https://example.com/apple-earnings",
                "body": "Apple Inc. reported strong fourth quarter earnings with revenue exceeding expectations. The company's iPhone sales were particularly strong, driven by the latest iPhone 15 series. Apple's services division also showed robust growth, with App Store revenue reaching new heights. The company's stock price rose 5% in after-hours trading following the announcement.",
                "published_date": "2024-01-15T10:00:00",
                "relevant_tickers": ["AAPL"],
                "main_ticker": "AAPL"
            },
            {
                "title": "Microsoft Azure Growth Continues",
                "url": "https://example.com/microsoft-azure",
                "body": "Microsoft Corporation's Azure cloud platform continues to show strong growth in the latest quarter. The company reported 25% year-over-year growth in Azure revenue, driven by increased enterprise adoption and new AI services. Microsoft's Office 365 and Teams platforms also contributed to the strong performance. The company's stock price increased 3% following the earnings report.",
                "published_date": "2024-01-14T09:00:00",
                "relevant_tickers": ["MSFT"],
                "main_ticker": "MSFT"
            }
        ]
        
        with tempfile.TemporaryDirectory() as temp_dir:
            # Step 1: Create raw articles file
            raw_articles_file = Path(temp_dir) / "articles.jsonl"
            with open(raw_articles_file, 'w') as f:
                for article in test_articles:
                    f.write(json.dumps(article) + '\n')
            
            # Step 2: Process and chunk articles
            chunks_file = Path(temp_dir) / "chunks.jsonl"
            process_jsonl(str(raw_articles_file), str(chunks_file))
            
            # Verify chunks were created
            assert chunks_file.exists()
            with open(chunks_file, 'r') as f:
                chunks = [json.loads(line) for line in f]
                assert len(chunks) > 0
                assert all('content' in chunk for chunk in chunks)
                assert all('metadata' in chunk for chunk in chunks)
            
            # Step 3: Build vector index
            with patch('finnews.rag.embedder.HuggingFaceEmbeddings') as mock_embeddings, \
                 patch('finnews.rag.embedder.Chroma') as mock_chroma:
                
                # Mock the embedding model
                mock_embedding_model = MagicMock()
                mock_embeddings.return_value = mock_embedding_model
                
                # Mock the Chroma vectorstore
                mock_vectorstore = MagicMock()
                mock_vectorstore.get.return_value = {"ids": []}  # No existing documents
                mock_chroma.return_value = mock_vectorstore
                
                # Build the index
                vectorstore = build_chroma_index(
                    input_file=str(chunks_file),
                    output_path=temp_dir + "/chroma_store",
                    model_name="test-model",
                    batch_size=1
                )
                
                # Verify the vectorstore was created
                assert vectorstore == mock_vectorstore
                mock_chroma.assert_called_once()
                mock_embeddings.assert_called_once_with(model_name="test-model")

    def test_chunking_quality(self):
        """Test that chunking produces high-quality chunks."""
        # Create a long article
        long_article = {
            "title": "Comprehensive Analysis of Tech Stocks",
            "url": "https://example.com/tech-analysis",
            "body": "The technology sector has shown remarkable resilience in the face of economic uncertainty. Apple Inc. continues to lead the smartphone market with its innovative iPhone series. The company's focus on services and ecosystem integration has created a sustainable competitive advantage. Microsoft Corporation has successfully transitioned to a cloud-first business model, with Azure becoming a major revenue driver. The company's enterprise software solutions remain dominant in the market. Google's parent company Alphabet Inc. maintains its leadership in search and digital advertising while investing heavily in artificial intelligence and machine learning capabilities. The company's YouTube platform continues to grow and generate significant advertising revenue. Amazon.com Inc. has diversified beyond e-commerce into cloud computing, digital streaming, and logistics services. The company's AWS division has become a major profit center. Meta Platforms Inc. is investing heavily in the metaverse and virtual reality technologies, though the returns on these investments remain uncertain. The company's core social media platforms continue to generate substantial advertising revenue.",
            "published_date": "2024-01-15T10:00:00",
            "relevant_tickers": ["AAPL", "MSFT", "GOOGL", "AMZN", "META"],
            "main_ticker": "AAPL"
        }
        
        # Chunk the article
        docs = chunk_articles([long_article], max_characters=200)
        
        # Verify chunking quality
        assert len(docs) > 1  # Should be split into multiple chunks
        assert all(len(doc.page_content) <= 200 for doc in docs)  # Respects max_characters
        assert all(len(doc.page_content) > 50 for doc in docs)  # Chunks are not too small
        
        # Verify metadata is preserved
        for doc in docs:
            assert doc.metadata["title"] == "Comprehensive Analysis of Tech Stocks"
            assert doc.metadata["url"] == "https://example.com/tech-analysis"
            assert doc.metadata["relevant_tickers"] == ["AAPL", "MSFT", "GOOGL", "AMZN", "META"]

    def test_retrieval_ranking(self):
        """Test that retrieval ranking works correctly."""
        from langchain.schema import Document
        
        # Create test documents with different characteristics
        docs = [
            Document(
                "Apple Inc. reported strong quarterly earnings with iPhone sales exceeding expectations.",
                {"published_date": "2024-01-15T10:00:00", "relevant_tickers": "AAPL, MSFT"}
            ),
            Document(
                "Microsoft's Azure cloud platform showed 25% growth in the latest quarter.",
                {"published_date": "2024-01-14T09:00:00", "relevant_tickers": "MSFT, GOOGL"}
            ),
            Document(
                "Short content.",
                {"published_date": "2024-01-15T10:00:00", "relevant_tickers": "AAPL"}
            )
        ]
        
        # Test reranking with ticker preference
        ranked_docs = article_chunk_reranker(docs, target_tickers=["AAPL"])
        
        # Documents with AAPL ticker should be ranked higher
        assert "Apple Inc." in ranked_docs[0].page_content
        assert "Short content." in ranked_docs[-1].page_content  # Short content should be penalized

    def test_rag_chat_integration(self):
        """Test the complete RAG chat integration."""
        from langchain.schema import Document
        
        # Mock vector stores
        mock_article_store = MagicMock()
        mock_chat_store = MagicMock()
        
        # Mock retriever functions
        with patch('finnews.rag.rag_chain.article_chunk_retriever') as mock_article_retriever, \
             patch('finnews.rag.rag_chain.retrieve_chat_memory') as mock_chat_retriever, \
             patch('finnews.rag.rag_chain.add_chat_memory') as mock_add_memory:
            
            # Mock retrieved documents
            mock_article_docs = [
                Document(page_content="Apple reported strong earnings", metadata={"title": "Apple Earnings", "url": "https://example.com"})
            ]
            mock_chat_docs = [
                Document(page_content="Previous question about Apple", metadata={"role": "user"})
            ]
            
            mock_article_retriever.return_value = mock_article_docs
            mock_chat_retriever.return_value = mock_chat_docs
            mock_add_memory.return_value = None
            
            # Mock LLM
            with patch('finnews.rag.rag_chain.ChatOpenAI') as mock_llm_class:
                mock_llm = MagicMock()
                mock_llm_class.return_value = mock_llm
                
                # Mock the chain invoke
                mock_response = MagicMock()
                mock_response.content = "Based on the latest news, Apple has shown strong performance..."
                mock_llm.__ror__.return_value.invoke.return_value = mock_response
                
                # Test RAG chat
                result = rag_chat(
                    question="What is the latest news about Apple?",
                    conversation_id="test_conv",
                    user_id="test_user",
                    target_tickers=["AAPL"],
                    article_store=mock_article_store,
                    chat_store=mock_chat_store
                )
                
                # Verify result structure
                assert "conversation_id" in result
                assert "user_id" in result
                assert "question" in result
                assert "answer" in result
                assert "sources" in result
                
                # Verify retriever functions were called
                mock_article_retriever.assert_called_once()
                mock_chat_retriever.assert_called_once()
                mock_add_memory.assert_called_once()

    def test_error_handling_in_pipeline(self):
        """Test error handling throughout the pipeline."""
        # Test chunking with invalid data
        invalid_articles = [
            {"title": "Test", "body": ""},  # Empty body
            {"title": "Test 2", "body": "Valid content"},
            {"title": "Test 3"}  # Missing body
        ]
        
        docs = chunk_articles(invalid_articles)
        
        # Should only process valid articles
        assert len(docs) == 1  # Only the valid article
        assert docs[0].page_content == "Valid content"
        
        # Test chunking with very long content
        very_long_article = {
            "title": "Long Article",
            "body": "This is a very long article. " * 1000,  # Very long content
            "published_date": "2024-01-15T10:00:00",
            "relevant_tickers": ["AAPL"]
        }
        
        docs = chunk_articles([very_long_article], max_characters=200)
        
        # Should create multiple chunks
        assert len(docs) > 1
        assert all(len(doc.page_content) <= 200 for doc in docs)

    def test_memory_persistence(self):
        """Test that chat memory persists correctly."""
        from langchain.schema import Document
        
        # Mock chat store
        mock_chat_store = MagicMock()
        
        with patch('finnews.rag.rag_chain.add_chat_memory') as mock_add_memory:
            # Test adding chat memory
            from finnews.rag.retriever import add_chat_memory
            
            add_chat_memory(
                mock_chat_store,
                conversation_id="test_conv",
                user_id="test_user",
                question="What is Apple's stock price?",
                answer="Apple's stock is trading at $150."
            )
            
            # Verify add_documents was called
            mock_chat_store.add_documents.assert_called_once()
            
            # Verify the documents have correct structure
            call_args = mock_chat_store.add_documents.call_args
            documents = call_args[1]['documents']
            ids = call_args[1]['ids']
            
            assert len(documents) == 2  # User and assistant messages
            assert len(ids) == 2
            
            # Check user message
            user_doc = documents[0]
            assert user_doc.page_content == "What is Apple's stock price?"
            assert user_doc.metadata["role"] == "user"
            assert user_doc.metadata["conversation_id"] == "test_conv"
            
            # Check assistant message
            assistant_doc = documents[1]
            assert assistant_doc.page_content == "Apple's stock is trading at $150."
            assert assistant_doc.metadata["role"] == "assistant"
            assert assistant_doc.metadata["conversation_id"] == "test_conv"

    def test_ticker_filtering(self):
        """Test that ticker filtering works correctly in retrieval."""
        from langchain.schema import Document
        
        # Create documents with different tickers
        docs = [
            Document(page_content="Apple reported strong earnings", metadata={"relevant_tickers": "AAPL, MSFT"}),
            Document(page_content="Microsoft Azure growth continues", metadata={"relevant_tickers": "MSFT, GOOGL"}),
            Document(page_content="Google's AI investments", metadata={"relevant_tickers": "GOOGL, AMZN"}),
            Document(page_content="Amazon's cloud dominance", metadata={"relevant_tickers": "AMZN, AAPL"})
        ]
        
        # Test filtering for AAPL
        ranked_docs = article_chunk_reranker(docs, target_tickers=["AAPL"])
        
        # Documents with AAPL should be ranked higher
        aapl_docs = [doc for doc in ranked_docs if "AAPL" in doc.metadata["relevant_tickers"]]
        non_aapl_docs = [doc for doc in ranked_docs if "AAPL" not in doc.metadata["relevant_tickers"]]
        
        # All AAPL documents should come before non-AAPL documents
        aapl_positions = [ranked_docs.index(doc) for doc in aapl_docs]
        non_aapl_positions = [ranked_docs.index(doc) for doc in non_aapl_docs]
        
        if aapl_positions and non_aapl_positions:
            assert max(aapl_positions) < min(non_aapl_positions)

    def test_date_handling(self):
        """Test that date handling works correctly in reranking."""
        from langchain.schema import Document
        from datetime import datetime, timedelta
        
        # Create documents with different dates
        now = datetime.now()
        old_date = (now - timedelta(days=30)).isoformat()
        recent_date = (now - timedelta(days=1)).isoformat()
        
        docs = [
            Document(page_content="Old news", metadata={"published_date": old_date}),
            Document(page_content="Recent news", metadata={"published_date": recent_date}),
            Document(page_content="No date news", metadata={"published_date": ""})
        ]
        
        # Test reranking
        ranked_docs = article_chunk_reranker(docs)
        
        # Recent news should be ranked higher
        assert "Recent news" in ranked_docs[0].page_content
        assert "Old news" in ranked_docs[1].page_content
        assert "No date news" in ranked_docs[2].page_content
