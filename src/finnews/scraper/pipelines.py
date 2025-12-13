import json

from finnews.common.config import settings
from finnews.common.io_utils import ensure_file_dir
from finnews.scraper.utils import load_existing_urls

# Module-level counter for articles scraped in current run
# Used by runner.py to get article count after scraping completes
_articles_scraped_count = 0


class SaveNewsJSONLPipeline:
    def __init__(self):
        self.output_file = str(settings.RAW_NEWS_PATH)
        ensure_file_dir(self.output_file)

        # Duplicate detection: Load existing URLs to prevent duplicates
        self.seen_urls = load_existing_urls(self.output_file)

        self.file = None
        self.items_scraped = 0  # Simple counter for scraped articles

    def open_spider(self, spider):
        """Open the file when spider starts."""
        global _articles_scraped_count
        _articles_scraped_count = 0  # Reset global counter for new scrape run

        self.file = open(self.output_file, "a+", encoding="utf-8")
        self.items_scraped = 0

    def process_item(self, item, spider):
        url = item.get("url")
        # Duplicate check before persisting to storage
        if not url or url in self.seen_urls:
            if url:
                spider.logger.info(f"Duplicate skipped: {url}")
            return None

        self.seen_urls.add(url)

        if self.file is None:
            self.file = open(self.output_file, "a+", encoding="utf-8")

        self.file.write(json.dumps(dict(item)) + "\n")
        self.items_scraped += 1

        # Update global counter for runner to access
        global _articles_scraped_count
        _articles_scraped_count += 1

        return item

    def close_spider(self, spider) -> None:
        """Close file and update metadata with final article count."""
        if self.file:
            self.file.close()
            self.file = None

        # Store final count on spider for runner to access
        spider.articles_found = self.items_scraped
        spider.logger.info(f"Scraped {self.items_scraped} new articles")
