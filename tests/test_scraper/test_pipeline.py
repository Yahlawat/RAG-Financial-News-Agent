"""Tests for the scraper pipeline."""

import json
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

from finnews.scraper.items import NewsArticleItem
from finnews.scraper.pipelines import SaveNewsJSONLPipeline


class TestSaveNewsJSONLPipeline:
    """Test the SaveNewsJSONLPipeline class."""

    def test_pipeline_initialization(self):
        """Test pipeline initialization."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".jsonl") as temp_file:
            with patch("finnews.scraper.pipelines.settings") as mock_settings:
                mock_settings.raw_news = temp_file.name

                pipeline = SaveNewsJSONLPipeline()

                assert pipeline.output_file == temp_file.name
                assert pipeline.seen_urls == set()
                assert pipeline.file is None  # File is opened in open_spider

    def test_pipeline_initialization_with_existing_file(self):
        """Test pipeline initialization with existing articles file."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".jsonl") as temp_file:
            # Write some existing articles
            temp_file.write('{"url": "https://example.com/existing1", "title": "Existing 1"}\n')
            temp_file.write('{"url": "https://example.com/existing2", "title": "Existing 2"}\n')
            temp_file.flush()

            with patch("finnews.scraper.pipelines.settings") as mock_settings:
                mock_settings.raw_news = temp_file.name

                pipeline = SaveNewsJSONLPipeline()

                assert "https://example.com/existing1" in pipeline.seen_urls
                assert "https://example.com/existing2" in pipeline.seen_urls

    def test_pipeline_initialization_with_invalid_json(self):
        """Test pipeline initialization with invalid JSON in existing file."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".jsonl") as temp_file:
            # Write invalid JSON
            temp_file.write("invalid json\n")
            temp_file.write('{"url": "https://example.com/valid", "title": "Valid"}\n')
            temp_file.flush()

            with patch("finnews.scraper.pipelines.settings") as mock_settings:
                mock_settings.raw_news = temp_file.name

                # Should not raise exception
                pipeline = SaveNewsJSONLPipeline()
                assert "https://example.com/valid" in pipeline.seen_urls

    def test_process_item_new_article(self):
        """Test processing a new article."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".jsonl") as temp_file:
            with patch("finnews.scraper.pipelines.settings") as mock_settings:
                mock_settings.raw_news = temp_file.name

                pipeline = SaveNewsJSONLPipeline()

                # Mock spider
                spider = MagicMock()
                spider.logger = MagicMock()

                # Open the file (simulate spider start)
                pipeline.open_spider(spider)

                # Create test item
                item = NewsArticleItem(
                    title="Test Article",
                    url="https://example.com/test",
                    source="Test Source",
                    body="Test body content",
                    main_ticker="AAPL",
                    relevant_tickers=["AAPL", "MSFT"],
                    published_date="2024-01-01T00:00:00",
                    scraped_at="2024-01-01T00:00:00",
                )

                # Process item
                result = pipeline.process_item(item, spider)

                # Should return the item
                assert result == item

                # Should add URL to seen_urls
                assert "https://example.com/test" in pipeline.seen_urls

                # Should write to file
                pipeline.file.flush()
                pipeline.file.seek(0)
                written_data = pipeline.file.read()
                assert "Test Article" in written_data
                assert "https://example.com/test" in written_data

    def test_process_item_duplicate_article(self):
        """Test processing a duplicate article."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".jsonl") as temp_file:
            with patch("finnews.scraper.pipelines.settings") as mock_settings:
                mock_settings.raw_news = temp_file.name

                pipeline = SaveNewsJSONLPipeline()

                # Add URL to seen_urls
                pipeline.seen_urls.add("https://example.com/duplicate")

                # Create test item with duplicate URL
                item = NewsArticleItem(
                    title="Duplicate Article",
                    url="https://example.com/duplicate",
                    source="Test Source",
                )

                # Mock spider
                spider = MagicMock()
                spider.logger = MagicMock()

                # Process item
                result = pipeline.process_item(item, spider)

                # Should return None (duplicate)
                assert result is None

                # Should log the duplicate
                spider.logger.info.assert_called_once()
                assert "Duplicate skipped" in spider.logger.info.call_args[0][0]

    def test_process_item_with_none_url(self):
        """Test processing an item with None URL."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".jsonl") as temp_file:
            with patch("finnews.scraper.pipelines.settings") as mock_settings:
                mock_settings.raw_news = temp_file.name

                pipeline = SaveNewsJSONLPipeline()

                # Create test item with None URL
                item = NewsArticleItem(title="Test Article", url=None, source="Test Source")

                # Mock spider
                spider = MagicMock()
                spider.logger = MagicMock()

                # Process item
                result = pipeline.process_item(item, spider)

                # Should return None (no URL)
                assert result is None

    def test_process_item_with_empty_url(self):
        """Test processing an item with empty URL."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".jsonl") as temp_file:
            with patch("finnews.scraper.pipelines.settings") as mock_settings:
                mock_settings.raw_news = temp_file.name

                pipeline = SaveNewsJSONLPipeline()

                # Create test item with empty URL
                item = NewsArticleItem(title="Test Article", url="", source="Test Source")

                # Mock spider
                spider = MagicMock()
                spider.logger = MagicMock()

                # Process item
                result = pipeline.process_item(item, spider)

                # Should return None (empty URL)
                assert result is None

    def test_close_spider(self):
        """Test close_spider method."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".jsonl") as temp_file:
            with patch("finnews.scraper.pipelines.settings") as mock_settings:
                mock_settings.raw_news = temp_file.name

                pipeline = SaveNewsJSONLPipeline()

                # Mock spider
                spider = MagicMock()

                # Close spider
                pipeline.close_spider(spider)

                # File should be closed
                assert pipeline.file.closed

    def test_process_item_json_serialization(self):
        """Test that items are properly serialized to JSON."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".jsonl") as temp_file:
            with patch("finnews.scraper.pipelines.settings") as mock_settings:
                mock_settings.raw_news = temp_file.name

                pipeline = SaveNewsJSONLPipeline()

                # Create test item with various data types
                item = NewsArticleItem(
                    title="Test Article",
                    url="https://example.com/test",
                    source="Test Source",
                    body="Test body content",
                    main_ticker="AAPL",
                    relevant_tickers=["AAPL", "MSFT"],
                    published_date="2024-01-01T00:00:00",
                    scraped_at="2024-01-01T00:00:00",
                )

                # Mock spider
                spider = MagicMock()
                spider.logger = MagicMock()

                # Process item
                pipeline.process_item(item, spider)

                # Flush and read the written data
                pipeline.file.flush()
                pipeline.file.seek(0)
                written_data = pipeline.file.read()

                # Parse the JSON to verify it's valid
                lines = written_data.strip().split("\n")
                assert len(lines) == 1

                parsed_item = json.loads(lines[0])
                assert parsed_item["title"] == "Test Article"
                assert parsed_item["url"] == "https://example.com/test"
                assert parsed_item["relevant_tickers"] == ["AAPL", "MSFT"]

    def test_pipeline_with_large_dataset(self):
        """Test pipeline with a large number of items."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".jsonl") as temp_file:
            with patch("finnews.scraper.pipelines.settings") as mock_settings:
                mock_settings.raw_news = temp_file.name

                pipeline = SaveNewsJSONLPipeline()

                # Mock spider
                spider = MagicMock()
                spider.logger = MagicMock()

                # Process many items
                for i in range(100):
                    item = NewsArticleItem(
                        title=f"Article {i}",
                        url=f"https://example.com/article{i}",
                        source="Test Source",
                    )

                    result = pipeline.process_item(item, spider)
                    assert result == item

                # All URLs should be in seen_urls
                assert len(pipeline.seen_urls) == 100

                # All items should be written to file
                pipeline.file.flush()
                pipeline.file.seek(0)
                written_data = pipeline.file.read()
                lines = written_data.strip().split("\n")
                assert len(lines) == 100

    def test_pipeline_file_creation(self):
        """Test that pipeline creates the output directory if it doesn't exist."""
        with tempfile.TemporaryDirectory() as temp_dir:
            output_file = Path(temp_dir) / "nonexistent" / "articles.jsonl"

            with patch("finnews.scraper.pipelines.settings") as mock_settings:
                mock_settings.raw_news = str(output_file)

                # Should not raise exception
                pipeline = SaveNewsJSONLPipeline()

                # Directory should be created
                assert output_file.parent.exists()
