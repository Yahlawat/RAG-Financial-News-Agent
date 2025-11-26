"""API endpoints for scraping control and status."""

import logging
import threading
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from finnews.scraper.metadata import (
    get_scrape_status,
    get_tickers_metadata,
    reset_scrape_status,
)
from finnews.scraper.runner import run_spider_with_tickers
from finnews.ui.user_profile import get_portfolio_tickers

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/scrape", tags=["scraping"])

# Global lock to prevent concurrent scraping
_scrape_lock = threading.Lock()
_scrape_thread: Optional[threading.Thread] = None


class ScrapeStartRequest(BaseModel):
    """Request model for starting a scrape."""

    user_id: str


class ScrapeStartResponse(BaseModel):
    """Response model for scrape start."""

    status: str
    message: str
    tickers: List[str]


class ScrapeStatusResponse(BaseModel):
    """Response model for scrape status."""

    status: str
    started_at: Optional[str]
    tickers_in_progress: List[str]
    completed: int
    total: int
    articles_found: int
    time_elapsed_seconds: Optional[float]
    pipeline_stage: str
    stage_message: str


class TickerMetadataRequest(BaseModel):
    """Request model for ticker metadata."""

    tickers: List[str]


class TickerMetadataItem(BaseModel):
    """Metadata for a single ticker."""

    ticker: str
    last_scraped: Optional[str]
    articles_count: int
    never_scraped: bool


class TickerMetadataResponse(BaseModel):
    """Response model for ticker metadata."""

    metadata: List[TickerMetadataItem]


def _run_scraper_thread(tickers: List[str]) -> None:
    """Background thread function to run the scraper.

    Args:
        tickers: List of tickers to scrape
    """
    try:
        run_spider_with_tickers(tickers)
    except Exception as e:
        logger.error(f"Scraper thread error: {e}", exc_info=True)
    finally:
        # Release the lock when done
        global _scrape_thread
        _scrape_thread = None


@router.post("/start", response_model=ScrapeStartResponse)
async def start_scrape(request: ScrapeStartRequest):
    """Start scraping for a user's portfolio tickers.

    Args:
        request: Contains user_id

    Returns:
        ScrapeStartResponse with status and ticker list

    Raises:
        HTTPException: If scraping is already in progress or user has no tickers
    """
    global _scrape_thread

    # Check if scraping is already running
    if _scrape_thread is not None and _scrape_thread.is_alive():
        return ScrapeStartResponse(
            status="already_running", message="A scraping job is already in progress", tickers=[]
        )

    # Get user's portfolio tickers
    tickers = get_portfolio_tickers(request.user_id)

    if not tickers:
        raise HTTPException(status_code=400, detail="User has no portfolio tickers to scrape")

    # Reset scrape status before starting
    reset_scrape_status()

    # Start scraping in background thread
    _scrape_thread = threading.Thread(target=_run_scraper_thread, args=(tickers,), daemon=True)
    _scrape_thread.start()

    logger.info(f"Started scraping {len(tickers)} tickers for user {request.user_id}")

    return ScrapeStartResponse(
        status="started", message=f"Started scraping {len(tickers)} tickers", tickers=tickers
    )


@router.get("/status", response_model=ScrapeStatusResponse)
async def get_scrape_status_endpoint():
    """Get the current scraping status.

    Returns:
        ScrapeStatusResponse with current progress
    """
    status = get_scrape_status()

    # Calculate time elapsed if scraping is running
    time_elapsed = None
    if status.started_at:
        try:
            start_time = datetime.fromisoformat(status.started_at)
            time_elapsed = (datetime.now() - start_time).total_seconds()

            # Auto-reset stuck "running" states (older than 30 minutes)
            # This handles cases where the scraper crashed without updating status
            if status.status == "running" and time_elapsed > 1800:  # 30 minutes
                logger.warning(
                    f"Auto-resetting stuck scraping job (running for {int(time_elapsed)}s). "
                    "This likely indicates the scraper crashed."
                )
                reset_scrape_status()
                status = get_scrape_status()
                time_elapsed = None
        except ValueError:
            pass

    # Generate stage-specific message
    stage_message = _get_stage_message(status)

    return ScrapeStatusResponse(
        status=status.status,
        started_at=status.started_at,
        tickers_in_progress=status.tickers_in_progress,
        completed=status.completed,
        total=status.total,
        articles_found=status.articles_found,
        time_elapsed_seconds=time_elapsed,
        pipeline_stage=status.pipeline_stage,
        stage_message=stage_message,
    )


STAGE_MESSAGES = {
    "idle": "Ready to scrape",
    "scraping": "Scraping articles...",
    "chunking": "Processing article chunks...",
    "chunking_complete": "Processing article chunks...",
    "embedding": "Generating embeddings...",
    "completed": "Pipeline complete! Articles ready for querying",
    "error": "Pipeline encountered an error",
}


def _get_stage_message(status) -> str:
    """Generate a human-readable message for the current pipeline stage.

    Args:
        status: ScrapeStatus object

    Returns:
        Human-readable stage message
    """
    stage = status.pipeline_stage

    if stage.startswith("error_"):
        error_stage = stage.replace("error_", "")
        return f"Error in {error_stage} stage"

    msg = STAGE_MESSAGES.get(stage, f"Status: {stage}")
    if stage == "scraping" and status.total > 0:
        msg = f"Scraping articles... {status.completed}/{status.total} tickers"
    return msg


@router.post("/tickers/metadata", response_model=TickerMetadataResponse)
async def get_tickers_metadata_endpoint(request: TickerMetadataRequest):
    """Get scraping metadata for specific tickers.

    Args:
        request: Contains list of tickers

    Returns:
        TickerMetadataResponse with metadata for each ticker
    """
    metadata_dict = get_tickers_metadata(request.tickers)

    items = [
        TickerMetadataItem(
            ticker=ticker,
            last_scraped=metadata.last_scraped if metadata else None,
            articles_count=metadata.articles_count if metadata else 0,
            never_scraped=not bool(metadata),
        )
        for ticker, metadata in metadata_dict.items()
    ]

    return TickerMetadataResponse(metadata=items)


@router.post("/reset")
async def reset_scrape_status_endpoint():
    """Reset scrape status to idle.

    This endpoint is typically called by the UI after displaying
    a completion message to clear the status for the next scrape.

    Returns:
        Dict with status confirmation
    """
    reset_scrape_status()
    logger.info("Scrape status reset to idle via API endpoint")
    return {"status": "reset", "message": "Scrape status reset to idle"}
