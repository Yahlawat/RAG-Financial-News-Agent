"""Ticker-level scrape metadata tracking.

Note: All timestamps use naive datetime objects (no timezone info) in local time.
This ensures consistency across the application. If timezone-aware timestamps
are needed in the future, update all datetime.now() calls to datetime.now(timezone.utc).
"""

import logging
import threading
from datetime import datetime

from finnews.common.config import settings
from finnews.common.io_utils import read_json, write_json

logger = logging.getLogger(__name__)

# Thread lock for concurrent access to metadata file
_metadata_lock = threading.Lock()


class TickerMetadata:
    """Metadata for a single ticker's scraping history."""

    def __init__(
        self,
        last_scraped: str | None = None,
        articles_count: int = 0,
    ):
        self.last_scraped = last_scraped
        self.articles_count = articles_count

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "last_scraped": self.last_scraped,
            "articles_count": self.articles_count,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "TickerMetadata":
        """Create from dictionary."""
        return cls(
            last_scraped=data.get("last_scraped"),
            articles_count=data.get("articles_count", 0),
        )


class ScrapeStatus:
    """Current scraping job status."""

    def __init__(
        self,
        status: str = "idle",
        started_at: str | None = None,
        tickers_in_progress: list[str] | None = None,
        completed: int = 0,
        total: int = 0,
        articles_found: int = 0,
        pipeline_stage: str = "idle",
    ):
        self.status = status  # idle, running, completed, error
        self.started_at = started_at
        self.tickers_in_progress = tickers_in_progress or []
        self.completed = completed
        self.total = total
        self.articles_found = articles_found
        # Pipeline stage: "idle", "running", "processing", "completed"
        self.pipeline_stage = pipeline_stage

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "status": self.status,
            "started_at": self.started_at,
            "tickers_in_progress": self.tickers_in_progress,
            "progress": {
                "completed": self.completed,
                "total": self.total,
            },
            "articles_found": self.articles_found,
            "pipeline_stage": self.pipeline_stage,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "ScrapeStatus":
        """Create from dictionary."""
        progress = data.get("progress", {})
        return cls(
            status=data.get("status", "idle"),
            started_at=data.get("started_at"),
            tickers_in_progress=data.get("tickers_in_progress", []),
            completed=progress.get("completed", 0),
            total=progress.get("total", 0),
            articles_found=data.get("articles_found", 0),
            pipeline_stage=data.get("pipeline_stage", "idle"),
        )


def _read_metadata() -> dict:
    """Read metadata from file.

    Returns:
        Dictionary with 'tickers' and 'current_scrape' keys
    """
    metadata_path = str(settings.SCRAPE_METADATA_FILE)
    data = read_json(metadata_path)

    if not data:
        # Initialize with empty structure
        data = {
            "tickers": {},
            "current_scrape": ScrapeStatus().to_dict(),
        }

    return data


def _write_metadata(data: dict) -> None:
    """Write metadata to file.

    Args:
        data: Dictionary with 'tickers' and 'current_scrape' keys
    """
    metadata_path = str(settings.SCRAPE_METADATA_FILE)
    write_json(metadata_path, data)


def get_ticker_last_scrape(ticker: str) -> TickerMetadata | None:
    """Get the last scrape metadata for a specific ticker.

    Args:
        ticker: The ticker symbol

    Returns:
        TickerMetadata if ticker has been scraped, None otherwise
    """
    with _metadata_lock:
        data = _read_metadata()
        ticker_data = data.get("tickers", {}).get(ticker.upper())

        if ticker_data:
            return TickerMetadata.from_dict(ticker_data)
        return None


def get_tickers_metadata(ticker_list: list[str]) -> dict[str, TickerMetadata | None]:
    """Get metadata for multiple tickers.

    Args:
        ticker_list: List of ticker symbols

    Returns:
        Dictionary mapping ticker to TickerMetadata (or None if never scraped)
    """
    with _metadata_lock:
        data = _read_metadata()
        tickers_data = data.get("tickers", {})

        result = {}
        for ticker in ticker_list:
            ticker_upper = ticker.upper()
            if ticker_upper in tickers_data:
                result[ticker_upper] = TickerMetadata.from_dict(tickers_data[ticker_upper])
            else:
                result[ticker_upper] = None

        return result


