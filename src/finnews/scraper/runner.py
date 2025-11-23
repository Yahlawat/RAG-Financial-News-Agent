import logging
import subprocess
import sys
from typing import List

from scrapy import cmdline
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings

from finnews.scraper.spiders.finviz_spider import FinVizSpider
from finnews.scraper.metadata import (
    start_scrape,
    complete_scrape,
    reset_scrape_status,
    start_chunking,
    complete_chunking,
    start_embedding,
    complete_pipeline,
    set_pipeline_error,
)
from finnews.common.config import settings

logger = logging.getLogger(__name__)


def _run_post_processing_pipeline() -> None:
    """Run the chunking and embedding pipeline after scraping.

    This function is called automatically after successful scraping if
    AUTO_PROCESS_PIPELINE is enabled in settings.
    """
    try:
        # Step 1: Chunking
        logger.info("Step 1/2: Starting chunking process...")
        start_chunking(total_articles=0)  # Count will be updated by chunker

        from finnews.rag.chunker import main as chunker_main
        chunker_main()

        complete_chunking()
        logger.info("Chunking completed successfully")

        # Step 2: Embedding
        logger.info("Step 2/2: Starting embedding generation...")
        start_embedding()

        from finnews.rag.embedder import main as embedder_main
        embedder_main()

        logger.info("Embedding completed successfully")

        # Mark entire pipeline as complete
        complete_pipeline(status="completed")
        logger.info("Full pipeline completed successfully! Articles are now queryable.")

    except Exception as e:
        logger.error(f"Error in post-processing pipeline: {e}", exc_info=True)
        # Determine which stage failed
        from finnews.scraper.metadata import get_scrape_status
        status = get_scrape_status()

        if status.pipeline_stage == "chunking":
            set_pipeline_error("chunking", str(e))
        elif status.pipeline_stage == "embedding":
            set_pipeline_error("embedding", str(e))
        else:
            set_pipeline_error("unknown", str(e))

        raise


def main() -> None:
    """Run the spider using command line interface (backwards compatible)."""
    cmdline.execute(["scrapy", "crawl", "finviz_news"])


def run_spider_with_tickers(tickers: List[str]) -> None:
    """Run the spider with custom tickers using subprocess.

    This function runs scrapy in a separate process to avoid reactor issues.
    Designed to be called from a background thread in the API.

    Args:
        tickers: List of ticker symbols to scrape
    """
    if not tickers:
        logger.warning("No tickers provided, aborting scrape")
        return

    try:
        # Mark scraping as started
        start_scrape(tickers)
        logger.info(f"Starting scrape for {len(tickers)} tickers: {tickers}")

        # Calculate dynamic timeout based on number of tickers
        # Formula: (tickers × timeout_per_ticker) + buffer, with a minimum
        calculated_timeout = (len(tickers) * settings.SCRAPE_TIMEOUT_PER_TICKER) + settings.SCRAPE_TIMEOUT_BUFFER
        timeout_seconds = max(calculated_timeout, settings.SCRAPE_MIN_TIMEOUT)

        logger.info(
            f"Scraping timeout set to {timeout_seconds} seconds "
            f"({timeout_seconds // 60} minutes) for {len(tickers)} tickers"
        )

        # Create subprocess command to run scrapy
        # We use Python's -c flag to run a script directly
        tickers_str = ",".join(tickers)
        script = f"""
import sys
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings
from finnews.scraper.spiders.finviz_spider import FinVizSpider

tickers = '{tickers_str}'.split(',')
settings = get_project_settings()
process = CrawlerProcess(settings)
process.crawl(FinVizSpider, tickers=tickers)
process.start()
"""

        # Run the subprocess with calculated timeout
        result = subprocess.run(
            [sys.executable, "-c", script],
            capture_output=True,
            text=True,
            timeout=timeout_seconds
        )

        if result.returncode == 0:
            logger.info("Scraping completed successfully")
            complete_scrape(status="completed", articles_found=0)

            # Run automatic pipeline if enabled
            if settings.AUTO_PROCESS_PIPELINE:
                logger.info("Starting automatic post-processing pipeline")
                _run_post_processing_pipeline()
            else:
                logger.info("Auto-processing disabled. Run 'finnews-chunk' and 'finnews-embed' manually.")
                # Mark pipeline as completed (without reset) so UI can show success message
                complete_pipeline(status="completed")
        else:
            logger.error(f"Scraping failed with return code {result.returncode}")
            logger.error(f"stderr: {result.stderr}")
            set_pipeline_error("scraping", f"Return code: {result.returncode}")
            complete_scrape(status="error", articles_found=0)

    except subprocess.TimeoutExpired:
        logger.error(
            f"Scraping timed out after {timeout_seconds} seconds ({timeout_seconds // 60} minutes). "
            f"Consider increasing SCRAPE_TIMEOUT_PER_TICKER or SCRAPE_TIMEOUT_BUFFER in config."
        )
        complete_scrape(status="error", articles_found=0)
    except Exception as e:
        logger.error(f"Error during scraping: {e}", exc_info=True)
        complete_scrape(status="error", articles_found=0)
        raise


def run_spider_with_tickers_direct(tickers: List[str]) -> None:
    """Run the spider with custom tickers directly (for CLI use only).

    WARNING: This can only be called once per process due to Scrapy reactor limitations.
    Use run_spider_with_tickers() for API/threading scenarios.

    Args:
        tickers: List of ticker symbols to scrape
    """
    if not tickers:
        logger.warning("No tickers provided, aborting scrape")
        return

    try:
        # Mark scraping as started
        start_scrape(tickers)
        logger.info(f"Starting scrape for {len(tickers)} tickers: {tickers}")

        # Get Scrapy settings
        settings = get_project_settings()

        # Create crawler process
        process = CrawlerProcess(settings)

        # Schedule the spider with custom tickers
        process.crawl(FinVizSpider, tickers=tickers)

        # Start the crawling process (blocking call)
        process.start()

        # Mark scraping as completed
        complete_scrape(status="completed", articles_found=0)
        logger.info("Scraping completed successfully")

    except Exception as e:
        logger.error(f"Error during scraping: {e}", exc_info=True)
        complete_scrape(status="error", articles_found=0)
        raise 

