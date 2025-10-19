"""Comprehensive tests for the retriever module."""
import math
import tempfile
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from finnews.rag.retriever import (
    load_vectorstore,
    article_chunk_reranker,
    article_chunk_retriever,
    add_chat_memory,
    retrieve_chat_memory,
    get_full_chat_history
)


class TestLoadVectorstore:
    """Test the load_vectorstore function."""

    @patch('finnews.rag.retriever.HuggingFaceEmbeddings')
    @patch('finnews.rag.retriever.Chroma')
    def test_load_vectorstore_success(self, mock_chroma, mock_embeddings):
        """Test successful loading of vectorstore."""
        # Mock the embedding model
        mock_embedding_model = MagicMock()
        mock_embeddings.return_value = mock_embedding_model
        
        # Mock the Chroma vectorstore
        mock_vectorstore = MagicMock()
        mock_chroma.return_value = mock_vectorstore
        
        with tempfile.TemporaryDirectory() as temp_dir:
            result = load_vectorstore(temp_dir, "test-model")
            
            # Verify embeddings were created
            mock_embeddings.assert_called_once_with(model_name="test-model")
            
            # Verify Chroma was initialized
            mock_chroma.assert_called_once_with(
                persist_directory=temp_dir,
                embedding_function=mock_embedding_model
            )
            
            assert result == mock_vectorstore

    @patch('finnews.rag.retriever.HuggingFaceEmbeddings')
    @patch('finnews.rag.retriever.Chroma')
    def test_load_vectorstore_default_model(self, mock_chroma, mock_embeddings):
        """Test loading vectorstore with default model."""
        mock_embeddings.return_value = MagicMock()
        mock_chroma.return_value = MagicMock()
        
        with tempfile.TemporaryDirectory() as temp_dir:
            load_vectorstore(temp_dir)
            mock_embeddings.assert_called_once_with(model_name="BAAI/bge-base-en-v1.5")

    @patch('finnews.rag.retriever.HuggingFaceEmbeddings')
    @patch('finnews.rag.retriever.Chroma')
    def test_load_vectorstore_creates_directory(self, mock_chroma, mock_embeddings):
        """Test that load_vectorstore creates the directory if it doesn't exist."""
        mock_embeddings.return_value = MagicMock()
        mock_chroma.return_value = MagicMock()
        
        with tempfile.TemporaryDirectory() as temp_dir:
            nonexistent_dir = Path(temp_dir) / "nonexistent"
            load_vectorstore(str(nonexistent_dir))
            
            # Directory should be created
            assert nonexistent_dir.exists()


