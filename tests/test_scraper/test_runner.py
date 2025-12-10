"""Critical tests for scraper runner - handles multi-ticker scraping and timeouts."""

import subprocess
from unittest.mock import MagicMock, patch

import pytest

from finnews.scraper.runner import run_spider_with_tickers


class TestRunSpiderWithTickers:
    """Test the scraper runner that handles background scraping."""

    @patch("finnews.scraper.runner.subprocess.run")
    @patch("finnews.scraper.runner.start_scrape")
    @patch("finnews.scraper.runner.complete_scrape")
    @patch("finnews.scraper.runner.settings")
    def test_run_spider_basic_success(
        self, mock_settings, mock_complete, mock_start, mock_subprocess
    ):
        """Test successful scraper run with basic tickers."""
        # Setup settings
        mock_settings.SCRAPE_TIMEOUT_PER_TICKER = 30
        mock_settings.SCRAPE_TIMEOUT_BUFFER = 60
        mock_settings.SCRAPE_MIN_TIMEOUT = 120
        mock_settings.AUTO_PROCESS_PIPELINE = False

        # Mock successful subprocess
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_subprocess.return_value = mock_result

        # Run scraper
        run_spider_with_tickers(["AAPL", "MSFT"])

        # Verify scraping was started
        mock_start.assert_called_once_with(["AAPL", "MSFT"])

        # Verify subprocess was called
        mock_subprocess.assert_called_once()
        call_args = mock_subprocess.call_args

        # Should include tickers in command
        assert "AAPL,MSFT" in call_args[0][0][2]

        # Verify scraping was marked complete
        mock_complete.assert_called_once_with(status="completed", articles_found=0)

    @patch("finnews.scraper.runner.subprocess.run")
    @patch("finnews.scraper.runner.start_scrape")
    @patch("finnews.scraper.runner.complete_scrape")
    @patch("finnews.scraper.runner.settings")
    def test_run_spider_empty_tickers(
        self, mock_settings, mock_complete, mock_start, mock_subprocess
    ):
        """Test that empty ticker list is handled gracefully."""
        # Run with empty list
        run_spider_with_tickers([])

        # Should not start scraping
        mock_start.assert_not_called()
        mock_subprocess.assert_not_called()
        mock_complete.assert_not_called()

    @patch("finnews.scraper.runner.subprocess.run")
    @patch("finnews.scraper.runner.start_scrape")
    @patch("finnews.scraper.runner.complete_scrape")
    @patch("finnews.scraper.runner.set_pipeline_error")
    @patch("finnews.scraper.runner.settings")
    def test_run_spider_scraping_failure(
        self, mock_settings, mock_error, mock_complete, mock_start, mock_subprocess
    ):
        """Test handling of scraper failures."""
        mock_settings.SCRAPE_TIMEOUT_PER_TICKER = 30
        mock_settings.SCRAPE_TIMEOUT_BUFFER = 60
        mock_settings.SCRAPE_MIN_TIMEOUT = 120
        mock_settings.AUTO_PROCESS_PIPELINE = False

        # Mock failed subprocess
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stderr = "Scraping error occurred"
        mock_subprocess.return_value = mock_result

        # Run scraper
        run_spider_with_tickers(["AAPL"])

        # Should mark as started
        mock_start.assert_called_once()

        # Should handle error
        mock_error.assert_called_once()
        assert "scraping" in mock_error.call_args[0][0]

        # Should mark scraping as failed
        mock_complete.assert_called_once_with(status="error", articles_found=0)

    @patch("finnews.scraper.runner.subprocess.run")
    @patch("finnews.scraper.runner.start_scrape")
    @patch("finnews.scraper.runner.complete_scrape")
    @patch("finnews.scraper.runner.settings")
    def test_run_spider_timeout_calculation(
        self, mock_settings, mock_complete, mock_start, mock_subprocess
    ):
        """Test that timeout is calculated correctly based on ticker count."""
        mock_settings.SCRAPE_TIMEOUT_PER_TICKER = 30  # 30 seconds per ticker
        mock_settings.SCRAPE_TIMEOUT_BUFFER = 60  # 60 second buffer
        mock_settings.SCRAPE_MIN_TIMEOUT = 120  # Minimum 2 minutes
        mock_settings.AUTO_PROCESS_PIPELINE = False

        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_subprocess.return_value = mock_result

        # Run with 5 tickers
        tickers = ["AAPL", "MSFT", "GOOGL", "TSLA", "AMZN"]
        run_spider_with_tickers(tickers)

        # Expected timeout: (5 * 30) + 60 = 210 seconds
        # But should be at least 120 seconds (min timeout)
        expected_timeout = (5 * 30) + 60  # 210 seconds

        # Verify timeout was passed to subprocess
        call_args = mock_subprocess.call_args
        actual_timeout = call_args[1]["timeout"]

        assert actual_timeout == expected_timeout

    @patch("finnews.scraper.runner.subprocess.run")
    @patch("finnews.scraper.runner.start_scrape")
    @patch("finnews.scraper.runner.complete_scrape")
    @patch("finnews.scraper.runner.settings")
    def test_run_spider_minimum_timeout(
        self, mock_settings, mock_complete, mock_start, mock_subprocess
    ):
        """Test that minimum timeout is enforced."""
        mock_settings.SCRAPE_TIMEOUT_PER_TICKER = 10
        mock_settings.SCRAPE_TIMEOUT_BUFFER = 10
        mock_settings.SCRAPE_MIN_TIMEOUT = 300  # 5 minutes minimum
        mock_settings.AUTO_PROCESS_PIPELINE = False

        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_subprocess.return_value = mock_result

        # Run with 1 ticker (would calculate to 20 seconds, but min is 300)
        run_spider_with_tickers(["AAPL"])

        # Should use minimum timeout
        call_args = mock_subprocess.call_args
        actual_timeout = call_args[1]["timeout"]

        assert actual_timeout == 300

    @patch("finnews.scraper.runner.subprocess.run")
    @patch("finnews.scraper.runner.start_scrape")
    @patch("finnews.scraper.runner.complete_scrape")
    @patch("finnews.scraper.runner.settings")
    def test_run_spider_timeout_expired(
        self, mock_settings, mock_complete, mock_start, mock_subprocess
    ):
        """Test handling of subprocess timeout."""
        mock_settings.SCRAPE_TIMEOUT_PER_TICKER = 30
        mock_settings.SCRAPE_TIMEOUT_BUFFER = 60
        mock_settings.SCRAPE_MIN_TIMEOUT = 120
        mock_settings.AUTO_PROCESS_PIPELINE = False

        # Mock timeout exception
        mock_subprocess.side_effect = subprocess.TimeoutExpired(cmd="scrapy", timeout=120)

        # Run scraper
        run_spider_with_tickers(["AAPL"])

        # Should mark as started
        mock_start.assert_called_once()

        # Should mark scraping as failed
        mock_complete.assert_called_once_with(status="error", articles_found=0)

    @patch("finnews.scraper.runner.subprocess.run")
    @patch("finnews.scraper.runner.start_scrape")
    @patch("finnews.scraper.runner.complete_scrape")
    @patch("finnews.scraper.runner._run_post_processing_pipeline")
    @patch("finnews.scraper.runner.settings")
    def test_run_spider_auto_processing_enabled(
        self, mock_settings, mock_pipeline, mock_complete, mock_start, mock_subprocess
    ):
        """Test that automatic post-processing pipeline is triggered when enabled."""
        mock_settings.SCRAPE_TIMEOUT_PER_TICKER = 30
        mock_settings.SCRAPE_TIMEOUT_BUFFER = 60
        mock_settings.SCRAPE_MIN_TIMEOUT = 120
        mock_settings.AUTO_PROCESS_PIPELINE = True  # Enable auto-processing

        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_subprocess.return_value = mock_result

        # Run scraper
        run_spider_with_tickers(["AAPL"])

        # Should trigger post-processing
        mock_pipeline.assert_called_once()

    @patch("finnews.scraper.runner.subprocess.run")
    @patch("finnews.scraper.runner.start_scrape")
    @patch("finnews.scraper.runner.complete_scrape")
    @patch("finnews.scraper.runner.complete_pipeline")
    @patch("finnews.scraper.runner.settings")
    def test_run_spider_auto_processing_disabled(
        self, mock_settings, mock_complete_pipeline, mock_complete, mock_start, mock_subprocess
    ):
        """Test that post-processing is skipped when disabled."""
        mock_settings.SCRAPE_TIMEOUT_PER_TICKER = 30
        mock_settings.SCRAPE_TIMEOUT_BUFFER = 60
        mock_settings.SCRAPE_MIN_TIMEOUT = 120
        mock_settings.AUTO_PROCESS_PIPELINE = False  # Disable auto-processing

        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_subprocess.return_value = mock_result

        # Run scraper
        run_spider_with_tickers(["AAPL"])

        # Should mark pipeline as complete (for UI) but not run it
        mock_complete_pipeline.assert_called_once_with(status="completed")

    @patch("finnews.scraper.runner.subprocess.run")
    @patch("finnews.scraper.runner.start_scrape")
    @patch("finnews.scraper.runner.settings")
    def test_run_spider_exception_handling(self, mock_settings, mock_start, mock_subprocess):
        """Test that unexpected exceptions are properly handled."""
        mock_settings.SCRAPE_TIMEOUT_PER_TICKER = 30
        mock_settings.SCRAPE_TIMEOUT_BUFFER = 60
        mock_settings.SCRAPE_MIN_TIMEOUT = 120
        mock_settings.AUTO_PROCESS_PIPELINE = False

        # Mock unexpected exception
        mock_subprocess.side_effect = Exception("Unexpected error")

        # Should raise exception
        with pytest.raises(Exception, match="Unexpected error"):
            run_spider_with_tickers(["AAPL"])

    @patch("finnews.scraper.runner.subprocess.run")
    @patch("finnews.scraper.runner.start_scrape")
    @patch("finnews.scraper.runner.complete_scrape")
    @patch("finnews.scraper.runner.settings")
    def test_run_spider_large_ticker_list(
        self, mock_settings, mock_complete, mock_start, mock_subprocess
    ):
        """Test scraping with large number of tickers."""
        mock_settings.SCRAPE_TIMEOUT_PER_TICKER = 30
        mock_settings.SCRAPE_TIMEOUT_BUFFER = 60
        mock_settings.SCRAPE_MIN_TIMEOUT = 120
        mock_settings.AUTO_PROCESS_PIPELINE = False

        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_subprocess.return_value = mock_result

        # Run with 50 tickers
        tickers = [f"TICK{i}" for i in range(50)]
        run_spider_with_tickers(tickers)

        # Timeout should scale appropriately
        # (50 * 30) + 60 = 1560 seconds (26 minutes)
        expected_timeout = (50 * 30) + 60

        call_args = mock_subprocess.call_args
        actual_timeout = call_args[1]["timeout"]

        assert actual_timeout == expected_timeout

        # Should include all tickers
        command = call_args[0][0][2]
        for ticker in tickers[:5]:  # Check first few
            assert ticker in command


