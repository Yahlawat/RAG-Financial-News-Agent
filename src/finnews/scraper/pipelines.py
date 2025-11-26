import json
from finnews.common.config import settings
from finnews.common.io_utils import ensure_file_dir
from finnews.scraper.utils import load_existing_urls

class SaveNewsJSONLPipeline:
    def __init__(self):
        self.output_file = str(settings.RAW_NEWS_PATH)
        ensure_file_dir(self.output_file)

        # Load existing URLs using utility function
        self.seen_urls = load_existing_urls(self.output_file)

        self.file = None

    def open_spider(self, spider):
        """Open the file when spider starts."""
        self.file = open(self.output_file, "a+", encoding="utf-8")

    def process_item(self, item, spider):
        url = item.get("url")
        if not url or url in self.seen_urls:
            if url:
                spider.logger.info(f"Duplicate skipped: {url}")
            return None

        self.seen_urls.add(url)
        
        if self.file is None:
            self.file = open(self.output_file, "a+", encoding="utf-8")
        
        self.file.write(json.dumps(dict(item)) + "\n")
        return item

    def close_spider(self, spider) -> None:
        if self.file:
            self.file.close()
            self.file = None