class TestArticleChunkReranker:
    """Test the article_chunk_reranker function."""

    def test_reranker_basic_functionality(self):
        """Test basic reranking functionality."""
        from langchain.schema import Document
        
        # Create test documents
        docs = [
            Document(page_content="Short content", metadata={"published_date": "2024-01-01T00:00:00"}),
            Document(page_content="This is a much longer piece of content that should score better", 
                    metadata={"published_date": "2024-01-01T00:00:00"})
        ]
        
        result = article_chunk_reranker(docs)
        
        # Longer content should be ranked higher
        assert len(result) == 2
        assert result[0].page_content == "This is a much longer piece of content that should score better"

    def test_reranker_recency_boost(self):
        """Test that recent articles get higher scores."""
        from langchain.schema import Document
        
        now = datetime.now()
        old_date = (now - timedelta(days=30)).isoformat()
        recent_date = (now - timedelta(days=1)).isoformat()
        
        docs = [
            Document(page_content="Old content", metadata={"published_date": old_date}),
            Document(page_content="Recent content", metadata={"published_date": recent_date})
        ]
        
        result = article_chunk_reranker(docs)
        
        # Recent content should be ranked higher
        assert result[0].page_content == "Recent content"

    def test_reranker_ticker_matching(self):
        """Test that documents with matching tickers get higher scores."""
        from langchain.schema import Document
        
        docs = [
            Document(page_content="Content about AAPL", metadata={"relevant_tickers": "MSFT, GOOGL"}),
            Document(page_content="Content about MSFT", metadata={"relevant_tickers": "AAPL, MSFT"})
        ]
        
        result = article_chunk_reranker(docs, target_tickers=["MSFT"])
        
        # Document with MSFT ticker should be ranked higher
        assert result[0].page_content == "Content about MSFT"

    def test_reranker_short_chunk_penalty(self):
        """Test that very short chunks get penalized."""
        from langchain.schema import Document
        
        docs = [
            Document(page_content="Short", metadata={"published_date": "2024-01-01T00:00:00"}),
            Document(page_content="This is a much longer piece of content that should score better than the short one", metadata={"published_date": "2024-01-01T00:00:00"})
        ]
        
        result = article_chunk_reranker(docs)
        
        # Longer content should be ranked higher despite same date
        assert result[0].page_content == "This is a much longer piece of content that should score better than the short one"

    def test_reranker_invalid_date_handling(self):
        """Test handling of invalid publication dates."""
        from langchain.schema import Document
        
        docs = [
            Document(page_content="Content with invalid date", metadata={"published_date": "invalid-date"}),
            Document(page_content="Content with valid date", metadata={"published_date": "2024-01-01T00:00:00"})
        ]
        
        # Should not raise exception
        result = article_chunk_reranker(docs)
        assert len(result) == 2

    def test_reranker_empty_tickers(self):
        """Test reranking with empty ticker list."""
        from langchain.schema import Document
        
        docs = [
            Document(page_content="Content 1", metadata={"relevant_tickers": "AAPL"}),
            Document(page_content="Content 2", metadata={"relevant_tickers": "MSFT"})
        ]
        
        result = article_chunk_reranker(docs, target_tickers=[])
        
        # Should not crash and return documents
        assert len(result) == 2

    def test_reranker_none_tickers(self):
        """Test reranking with None ticker list."""
        from langchain.schema import Document
        
        docs = [
            Document(page_content="Content 1", metadata={"relevant_tickers": "AAPL"}),
            Document(page_content="Content 2", metadata={"relevant_tickers": "MSFT"})
        ]
        
        result = article_chunk_reranker(docs, target_tickers=None)
        
        # Should not crash and return documents
        assert len(result) == 2


class TestArticleChunkRetriever:
    """Test the article_chunk_retriever function."""

    def test_retriever_basic_functionality(self):
        """Test basic retrieval functionality."""
        from langchain.schema import Document
        
        # Mock vectorstore
        mock_vectorstore = MagicMock()
        mock_retriever = MagicMock()
        mock_vectorstore.as_retriever.return_value = mock_retriever
        
        # Mock retrieved documents
        mock_docs = [
            Document(page_content="Test content 1", metadata={"title": "Test 1"}),
            Document(page_content="Test content 2", metadata={"title": "Test 2"})
        ]
        mock_retriever.invoke.return_value = mock_docs
        
        result = article_chunk_retriever(mock_vectorstore, "test query", top_n=2)
        
        # Verify retriever was called correctly
        mock_vectorstore.as_retriever.assert_called_once_with(search_kwargs={"k": 15})
        mock_retriever.invoke.assert_called_once_with("test query")
        
        # Should return reranked documents
        assert len(result) <= 2

    def test_retriever_with_tickers(self):
        """Test retrieval with ticker filtering."""
        from langchain.schema import Document
        
        # Mock vectorstore
        mock_vectorstore = MagicMock()
        mock_retriever = MagicMock()
        mock_vectorstore.as_retriever.return_value = mock_retriever
        
        # Mock retrieved documents
        mock_docs = [
            Document(page_content="AAPL content", metadata={"relevant_tickers": "AAPL, MSFT"}),
            Document(page_content="MSFT content", metadata={"relevant_tickers": "MSFT, GOOGL"})
        ]
        mock_retriever.invoke.return_value = mock_docs
        
        result = article_chunk_retriever(
            mock_vectorstore, 
            "test query", 
            target_tickers=["AAPL"], 
            top_n=1
        )
        
        # Should return documents with AAPL ticker
        assert len(result) == 1
        assert "AAPL" in result[0].metadata["relevant_tickers"]

    def test_retriever_custom_top_n(self):
        """Test retrieval with custom top_n parameter."""
        from langchain.schema import Document
        
        # Mock vectorstore
        mock_vectorstore = MagicMock()
        mock_retriever = MagicMock()
        mock_vectorstore.as_retriever.return_value = mock_retriever
        
        # Mock retrieved documents
        mock_docs = [Document(f"Content {i}", {"title": f"Test {i}"}) for i in range(10)]
        mock_retriever.invoke.return_value = mock_docs
        
        result = article_chunk_retriever(mock_vectorstore, "test query", top_n=3)
        
        # Should return only top 3 documents
        assert len(result) == 3


