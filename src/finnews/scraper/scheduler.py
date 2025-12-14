import logging
from typing import Optional

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from finnews.common.config import settings
from finnews.common.logging import setup_logging
from finnews.scraper.metadata import is_scrape_running
from finnews.scraper.runner import run_scraper

setup_logging(component="scheduler", level=logging.INFO, console=True)
logger = logging.getLogger(__name__)

_scheduler: BackgroundScheduler | None = None


def get_all_unique_tickers() -> list[str]:
    """Get all tickers from the tickers.txt file."""
    from finnews.common.ticker_manager import load_tickers

    try:
        tickers = load_tickers()
        logger.info("Loaded %d tickers from tickers.txt", len(tickers))
        return tickers
    except Exception as e:
        logger.exception("Failed to load tickers: %s", e)
        return []


def run_scheduled_scrape() -> None:
    """Main scheduled scraping job."""
    logger.info("Starting scheduled scraping job")

    # Prevent concurrent scrapes
    if is_scrape_running():
        logger.warning("Scrape already in progress. Skipping scheduled scrape.")
        return

    try:
        tickers = get_all_unique_tickers()

        if not tickers:
            logger.warning("No tickers found in data/tickers.txt. Skipping scrape.")
            return

        logger.info("Scheduled scrape starting for %d tickers: %s", len(tickers), tickers)

        # Run the scraper
        run_scraper(tickers)

        logger.info("Scheduled scrape completed successfully")

    except Exception as e:
        logger.exception("Scheduled scrape failed: %s", e)


def scrape_new_tickers(new_tickers: list[str]) -> None:
    """On-demand scraping for newly added tickers."""
    if not new_tickers:
        logger.warning("No tickers provided for on-demand scraping")
        return

    # Prevent concurrent scrapes
    if is_scrape_running():
        logger.warning("Scrape already in progress. Skipping on-demand scrape.")
        return

    logger.info("Starting on-demand scrape for new tickers: %s", new_tickers)

    try:
        run_scraper(new_tickers)
        logger.info("On-demand scrape initiated for %d ticker(s)", len(new_tickers))

    except Exception as e:
        logger.exception("On-demand scrape failed: %s", e)


def start_scheduler() -> BackgroundScheduler:
    """Initialize and start the background scheduler."""
    global _scheduler

    if _scheduler is not None:
        logger.warning("Scheduler already running")
        return _scheduler

    logger.info("Initializing scraping scheduler")

    _scheduler = BackgroundScheduler(timezone="UTC", daemon=True)

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
    """Stop the background scheduler."""
    global _scheduler

    if _scheduler is None:
        logger.warning("Scheduler not running")
        return

    logger.info("Stopping scheduler")
    _scheduler.shutdown(wait=True)
    _scheduler = None
    logger.info("Scheduler stopped")


def get_scheduler() -> Optional[BackgroundScheduler]:
    """Get the current scheduler instance."""
    return _scheduler
