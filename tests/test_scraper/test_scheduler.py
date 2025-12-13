"""Critical tests for automated scraping scheduler - handles background scraping jobs."""

from unittest.mock import MagicMock, patch

import pytest

from finnews.scraper.scheduler import (
    get_all_unique_tickers,
    run_scheduled_scrape,
    scrape_new_tickers,
    start_scheduler,
    stop_scheduler,
)


class TestGetAllUniqueTickers:
    """Test loading tickers from tickers.txt file."""

    @patch("finnews.common.ticker_manager.load_tickers")
    def test_get_all_unique_tickers_success(self, mock_load):
        """Test successfully loading tickers from file."""
        mock_load.return_value = ["AAPL", "GOOGL", "MSFT", "TSLA"]

        tickers = get_all_unique_tickers()

        assert tickers == ["AAPL", "GOOGL", "MSFT", "TSLA"]
        mock_load.assert_called_once()

    @patch("finnews.common.ticker_manager.load_tickers")
    def test_get_all_unique_tickers_empty(self, mock_load):
        """Test when tickers file is empty."""
        mock_load.return_value = []

        tickers = get_all_unique_tickers()

        assert tickers == []

    @patch("finnews.common.ticker_manager.load_tickers")
    def test_get_all_unique_tickers_error(self, mock_load):
        """Test handling of errors when loading tickers."""
        mock_load.side_effect = Exception("File read error")

        tickers = get_all_unique_tickers()

        assert tickers == []


class TestRunScheduledScrape:
    """Test the scheduled scraping job."""

    @patch("finnews.scraper.scheduler.run_scraper")
    @patch("finnews.scraper.scheduler.get_all_unique_tickers")
    def test_run_scheduled_scrape_success(self, mock_get_tickers, mock_run_scraper):
        """Test successful scheduled scrape."""
        # Mock ticker retrieval
        mock_get_tickers.return_value = ["AAPL", "MSFT", "GOOGL"]

        # Run scheduled scrape
        run_scheduled_scrape()

        # Should get tickers
        mock_get_tickers.assert_called_once()

        # Should run scraper with all tickers
        mock_run_scraper.assert_called_once_with(["AAPL", "MSFT", "GOOGL"])

    @patch("finnews.scraper.scheduler.run_scraper")
    @patch("finnews.scraper.scheduler.get_all_unique_tickers")
    def test_run_scheduled_scrape_no_tickers(self, mock_get_tickers, mock_run_scraper):
        """Test scheduled scrape when no tickers exist."""
        # Mock empty ticker list
        mock_get_tickers.return_value = []

        # Run scheduled scrape
        run_scheduled_scrape()

        # Should not run scraper
        mock_run_scraper.assert_not_called()

    @patch("finnews.scraper.scheduler.run_scraper")
    @patch("finnews.scraper.scheduler.get_all_unique_tickers")
    def test_run_scheduled_scrape_failure_handling(self, mock_get_tickers, mock_run_scraper):
        """Test handling of scraper failures in scheduled job."""
        mock_get_tickers.return_value = ["AAPL"]

        # Mock scraper failure
        mock_run_scraper.side_effect = Exception("Scraper error")

        # Should not raise exception (scheduled job should be resilient)
        run_scheduled_scrape()

        # Scraper should have been called despite error
        mock_run_scraper.assert_called_once()


class TestScrapeNewTickers:
    """Test on-demand scraping for new tickers."""

    @patch("finnews.scraper.scheduler.run_scraper")
    def test_scrape_new_tickers_success(self, mock_run_scraper):
        """Test on-demand scraping for new tickers."""
        new_tickers = ["TSLA", "NVDA"]

        scrape_new_tickers(new_tickers)

        # Should run scraper
        mock_run_scraper.assert_called_once_with(["TSLA", "NVDA"])

    @patch("finnews.scraper.scheduler.run_scraper")
    def test_scrape_new_tickers_empty_list(self, mock_run_scraper):
        """Test on-demand scraping with empty ticker list."""
        scrape_new_tickers([])

        # Should not run scraper
        mock_run_scraper.assert_not_called()

    @patch("finnews.scraper.scheduler.run_scraper")
    def test_scrape_new_tickers_failure_handling(self, mock_run_scraper):
        """Test handling of failures in on-demand scraping."""
        # Mock scraper failure
        mock_run_scraper.side_effect = Exception("Scraper failed")

        # Should not raise exception (should be resilient)
        scrape_new_tickers(["AAPL"])

        # Scraper should have been called
        mock_run_scraper.assert_called_once()

    @patch("finnews.scraper.scheduler.run_scraper")
    def test_scrape_new_tickers_single_ticker(self, mock_run_scraper):
        """Test on-demand scraping for single ticker."""
        scrape_new_tickers(["AAPL"])

        # Should run scraper with single ticker
        mock_run_scraper.assert_called_once_with(["AAPL"])