class TestAddChatMemory:
    """Test the add_chat_memory function."""

    def test_add_chat_memory_success(self):
        """Test successful addition of chat memory."""
        from langchain.schema import Document
        
        # Mock chat store
        mock_chat_store = MagicMock()
        
        add_chat_memory(
            mock_chat_store,
            conversation_id="test_conv",
            user_id="test_user",
            question="Test question?",
            answer="Test answer."
        )
        
        # Verify add_documents was called
        mock_chat_store.add_documents.assert_called_once()
        
        # Check that two documents were added (user and assistant)
        call_args = mock_chat_store.add_documents.call_args
        documents = call_args[1]['documents']
        ids = call_args[1]['ids']
        
        assert len(documents) == 2
        assert len(ids) == 2
        
        # Check document content
        user_doc = documents[0]
        assistant_doc = documents[1]
        
        assert user_doc.page_content == "Test question?"
        assert assistant_doc.page_content == "Test answer."
        
        # Check metadata
        assert user_doc.metadata["role"] == "user"
        assert assistant_doc.metadata["role"] == "assistant"
        assert user_doc.metadata["conversation_id"] == "test_conv"
        assert assistant_doc.metadata["conversation_id"] == "test_conv"

    def test_add_chat_memory_with_non_string_answer(self):
        """Test adding chat memory with non-string answer."""
        from langchain.schema import Document
        
        # Mock chat store
        mock_chat_store = MagicMock()
        
        # Create a mock object with content attribute
        class MockAnswer:
            def __init__(self, content):
                self.content = content
        
        mock_answer = MockAnswer("Test answer content")
        
        add_chat_memory(
            mock_chat_store,
            conversation_id="test_conv",
            user_id="test_user",
            question="Test question?",
            answer=mock_answer
        )
        
        # Verify add_documents was called
        mock_chat_store.add_documents.assert_called_once()
        
        # Check that the answer was converted to string
        call_args = mock_chat_store.add_documents.call_args
        documents = call_args[1]['documents']
        assistant_doc = documents[1]
        
        assert assistant_doc.page_content == "Test answer content"

    def test_add_chat_memory_with_string_answer(self):
        """Test adding chat memory with string answer."""
        from langchain.schema import Document
        
        # Mock chat store
        mock_chat_store = MagicMock()
        
        add_chat_memory(
            mock_chat_store,
            conversation_id="test_conv",
            user_id="test_user",
            question="Test question?",
            answer="Test answer string"
        )
        
        # Verify add_documents was called
        mock_chat_store.add_documents.assert_called_once()
        
        # Check that the answer was stored as string
        call_args = mock_chat_store.add_documents.call_args
        documents = call_args[1]['documents']
        assistant_doc = documents[1]
        
        assert assistant_doc.page_content == "Test answer string"


