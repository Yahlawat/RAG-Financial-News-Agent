"""Tests for text chunking."""

import json
import tempfile
from pathlib import Path

from finnews.rag.chunker import chunk_articles, clean_chunk, process_jsonl


class TestCleanChunk:
    """Test text cleaning and normalization."""

    def test_clean_chunk_basic(self):
        """Test basic text cleaning."""
        text = "  This  is   a    test.  "
        result = clean_chunk(text)

        # Should normalize whitespace
        assert result == "This is a test."

    def test_clean_chunk_unicode_normalization(self):
        """Test Unicode normalization."""
        # Text with composed Unicode characters
        text = "café"  # é might be composed or decomposed
        result = clean_chunk(text)

        # Should normalize Unicode
        assert "caf" in result
        assert len(result) > 0

    def test_clean_chunk_remove_control_characters(self):
        """Test removal of control characters."""
        text = "Hello\x00World\x1F"  # Contains null and control chars
        result = clean_chunk(text)

        # Should remove control characters
        assert "\x00" not in result
        assert "\x1F" not in result
        assert "Hello" in result
        assert "World" in result

    def test_clean_chunk_encoding_issues(self):
        """Test fixing common encoding problems."""
        # Simulate common encoding issues
        text = "The company�?Ts revenue increased."
        result = clean_chunk(text)

        # Should replace encoding artifacts
        assert "�?T" not in result
        assert "'" in result or "revenue" in result

    def test_clean_chunk_multiple_spaces(self):
        """Test that multiple spaces are collapsed."""
        text = "Word1     Word2      Word3"
        result = clean_chunk(text)

        assert result == "Word1 Word2 Word3"

    def test_clean_chunk_empty_string(self):
        """Test handling of empty string."""
        result = clean_chunk("")
        assert result == ""

    def test_clean_chunk_whitespace_only(self):
        """Test handling of whitespace-only string."""
        result = clean_chunk("    \n\t   ")
        assert result == ""


