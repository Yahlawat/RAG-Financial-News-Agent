"""Tests for the common paths module."""
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from finnews.common.paths import ensure_dirs
from finnews.common.config import Settings


class TestEnsureDirs:
    """Test the ensure_dirs function."""

    def test_ensure_dirs_creates_directories(self):
        """Test that ensure_dirs creates all required directories."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Mock the settings to use our temp directory
            with patch('finnews.common.paths.settings') as mock_settings:
                mock_settings.CHROMA_DIR = Path(temp_dir) / "chroma_store"
                mock_settings.CHAT_MEMORY_DIR = Path(temp_dir) / "chat_memory"
                mock_settings.PROCESSED_CHUNKS_PATH = Path(temp_dir) / "processed_chunks" / "file.jsonl"
                mock_settings.RAW_NEWS_PATH = Path(temp_dir) / "raw_news" / "file.jsonl"
                mock_settings.TICKERS_DIR = Path(temp_dir) / "tickers"
                
                # Ensure directories don't exist initially
                assert not mock_settings.CHROMA_DIR.exists()
                assert not mock_settings.CHAT_MEMORY_DIR.exists()
                assert not mock_settings.PROCESSED_CHUNKS_PATH.parent.exists()
                assert not mock_settings.RAW_NEWS_PATH.parent.exists()
                assert not mock_settings.TICKERS_DIR.exists()
                
                # Call ensure_dirs
                ensure_dirs()
                
                # Check that directories were created
                assert mock_settings.CHROMA_DIR.exists()
                assert mock_settings.CHAT_MEMORY_DIR.exists()
                assert mock_settings.PROCESSED_CHUNKS_PATH.parent.exists()
                assert mock_settings.RAW_NEWS_PATH.parent.exists()
                assert mock_settings.TICKERS_DIR.exists()

    def test_ensure_dirs_handles_existing_directories(self):
        """Test that ensure_dirs doesn't fail if directories already exist."""
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch('finnews.common.paths.settings') as mock_settings:
                mock_settings.CHROMA_DIR = Path(temp_dir) / "chroma_store"
                mock_settings.CHAT_MEMORY_DIR = Path(temp_dir) / "chat_memory"
                mock_settings.PROCESSED_CHUNKS_PATH = Path(temp_dir) / "processed_chunks" / "file.jsonl"
                mock_settings.RAW_NEWS_PATH = Path(temp_dir) / "raw_news" / "file.jsonl"
                mock_settings.TICKERS_DIR = Path(temp_dir) / "tickers"
                
                # Create directories first
                mock_settings.CHROMA_DIR.mkdir(parents=True)
                mock_settings.CHAT_MEMORY_DIR.mkdir(parents=True)
                mock_settings.PROCESSED_CHUNKS_PATH.parent.mkdir(parents=True)
                mock_settings.RAW_NEWS_PATH.parent.mkdir(parents=True)
                mock_settings.TICKERS_DIR.mkdir(parents=True)
                
                # Call ensure_dirs - should not raise an exception
                ensure_dirs()
                
                # Directories should still exist
                assert mock_settings.CHROMA_DIR.exists()
                assert mock_settings.CHAT_MEMORY_DIR.exists()
                assert mock_settings.PROCESSED_CHUNKS_PATH.parent.exists()
                assert mock_settings.RAW_NEWS_PATH.parent.exists()
                assert mock_settings.TICKERS_DIR.exists()

    def test_ensure_dirs_creates_nested_directories(self):
        """Test that ensure_dirs creates nested directory structures."""
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch('finnews.common.paths.settings') as mock_settings:
                # Use deeply nested paths
                mock_settings.CHROMA_DIR = Path(temp_dir) / "data" / "deep" / "nested" / "chroma_store"
                mock_settings.CHAT_MEMORY_DIR = Path(temp_dir) / "data" / "deep" / "nested" / "chat_memory"
                mock_settings.PROCESSED_CHUNKS_PATH = Path(temp_dir) / "data" / "deep" / "nested" / "processed_chunks" / "file.jsonl"
                mock_settings.RAW_NEWS_PATH = Path(temp_dir) / "data" / "deep" / "nested" / "raw_news" / "file.jsonl"
                mock_settings.TICKERS_DIR = Path(temp_dir) / "data" / "deep" / "nested" / "tickers"
                
                # Call ensure_dirs
                ensure_dirs()
                
                # Check that all nested directories were created
                assert mock_settings.CHROMA_DIR.exists()
                assert mock_settings.CHAT_MEMORY_DIR.exists()
                assert mock_settings.PROCESSED_CHUNKS_PATH.parent.exists()
                assert mock_settings.RAW_NEWS_PATH.parent.exists()
                assert mock_settings.TICKERS_DIR.exists()

    def test_ensure_dirs_with_permission_error(self):
        """Test that ensure_dirs handles permission errors gracefully."""
        with patch('finnews.common.paths.settings') as mock_settings:
            # Mock a path that will raise PermissionError
            mock_path = MagicMock()
            mock_path.mkdir.side_effect = PermissionError("Permission denied")
            
            mock_settings.CHROMA_DIR = mock_path
            mock_settings.CHAT_MEMORY_DIR = mock_path
            mock_settings.PROCESSED_CHUNKS_PATH = mock_path
            mock_settings.RAW_NEWS_PATH = mock_path
            mock_settings.TICKERS_DIR = mock_path
            
            # Should raise PermissionError
            with pytest.raises(PermissionError):
                ensure_dirs()

    def test_ensure_dirs_with_file_instead_of_directory(self):
        """Test that ensure_dirs handles case where a file exists instead of directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch('finnews.common.paths.settings') as mock_settings:
                # Create a file where a directory should be
                file_path = Path(temp_dir) / "chroma_store"
                file_path.write_text("test")
                
                mock_settings.CHROMA_DIR = file_path
                mock_settings.CHAT_MEMORY_DIR = Path(temp_dir) / "chat_memory"
                mock_settings.PROCESSED_CHUNKS_PATH = Path(temp_dir) / "processed_chunks" / "file.jsonl"
                mock_settings.RAW_NEWS_PATH = Path(temp_dir) / "raw_news" / "file.jsonl"
                mock_settings.TICKERS_DIR = Path(temp_dir) / "tickers"
                
                # Should raise FileExistsError
                with pytest.raises(FileExistsError):
                    ensure_dirs()