class TestPostProcessingPipeline:
    """Test the automatic post-processing pipeline."""

    @patch("finnews.scraper.runner.embedder_main")
    @patch("finnews.scraper.runner.chunker_main")
    @patch("finnews.scraper.runner.start_chunking")
    @patch("finnews.scraper.runner.complete_chunking")
    @patch("finnews.scraper.runner.start_embedding")
    @patch("finnews.scraper.runner.complete_pipeline")
    def test_post_processing_pipeline_success(
        self,
        mock_complete_pipeline,
        mock_start_embed,
        mock_complete_chunk,
        mock_start_chunk,
        mock_chunker,
        mock_embedder,
    ):
        """Test successful execution of post-processing pipeline."""
        from finnews.scraper.runner import _run_post_processing_pipeline

        # Run pipeline
        _run_post_processing_pipeline()

        # Verify all steps were executed in order
        mock_start_chunk.assert_called_once()
        mock_chunker.assert_called_once()
        mock_complete_chunk.assert_called_once()

        mock_start_embed.assert_called_once()
        mock_embedder.assert_called_once()

        mock_complete_pipeline.assert_called_once_with(status="completed")

    @patch("finnews.scraper.runner.chunker_main")
    @patch("finnews.scraper.runner.start_chunking")
    @patch("finnews.scraper.runner.set_pipeline_error")
    def test_post_processing_pipeline_chunking_failure(
        self, mock_error, mock_start_chunk, mock_chunker
    ):
        """Test handling of chunking failures."""
        from finnews.scraper.runner import _run_post_processing_pipeline

        # Mock chunking failure
        mock_chunker.side_effect = Exception("Chunking failed")

        # Should raise exception
        with pytest.raises(Exception, match="Chunking failed"):
            _run_post_processing_pipeline()

        # Should record error
        mock_error.assert_called_once()
        assert "chunking" in mock_error.call_args[0][0]

    @patch("finnews.scraper.runner.embedder_main")
    @patch("finnews.scraper.runner.chunker_main")
    @patch("finnews.scraper.runner.start_chunking")
    @patch("finnews.scraper.runner.complete_chunking")
    @patch("finnews.scraper.runner.start_embedding")
    @patch("finnews.scraper.runner.set_pipeline_error")
    def test_post_processing_pipeline_embedding_failure(
        self,
        mock_error,
        mock_start_embed,
        mock_complete_chunk,
        mock_start_chunk,
        mock_chunker,
        mock_embedder,
    ):
        """Test handling of embedding failures."""
        from finnews.scraper.runner import _run_post_processing_pipeline

        # Mock embedding failure
        mock_embedder.side_effect = Exception("Embedding failed")

        # Should raise exception
        with pytest.raises(Exception, match="Embedding failed"):
            _run_post_processing_pipeline()

        # Should record error
        mock_error.assert_called_once()
        assert "embedding" in mock_error.call_args[0][0]