class TestSchedulerLifecycle:
    """Test scheduler initialization and shutdown."""

    @patch("finnews.scraper.scheduler.settings")
    def test_start_scheduler_enabled(self, mock_settings):
        """Test starting scheduler with scheduled scraping enabled."""
        mock_settings.SCRAPE_SCHEDULE_ENABLED = True
        mock_settings.SCRAPE_SCHEDULE_HOUR = 2
        mock_settings.SCRAPE_SCHEDULE_MINUTE = 0

        # Start scheduler
        scheduler = start_scheduler()

        # Should be running
        assert scheduler is not None
        assert scheduler.running

        # Should have scheduled job
        jobs = scheduler.get_jobs()
        assert len(jobs) == 1
        assert jobs[0].id == "daily_scrape"

        # Clean up
        stop_scheduler()

    @patch("finnews.scraper.scheduler.settings")
    def test_start_scheduler_disabled(self, mock_settings):
        """Test starting scheduler with scheduled scraping disabled."""
        mock_settings.SCRAPE_SCHEDULE_ENABLED = False

        # Start scheduler
        scheduler = start_scheduler()

        # Should be running but with no jobs
        assert scheduler is not None
        assert scheduler.running

        # Should have no scheduled jobs
        jobs = scheduler.get_jobs()
        assert len(jobs) == 0

        # Clean up
        stop_scheduler()

    @patch("finnews.scraper.scheduler.settings")
    def test_start_scheduler_already_running(self, mock_settings):
        """Test starting scheduler when already running."""
        mock_settings.SCRAPE_SCHEDULE_ENABLED = False

        # Start scheduler twice
        scheduler1 = start_scheduler()
        scheduler2 = start_scheduler()

        # Should return same instance
        assert scheduler1 is scheduler2

        # Clean up
        stop_scheduler()

    @patch("finnews.scraper.scheduler.settings")
    def test_stop_scheduler(self, mock_settings):
        """Test stopping scheduler."""
        mock_settings.SCRAPE_SCHEDULE_ENABLED = False

        # Start and stop
        start_scheduler()
        stop_scheduler()

        # Should be stopped
        from finnews.scraper.scheduler import get_scheduler

        assert get_scheduler() is None

    def test_stop_scheduler_not_running(self):
        """Test stopping scheduler when not running."""
        # Should not raise error
        stop_scheduler()

    @patch("finnews.scraper.scheduler.settings")
    def test_scheduler_custom_schedule(self, mock_settings):
        """Test scheduler with custom schedule time."""
        mock_settings.SCRAPE_SCHEDULE_ENABLED = True
        mock_settings.SCRAPE_SCHEDULE_HOUR = 14  # 2 PM UTC
        mock_settings.SCRAPE_SCHEDULE_MINUTE = 30

        scheduler = start_scheduler()

        # Verify job is scheduled
        jobs = scheduler.get_jobs()
        assert len(jobs) == 1

        # Verify schedule (job should be configured for 14:30 UTC)
        job = jobs[0]
        assert job.trigger.hour == 14  # type: ignore
        assert job.trigger.minute == 30  # type: ignore

        # Clean up
        stop_scheduler()

    @patch("finnews.scraper.scheduler.settings")
    def test_scheduler_timezone(self, mock_settings):
        """Test that scheduler uses UTC timezone."""
        mock_settings.SCRAPE_SCHEDULE_ENABLED = True
        mock_settings.SCRAPE_SCHEDULE_HOUR = 2
        mock_settings.SCRAPE_SCHEDULE_MINUTE = 0

        scheduler = start_scheduler()

        # Verify timezone
        assert scheduler.timezone.zone == "UTC"  # type: ignore

        # Clean up
        stop_scheduler()


class TestSchedulerIntegration:
    """Integration tests for scheduler behavior."""

    @patch("finnews.scraper.scheduler.run_scraper")
    @patch("finnews.scraper.scheduler.get_all_unique_tickers")
    @patch("finnews.scraper.scheduler.settings")
    def test_scheduler_job_execution(
        self, mock_settings, mock_get_tickers, mock_run_scraper
    ):
        """Test that scheduled job can execute."""
        mock_settings.SCRAPE_SCHEDULE_ENABLED = True
        mock_settings.SCRAPE_SCHEDULE_HOUR = 2
        mock_settings.SCRAPE_SCHEDULE_MINUTE = 0

        mock_get_tickers.return_value = ["AAPL", "MSFT"]

        # Start scheduler
        scheduler = start_scheduler()

        # Manually trigger the job (don't wait for actual schedule)
        jobs = scheduler.get_jobs()
        job = jobs[0]
        job.func()  # Execute job function

        # Verify job executed
        mock_get_tickers.assert_called_once()
        mock_run_scraper.assert_called_once_with(["AAPL", "MSFT"])

        # Clean up
        stop_scheduler()

    @patch("finnews.scraper.scheduler.settings")
    def test_scheduler_multiple_start_stop_cycles(self, mock_settings):
        """Test starting and stopping scheduler multiple times."""
        mock_settings.SCRAPE_SCHEDULE_ENABLED = False

        # Multiple cycles
        for _ in range(3):
            scheduler = start_scheduler()
            assert scheduler is not None
            assert scheduler.running

            stop_scheduler()

            from finnews.scraper.scheduler import get_scheduler

            assert get_scheduler() is None