class TestRetrieveChatMemory:
    """Test the retrieve_chat_memory function."""

    def test_retrieve_chat_memory_success(self):
        """Test successful retrieval of chat memory."""
        from langchain.schema import Document
        
        # Mock chat store
        mock_chat_store = MagicMock()
        mock_retriever = MagicMock()
        mock_chat_store.as_retriever.return_value = mock_retriever
        
        # Mock retrieved documents
        mock_docs = [
            Document(page_content="Previous question", metadata={"role": "user"}),
            Document(page_content="Previous answer", metadata={"role": "assistant"})
        ]
        mock_retriever.invoke.return_value = mock_docs
        
        result = retrieve_chat_memory(
            mock_chat_store,
            conversation_id="test_conv",
            query="current question",
            k=2
        )
        
        # Verify retriever was called correctly
        mock_chat_store.as_retriever.assert_called_once_with(
            search_kwargs={"k": 2, "filter": {"conversation_id": "test_conv"}}
        )
        mock_retriever.invoke.assert_called_once_with("current question")
        
        # Should return the mock documents
        assert result == mock_docs

    def test_retrieve_chat_memory_default_k(self):
        """Test retrieval with default k value."""
        from langchain.schema import Document
        
        # Mock chat store
        mock_chat_store = MagicMock()
        mock_retriever = MagicMock()
        mock_chat_store.as_retriever.return_value = mock_retriever
        mock_retriever.invoke.return_value = []
        
        retrieve_chat_memory(
            mock_chat_store,
            conversation_id="test_conv",
            query="current question"
        )
        
        # Verify default k=3 was used
        mock_chat_store.as_retriever.assert_called_once_with(
            search_kwargs={"k": 3, "filter": {"conversation_id": "test_conv"}}
        )


class TestGetFullChatHistory:
    """Test the get_full_chat_history function."""

    def test_get_full_chat_history_with_user_id(self):
        """Test getting full chat history with user_id filter."""
        from langchain.schema import Document
        
        # Mock chat store
        mock_chat_store = MagicMock()
        mock_chat_store.get.return_value = {
            "documents": ["Question 1", "Answer 1", "Question 2", "Answer 2"],
            "metadatas": [
                {"timestamp": "2024-01-01T10:00:00", "role": "user"},
                {"timestamp": "2024-01-01T10:01:00", "role": "assistant"},
                {"timestamp": "2024-01-01T10:02:00", "role": "user"},
                {"timestamp": "2024-01-01T10:03:00", "role": "assistant"}
            ]
        }
        
        result = get_full_chat_history(
            mock_chat_store,
            conversation_id="test_conv",
            user_id="test_user"
        )
        
        # Verify get was called with correct filter
        expected_filter = {
            "$and": [
                {"conversation_id": "test_conv"},
                {"user_id": "test_user"}
            ]
        }
        mock_chat_store.get.assert_called_once_with(
            where=expected_filter,
            include=["documents", "metadatas"]
        )
        
        # Should return documents sorted by timestamp
        assert len(result) == 4
        assert result[0].page_content == "Question 1"
        assert result[1].page_content == "Answer 1"

    def test_get_full_chat_history_without_user_id(self):
        """Test getting full chat history without user_id filter."""
        from langchain.schema import Document
        
        # Mock chat store
        mock_chat_store = MagicMock()
        mock_chat_store.get.return_value = {
            "documents": ["Question 1", "Answer 1"],
            "metadatas": [
                {"timestamp": "2024-01-01T10:00:00", "role": "user"},
                {"timestamp": "2024-01-01T10:01:00", "role": "assistant"}
            ]
        }
        
        result = get_full_chat_history(
            mock_chat_store,
            conversation_id="test_conv"
        )
        
        # Verify get was called with conversation_id only
        expected_filter = {"conversation_id": "test_conv"}
        mock_chat_store.get.assert_called_once_with(
            where=expected_filter,
            include=["documents", "metadatas"]
        )
        
        # Should return documents
        assert len(result) == 2

    def test_get_full_chat_history_empty_result(self):
        """Test getting full chat history when no results found."""
        from langchain.schema import Document
        
        # Mock chat store
        mock_chat_store = MagicMock()
        mock_chat_store.get.return_value = {
            "documents": [],
            "metadatas": []
        }
        
        result = get_full_chat_history(
            mock_chat_store,
            conversation_id="test_conv"
        )
        
        # Should return empty list
        assert result == []
