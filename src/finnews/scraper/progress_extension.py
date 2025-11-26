"""Scrapy extension for tracking scraping progress."""

import logging
from typing import Dict

from scrapy import signals
from scrapy.crawler import Crawler

from finnews.scraper.metadata import update_scrape_progress, update_ticker_scrape

logger = logging.getLogger(__name__)


class ProgressTrackerExtension:
    """Extension to track scraping progress and update metadata."""

    def __init__(self):
        self.items_scraped = 0
        self.ticker_counts: Dict[str, int] = {}

    @classmethod
    def from_crawler(cls, crawler: Crawler):
        """Initialize the extension from crawler settings.

        Args:
            crawler: Scrapy crawler instance

        Returns:
            ProgressTrackerExtension instance
        """
        # Instantiate the extension
        ext = cls()

        # Connect signals
        crawler.signals.connect(ext.spider_opened, signal=signals.spider_opened)
        crawler.signals.connect(ext.item_scraped, signal=signals.item_scraped)
        crawler.signals.connect(ext.spider_closed, signal=signals.spider_closed)

        return ext

    def spider_opened(self, spider):
        """Called when the spider is opened.

        Args:
            spider: Scrapy spider instance
        """
        logger.info(f"Spider opened: {spider.name}")
        self.items_scraped = 0
        self.ticker_counts = {}

    def item_scraped(self, item, spider):
        """Called when an item is scraped.

        Args:
            item: Scraped item
            spider: Scrapy spider instance
        """
        self.items_scraped += 1

        # Track articles per ticker
        main_ticker = item.get("main_ticker")
        if main_ticker:
            main_ticker = main_ticker.upper()
            self.ticker_counts[main_ticker] = self.ticker_counts.get(main_ticker, 0) + 1

        # Update progress periodically (every 5 items for more responsive feedback)
        if self.items_scraped % 5 == 0:
            # Calculate how many tickers have been processed
            tickers_completed = len(self.ticker_counts)
            update_scrape_progress(completed=tickers_completed, articles_found=self.items_scraped)
            logger.info(f"Progress: {self.items_scraped} articles, {tickers_completed} tickers")

    def spider_closed(self, spider, reason):
        """Called when the spider is closed.

        Args:
            spider: Scrapy spider instance
            reason: Reason for closing
        """
        logger.info(
            f"Spider closed: {spider.name}, reason: {reason}, total items: {self.items_scraped}"
        )

        # Update ticker metadata
        for ticker, count in self.ticker_counts.items():
            update_ticker_scrape(ticker, count)

        # Final progress update
        update_scrape_progress(completed=len(self.ticker_counts), articles_found=self.items_scraped)