class TestChunkArticles:
    """Test article chunking functionality."""

    def test_chunk_articles_basic(self):
        """Test basic article chunking."""
        articles = [
            {
                "title": "Test Article",
                "url": "https://example.com/test",
                "body": "This is a test article body. " * 100,  # Long enough to chunk
                "published_date": "2024-01-01",
                "relevant_tickers": ["AAPL"],
            }
        ]

        chunks = chunk_articles(articles, max_characters=200)

        # Should create multiple chunks
        assert len(chunks) > 1

        # Each chunk should have metadata
        for chunk in chunks:
            assert chunk.metadata["title"] == "Test Article"
            assert chunk.metadata["url"] == "https://example.com/test"
            assert chunk.metadata["published_date"] == "2024-01-01"
            assert chunk.metadata["relevant_tickers"] == ["AAPL"]

    def test_chunk_articles_respects_max_characters(self):
        """Test that chunks don't exceed max_characters."""
        articles = [
            {
                "title": "Test",
                "url": "https://example.com",
                "body": "word " * 500,  # Very long text
                "published_date": "2024-01-01",
                "relevant_tickers": [],
            }
        ]

        max_chars = 300
        chunks = chunk_articles(articles, max_characters=max_chars)

        # Chunks should not significantly exceed max_characters
        # (small overage allowed for word boundaries)
        for chunk in chunks:
            assert len(chunk.page_content) <= max_chars + 100  # Allow some buffer

    def test_chunk_articles_preserves_metadata(self):
        """Test that all metadata is preserved in chunks."""
        articles = [
            {
                "title": "Apple Earnings",
                "url": "https://example.com/apple",
                "body": "Apple reported strong earnings. " * 50,
                "published_date": "2024-01-01T10:00:00",
                "relevant_tickers": ["AAPL", "MSFT"],
            }
        ]

        chunks = chunk_articles(articles)

        for chunk in chunks:
            assert chunk.metadata["title"] == "Apple Earnings"
            assert chunk.metadata["url"] == "https://example.com/apple"
            assert chunk.metadata["published_date"] == "2024-01-01T10:00:00"
            assert chunk.metadata["relevant_tickers"] == ["AAPL", "MSFT"]

    def test_chunk_articles_skips_empty_body(self):
        """Test that articles with empty body are skipped."""
        articles = [
            {"title": "Empty Article", "url": "https://example.com/empty", "body": ""},
            {
                "title": "Valid Article",
                "url": "https://example.com/valid",
                "body": "This has content.",
            },
        ]

        chunks = chunk_articles(articles)

        # Only valid article should be chunked
        assert len(chunks) >= 1
        assert all("Valid Article" in chunk.metadata.get("title", "") for chunk in chunks)

    def test_chunk_articles_skips_whitespace_only_body(self):
        """Test that articles with whitespace-only body are skipped."""
        articles = [
            {"title": "Whitespace", "url": "https://example.com", "body": "   \n\t   "},
            {"title": "Valid", "url": "https://example.com/valid", "body": "Content here."},
        ]

        chunks = chunk_articles(articles)

        # Should only chunk valid article
        assert all("Valid" in chunk.metadata.get("title", "") for chunk in chunks)

    def test_chunk_articles_multiple_articles(self):
        """Test chunking multiple articles."""
        articles = [
            {
                "title": f"Article {i}",
                "url": f"https://example.com/{i}",
                "body": f"This is article {i}. " * 50,
                "published_date": f"2024-01-{i:02d}",
                "relevant_tickers": [f"TICK{i}"],
            }
            for i in range(1, 4)
        ]

        chunks = chunk_articles(articles)

        # Should have chunks from all articles
        assert len(chunks) > 3  # At least one chunk per article

        # Check that all articles are represented
        titles = {chunk.metadata["title"] for chunk in chunks}
        assert "Article 1" in titles
        assert "Article 2" in titles
        assert "Article 3" in titles

    def test_chunk_articles_handles_missing_metadata(self):
        """Test handling of articles with missing metadata fields."""
        articles = [
            {
                "body": "Article body content here.",
                # Missing title, url, published_date, relevant_tickers
            }
        ]

        chunks = chunk_articles(articles)

        # Should still create chunks
        assert len(chunks) > 0

        # Metadata should have None/default values
        chunk = chunks[0]
        assert chunk.metadata.get("title") is None
        assert chunk.metadata.get("url") is None
        assert chunk.metadata.get("published_date") is None

    def test_chunk_articles_cleans_text(self):
        """Test that text is cleaned during chunking."""
        articles = [
            {
                "title": "Test",
                "url": "https://example.com",
                "body": "Text  with   multiple    spaces\x00and\x1Fcontrol chars.",
                "published_date": "2024-01-01",
                "relevant_tickers": [],
            }
        ]

        chunks = chunk_articles(articles)

        # Text should be cleaned
        assert len(chunks) > 0
        text = chunks[0].page_content

        # Should not have control characters
        assert "\x00" not in text
        assert "\x1F" not in text

        # Should have normalized spaces
        assert "   " not in text

    def test_chunk_articles_overlap(self):
        """Test that chunks have overlap for context preservation."""
        articles = [
            {
                "title": "Test",
                "url": "https://example.com",
                "body": "Sentence one. Sentence two. Sentence three. Sentence four. Sentence five. "
                * 20,
                "published_date": "2024-01-01",
                "relevant_tickers": [],
            }
        ]

        chunks = chunk_articles(articles, max_characters=200)

        # Should have multiple chunks
        assert len(chunks) > 1

        # Adjacent chunks should have some overlap
        # (checking that the same sentence appears in consecutive chunks)
        if len(chunks) >= 2:
            chunk1_words = set(chunks[0].page_content.split())
            chunk2_words = set(chunks[1].page_content.split())
            overlap = chunk1_words & chunk2_words

            # Should have some word overlap
            assert len(overlap) > 0


