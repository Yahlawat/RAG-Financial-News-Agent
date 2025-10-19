"""Tests for the FastAPI main module."""
import tempfile
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from finnews.api.main import app, ChatRequest, init_vectorstores


class TestChatRequest:
    """Test the ChatRequest model."""

    def test_chat_request_required_fields(self):
        """Test ChatRequest with required fields only."""
        request = ChatRequest(
            question="What is the latest news about AAPL?",
            user_id="test_user",
            conversation_id="test_conv"
        )
        
        assert request.question == "What is the latest news about AAPL?"
        assert request.user_id == "test_user"
        assert request.conversation_id == "test_conv"
        assert request.tickers is None
        assert request.top_k == 5
        assert request.chat_k == 3

    def test_chat_request_with_optional_fields(self):
        """Test ChatRequest with all optional fields."""
        request = ChatRequest(
            question="What is the latest news about AAPL?",
            user_id="test_user",
            conversation_id="test_conv",
            tickers=["AAPL", "MSFT"],
            top_k=10,
            chat_k=5
        )
        
        assert request.tickers == ["AAPL", "MSFT"]
        assert request.top_k == 10
        assert request.chat_k == 5

    def test_chat_request_validation(self):
        """Test ChatRequest validation."""
        # Test with missing required fields
        with pytest.raises(ValueError):
            ChatRequest(
                question="What is the latest news?",
                # Missing user_id and conversation_id
            )

    def test_chat_request_empty_tickers(self):
        """Test ChatRequest with empty tickers list."""
        request = ChatRequest(
            question="What is the latest news?",
            user_id="test_user",
            conversation_id="test_conv",
            tickers=[]
        )
        
        assert request.tickers == []


class TestInitVectorstores:
    """Test the init_vectorstores function."""

    @patch('finnews.api.main.load_vectorstore')
    @patch('finnews.api.main.settings')
    def test_init_vectorstores_success(self, mock_settings, mock_load_vectorstore):
        """Test successful initialization of vector stores."""
        # Mock settings
        mock_settings.chroma_store = "test_chroma_path"
        mock_settings.chat_memory = "test_chat_path"
        
        # Mock vector stores
        mock_article_store = MagicMock()
        mock_chat_store = MagicMock()
        mock_load_vectorstore.side_effect = [mock_article_store, mock_chat_store]
        
        # Call the function
        init_vectorstores()
        
        # Verify load_vectorstore was called with correct paths
        assert mock_load_vectorstore.call_count == 2
        mock_load_vectorstore.assert_any_call("test_chroma_path")
        mock_load_vectorstore.assert_any_call("test_chat_path")
        
        # Verify global variables are set
        from finnews.api.main import article_store, chat_store
        assert article_store == mock_article_store
        assert chat_store == mock_chat_store

    @patch('finnews.api.main.load_vectorstore')
    @patch('finnews.api.main.settings')
    def test_init_vectorstores_exception(self, mock_settings, mock_load_vectorstore):
        """Test initialization with exception."""
        # Mock settings
        mock_settings.chroma_store = "test_chroma_path"
        mock_settings.chat_memory = "test_chat_path"
        
        # Mock load_vectorstore to raise exception
        mock_load_vectorstore.side_effect = Exception("Vector store error")
        
        # Should raise exception
        with pytest.raises(Exception, match="Vector store error"):
            init_vectorstores()


