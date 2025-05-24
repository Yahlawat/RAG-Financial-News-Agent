import os
import json
from scrapy.exceptions import DropItem

class SaveToTickerJsonPipeline:

    def __init__(self):
        self.base_dir = './data/raw_news'
        os.makedirs(self.base_dir, exist_ok=True)
        self.ticker_data = {}  # Dict of {ticker: [articles]}
        self.ticker_urls = {}  # Dict of {ticker: set(urls)}

    def process_item(self, item, spider):
        ticker = item.get('ticker')
        url = item.get('url')

        if not ticker or not url:
            raise DropItem(f"Missing ticker or URL in {item}")

        # Load data if we haven't seen this ticker yet
        if ticker not in self.ticker_data:
            filepath = os.path.join(self.base_dir, f"{ticker}.json")
            if os.path.exists(filepath):
                with open(filepath, 'r') as f:
                    try:
                        self.ticker_data[ticker] = json.load(f)
                    except json.JSONDecodeError:
                        self.ticker_data[ticker] = []
            else:
                self.ticker_data[ticker] = []

            # Also load URL set
            self.ticker_urls[ticker] = {a['url'] for a in self.ticker_data[ticker]}

        # Deduplication / update
        existing_articles = self.ticker_data[ticker]
        url_set = self.ticker_urls[ticker]
        item_dict = dict(item)
        updated = False

        for article in existing_articles:
            if article['url'] == url:
                for field in ['body', 'published_date']:
                    if not article.get(field) and item_dict.get(field):
                        article[field] = item_dict[field]
                updated = True
                break

        if not updated and url not in url_set:
            existing_articles.append(item_dict)
            url_set.add(url)

        return item

    def close_spider(self, spider):
        """
        Save all ticker-specific JSON files to disk when spider finishes.
        """
        for ticker, articles in self.ticker_data.items():
            filepath = os.path.join(self.base_dir, f"{ticker}.json")
            with open(filepath, 'w') as f:
                json.dump(articles, f, indent=2)
