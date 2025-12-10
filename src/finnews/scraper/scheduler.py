"""
Automated scraping scheduler for financial news.

This module provides scheduled and on-demand scraping functionality:
- Daily scheduled scraping of all unique tickers across all user portfolios
- On-demand scraping for newly added tickers
"""

import logging

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from finnews.common.config import settings
from finnews.common.logging import setup_logging
from finnews.scraper.runner import run_scraper

setup_logging(component="scheduler", level=logging.INFO, console=True)
logger = logging.getLogger(__name__)

# Global scheduler instance
_scheduler: BackgroundScheduler | None = None


def get_all_unique_tickers() -> list[str]:
    """
    Get all unique tickers from all user portfolios.

    Returns:
        List of unique ticker symbols (uppercase, sorted)
    """
    from finnews.ui.user_profile import USER_PROFILES_DIR

    tickers = set()

    try:
        if not USER_PROFILES_DIR.exists():
            logger.warning("User profiles directory does not exist: %s", USER_PROFILES_DIR)
            return []

        # Load all user profile files
        for profile_file in USER_PROFILES_DIR.glob("*_profile.json"):
            try:
                import json

                with open(profile_file, "r", encoding="utf-8") as f:
                    profile_data = json.load(f)
                    portfolio_tickers = profile_data.get("portfolio_tickers", [])
                    tickers.update(t.strip().upper() for t in portfolio_tickers if t.strip())

            except Exception as e:
                logger.error("Failed to load profile %s: %s", profile_file, e)
                continue

        ticker_list = sorted(list(tickers))
        logger.info("Aggregated %d unique tickers from all user portfolios", len(ticker_list))
        return ticker_list

    except Exception as e:
        logger.exception("Failed to aggregate tickers: %s", e)
        return []


def run_scheduled_scrape() -> None:
    """
    Main scheduled scraping job - runs daily to scrape all unique tickers.
    """
    logger.info("Starting scheduled scraping job")

    try:
        tickers = get_all_unique_tickers()

        if not tickers:
            logger.warning("No tickers found across all user portfolios. Skipping scrape.")
            return

        logger.info("Scheduled scrape starting for %d tickers: %s", len(tickers), tickers)

        # Run the scraper
        run_scraper(tickers)

        logger.info("Scheduled scrape completed successfully")

    except Exception as e:
        logger.exception("Scheduled scrape failed: %s", e)


def scrape_new_tickers(new_tickers: list[str]) -> None:
    """
    On-demand scraping for newly added tickers.

    Args:
        new_tickers: List of ticker symbols to scrape immediately
    """
    if not new_tickers:
        logger.warning("No tickers provided for on-demand scraping")
        return

    logger.info("Starting on-demand scrape for new tickers: %s", new_tickers)

    try:
        # Run scraper for the new tickers
        run_scraper(new_tickers)
        logger.info("On-demand scrape initiated for %d ticker(s)", len(new_tickers))

    except Exception as e:
        logger.exception("On-demand scrape failed: %s", e)


def start_scheduler() -> BackgroundScheduler:
    """
    Initialize and start the background scheduler.

    Returns:
        The running scheduler instance
    """
    global _scheduler

    if _scheduler is not None:
        logger.warning("Scheduler already running")
        return _scheduler

    logger.info("Initializing scraping scheduler")

    _scheduler = BackgroundScheduler(
        timezone="UTC",  # Use UTC for consistency
        daemon=True,  # Daemon thread - won't block shutdown
    )

    # Add daily scraping job
    if settings.SCRAPE_SCHEDULE_ENABLED:
        trigger = CronTrigger(
            hour=settings.SCRAPE_SCHEDULE_HOUR,
            minute=settings.SCRAPE_SCHEDULE_MINUTE,
            timezone="UTC",
        )

        _scheduler.add_job(
            run_scheduled_scrape,
            trigger=trigger,
            id="daily_scrape",
            name="Daily Financial News Scrape",
            replace_existing=True,
        )

        logger.info(
            "Scheduled daily scraping at %02d:%02d UTC",
            settings.SCRAPE_SCHEDULE_HOUR,
            settings.SCRAPE_SCHEDULE_MINUTE,
        )
    else:
        logger.info("Scheduled scraping is disabled in settings")

    _scheduler.start()
    logger.info("Scheduler started successfully")

    return _scheduler


def stop_scheduler() -> None:
    """
    Stop the background scheduler gracefully.
    """
    global _scheduler

    if _scheduler is None:
        logger.warning("Scheduler not running")
        return

    logger.info("Stopping scheduler")
    _scheduler.shutdown(wait=True)
    _scheduler = None
    logger.info("Scheduler stopped")


def get_scheduler() -> Optional[BackgroundScheduler]:
    """
    Get the current scheduler instance.

    Returns:
        Scheduler instance if running, None otherwise
    """
    return _scheduler