class TestChatEndpoint:
    """Test the /chat endpoint."""

    @patch('finnews.api.main.rag_chat')
    @patch('finnews.api.main.article_store', MagicMock())
    @patch('finnews.api.main.chat_store', MagicMock())
    def test_chat_endpoint_success(self, mock_rag_chat):
        """Test successful chat endpoint request."""
        # Mock RAG chat response
        mock_response = {
            "conversation_id": "test_conv",
            "user_id": "test_user",
            "question": "What is the latest news about AAPL?",
            "answer": "Based on the latest news, AAPL has shown strong performance...",
            "sources": [
                {
                    "title": "Apple Reports Strong Q4 Earnings",
                    "url": "https://example.com/apple-earnings",
                    "published_date": "2024-01-01"
                }
            ]
        }
        mock_rag_chat.return_value = mock_response
        
        # Create test client
        client = TestClient(app)
        
        # Make request
        response = client.post("/chat", json={
            "question": "What is the latest news about AAPL?",
            "user_id": "test_user",
            "conversation_id": "test_conv"
        })
        
        # Verify response
        assert response.status_code == 200
        assert response.json() == mock_response
        
        # Verify RAG chat was called correctly
        mock_rag_chat.assert_called_once()
        call_args = mock_rag_chat.call_args
        assert call_args[1]['question'] == "What is the latest news about AAPL?"
        assert call_args[1]['user_id'] == "test_user"
        assert call_args[1]['conversation_id'] == "test_conv"

    @patch('finnews.api.main.rag_chat')
    @patch('finnews.api.main.article_store', MagicMock())
    @patch('finnews.api.main.chat_store', MagicMock())
    def test_chat_endpoint_with_tickers(self, mock_rag_chat):
        """Test chat endpoint with tickers filter."""
        # Mock RAG chat response
        mock_response = {
            "conversation_id": "test_conv",
            "user_id": "test_user",
            "question": "What is the latest news about AAPL and MSFT?",
            "answer": "Based on the latest news...",
            "sources": []
        }
        mock_rag_chat.return_value = mock_response
        
        # Create test client
        client = TestClient(app)
        
        # Make request with tickers
        response = client.post("/chat", json={
            "question": "What is the latest news about AAPL and MSFT?",
            "user_id": "test_user",
            "conversation_id": "test_conv",
            "tickers": ["AAPL", "MSFT"],
            "top_k": 10,
            "chat_k": 5
        })
        
        # Verify response
        assert response.status_code == 200
        
        # Verify RAG chat was called with tickers
        call_args = mock_rag_chat.call_args
        assert call_args[1]['target_tickers'] == ["AAPL", "MSFT"]
        assert call_args[1]['top_k'] == 10
        assert call_args[1]['chat_k'] == 5

    @patch('finnews.api.main.rag_chat')
    @patch('finnews.api.main.article_store', MagicMock())
    @patch('finnews.api.main.chat_store', MagicMock())
    def test_chat_endpoint_rag_exception(self, mock_rag_chat):
        """Test chat endpoint when RAG chat raises exception."""
        # Mock RAG chat to raise exception
        mock_rag_chat.side_effect = Exception("RAG processing failed")
        
        # Create test client
        client = TestClient(app)
        
        # Make request
        response = client.post("/chat", json={
            "question": "What is the latest news about AAPL?",
            "user_id": "test_user",
            "conversation_id": "test_conv"
        })
        
        # Verify error response
        assert response.status_code == 500
        assert response.json() == {"detail": "Internal server error"}

    def test_chat_endpoint_invalid_request(self):
        """Test chat endpoint with invalid request data."""
        client = TestClient(app)
        
        # Test with missing required fields
        response = client.post("/chat", json={
            "question": "What is the latest news?",
            # Missing user_id and conversation_id
        })
        
        assert response.status_code == 422  # Validation error

    def test_chat_endpoint_invalid_json(self):
        """Test chat endpoint with invalid JSON."""
        client = TestClient(app)
        
        # Test with invalid JSON
        response = client.post("/chat", data="invalid json")
        
        assert response.status_code == 422

    @patch('finnews.api.main.rag_chat')
    @patch('finnews.api.main.article_store', None)  # No article store
    @patch('finnews.api.main.chat_store', None)  # No chat store
    def test_chat_endpoint_no_vector_stores(self, mock_rag_chat):
        """Test chat endpoint when vector stores are not initialized."""
        # Mock RAG chat response
        mock_response = {
            "conversation_id": "test_conv",
            "user_id": "test_user",
            "question": "What is the latest news?",
            "answer": "Test answer",
            "sources": []
        }
        mock_rag_chat.return_value = mock_response
        
        # Mock load_vectorstore to return mock stores
        with patch('finnews.api.main.load_vectorstore') as mock_load_vectorstore:
            mock_load_vectorstore.return_value = MagicMock()
            
            client = TestClient(app)
            
            # Make request
            response = client.post("/chat", json={
                "question": "What is the latest news?",
                "user_id": "test_user",
                "conversation_id": "test_conv"
            })
            
            # Verify response
            assert response.status_code == 200
            assert response.json() == mock_response
            
            # Verify load_vectorstore was called
            assert mock_load_vectorstore.call_count == 2


class TestAppStartup:
    """Test app startup behavior."""

    def test_app_startup_event(self):
        """Test that startup event is registered."""
        # Check that the startup event is registered
        startup_events = [event for event in app.router.on_startup]
        assert len(startup_events) > 0
        
        # Check that init_vectorstores is one of the startup events
        startup_functions = [event.func for event in startup_events]
        assert init_vectorstores in startup_functions

    def test_app_has_chat_endpoint(self):
        """Test that app has the chat endpoint."""
        # Get all routes
        routes = [route.path for route in app.routes]
        assert "/chat" in routes

    def test_app_has_cors_middleware(self):
        """Test that app has CORS middleware if configured."""
        # This test would need to be updated if CORS is added
        # For now, just verify the app exists
        assert app is not None


class TestRunFunction:
    """Test the run function."""

    @patch('finnews.api.main.uvicorn.run')
    @patch('finnews.api.main.settings')
    def test_run_function_default_params(self, mock_settings, mock_uvicorn_run):
        """Test run function with default parameters."""
        from finnews.api.main import run
        
        # Mock settings
        mock_settings.api_host = "127.0.0.1"
        mock_settings.api_port = 8000
        
        # Call run function
        run()
        
        # Verify uvicorn.run was called with correct parameters
        mock_uvicorn_run.assert_called_once_with(app, host="127.0.0.1", port=8000)

    @patch('finnews.api.main.uvicorn.run')
    def test_run_function_custom_params(self, mock_uvicorn_run):
        """Test run function with custom parameters."""
        from finnews.api.main import run
        
        # Call run function with custom parameters
        run(host="0.0.0.0", port=9000)
        
        # Verify uvicorn.run was called with custom parameters
        mock_uvicorn_run.assert_called_once_with(app, host="0.0.0.0", port=9000)
