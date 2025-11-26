"""Tests for the common paths module."""

from unittest.mock import patch

from finnews.common.paths import ensure_dirs


class TestEnsureDirs:
    """Test the ensure_dirs function."""

    def test_ensure_dirs_creates_directories(self, mock_settings):
        """Test that ensure_dirs creates all required directories."""
        with patch("finnews.common.paths.settings", mock_settings):
            # Directories don't exist initially
            assert not mock_settings.CHROMA_DIR.exists()
            assert not mock_settings.CHAT_MEMORY_DIR.exists()

            ensure_dirs()

            # Directories should be created
            assert mock_settings.CHROMA_DIR.exists()
            assert mock_settings.CHAT_MEMORY_DIR.exists()
            assert mock_settings.PROCESSED_CHUNKS_PATH.parent.exists()
            assert mock_settings.RAW_NEWS_PATH.parent.exists()
            assert mock_settings.TICKERS_DIR.exists()

    def test_ensure_dirs_idempotent(self, mock_settings):
        """Test that ensure_dirs can be called multiple times safely."""
        with patch("finnews.common.paths.settings", mock_settings):
            # Create directories
            ensure_dirs()

            # Call again - should not raise
            ensure_dirs()

            # Directories should still exist
            assert mock_settings.CHROMA_DIR.exists()
            assert mock_settings.CHAT_MEMORY_DIR.exists()


# Note: We don't extensively test edge cases like PermissionError or FileExistsError
# because:
# 1. These are OS-level errors that rarely occur in practice
# 2. Testing them requires complex mocking that provides little value
# 3. The function uses Path.mkdir(parents=True, exist_ok=True) which handles these cases
