"""Metadata tracking for scraper status."""

import logging
from datetime import datetime
from pathlib import Path
from threading import Lock

from finnews.common.config import settings
from finnews.common.io_utils import read_json, write_json

logger = logging.getLogger(__name__)

# Thread lock for concurrent access to metadata file
_metadata_lock = Lock()


def _read_metadata() -> dict:
    """Read metadata from file."""
    metadata_path = str(settings.SCRAPE_METADATA_FILE)
    data = read_json(metadata_path)

    if not data:
        # Initialize with empty structure
        data = {
            "current_scrape": {"status": "idle"},
            "tickers": {},
        }

    return data


def _write_metadata(data: dict) -> None:
    """Write metadata to file."""
    metadata_path = str(settings.SCRAPE_METADATA_FILE)
    write_json(metadata_path, data)


def get_scrape_status() -> dict:
    """Get current scraping job status."""
    with _metadata_lock:
        data = _read_metadata()
        status = data.get("current_scrape", {"status": "idle"})

        if "progress" not in status and status.get("status") != "idle":
            status["progress"] = {
                "completed": status.get("completed", 0),
                "total": status.get("total", 0),
            }

        return status


def start_scrape(tickers: list[str]) -> None:
    """Mark scraping as started."""
    with _metadata_lock:
        data = _read_metadata()
        data["current_scrape"] = {
            "status": "running",
            "started_at": datetime.now().isoformat(),
            "progress": {
                "completed": 0,
                "total": len(tickers),
            },
            "articles_found": 0,
        }
        _write_metadata(data)
        logger.info(f"Started scraping {len(tickers)} tickers")


def complete_scrape(status: str = "completed", articles_found: int = 0) -> None:
    """Mark scraping as completed."""
    with _metadata_lock:
        data = _read_metadata()
        scrape = data.get("current_scrape", {})
        scrape["status"] = status
        scrape["completed_at"] = datetime.now().isoformat()
        scrape["articles_found"] = articles_found
        data["current_scrape"] = scrape
        _write_metadata(data)
        logger.info(f"Scraping {status}: {articles_found} articles found")


def reset_scrape_status() -> None:
    """Reset scraping status to idle."""
    with _metadata_lock:
        data = _read_metadata()
        data["current_scrape"] = {"status": "idle"}
        _write_metadata(data)
        logger.info("Reset scraping status to idle")


def start_chunking(total_articles: int = 0) -> None:
    """Mark post-processing stage as started."""
    with _metadata_lock:
        data = _read_metadata()
        scrape = data.get("current_scrape", {})
        scrape["status"] = "running"
        scrape["pipeline_stage"] = "processing"
        data["current_scrape"] = scrape
        _write_metadata(data)
        logger.info(f"Started post-processing {total_articles} articles")


def complete_pipeline(status: str = "completed") -> None:
    """Mark pipeline as completed."""
    with _metadata_lock:
        data = _read_metadata()
        scrape = data.get("current_scrape", {})
        scrape["status"] = status
        scrape["pipeline_stage"] = "completed" if status == "completed" else "error"
        data["current_scrape"] = scrape
        _write_metadata(data)

        if status == "completed":
            logger.info("Full pipeline completed successfully")
        else:
            logger.error("Pipeline completed with errors")


def set_pipeline_error(stage: str, error_message: str = "") -> None:
    """Mark pipeline as failed."""
    with _metadata_lock:
        data = _read_metadata()
        scrape = data.get("current_scrape", {})
        scrape["status"] = "error"
        scrape["pipeline_stage"] = "error"
        data["current_scrape"] = scrape
        _write_metadata(data)
        logger.error(f"Pipeline error in {stage} stage: {error_message}")


def get_tickers_metadata(ticker_list: list[str]) -> dict[str, dict | None]:
    """Get metadata for multiple tickers."""
    with _metadata_lock:
        data = _read_metadata()
        tickers_data = data.get("tickers", {})

        result = {}
        for ticker in ticker_list:
            ticker_upper = ticker.upper()
            result[ticker_upper] = tickers_data.get(ticker_upper)

        return result


def update_ticker_scrape(ticker: str, articles_count: int = 0) -> None:
    """Update metadata when a ticker is scraped."""
    with _metadata_lock:
        data = _read_metadata()
        ticker_upper = ticker.upper()
        data["tickers"][ticker_upper] = {
            "last_scraped": datetime.now().isoformat(),
            "articles_count": articles_count,
        }
        _write_metadata(data)
        logger.info(f"Updated metadata for ticker {ticker_upper}: {articles_count} articles")


def is_scrape_running() -> bool:
    """Check if a scrape is currently running."""
    status = get_scrape_status()
    return status.get("status") == "running"
