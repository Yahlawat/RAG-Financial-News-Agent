"""Tests for the FinViz spider."""

import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

from finnews.scraper.items import NewsArticleItem
from finnews.scraper.spiders.finviz_spider import FinVizSpider


class TestFinVizSpider:
    """Test the FinVizSpider class."""

    def test_spider_initialization(self):
        """Test spider initialization with tickers file."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".csv") as temp_file:
            temp_file.write("AAPL\nMSFT\nGOOGL\n")
            temp_file.flush()

            with patch("finnews.scraper.spiders.finviz_spider.settings") as mock_settings:
                mock_settings.tickers_csv = temp_file.name
                mock_settings.raw_news = Path(temp_file.name).parent / "articles.jsonl"

                spider = FinVizSpider()

                assert spider.name == "finviz_news"
                assert spider.allowed_domains == ["finviz.com"]
                assert spider.tickers == ["AAPL", "MSFT", "GOOGL"]

    def test_spider_initialization_with_existing_articles(self):
        """Test spider initialization with existing articles file."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".csv") as tickers_file:
            tickers_file.write("AAPL\nMSFT\n")
            tickers_file.flush()

            with tempfile.NamedTemporaryFile(
                mode="w", delete=False, suffix=".jsonl"
            ) as articles_file:
                articles_file.write(
                    '{"url": "https://example.com/existing", "title": "Existing"}\n'
                )
                articles_file.flush()

                with patch("finnews.scraper.spiders.finviz_spider.settings") as mock_settings:
                    mock_settings.tickers_csv = tickers_file.name
                    mock_settings.raw_news = articles_file.name

                    spider = FinVizSpider()

                    assert "https://example.com/existing" in spider.existing_urls

    def test_spider_initialization_with_invalid_json(self):
        """Test spider initialization with invalid JSON in articles file."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".csv") as tickers_file:
            tickers_file.write("AAPL\n")
            tickers_file.flush()

            with tempfile.NamedTemporaryFile(
                mode="w", delete=False, suffix=".jsonl"
            ) as articles_file:
                articles_file.write(
                    'invalid json\n{"url": "https://example.com/valid", "title": "Valid"}\n'
                )
                articles_file.flush()

                with patch("finnews.scraper.spiders.finviz_spider.settings") as mock_settings:
                    mock_settings.tickers_csv = tickers_file.name
                    mock_settings.raw_news = articles_file.name

                    # Should not raise exception
                    spider = FinVizSpider()
                    assert "https://example.com/valid" in spider.existing_urls

    def test_start_requests(self):
        """Test start_requests method."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".csv") as temp_file:
            temp_file.write("AAPL\nMSFT\n")
            temp_file.flush()

            with patch("finnews.scraper.spiders.finviz_spider.settings") as mock_settings:
                mock_settings.tickers_csv = temp_file.name
                mock_settings.raw_news = Path(temp_file.name).parent / "articles.jsonl"

                spider = FinVizSpider()
                requests = list(spider.start_requests())

                assert len(requests) == 2
                assert requests[0].url == "https://finviz.com/quote.ashx?t=AAPL&p=d"
                assert requests[0].meta["ticker"] == "AAPL"
                assert requests[1].url == "https://finviz.com/quote.ashx?t=MSFT&p=d"
                assert requests[1].meta["ticker"] == "MSFT"

    def test_parse_main_with_articles(self):
        """Test parse_main method with valid articles."""
        # Create mock response
        response = MagicMock()
        response.meta = {"ticker": "AAPL"}

        # Mock article blocks
        article1 = MagicMock()
        article1.css.return_value.get.side_effect = [
            "Test Title 1",
            "https://finviz.com/news1",
            "Source 1",
        ]

        article2 = MagicMock()
        article2.css.return_value.get.side_effect = ["Test Title 2", "/news2", "Source 2"]

        response.css.return_value = [article1, article2]

        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".csv") as temp_file:
            temp_file.write("AAPL\n")
            temp_file.flush()

            with patch("finnews.scraper.spiders.finviz_spider.settings") as mock_settings:
                mock_settings.tickers_csv = temp_file.name
                mock_settings.raw_news = Path(temp_file.name).parent / "articles.jsonl"

                spider = FinVizSpider()
                items = list(spider.parse_main(response))

                # Should return 2 items
                assert len(items) == 2

                # Check first item
                assert items[0]["title"] == "Test Title 1"
                assert items[0]["url"] == "https://finviz.com/news1"
                assert items[0]["source"] == "Source 1"
                assert items[0]["main_ticker"] == "AAPL"

                # Check second item (relative URL should be converted)
                assert items[1]["title"] == "Test Title 2"
                assert items[1]["url"] == "https://finviz.com/news2"
                assert items[1]["source"] == "Source 2"
                assert items[1]["main_ticker"] == "AAPL"

    def test_parse_main_skip_duplicates(self):
        """Test parse_main method skips duplicate URLs."""
        # Create mock response
        response = MagicMock()
        response.meta = {"ticker": "AAPL"}

        # Mock article blocks
        article = MagicMock()
        article.css.return_value.get.side_effect = [
            "Test Title",
            "https://finviz.com/duplicate",
            "Source",
        ]

        response.css.return_value = [article]

        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".csv") as temp_file:
            temp_file.write("AAPL\n")
            temp_file.flush()

            with patch("finnews.scraper.spiders.finviz_spider.settings") as mock_settings:
                mock_settings.tickers_csv = temp_file.name
                mock_settings.raw_news = Path(temp_file.name).parent / "articles.jsonl"

                spider = FinVizSpider()
                # Add URL to existing URLs
                spider.existing_urls.add("https://finviz.com/duplicate")

                items = list(spider.parse_main(response))

                # Should skip duplicate
                assert len(items) == 0

    def test_parse_main_skip_invalid_urls(self):
        """Test parse_main method skips invalid URLs."""
        # Create mock response
        response = MagicMock()
        response.meta = {"ticker": "AAPL"}

        # Mock article blocks with invalid URLs
        article1 = MagicMock()
        article1.css.return_value.get.side_effect = ["Test Title 1", None, "Source 1"]  # No URL

        article2 = MagicMock()
        article2.css.return_value.get.side_effect = ["Test Title 2", "", "Source 2"]  # Empty URL

        response.css.return_value = [article1, article2]

        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".csv") as temp_file:
            temp_file.write("AAPL\n")
            temp_file.flush()

            with patch("finnews.scraper.spiders.finviz_spider.settings") as mock_settings:
                mock_settings.tickers_csv = temp_file.name
                mock_settings.raw_news = Path(temp_file.name).parent / "articles.jsonl"

                spider = FinVizSpider()
                items = list(spider.parse_main(response))

                # Should skip invalid URLs
                assert len(items) == 0

    def test_parse_article_finviz_url(self):
        """Test parse_article method for FinViz URLs."""
        # Create mock response
        response = MagicMock()
        response.meta = {
            "item": NewsArticleItem(
                title="Test Title",
                url="https://finviz.com/news/123",
                source="FinViz",
                main_ticker="AAPL",
            )
        }

        # Mock ticker badges
        ticker_badge = MagicMock()
        ticker_badge.getall.return_value = ["AAPL", "MSFT"]
        response.css.return_value = ticker_badge

        # Mock publish info
        publish_info = MagicMock()
        publish_info.css.return_value.getall.return_value = ["Author", "January 1, 2024, 10:00 AM"]
        response.css.return_value = publish_info

        # Mock article body
        body_block = MagicMock()
        body_block.css.return_value.getall.return_value = ["Paragraph 1", "Paragraph 2"]
        response.css.return_value = body_block

        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".csv") as temp_file:
            temp_file.write("AAPL\n")
            temp_file.flush()

            with patch("finnews.scraper.spiders.finviz_spider.settings") as mock_settings:
                mock_settings.tickers_csv = temp_file.name
                mock_settings.raw_news = Path(temp_file.name).parent / "articles.jsonl"

                spider = FinVizSpider()
                items = list(spider.parse_article(response))

                # Should return 1 item
                assert len(items) == 1
                item = items[0]

                # Check relevant tickers
                assert set(item["relevant_tickers"]) == {"AAPL", "MSFT"}

                # Check published date
                assert item["published_date"] == "2024-01-01T10:00:00"

                # Check body
                assert item["body"] == "Paragraph 1 Paragraph 2"

    def test_parse_article_invalid_date(self):
        """Test parse_article method with invalid date format."""
        # Create mock response
        response = MagicMock()
        response.meta = {
            "item": NewsArticleItem(
                title="Test Title",
                url="https://finviz.com/news/123",
                source="FinViz",
                main_ticker="AAPL",
            )
        }

        # Mock ticker badges
        ticker_badge = MagicMock()
        ticker_badge.getall.return_value = ["AAPL"]
        response.css.return_value = ticker_badge

        # Mock publish info with invalid date
        publish_info = MagicMock()
        publish_info.css.return_value.getall.return_value = ["Author", "Invalid Date Format"]
        response.css.return_value = publish_info

        # Mock article body
        body_block = MagicMock()
        body_block.css.return_value.getall.return_value = ["Paragraph 1"]
        response.css.return_value = body_block

        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".csv") as temp_file:
            temp_file.write("AAPL\n")
            temp_file.flush()

            with patch("finnews.scraper.spiders.finviz_spider.settings") as mock_settings:
                mock_settings.tickers_csv = temp_file.name
                mock_settings.raw_news = Path(temp_file.name).parent / "articles.jsonl"

                spider = FinVizSpider()
                items = list(spider.parse_article(response))

                # Should return 1 item with None published_date
                assert len(items) == 1
                item = items[0]
                assert item["published_date"] is None

    def test_parse_article_non_finviz_url(self):
        """Test parse_article method for non-FinViz URLs."""
        # Create mock response
        response = MagicMock()
        response.meta = {
            "item": NewsArticleItem(
                title="Test Title",
                url="https://external.com/news",
                source="External",
                main_ticker="AAPL",
            )
        }

        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".csv") as temp_file:
            temp_file.write("AAPL\n")
            temp_file.flush()

            with patch("finnews.scraper.spiders.finviz_spider.settings") as mock_settings:
                mock_settings.tickers_csv = temp_file.name
                mock_settings.raw_news = Path(temp_file.name).parent / "articles.jsonl"

                spider = FinVizSpider()
                items = list(spider.parse_article(response))

                # Should return the item as-is (no processing)
                assert len(items) == 1
                item = items[0]
                assert item["url"] == "https://external.com/news"
                assert item["relevant_tickers"] == []
                assert item["published_date"] is None
                assert item["body"] == ""

    def test_spider_with_empty_tickers_file(self):
        """Test spider with empty tickers file."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".csv") as temp_file:
            temp_file.write("")  # Empty file
            temp_file.flush()

            with patch("finnews.scraper.spiders.finviz_spider.settings") as mock_settings:
                mock_settings.tickers_csv = temp_file.name
                mock_settings.raw_news = Path(temp_file.name).parent / "articles.jsonl"

                spider = FinVizSpider()
                requests = list(spider.start_requests())

                # Should not generate any requests
                assert len(requests) == 0

    def test_spider_with_whitespace_tickers(self):
        """Test spider with tickers file containing whitespace."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".csv") as temp_file:
            temp_file.write("  AAPL  \n\n  MSFT  \n  \n  GOOGL  \n")
            temp_file.flush()

            with patch("finnews.scraper.spiders.finviz_spider.settings") as mock_settings:
                mock_settings.tickers_csv = temp_file.name
                mock_settings.raw_news = Path(temp_file.name).parent / "articles.jsonl"

                spider = FinVizSpider()

                # Should strip whitespace and filter empty lines
                assert spider.tickers == ["AAPL", "MSFT", "GOOGL"]