def update_ticker_scrape(ticker: str, articles_count: int = 0) -> None:
    """Update metadata when a ticker is scraped.

    Args:
        ticker: The ticker symbol
        articles_count: Number of articles found for this ticker
    """
    with _metadata_lock:
        data = _read_metadata()

        # Update ticker metadata
        ticker_upper = ticker.upper()
        data["tickers"][ticker_upper] = {
            "last_scraped": datetime.now().isoformat(),
            "articles_count": articles_count,
        }

        _write_metadata(data)
        logger.info(f"Updated metadata for ticker {ticker_upper}: {articles_count} articles")


def get_scrape_status() -> ScrapeStatus:
    """Get the current scraping job status.

    Returns:
        ScrapeStatus object
    """
    with _metadata_lock:
        data = _read_metadata()
        status_data = data.get("current_scrape", {})
        return ScrapeStatus.from_dict(status_data)


def start_scrape(tickers: list[str]) -> None:
    """Mark scraping as started.

    Args:
        tickers: List of tickers to be scraped
    """
    with _metadata_lock:
        data = _read_metadata()

        data["current_scrape"] = {
            "status": "running",
            "started_at": datetime.now().isoformat(),
            "tickers_in_progress": [t.upper() for t in tickers],
            "progress": {
                "completed": 0,
                "total": len(tickers),
            },
            "articles_found": 0,
            "pipeline_stage": "running",
        }

        _write_metadata(data)
        logger.info(f"Started scraping {len(tickers)} tickers")


def update_scrape_progress(completed: int, articles_found: int) -> None:
    """Update scraping progress.

    Args:
        completed: Number of tickers completed
        articles_found: Total articles found so far
    """
    with _metadata_lock:
        data = _read_metadata()
        current_scrape = data.get("current_scrape", {})

        current_scrape["progress"]["completed"] = completed
        current_scrape["articles_found"] = articles_found
        data["current_scrape"] = current_scrape

        _write_metadata(data)


def complete_scrape(status: str = "completed", articles_found: int = 0) -> None:
    """Mark scraping as completed.

    Args:
        status: Final status (completed or error)
        articles_found: Total articles found
    """
    with _metadata_lock:
        data = _read_metadata()
        current_scrape = data.get("current_scrape", {})

        current_scrape["status"] = status
        current_scrape["articles_found"] = articles_found
        data["current_scrape"] = current_scrape

        _write_metadata(data)
        logger.info(f"Scraping {status}: {articles_found} articles found")


def reset_scrape_status() -> None:
    """Reset scraping status to idle."""
    with _metadata_lock:
        data = _read_metadata()
        data["current_scrape"] = ScrapeStatus().to_dict()
        _write_metadata(data)
        logger.info("Reset scraping status to idle")


def start_chunking(total_articles: int = 0) -> None:
    """Mark post-processing (chunking + embedding) stage as started.

    Args:
        total_articles: Total number of articles scraped
    """
    with _metadata_lock:
        data = _read_metadata()
        current_scrape = data.get("current_scrape", {})

        current_scrape["pipeline_stage"] = "processing"
        current_scrape["status"] = "running"
        data["current_scrape"] = current_scrape

        _write_metadata(data)
        logger.info(f"Started post-processing {total_articles} articles")


def complete_chunking() -> None:
    """Mark chunking stage as completed (now a no-op, kept for backward compatibility)."""
    logger.info("Chunking completed (continuing to embedding)")


def start_embedding() -> None:
    """Mark embedding stage as started (now a no-op since processing stage covers both)."""
    logger.info("Started embedding generation")


def complete_pipeline(status: str = "completed") -> None:
    """Mark the entire pipeline as completed.

    Args:
        status: Final status (completed or error)
    """
    with _metadata_lock:
        data = _read_metadata()
        current_scrape = data.get("current_scrape", {})

        if status == "completed":
            current_scrape["pipeline_stage"] = "completed"
            current_scrape["status"] = "completed"
            logger.info("Full pipeline completed successfully")
        else:
            current_scrape["pipeline_stage"] = "error"
            current_scrape["status"] = "error"
            logger.error("Pipeline completed with errors")

        data["current_scrape"] = current_scrape
        _write_metadata(data)
        # Status will be reset by the UI after displaying the completion message


def set_pipeline_error(stage: str, error_message: str = "") -> None:
    """Mark pipeline as failed at a specific stage.

    Args:
        stage: The pipeline stage where error occurred
        error_message: Optional error description
    """
    with _metadata_lock:
        data = _read_metadata()
        current_scrape = data.get("current_scrape", {})

        current_scrape["pipeline_stage"] = "error"
        current_scrape["status"] = "error"
        data["current_scrape"] = current_scrape

        _write_metadata(data)
        logger.error(f"Pipeline error in {stage} stage: {error_message}")
