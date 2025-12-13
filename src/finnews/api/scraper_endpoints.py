"""API endpoints for scraping status monitoring and ticker metadata.
"""

import logging
from datetime import datetime

from fastapi import APIRouter
from pydantic import BaseModel

from finnews.scraper.metadata import (
    get_scrape_status,
    get_tickers_metadata,
    reset_scrape_status,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/scrape", tags=["scraping"])


class ScrapeStatusResponse(BaseModel):
    """Response model for scrape status."""

    status: str
    started_at: str | None
    tickers_in_progress: list[str]
    completed: int
    total: int
    articles_found: int
    time_elapsed_seconds: float | None
    pipeline_stage: str
    stage_message: str


class TickerMetadataRequest(BaseModel):
    """Request model for ticker metadata."""

    tickers: list[str]


class TickerMetadataItem(BaseModel):
    """Metadata for a single ticker."""

    ticker: str
    last_scraped: str | None
    articles_count: int
    never_scraped: bool


class TickerMetadataResponse(BaseModel):
    """Response model for ticker metadata."""

    metadata: list[TickerMetadataItem]


# Note: Manual scraping endpoints /start and /reset have been removed
# Scraping is now automated via the scheduler (see scheduler.py)


@router.get("/status", response_model=ScrapeStatusResponse)
def get_scrape_status_endpoint():
    """Get the current scraping status.

    Returns:
        ScrapeStatusResponse with current progress
    """
    status = get_scrape_status()

    # Calculate time elapsed if scraping is running
    time_elapsed = None
    if status.get("started_at"):
        try:
            start_time = datetime.fromisoformat(status["started_at"])
            time_elapsed = (datetime.now() - start_time).total_seconds()

            # Auto-reset stuck "running" states (older than 30 minutes)
            # This handles cases where the scraper crashed without updating status
            if status.get("status") == "running" and time_elapsed > 1800:  # 30 minutes
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

    # Extract progress data
    progress = status.get("progress", {})

    return ScrapeStatusResponse(
        status=status.get("status", "idle"),
        started_at=status.get("started_at"),
        tickers_in_progress=status.get("tickers_in_progress", []),
        completed=progress.get("completed", 0),
        total=progress.get("total", 0),
        articles_found=status.get("articles_found", 0),
        time_elapsed_seconds=time_elapsed,
        pipeline_stage=status.get("pipeline_stage", "idle"),
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


def _get_stage_message(status: dict) -> str:
    """Generate a human-readable message for the current pipeline stage.

    Args:
        status: Status dict

    Returns:
        Human-readable stage message
    """
    stage = status.get("pipeline_stage", "idle")

    if stage and stage.startswith("error_"):
        error_stage = stage.replace("error_", "")
        return f"Error in {error_stage} stage"

    msg = STAGE_MESSAGES.get(stage, f"Status: {stage}")
    progress = status.get("progress", {})
    if stage == "scraping" and progress.get("total", 0) > 0:
        msg = f"Scraping articles... {progress.get('completed', 0)}/{progress['total']} tickers"
    return msg


@router.post("/tickers/metadata", response_model=TickerMetadataResponse)
def get_tickers_metadata_endpoint(request: TickerMetadataRequest):
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
            last_scraped=metadata.get("last_scraped") if metadata else None,
            articles_count=metadata.get("articles_count", 0) if metadata else 0,
            never_scraped=not bool(metadata),
        )
        for ticker, metadata in metadata_dict.items()
    ]

    return TickerMetadataResponse(metadata=items)
