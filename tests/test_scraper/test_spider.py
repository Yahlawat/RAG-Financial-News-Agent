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
                mock_settings.RAW_NEWS_PATH = Path(temp_file.name).parent / "articles.jsonl"

                spider = FinVizSpider(tickers=["AAPL", "MSFT", "GOOGL"])

                assert spider.name == "finviz_news"
                assert spider.allowed_domains == ["finviz.com"]
                assert set(spider.tickers) == {"AAPL", "MSFT", "GOOGL"}

    def test_spider_initialization_with_existing_articles(self):
        """Test spider initialization with existing articles file."""
        spider = FinVizSpider(tickers=["AAPL", "MSFT"])

        assert set(spider.tickers) == {"AAPL", "MSFT"}

    def test_spider_initialization_with_invalid_json(self):
        """Test spider initialization without raising exception."""
        # Should not raise exception
        spider = FinVizSpider(tickers=["AAPL"])
        assert spider.tickers == ["AAPL"]

    def test_start_requests(self):
        """Test start_requests method."""
        spider = FinVizSpider(tickers=["AAPL", "MSFT"])
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

        spider = FinVizSpider(tickers=["AAPL"])
        items = list(spider.parse_main(response))

        # Should return 2 items
        assert len(items) == 2

        # Check first item (scrapy.Request object)
        assert items[0].url == "https://finviz.com/news1"
        assert items[0].meta["item"]["title"] == "Test Title 1"
        assert items[0].meta["item"]["main_ticker"] == "AAPL"

        # Check second item (relative URL should be converted, scrapy.Request)
        assert items[1].url == "https://finviz.com/news2"
        assert items[1].meta["item"]["title"] == "Test Title 2"
        assert items[1].meta["item"]["main_ticker"] == "AAPL"

    def test_parse_main_skip_duplicates(self):
        """Test parse_main method with duplicate handling in pipeline."""
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

        spider = FinVizSpider(tickers=["AAPL"])
        items = list(spider.parse_main(response))

        # Should return item (duplicate detection handled by pipeline)
        assert len(items) == 1

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

        spider = FinVizSpider(tickers=["AAPL"])
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

        # Mock ticker badges - div.ticker-badge_name::text
        ticker_badge_mock = MagicMock()
        ticker_badge_mock.getall.return_value = ["AAPL", "MSFT"]

        # Mock publish info - div.news-publish-info div::text
        publish_info_mock = MagicMock()
        publish_info_mock.getall.return_value = ["Author", "January 1, 2024, 10:00 AM"]

        # Mock article body - div.text-justify and p::text, p strong::text
        body_block_mock = MagicMock()
        body_paragraphs_mock = MagicMock()
        body_paragraphs_mock.getall.return_value = ["Paragraph 1", "Paragraph 2"]
        body_block_mock.css.return_value = body_paragraphs_mock

        # Setup CSS selector chain
        def css_side_effect(selector):
            if "div.ticker-badge_name::text" in selector:
                return ticker_badge_mock
            elif "div.news-publish-info div::text" in selector:
                return publish_info_mock
            elif "div.text-justify" in selector:
                return body_block_mock
            return MagicMock()

        response.css.side_effect = css_side_effect

        spider = FinVizSpider(tickers=["AAPL"])
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
                published_date=None,  # Explicitly set initial value
            )
        }

        # Mock ticker badges
        ticker_badge_mock = MagicMock()
        ticker_badge_mock.getall.return_value = ["AAPL"]

        # Mock publish info with invalid date
        publish_info_mock = MagicMock()
        publish_info_mock.getall.return_value = ["Author", "Invalid Date Format"]

        # Mock article body
        body_block_mock = MagicMock()
        body_paragraphs_mock = MagicMock()
        body_paragraphs_mock.getall.return_value = ["Paragraph 1"]
        body_block_mock.css.return_value = body_paragraphs_mock

        # Setup CSS selector chain
        def css_side_effect(selector):
            if "div.ticker-badge_name::text" in selector:
                return ticker_badge_mock
            elif "div.news-publish-info div::text" in selector:
                return publish_info_mock
            elif "div.text-justify" in selector:
                return body_block_mock
            return MagicMock()

        response.css.side_effect = css_side_effect

        spider = FinVizSpider(tickers=["AAPL"])
        items = list(spider.parse_article(response))

        # Should return 1 item - published_date remains None when parsing fails
        assert len(items) == 1
        item = items[0]
        assert item.get("published_date") is None

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
                published_date=None,
                body="",
                relevant_tickers=[],
            )
        }

        # Mock empty results for all selectors
        ticker_badge_mock = MagicMock()
        ticker_badge_mock.getall.return_value = []

        publish_info_mock = MagicMock()
        publish_info_mock.getall.return_value = []

        body_block_mock = MagicMock()
        body_paragraphs_mock = MagicMock()
        body_paragraphs_mock.getall.return_value = []
        body_block_mock.css.return_value = body_paragraphs_mock

        def css_side_effect(selector):
            if "div.ticker-badge_name::text" in selector:
                return ticker_badge_mock
            elif "div.news-publish-info div::text" in selector:
                return publish_info_mock
            elif "div.text-justify" in selector:
                return body_block_mock
            return MagicMock()

        response.css.side_effect = css_side_effect

        spider = FinVizSpider(tickers=["AAPL"])
        items = list(spider.parse_article(response))

        # Should return the item with minimal processing
        assert len(items) == 1
        item = items[0]
        assert item["url"] == "https://external.com/news"
        assert item["relevant_tickers"] == []
        assert item.get("published_date") is None
        assert item["body"] == ""

    def test_spider_with_empty_tickers_file(self):
        """Test spider with empty tickers list."""
        import pytest

        # Should raise ValueError with empty tickers
        with pytest.raises(ValueError, match="tickers parameter is required"):
            spider = FinVizSpider(tickers=[])

    def test_spider_with_whitespace_tickers(self):
        """Test spider with tickers containing whitespace."""
        spider = FinVizSpider(tickers=["  AAPL  ", "", "  MSFT  ", "  ", "  GOOGL  "])

        # Should strip whitespace and filter empty strings
        assert set(spider.tickers) == {"AAPL", "MSFT", "GOOGL"}
