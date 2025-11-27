"""Critical tests for the FastAPI API endpoints.

NOTE: API endpoint tests are currently skipped due to a known compatibility
issue between httpx 0.28+ and starlette 0.36.x. To enable these tests:
- Downgrade httpx: pip install "httpx<0.28"
- Or upgrade starlette: pip install "starlette>=0.37.0"

See: https://github.com/encode/starlette/issues/2438
"""

from unittest.mock import MagicMock, patch

import pytest

from finnews.api.main import ChatRequest, app

# Mark to skip API tests if httpx/starlette incompatibility detected
skip_api_tests = False
try:
    from fastapi.testclient import TestClient
    # Try to create a test client to check compatibility
    _test_client = TestClient(app)
except TypeError as e:
    if "unexpected keyword argument 'app'" in str(e):
        skip_api_tests = True
        pytestmark = pytest.mark.skip(reason="httpx/starlette version incompatibility - see module docstring")


# ============================================================================
# ChatRequest Model Tests
# ============================================================================


class TestChatRequest:
    """Test the ChatRequest Pydantic model."""

    def test_required_fields_only(self):
        """Test ChatRequest with only required fields."""
        request = ChatRequest(
            question="What is the latest news about AAPL?",
            user_id="test_user",
            conversation_id="test_conv",
        )

        assert request.question == "What is the latest news about AAPL?"
        assert request.user_id == "test_user"
        assert request.conversation_id == "test_conv"
        assert request.tickers is None
        assert request.top_k == 5
        assert request.chat_k == 3

    def test_all_fields(self):
        """Test ChatRequest with all fields."""
        request = ChatRequest(
            question="What is the latest news?",
            user_id="test_user",
            conversation_id="test_conv",
            tickers=["AAPL", "MSFT"],
            top_k=10,
            chat_k=5,
        )

        assert request.tickers == ["AAPL", "MSFT"]
        assert request.top_k == 10
        assert request.chat_k == 5


# ============================================================================
# API Endpoint Tests
# ============================================================================


class TestHealthEndpoint:
    """Test health check endpoint."""

    @patch("finnews.api.main.article_store")
    @patch("finnews.api.main.chat_store")
    def test_health_check_healthy(self, mock_chat_store, mock_article_store):
        """Test health check when stores are loaded."""
        # Mock stores as loaded
        mock_article_store.__bool__.return_value = True
        mock_chat_store.__bool__.return_value = True

        client = TestClient(app)
        response = client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"

    def test_health_check_structure(self):
        """Test health check response structure."""
        client = TestClient(app)
        response = client.get("/health")

        assert response.status_code == 200
        data = response.json()

        # Should have expected fields
        assert "status" in data
        assert "article_store_loaded" in data
        assert "chat_store_loaded" in data


