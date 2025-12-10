"""Tests for the common config module."""

import os
from pathlib import Path
from unittest.mock import patch

import pytest
from pydantic import ValidationError

from finnews.common.config import Settings


class TestSettings:
    """Test the Settings configuration class."""

    def test_default_values(self):
        """Test that default values are set correctly."""
        with patch.dict(os.environ, {}, clear=True):
            settings = Settings()

            # Test API settings
            assert settings.OPENAI_API_KEY is None
            assert settings.LLM_MODEL == "gpt-4o-mini"

            # Test network settings
            assert settings.API_HOST == "127.0.0.1"
            assert settings.API_PORT == 8000
            assert settings.STREAMLIT_PORT == 8501

        # Test path settings
        assert isinstance(settings.CHROMA_DIR, Path)
        assert isinstance(settings.CHAT_MEMORY_DIR, Path)
        assert isinstance(settings.PROCESSED_CHUNKS_DIR, Path)
        assert isinstance(settings.TICKERS_DIR, Path)

    def test_environment_variable_loading(self):
        """Test that environment variables are loaded correctly."""
        with patch.dict(
            os.environ,
            {
                "OPENAI_API_KEY": "test-key-123",
                "LLM_MODEL": "gpt-4",
                "API_HOST": "0.0.0.0",
                "API_PORT": "9000",
            },
        ):
            settings = Settings()
            assert settings.OPENAI_API_KEY == "test-key-123"
            assert settings.LLM_MODEL == "gpt-4"
            assert settings.API_HOST == "0.0.0.0"
            assert settings.API_PORT == 9000

    def test_file_paths(self):
        """Test that file paths are constructed correctly."""
        settings = Settings()

        # Test specific file names
        assert settings.PROCESSED_CHUNKS_PATH.name == "chunked_articles.jsonl"
        assert settings.RAW_NEWS_PATH.name == "articles.jsonl"
        assert settings.CHAT_SESSIONS_FILE.name == "chat_sessions.json"
        assert (settings.TICKERS_DIR / "tickers.csv").name == "tickers.csv"

    def test_invalid_api_port(self):
        """Test validation of invalid API port."""
        with patch.dict(os.environ, {"API_PORT": "invalid"}):
            with pytest.raises(ValidationError):
                Settings()

    def test_invalid_streamlit_port(self):
        """Test validation of invalid Streamlit port."""
        with patch.dict(os.environ, {"STREAMLIT_PORT": "not_a_number"}):
            with pytest.raises(ValidationError):
                Settings()

    def test_path_construction(self):
        """Test that paths are constructed relative to the correct root."""
        settings = Settings()

        # All paths should be under the same root
        root = settings.CHROMA_DIR.parent.parent
        assert settings.CHROMA_DIR.is_relative_to(root)
        assert settings.CHAT_MEMORY_DIR.is_relative_to(root)
        assert settings.PROCESSED_CHUNKS_DIR.is_relative_to(root)
        assert settings.TICKERS_DIR.is_relative_to(root)
        assert settings.RAW_NEWS_PATH.is_relative_to(root)
        assert settings.PROCESSED_CHUNKS_PATH.is_relative_to(root)
        assert settings.CHAT_SESSIONS_FILE.is_relative_to(root)

    def test_settings_singleton(self):
        """Test that settings instance behaves as expected."""
        settings1 = Settings()
        settings2 = Settings()

        # Should be different instances but with same values
        assert settings1 is not settings2
        assert settings1.API_PORT == settings2.API_PORT
        assert settings1.LLM_MODEL == settings2.LLM_MODEL
