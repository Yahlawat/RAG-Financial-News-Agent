import logging
import multiprocessing
from typing import Optional

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from finnews.common.config import settings
from finnews.common.logging import setup_logging
from finnews.scraper.metadata import is_scrape_running
from finnews.scraper.runner import run_scraper
from finnews.scripts.pipeline import run_pipeline

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


def _scraper_process_main(tickers: list[str]) -> None:
    """Entry point of the scraper child process."""
    setup_logging(component="scraper", level=logging.INFO, console=True)
    run_scraper(tickers)


def run_scraper_in_subprocess(tickers: list[str]) -> None:
    """Run the scraper in a fresh process.

    Scrapy's Twisted reactor must run in the main thread and cannot be restarted,
    so it can't run directly in the scheduler's worker thread.
    """
    process = multiprocessing.get_context("spawn").Process(
        target=_scraper_process_main, args=(tickers,)
    )
    process.start()
    process.join()
    if process.exitcode != 0:
        raise RuntimeError(f"Scraper process exited with code {process.exitcode}")


def run_scheduled_scrape() -> None:
    """Main scheduled job: cleanup, scrape, chunk and embed.

    Only scraping runs in a child process. Chunking and embedding run here, so the
    vector store updates go through this process's Chroma client and are visible
    to the API immediately.
    """
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

        run_pipeline(tickers, scrape=run_scraper_in_subprocess)

        logger.info("Scheduled scrape completed successfully")

    except Exception as e:
        logger.exception("Scheduled scrape failed: %s", e)


def scrape_new_tickers(new_tickers: list[str]) -> None:
    """On-demand scrape, chunk and embed for newly added tickers."""
    if not new_tickers:
        logger.warning("No tickers provided for on-demand scraping")
        return

    # Prevent concurrent scrapes
    if is_scrape_running():
        logger.warning("Scrape already in progress. Skipping on-demand scrape.")
        return

    logger.info("Starting on-demand scrape for new tickers: %s", new_tickers)

    try:
        run_pipeline(new_tickers, scrape=run_scraper_in_subprocess, cleanup=False)
        logger.info("On-demand scrape completed for %d ticker(s)", len(new_tickers))

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
