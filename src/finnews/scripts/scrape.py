"""
Manual scraping script.

Supports reading tickers from data/tickers.txt or via CLI arguments.
"""

import argparse
import logging
import sys

from finnews.common.logging import setup_logging
from finnews.common.paths import ensure_dirs
from finnews.common.ticker_manager import load_tickers
from finnews.scraper.runner import run_scraper

setup_logging(component="scraper", level=logging.INFO, console=True)
logger = logging.getLogger(__name__)


def main() -> int:
    """CLI entry point for manual scraping."""
    parser = argparse.ArgumentParser(
        description="Manual scraping for financial news articles"
    )
    parser.add_argument(
        "--tickers",
        type=str,
        help="Comma-separated list of tickers to scrape (overrides tickers.txt)",
    )
    args = parser.parse_args()

    ensure_dirs()

    logger.info("=" * 60)
    logger.info("Manual Scraping")
    logger.info("=" * 60)

    if args.tickers:
        tickers = [t.strip().upper() for t in args.tickers.split(",") if t.strip()]
        logger.info(f"Using tickers from CLI argument: {', '.join(tickers)}")
    else:
        logger.info("Loading tickers from data/tickers.txt...")
        tickers = load_tickers()

        if not tickers:
            logger.warning("No tickers found in data/tickers.txt")
            logger.info("Add tickers to data/tickers.txt (one per line) or use --tickers flag")
            return 1

        logger.info(f"Found {len(tickers)} ticker(s): {', '.join(tickers)}")

    logger.info("")

    try:
        logger.info("Starting scraper...")
        run_scraper(tickers)
        logger.info("Scraping completed successfully!")
        logger.info("")
        logger.info("Next steps:")
        logger.info("  - Process articles: finnews-chunk")
        logger.info("  - Generate embeddings: finnews-embed")
        logger.info("  - Or run full pipeline: finnews-pipeline")

        return 0

    except Exception as e:
        logger.error("Scraping failed!")
        logger.exception(f"Error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