class TestChatEndpoint:
    """Test chat endpoint - critical for main application functionality."""

    @patch("finnews.api.main.article_store", MagicMock())
    @patch("finnews.api.main.chat_store", MagicMock())
    @patch("finnews.api.main.rag_chat")
    @patch("finnews.api.main.get_portfolio_tickers")
    def test_chat_endpoint_success(self, mock_get_tickers, mock_rag_chat):
        """Test successful chat request."""
        # Mock portfolio tickers
        mock_get_tickers.return_value = ["AAPL", "MSFT"]

        # Mock RAG response
        mock_rag_chat.return_value = {
            "conversation_id": "test_conv",
            "user_id": "test_user",
            "question": "What about Apple?",
            "answer": "Apple reported strong earnings.",
            "sources": [
                {
                    "title": "Apple Earnings",
                    "url": "https://example.com/apple",
                    "published_date": "2024-01-01",
                }
            ],
        }

        client = TestClient(app)
        response = client.post(
            "/chat",
            json={
                "question": "What about Apple?",
                "user_id": "test_user",
                "conversation_id": "test_conv",
            },
        )

        assert response.status_code == 200
        data = response.json()

        assert data["question"] == "What about Apple?"
        assert data["answer"] == "Apple reported strong earnings."
        assert len(data["sources"]) == 1

    @patch("finnews.api.main.article_store", MagicMock())
    @patch("finnews.api.main.chat_store", MagicMock())
    @patch("finnews.api.main.rag_chat")
    @patch("finnews.api.main.get_portfolio_tickers")
    def test_chat_endpoint_with_explicit_tickers(self, mock_get_tickers, mock_rag_chat):
        """Test chat with explicit ticker filter."""
        mock_rag_chat.return_value = {
            "conversation_id": "test_conv",
            "user_id": "test_user",
            "question": "What about Tesla?",
            "answer": "Tesla news here.",
            "sources": [],
        }

        client = TestClient(app)
        response = client.post(
            "/chat",
            json={
                "question": "What about Tesla?",
                "user_id": "test_user",
                "conversation_id": "test_conv",
                "tickers": ["TSLA"],
            },
        )

        assert response.status_code == 200

        # Should not load portfolio tickers when explicitly provided
        mock_get_tickers.assert_not_called()

        # Verify tickers were passed to RAG
        call_args = mock_rag_chat.call_args[1]
        assert call_args["target_tickers"] == ["TSLA"]

    @patch("finnews.api.main.article_store", MagicMock())
    @patch("finnews.api.main.chat_store", MagicMock())
    @patch("finnews.api.main.rag_chat")
    @patch("finnews.api.main.get_portfolio_tickers")
    def test_chat_endpoint_auto_load_portfolio(self, mock_get_tickers, mock_rag_chat):
        """Test that portfolio tickers are auto-loaded when not provided."""
        mock_get_tickers.return_value = ["AAPL", "MSFT"]

        mock_rag_chat.return_value = {
            "conversation_id": "test_conv",
            "user_id": "test_user",
            "question": "Latest news?",
            "answer": "News here.",
            "sources": [],
        }

        client = TestClient(app)
        response = client.post(
            "/chat",
            json={
                "question": "Latest news?",
                "user_id": "test_user",
                "conversation_id": "test_conv",
                # No tickers provided
            },
        )

        assert response.status_code == 200

        # Should load portfolio tickers
        mock_get_tickers.assert_called_once_with("test_user")

        # Should pass portfolio tickers to RAG
        call_args = mock_rag_chat.call_args[1]
        assert call_args["target_tickers"] == ["AAPL", "MSFT"]

    @patch("finnews.api.main.article_store", MagicMock())
    @patch("finnews.api.main.chat_store", MagicMock())
    @patch("finnews.api.main.rag_chat")
    def test_chat_endpoint_rag_failure(self, mock_rag_chat):
        """Test handling of RAG pipeline failures."""
        # Mock RAG failure
        mock_rag_chat.side_effect = Exception("RAG pipeline error")

        client = TestClient(app)
        response = client.post(
            "/chat",
            json={
                "question": "Test question",
                "user_id": "test_user",
                "conversation_id": "test_conv",
            },
        )

        # Should return 500 error
        assert response.status_code == 500
        data = response.json()
        assert "detail" in data

    def test_chat_endpoint_missing_required_fields(self):
        """Test validation of required fields."""
        client = TestClient(app)
        # Missing question
        response = client.post(
            "/chat",
            json={
                "user_id": "test_user",
                "conversation_id": "test_conv",
            },
        )

        # Should return validation error
        assert response.status_code == 422

    @patch("finnews.api.main.article_store", MagicMock())
    @patch("finnews.api.main.chat_store", MagicMock())
    @patch("finnews.api.main.rag_chat")
    @patch("finnews.api.main.get_portfolio_tickers")
    def test_chat_endpoint_custom_parameters(self, mock_get_tickers, mock_rag_chat):
        """Test chat with custom top_k and chat_k parameters."""
        mock_get_tickers.return_value = []

        mock_rag_chat.return_value = {
            "conversation_id": "test_conv",
            "user_id": "test_user",
            "question": "Test",
            "answer": "Answer",
            "sources": [],
        }

        client = TestClient(app)
        response = client.post(
            "/chat",
            json={
                "question": "Test",
                "user_id": "test_user",
                "conversation_id": "test_conv",
                "top_k": 10,
                "chat_k": 5,
            },
        )

        assert response.status_code == 200

        # Verify custom parameters were passed
        call_args = mock_rag_chat.call_args[1]
        assert call_args["top_k"] == 10
        assert call_args["chat_k"] == 5

    @patch("finnews.api.main.article_store", MagicMock())
    @patch("finnews.api.main.chat_store", MagicMock())
    @patch("finnews.api.main.rag_chat")
    @patch("finnews.api.main.get_portfolio_tickers")
    def test_chat_endpoint_empty_portfolio(self, mock_get_tickers, mock_rag_chat):
        """Test chat when user has no portfolio tickers."""
        # User has no tickers
        mock_get_tickers.return_value = []

        mock_rag_chat.return_value = {
            "conversation_id": "test_conv",
            "user_id": "test_user",
            "question": "General news?",
            "answer": "General market news.",
            "sources": [],
        }

        client = TestClient(app)
        response = client.post(
            "/chat",
            json={
                "question": "General news?",
                "user_id": "test_user",
                "conversation_id": "test_conv",
            },
        )

        assert response.status_code == 200

        # Should pass empty ticker list (no filtering)
        call_args = mock_rag_chat.call_args[1]
        assert call_args["target_tickers"] == []
