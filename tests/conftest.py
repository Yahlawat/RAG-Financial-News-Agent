"""Shared pytest fixtures for all tests."""
import tempfile
from pathlib import Path
from unittest.mock import MagicMock
from datetime import datetime

import pytest


# ============================================================================
# Mock Response Fixtures
# ============================================================================

@pytest.fixture
def mock_api_response():
    """Standard mock API response for chat endpoints."""
    mock = MagicMock()
    mock.json.return_value = {
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
    mock.raise_for_status.return_value = None
    mock.status_code = 200
    return mock


@pytest.fixture
def mock_api_response_empty_sources():
    """Mock API response with no sources."""
    mock = MagicMock()
    mock.json.return_value = {
        "conversation_id": "test_conv",
        "user_id": "test_user",
        "question": "What is the latest news?",
        "answer": "Test answer",
        "sources": []
    }
    mock.raise_for_status.return_value = None
    mock.status_code = 200
    return mock


# ============================================================================
# Temporary Directory Fixtures
# ============================================================================

@pytest.fixture
def temp_dir():
    """Provide a temporary directory for tests."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def temp_file():
    """Provide a temporary file for tests."""
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.jsonl') as f:
        yield Path(f.name)
    Path(f.name).unlink(missing_ok=True)


# ============================================================================
# Mock Data Fixtures
# ============================================================================

@pytest.fixture
def sample_article():
    """Sample article data for testing."""
    return {
        "title": "Apple Reports Strong Q4 Earnings",
        "url": "https://example.com/apple-earnings",
        "body": "Apple Inc. reported strong Q4 earnings today, beating analyst expectations.",
        "published_date": "2024-01-01",
        "tickers": ["AAPL"],
        "source": "FinViz"
    }


@pytest.fixture
def sample_articles():
    """Multiple sample articles for testing."""
    return [
        {
            "title": "Apple Reports Strong Q4 Earnings",
            "url": "https://example.com/apple-earnings",
            "body": "Apple Inc. reported strong Q4 earnings today.",
            "published_date": "2024-01-01",
            "tickers": ["AAPL"],
            "source": "FinViz"
        },
        {
            "title": "Microsoft Announces New Product",
            "url": "https://example.com/msft-product",
            "body": "Microsoft unveiled a new product line today.",
            "published_date": "2024-01-02",
            "tickers": ["MSFT"],
            "source": "FinViz"
        }
    ]


@pytest.fixture
def sample_chunk():
    """Sample article chunk with metadata."""
    return {
        "chunk_text": "Apple Inc. reported strong Q4 earnings today.",
        "chunk_index": 0,
        "title": "Apple Reports Strong Q4 Earnings",
        "url": "https://example.com/apple-earnings",
        "published_date": "2024-01-01",
        "tickers": ["AAPL"]
    }


# ============================================================================
# Mock Streamlit Fixtures
# ============================================================================

@pytest.fixture
def mock_streamlit():
    """Mock streamlit components."""
    mock_st = MagicMock()
    mock_st.title.return_value = None
    mock_st.text_input.return_value = "test_input"
    mock_st.button.return_value = False
    mock_st.subheader.return_value = None
    mock_st.write.return_value = None
    mock_st.markdown.return_value = None
    mock_st.error.return_value = None
    mock_st.success.return_value = None
    mock_st.info.return_value = None
    return mock_st


# ============================================================================
# Mock Vector Store Fixtures
# ============================================================================

@pytest.fixture
def mock_vectorstore():
    """Mock Chroma vector store."""
    mock = MagicMock()
    mock.as_retriever.return_value = MagicMock()
    return mock


@pytest.fixture
def mock_article_store():
    """Mock article vector store with sample documents."""
    mock = MagicMock()
    mock._collection.get.return_value = {
        "ids": ["1", "2"],
        "documents": ["Doc 1", "Doc 2"],
        "metadatas": [
            {"title": "Test 1", "url": "http://test1.com", "published_date": "2024-01-01"},
            {"title": "Test 2", "url": "http://test2.com", "published_date": "2024-01-02"}
        ]
    }
    return mock


@pytest.fixture
def mock_chat_store():
    """Mock chat memory vector store."""
    mock = MagicMock()
    mock._collection.get.return_value = {
        "ids": [],
        "documents": [],
        "metadatas": []
    }
    return mock


# ============================================================================
# Settings Fixtures
# ============================================================================

@pytest.fixture
def mock_settings(temp_dir):
    """Mock settings with temporary paths."""
    mock = MagicMock()
    mock.CHROMA_DIR = temp_dir / "chroma_store"
    mock.CHAT_MEMORY_DIR = temp_dir / "chat_memory"
    mock.PROCESSED_CHUNKS_DIR = temp_dir / "processed_chunks"
    mock.TICKERS_DIR = temp_dir / "tickers"
    mock.USER_PROFILES_DIR = temp_dir / "user_profiles"
    mock.RAW_NEWS_PATH = temp_dir / "raw_news" / "articles.jsonl"
    mock.PROCESSED_CHUNKS_PATH = temp_dir / "processed_chunks" / "chunked_articles.jsonl"
    mock.CHAT_SESSIONS_FILE = temp_dir / "chat_sessions" / "chat_sessions.json"
    mock.SCRAPE_METADATA_FILE = temp_dir / "scrape_metadata.json"
    mock.API_HOST = "127.0.0.1"
    mock.API_PORT = 8000
    mock.STREAMLIT_PORT = 8501
    mock.OPENAI_API_KEY = "test-key"
    mock.LLM_MODEL = "gpt-4o-mini"
    mock.EMBEDDING_MODEL = "BAAI/bge-base-en-v1.5"
    return mock
