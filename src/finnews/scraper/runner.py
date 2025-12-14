import logging

from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings

from finnews.common.logging import setup_logging
from finnews.scraper.metadata import (
    complete_pipeline,
    complete_scrape,
    set_pipeline_error,
    start_scrape,
)

setup_logging(component="scraper", level=logging.INFO, console=True, unified=True)
logger = logging.getLogger(__name__)


def run_scraper(tickers: list[str]) -> None:
    """
    Run the scraper for specified tickers.

    Args:
        tickers: List of stock ticker symbols to scrape

    Note:
        This function blocks until scraping completes
    """
    if not tickers:
        logger.warning("No tickers provided, aborting scrape")
        return

    try:
        start_scrape(tickers)
        logger.info(f"Starting scrape for {len(tickers)} tickers: {tickers}")

        from finnews.scraper.spiders.finviz_spider import FinVizSpider

        process = CrawlerProcess(get_project_settings())
        process.crawl(FinVizSpider, tickers=tickers)

        logger.info("Starting Scrapy crawler...")
        process.start()  # Blocks until complete

        from finnews.scraper import pipelines

        articles_found = pipelines._articles_scraped_count
        logger.info(f"Scraping completed successfully! Found {articles_found} articles")
        complete_scrape(status="completed", articles_found=articles_found)

        complete_pipeline(status="completed")
        logger.info("Scraping complete.")

    except Exception as e:
        logger.error(f"Error during scraping: {e}", exc_info=True)
        complete_scrape(status="error", articles_found=0)
        set_pipeline_error("scraping", str(e))
        raise


def run_spider_with_tickers(tickers: list[str]) -> None:
    """Deprecated: Use run_scraper() instead."""
    logger.warning("run_spider_with_tickers() is deprecated, use run_scraper()")
    run_scraper(tickers)


def main() -> None:
    """Run the spider using command line interface (deprecated)."""
    logger.warning("Direct execution of runner.py is deprecated, use 'finnews-scrape' instead")
    from scrapy import cmdline

    cmdline.execute(["scrapy", "crawl", "finviz_news"])
