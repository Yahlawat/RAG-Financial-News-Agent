"""Critical tests for automated scraping scheduler - handles background scraping jobs."""

import tempfile
from pathlib import Path
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
    """Test aggregating tickers from all user profiles."""

    @patch("finnews.scraper.scheduler.USER_PROFILES_DIR")
    def test_get_all_unique_tickers_multiple_users(self, mock_dir):
        """Test aggregating tickers from multiple user profiles."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            mock_dir.exists.return_value = True

            # Create user profile files
            profile1 = {"user_id": "user1", "portfolio_tickers": ["AAPL", "MSFT"]}
            profile2 = {"user_id": "user2", "portfolio_tickers": ["MSFT", "GOOGL"]}
            profile3 = {"user_id": "user3", "portfolio_tickers": ["TSLA"]}

            import json

            (tmpdir_path / "user1_profile.json").write_text(json.dumps(profile1))
            (tmpdir_path / "user2_profile.json").write_text(json.dumps(profile2))
            (tmpdir_path / "user3_profile.json").write_text(json.dumps(profile3))

            mock_dir.glob.return_value = [
                tmpdir_path / "user1_profile.json",
                tmpdir_path / "user2_profile.json",
                tmpdir_path / "user3_profile.json",
            ]

            # Get tickers
            tickers = get_all_unique_tickers()

            # Should return sorted unique tickers
            assert tickers == ["AAPL", "GOOGL", "MSFT", "TSLA"]

    @patch("finnews.scraper.scheduler.USER_PROFILES_DIR")
    def test_get_all_unique_tickers_empty(self, mock_dir):
        """Test when no user profiles exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            mock_dir.exists.return_value = True
            mock_dir.glob.return_value = []

            tickers = get_all_unique_tickers()

            assert tickers == []

    @patch("finnews.scraper.scheduler.USER_PROFILES_DIR")
    def test_get_all_unique_tickers_directory_missing(self, mock_dir):
        """Test when user profiles directory doesn't exist."""
        mock_dir.exists.return_value = False

        tickers = get_all_unique_tickers()

        assert tickers == []

    @patch("finnews.scraper.scheduler.USER_PROFILES_DIR")
    def test_get_all_unique_tickers_invalid_json(self, mock_dir):
        """Test handling of invalid JSON in profile files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            mock_dir.exists.return_value = True

            # Create invalid and valid profiles
            (tmpdir_path / "invalid_profile.json").write_text("invalid json")

            import json

            valid_profile = {"user_id": "user2", "portfolio_tickers": ["AAPL"]}
            (tmpdir_path / "user2_profile.json").write_text(json.dumps(valid_profile))

            mock_dir.glob.return_value = [
                tmpdir_path / "invalid_profile.json",
                tmpdir_path / "user2_profile.json",
            ]

            # Should skip invalid file and process valid one
            tickers = get_all_unique_tickers()

            assert tickers == ["AAPL"]

    @patch("finnews.scraper.scheduler.USER_PROFILES_DIR")
    def test_get_all_unique_tickers_case_normalization(self, mock_dir):
        """Test that tickers are normalized to uppercase."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            mock_dir.exists.return_value = True

            import json

            profile = {"user_id": "user1", "portfolio_tickers": ["aapl", "MsFt", "GOOGL"]}
            (tmpdir_path / "user1_profile.json").write_text(json.dumps(profile))

            mock_dir.glob.return_value = [tmpdir_path / "user1_profile.json"]

            tickers = get_all_unique_tickers()

            # All should be uppercase and sorted
            assert tickers == ["AAPL", "GOOGL", "MSFT"]


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
        mock_run_scraper.assert_called_once_with(["AAPL", "MSFT", "GOOGL"], wait=True)

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

        # Should run scraper in non-blocking mode
        mock_run_scraper.assert_called_once_with(["TSLA", "NVDA"], wait=False)

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
        mock_run_scraper.assert_called_once_with(["AAPL"], wait=False)


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
        mock_run_scraper.assert_called_once_with(["AAPL", "MSFT"], wait=True)

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
