import os
import json

class SaveNewsJSONLPipeline:
    def __init__(self):
        self.output_file = os.path.join("data", "raw_news", "articles.jsonl")
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

        self.file = open(self.output_file, "a", encoding="utf-8")

    def process_item(self, item, spider):
        url = item.get("url")
        if url in self.seen_urls:
            spider.logger.info(f"Duplicate skipped: {url}")
            return None

        self.seen_urls.add(url)
        self.file.write(json.dumps(dict(item)) + "\n")
        return item

    def close_spider(self, spider):
        self.file.close()
