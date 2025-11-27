"""
Manual scraping script for development and testing.

This script provides a CLI interface for manually triggering news scraping.
It aggregates all unique tickers from user portfolios and runs the scraper.

Note: For production use, scraping is automated via the scheduler.
This command is intended for development, testing, and debugging purposes.
"""

import logging
import sys

from finnews.common.config import settings
from finnews.common.logging import setup_logging
from finnews.common.paths import ensure_dirs
from finnews.scraper.runner import run_scraper
from finnews.ui.user_profile import get_all_unique_tickers

# Setup logging
setup_logging(component="scraper", level=logging.INFO, console=True)
logger = logging.getLogger(__name__)


def main() -> int:
    """
    CLI entry point for manual scraping (dev/testing only).

    Loads all unique tickers from user portfolios and runs the scraper.
    For production use, scraping is automated via the scheduler.

    Returns:
        Exit code (0 for success, 1 for error)
    """
    ensure_dirs()

    logger.info("=" * 60)
    logger.info("Manual Scraping (Development/Testing Mode)")
    logger.info("=" * 60)

    # Load tickers from user portfolios
    logger.info("Loading tickers from user portfolios...")
    tickers = get_all_unique_tickers()

    if not tickers:
        logger.warning("No tickers found in any user portfolio.")
        return 1

    logger.info(f"Found {len(tickers)} unique ticker(s): {', '.join(tickers)}")
    logger.info("")

    # Run the scraper
    try:
        logger.info("Starting scraper...")
        run_scraper(tickers)
        logger.info("Scraping completed successfully!")
     
        if settings.AUTO_PROCESS_PIPELINE:
            logger.info("Auto-processing is enabled. Articles will be chunked and embedded.")
        else:
            logger.info("Next steps:")
            logger.info("  1. Process articles: finnews-chunk")
            logger.info("  2. Generate embeddings: finnews-embed")

        return 0

    except Exception as e:
        logger.error("Scraping failed!")
        logger.exception(f"Error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
