"""Full data pipeline: cleanup → scrape → chunk → embed."""

import argparse
import logging
import sys
from collections.abc import Callable

from finnews.common.logging import setup_logging
from finnews.common.paths import ensure_dirs
from finnews.common.ticker_manager import load_tickers
from finnews.scraper.metadata import complete_pipeline, set_pipeline_error, set_pipeline_stage

logger = logging.getLogger(__name__)


def run_pipeline(
    tickers: list[str],
    scrape: Callable[[list[str]], None] | None = None,
    cleanup: bool = True,
) -> None:
    """Run cleanup → scrape → chunk → embed, raising if any step fails.

    Args:
        tickers: Ticker symbols to scrape
        scrape: Function that scrapes the given tickers (default: run_scraper in this process)
        cleanup: Whether to remove old articles first (default: True)
    """
    from finnews.rag.chunker import main as chunker_main
    from finnews.rag.embedder import main as embedder_main
    from finnews.scraper.runner import run_scraper
    from finnews.scripts.cleanup_old_articles import cleanup_and_rebuild

    scrape = scrape or run_scraper

    # (description, metadata stage, step). Scraping reports its own status.
    steps = []
    if cleanup:
        steps.append(
            ("Cleaning up old articles", None, lambda: cleanup_and_rebuild(days_to_keep=30, backup=True))
        )
    steps += [
        ("Scraping financial news", None, lambda: scrape(tickers)),
        ("Chunking articles", "chunking", chunker_main),
        ("Generating embeddings", "embedding", embedder_main),
    ]

    for number, (description, stage, step) in enumerate(steps, 1):
        logger.info(f"Step {number}/{len(steps)}: {description}...")
        if stage:
            set_pipeline_stage(stage)
        try:
            step()
        except Exception as e:
            logger.error(f"Step {number}/{len(steps)} failed: {e}")
            if stage:
                set_pipeline_error(stage, str(e))
            raise
        logger.info(f"Step {number}/{len(steps)} completed successfully")
        logger.info("")

    complete_pipeline(status="completed")


def main() -> int:
    """CLI entry point for full data pipeline."""
    setup_logging(component="pipeline", level=logging.INFO, console=True, unified=True)

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
        run_pipeline(tickers)
    except Exception:
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
