"""Full data pipeline: cleanup → scrape → chunk → embed."""

import argparse
import logging
import sys

from finnews.common.logging import setup_logging
from finnews.common.paths import ensure_dirs
from finnews.common.ticker_manager import load_tickers

setup_logging(component="pipeline", level=logging.INFO, console=True, unified=True)
logger = logging.getLogger(__name__)


def main() -> int:
    """CLI entry point for full data pipeline."""
    parser = argparse.ArgumentParser(
        description="Run full data pipeline: cleanup → scrape → chunk → embed"
    )
    parser.add_argument(
        "--tickers",
        type=str,
        help="Comma-separated list of tickers to scrape (overrides tickers.txt)",
    )
    args = parser.parse_args()

    ensure_dirs()

    logger.info("=" * 80)
    logger.info("FULL DATA PIPELINE")
    logger.info("=" * 80)

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
        logger.info("Step 1/4: Cleaning up old articles...")
        from finnews.scripts.cleanup_old_articles import cleanup_and_rebuild

        cleanup_and_rebuild(days_to_keep=30, backup=True)
        logger.info("Step 1/4 completed successfully")
        logger.info("")
    except Exception as e:
        logger.error(f"Step 1/4 failed: {e}")
        logger.exception("Full error details:")
        logger.error("Pipeline aborted. Fix errors and retry.")
        return 1

    try:
        logger.info("Step 2/4: Scraping financial news...")
        from finnews.scraper.runner import run_scraper

        run_scraper(tickers)
        logger.info("Step 2/4 completed successfully")
        logger.info("")
    except Exception as e:
        logger.error(f"Step 2/4 failed: {e}")
        logger.exception("Full error details:")
        logger.error("Pipeline aborted. Fix errors and retry.")
        return 1

    try:
        logger.info("Step 3/4: Chunking articles...")
        from finnews.rag.chunker import main as chunker_main

        chunker_main()
        logger.info("Step 3/4 completed successfully")
        logger.info("")
    except Exception as e:
        logger.error(f"Step 3/4 failed: {e}")
        logger.exception("Full error details:")
        logger.error("Pipeline aborted. Fix errors and retry.")
        return 1

    try:
        logger.info("Step 4/4: Generating embeddings...")
        from finnews.rag.embedder import main as embedder_main

        embedder_main()
        logger.info("Step 4/4 completed successfully")
        logger.info("")
    except Exception as e:
        logger.error(f"Step 4/4 failed: {e}")
        logger.exception("Full error details:")
        logger.error("Pipeline aborted. Fix errors and retry.")
        return 1

    logger.info("=" * 80)
    logger.info("Pipeline completed successfully!")
    logger.info("Articles are now queryable via finnews-ui or finnews-api")
    logger.info("=" * 80)

    return 0


if __name__ == "__main__":
    sys.exit(main())
