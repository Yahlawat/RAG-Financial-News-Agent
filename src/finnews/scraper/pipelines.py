import os
import json
from finnews.common.config import settings

class SaveNewsJSONLPipeline:
    def __init__(self):
        self.output_file = str(settings.raw_news)
        os.makedirs(os.path.dirname(self.output_file), exist_ok=True)

        self.seen_urls = set()
        if os.path.exists(self.output_file):
            with open(self.output_file, "r", encoding="utf-8") as f:
                for line in f:
                    try:
                        article = json.loads(line)
                        if "url" in article:
                            self.seen_urls.add(article["url"])
                    except json.JSONDecodeError:
                        continue

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