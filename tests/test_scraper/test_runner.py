"""Tests for scraper runner - direct Scrapy execution (no subprocess)."""

from unittest.mock import MagicMock, patch

import pytest

from finnews.scraper.runner import run_scraper, run_spider_with_tickers


class TestRunScraper:
    """Test the scraper runner with direct Scrapy execution."""

    @patch("finnews.scraper.pipelines._articles_scraped_count", 5)
    @patch("finnews.scraper.runner.CrawlerProcess")
    @patch("finnews.scraper.runner.complete_pipeline")
    @patch("finnews.scraper.runner.complete_scrape")
    @patch("finnews.scraper.runner.start_scrape")
    def test_run_scraper_basic_success(
        self, mock_start, mock_complete_scrape, mock_complete_pipeline, mock_process_class
    ):
        """Test successful scraping with direct execution."""
        # Arrange
        mock_process = MagicMock()
        mock_process_class.return_value = mock_process

        # Act
        run_scraper(["AAPL", "MSFT"])

        # Assert
        mock_start.assert_called_once_with(["AAPL", "MSFT"])
        mock_process.crawl.assert_called_once()
        mock_process.start.assert_called_once()  # Blocks until complete
        mock_complete_scrape.assert_called_once_with(
            status="completed",
            articles_found=5
        )
        mock_complete_pipeline.assert_called_once_with(status="completed")

    @patch("finnews.scraper.runner.complete_scrape")
    @patch("finnews.scraper.runner.start_scrape")
    def test_run_scraper_empty_tickers(self, mock_start, mock_complete):
        """Test handling of empty ticker list."""
        run_scraper([])

        mock_start.assert_not_called()
        mock_complete.assert_not_called()

    @patch("finnews.scraper.runner.CrawlerProcess")
    @patch("finnews.scraper.runner.complete_scrape")
    @patch("finnews.scraper.runner.start_scrape")
    @patch("finnews.scraper.runner.set_pipeline_error")
    def test_run_scraper_exception_handling(
        self, mock_error, mock_start, mock_complete, mock_process_class
    ):
        """Test exception handling during scraping."""
        # Arrange
        mock_process = MagicMock()
        mock_process.start.side_effect = RuntimeError("Spider crashed")
        mock_process_class.return_value = mock_process

        # Act & Assert
        with pytest.raises(RuntimeError, match="Spider crashed"):
            run_scraper(["AAPL"])

        mock_complete.assert_called_once_with(
            status="error",
            articles_found=0
        )
        mock_error.assert_called_once()
        assert "scraping" in mock_error.call_args[0][0]

    @patch("finnews.scraper.pipelines._articles_scraped_count", 0)
    @patch("finnews.scraper.runner.CrawlerProcess")
    def test_run_scraper_zero_articles(self, mock_process_class):
        """Test scraping that finds no new articles (all duplicates)."""
        mock_process = MagicMock()
        mock_process_class.return_value = mock_process

        # Should complete successfully even with 0 articles
        run_scraper(["NVDA"])

        mock_process.start.assert_called_once()

    @patch("finnews.scraper.pipelines._articles_scraped_count", 50)
    @patch("finnews.scraper.runner.CrawlerProcess")
    def test_run_scraper_large_article_count(self, mock_process_class):
        """Test scraping with many articles found."""
        mock_process = MagicMock()
        mock_process_class.return_value = mock_process

        run_scraper(["SPY"])

        mock_process.start.assert_called_once()


class TestRunSpiderWithTickers:
    """Test deprecated wrapper function."""

    @patch("finnews.scraper.runner.run_scraper")
    def test_run_spider_with_tickers_calls_run_scraper(self, mock_run_scraper):
        """Test that deprecated function calls new function."""
        run_spider_with_tickers(["AAPL", "MSFT"])

        mock_run_scraper.assert_called_once_with(["AAPL", "MSFT"])