class TestProcessJsonl:
    """Test JSONL processing pipeline."""

    def test_process_jsonl_basic(self):
        """Test basic JSONL processing."""
        with tempfile.NamedTemporaryFile(
            mode="w", delete=False, suffix=".jsonl"
        ) as input_file:
            # Write test articles
            articles = [
                {
                    "title": "Article 1",
                    "url": "https://example.com/1",
                    "body": "This is article one content. " * 50,
                    "published_date": "2024-01-01",
                    "relevant_tickers": ["AAPL"],
                },
                {
                    "title": "Article 2",
                    "url": "https://example.com/2",
                    "body": "This is article two content. " * 50,
                    "published_date": "2024-01-02",
                    "relevant_tickers": ["MSFT"],
                },
            ]

            for article in articles:
                input_file.write(json.dumps(article) + "\n")
            input_file.flush()

            with tempfile.NamedTemporaryFile(
                mode="w", delete=False, suffix=".jsonl"
            ) as output_file:
                # Process
                process_jsonl(input_file.name, output_file.name)

                # Read output
                with open(output_file.name, "r", encoding="utf-8") as f:
                    lines = f.readlines()

                # Should have chunks
                assert len(lines) > 0

                # Verify chunk format
                chunk = json.loads(lines[0])
                assert "content" in chunk
                assert "metadata" in chunk
                assert "title" in chunk["metadata"]

    def test_process_jsonl_preserves_all_articles(self):
        """Test that all articles are processed."""
        with tempfile.NamedTemporaryFile(
            mode="w", delete=False, suffix=".jsonl"
        ) as input_file:
            articles = [
                {
                    "title": f"Article {i}",
                    "url": f"https://example.com/{i}",
                    "body": f"Content for article {i}.",
                    "published_date": f"2024-01-{i:02d}",
                    "relevant_tickers": [f"TICK{i}"],
                }
                for i in range(1, 6)
            ]

            for article in articles:
                input_file.write(json.dumps(article) + "\n")
            input_file.flush()

            with tempfile.NamedTemporaryFile(
                mode="w", delete=False, suffix=".jsonl"
            ) as output_file:
                process_jsonl(input_file.name, output_file.name)

                # Read all chunks
                with open(output_file.name, "r", encoding="utf-8") as f:
                    chunks = [json.loads(line) for line in f]

                # Collect all titles from chunks
                titles = {chunk["metadata"]["title"] for chunk in chunks}

                # All articles should be represented
                assert len(titles) == 5
                for i in range(1, 6):
                    assert f"Article {i}" in titles

    def test_process_jsonl_skips_empty_bodies(self):
        """Test that articles with empty bodies are skipped."""
        with tempfile.NamedTemporaryFile(
            mode="w", delete=False, suffix=".jsonl"
        ) as input_file:
            articles = [
                {"title": "Empty", "url": "https://example.com/empty", "body": ""},
                {
                    "title": "Valid",
                    "url": "https://example.com/valid",
                    "body": "Valid content here.",
                },
            ]

            for article in articles:
                input_file.write(json.dumps(article) + "\n")
            input_file.flush()

            with tempfile.NamedTemporaryFile(
                mode="w", delete=False, suffix=".jsonl"
            ) as output_file:
                process_jsonl(input_file.name, output_file.name)

                # Read chunks
                with open(output_file.name, "r", encoding="utf-8") as f:
                    chunks = [json.loads(line) for line in f]

                # Only valid article should be in chunks
                assert all(chunk["metadata"]["title"] == "Valid" for chunk in chunks)

    def test_process_jsonl_creates_output_directory(self):
        """Test that output directory is created if it doesn't exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            input_file = Path(tmpdir) / "input.jsonl"
            output_file = Path(tmpdir) / "nonexistent" / "output.jsonl"

            # Write test article
            with open(input_file, "w", encoding="utf-8") as f:
                f.write(
                    json.dumps(
                        {"title": "Test", "url": "https://example.com", "body": "Content."}
                    )
                    + "\n"
                )

            # Process (should create directory)
            process_jsonl(str(input_file), str(output_file))

            # Output directory should exist
            assert output_file.parent.exists()
            assert output_file.exists()
