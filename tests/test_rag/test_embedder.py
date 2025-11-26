"""Tests for the embedder module."""

import json
import tempfile
from unittest.mock import MagicMock, patch

import pytest

from finnews.rag.embedder import batch, build_chroma_index, load_chunks_from_file


class TestLoadChunksFromFile:
    """Test the load_chunks_from_file function."""

    def test_load_chunks_from_file_success(self):
        """Test successful loading of chunks from file."""
        test_data = [
            {
                "content": "This is test content 1",
                "metadata": {
                    "title": "Test Article 1",
                    "url": "https://example.com/1",
                    "relevant_tickers": "AAPL, MSFT",
                    "published_date": "2024-01-01",
                },
            },
            {
                "content": "This is test content 2",
                "metadata": {
                    "title": "Test Article 2",
                    "url": "https://example.com/2",
                    "relevant_tickers": "GOOGL",
                    "published_date": "2024-01-02",
                },
            },
        ]

        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".jsonl") as temp_file:
            for item in test_data:
                temp_file.write(json.dumps(item) + "\n")
            temp_file.flush()

            documents, ids = load_chunks_from_file(temp_file.name)

            assert len(documents) == 2
            assert len(ids) == 2

            # Check first document
            assert documents[0].page_content == "This is test content 1"
            assert documents[0].metadata["title"] == "Test Article 1"
            assert documents[0].metadata["url"] == "https://example.com/1"
            assert documents[0].metadata["relevant_tickers"] == "AAPL, MSFT"
            assert documents[0].metadata["published_date"] == "2024-01-01"

            # Check second document
            assert documents[1].page_content == "This is test content 2"
            assert documents[1].metadata["title"] == "Test Article 2"
            assert documents[1].metadata["url"] == "https://example.com/2"
            assert documents[1].metadata["relevant_tickers"] == "GOOGL"
            assert documents[1].metadata["published_date"] == "2024-01-02"

    def test_load_chunks_from_file_empty_content(self):
        """Test loading chunks with empty content (should be skipped)."""
        test_data = [
            {"content": "Valid content", "metadata": {"title": "Valid Article"}},
            {
                "content": "",  # Empty content should be skipped
                "metadata": {"title": "Empty Article"},
            },
            {
                "content": "   ",  # Whitespace only should be skipped
                "metadata": {"title": "Whitespace Article"},
            },
        ]

        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".jsonl") as temp_file:
            for item in test_data:
                temp_file.write(json.dumps(item) + "\n")
            temp_file.flush()

            documents, ids = load_chunks_from_file(temp_file.name)

            # Only one document should be loaded (the valid one)
            assert len(documents) == 1
            assert len(ids) == 1
            assert documents[0].page_content == "Valid content"

    def test_load_chunks_from_file_missing_metadata(self):
        """Test loading chunks with missing metadata fields."""
        test_data = [
            {
                "content": "Test content",
                "metadata": {
                    "title": "Test Article",
                    # Missing other fields
                },
            }
        ]

        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".jsonl") as temp_file:
            for item in test_data:
                temp_file.write(json.dumps(item) + "\n")
            temp_file.flush()

            documents, ids = load_chunks_from_file(temp_file.name)

            assert len(documents) == 1
            assert documents[0].page_content == "Test content"
            assert documents[0].metadata["title"] == "Test Article"
            assert documents[0].metadata["url"] == ""
            assert documents[0].metadata["relevant_tickers"] == ""
            assert documents[0].metadata["published_date"] == ""

    def test_load_chunks_from_file_invalid_json(self):
        """Test loading chunks with invalid JSON lines."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".jsonl") as temp_file:
            temp_file.write('{"valid": "json"}\n')
            temp_file.write("invalid json line\n")
            temp_file.write('{"another": "valid"}\n')
            temp_file.flush()

            # Should not raise exception, just skip invalid lines
            documents, ids = load_chunks_from_file(temp_file.name)
            assert len(documents) == 2

    def test_load_chunks_from_file_nonexistent(self):
        """Test loading chunks from nonexistent file."""
        with pytest.raises(FileNotFoundError):
            load_chunks_from_file("nonexistent_file.jsonl")


class TestBatch:
    """Test the batch function."""

    def test_batch_empty_list(self):
        """Test batching an empty list."""
        result = list(batch([], 5))
        assert result == []

    def test_batch_single_item(self):
        """Test batching a single item."""
        result = list(batch([1], 5))
        assert result == [[1]]

    def test_batch_exact_multiple(self):
        """Test batching when list length is exact multiple of batch size."""
        result = list(batch([1, 2, 3, 4, 5, 6], 3))
        assert result == [[1, 2, 3], [4, 5, 6]]

    def test_batch_remainder(self):
        """Test batching when list length has remainder."""
        result = list(batch([1, 2, 3, 4, 5], 3))
        assert result == [[1, 2, 3], [4, 5]]

    def test_batch_larger_than_list(self):
        """Test batching when batch size is larger than list."""
        result = list(batch([1, 2], 5))
        assert result == [[1, 2]]

    def test_batch_size_one(self):
        """Test batching with batch size of 1."""
        result = list(batch([1, 2, 3], 1))
        assert result == [[1], [2], [3]]


class TestBuildChromaIndex:
    """Test the build_chroma_index function."""

    @patch("finnews.rag.embedder.HuggingFaceEmbeddings")
    @patch("finnews.rag.embedder.Chroma")
    def test_build_chroma_index_success(self, mock_chroma, mock_embeddings):
        """Test successful building of Chroma index."""
        # Mock the embedding model
        mock_embeddings.return_value = MagicMock()

        # Mock the Chroma vectorstore
        mock_vectorstore = MagicMock()
        mock_vectorstore.get.return_value = {"ids": []}  # No existing documents
        mock_chroma.return_value = mock_vectorstore

        # Create test data
        test_data = [
            {
                "content": "Test content 1",
                "metadata": {"title": "Test 1", "url": "https://example.com/1"},
            },
            {
                "content": "Test content 2",
                "metadata": {"title": "Test 2", "url": "https://example.com/2"},
            },
        ]

        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".jsonl") as temp_file:
            for item in test_data:
                temp_file.write(json.dumps(item) + "\n")
            temp_file.flush()

            with tempfile.TemporaryDirectory() as temp_dir:
                result = build_chroma_index(
                    input_file=temp_file.name,
                    output_path=temp_dir,
                    model_name="test-model",
                    batch_size=1,
                )

                # Verify Chroma was initialized correctly
                mock_chroma.assert_called_once()
                mock_embeddings.assert_called_once_with(model_name="test-model")

                # Verify documents were added
                assert mock_vectorstore.add_documents.called
                assert mock_vectorstore.persist.called

    @patch("finnews.rag.embedder.HuggingFaceEmbeddings")
    @patch("finnews.rag.embedder.Chroma")
    def test_build_chroma_index_existing_documents(self, mock_chroma, mock_embeddings):
        """Test building index when documents already exist."""
        # Mock the embedding model
        mock_embeddings.return_value = MagicMock()

        # Mock the Chroma vectorstore with existing documents
        mock_vectorstore = MagicMock()
        mock_vectorstore.get.return_value = {"ids": ["existing_id"]}
        mock_chroma.return_value = mock_vectorstore

        # Create test data
        test_data = [
            {"content": "Test content", "metadata": {"title": "Test", "url": "https://example.com"}}
        ]

        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".jsonl") as temp_file:
            for item in test_data:
                temp_file.write(json.dumps(item) + "\n")
            temp_file.flush()

            with tempfile.TemporaryDirectory() as temp_dir:
                result = build_chroma_index(
                    input_file=temp_file.name,
                    output_path=temp_dir,
                    model_name="test-model",
                    batch_size=1,
                )

                # Should not add documents if they already exist
                assert not mock_vectorstore.add_documents.called

    @patch("finnews.rag.embedder.HuggingFaceEmbeddings")
    @patch("finnews.rag.embedder.Chroma")
    def test_build_chroma_index_exception_handling(self, mock_chroma, mock_embeddings):
        """Test handling of exceptions during index building."""
        # Mock the embedding model
        mock_embeddings.return_value = MagicMock()

        # Mock the Chroma vectorstore to raise exception
        mock_vectorstore = MagicMock()
        mock_vectorstore.get.side_effect = Exception("Chroma error")
        mock_chroma.return_value = mock_vectorstore

        # Create test data
        test_data = [
            {"content": "Test content", "metadata": {"title": "Test", "url": "https://example.com"}}
        ]

        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".jsonl") as temp_file:
            for item in test_data:
                temp_file.write(json.dumps(item) + "\n")
            temp_file.flush()

            with tempfile.TemporaryDirectory() as temp_dir:
                # Should handle exception gracefully
                result = build_chroma_index(
                    input_file=temp_file.name,
                    output_path=temp_dir,
                    model_name="test-model",
                    batch_size=1,
                )

                # Should still return the vectorstore
                assert result == mock_vectorstore

    def test_build_chroma_index_nonexistent_file(self):
        """Test building index with nonexistent input file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            with pytest.raises(FileNotFoundError):
                build_chroma_index(input_file="nonexistent.jsonl", output_path=temp_dir)
