import scrapy
import pandas as pd
import os
import json
import re
from datetime import datetime

from finnews_scraper.items import NewsArticleItem


class FinVizSpider(scrapy.Spider):
    name = 'finviz_news'
    allowed_domains = ['finviz.com']

    def start_requests(self):
        """
        Read tickers from CSV and initiate scraping requests for each ticker's FinViz page.
        """
        ticker_file = './data/tickers/tickers.csv'
        tickers = pd.read_csv(ticker_file)['ticker_symbol'].tolist()

        for ticker in tickers:
            url = f'https://finviz.com/quote.ashx?t={ticker}&p=d'
            yield scrapy.Request(url=url, callback=self.parse_main, meta={'ticker': ticker})

    def parse_main(self, response):
        """
        Extract news articles for a given ticker and append only new articles to the main JSON file.
        """
        ticker = response.meta['ticker']
        article_blocks = response.css('table.fullview-news-outer tr')

        # Prepare output directory and file
        output_dir = './data/raw_news'
        os.makedirs(output_dir, exist_ok=True)
        filepath = os.path.join(output_dir, 'raw_scraped_news.json')

        # Load existing data and track previously seen URLs
        existing_articles = []
        existing_urls = set()
        if os.path.exists(filepath):
            with open(filepath, 'r') as f:
                existing_articles = json.load(f)
                existing_urls = {article['url'] for article in existing_articles}

        # Extract and collect new articles
        new_articles = []
        for article in article_blocks:
            title = article.css('a::text').get()
            url = article.css('a::attr(href)').get()

            if url and url.startswith('/'):
                url = 'https://finviz.com' + url
            if not url or url in existing_urls:
                continue  # Skip if duplicate or invalid

            source = article.css('span::text').get()
            if source:
                source = re.sub(r'^\(|\)$', '', source.strip())

            item = NewsArticleItem(
                title=title,
                url=url,
                source=source,
                scraped_at=datetime.utcnow().isoformat(),
                ticker=ticker
            )

            # Yield to parse_article only for finviz.com urls
            if url.startswith('https://finviz.com/'):
                yield scrapy.Request(url=url, callback=self.parse_article, meta={'item': item})
            else:
                new_articles.append(dict(item))
                yield item

        # Save all articles to a single JSON file
        if new_articles:
            all_articles = existing_articles + new_articles
            with open(filepath, 'w') as f:
                json.dump(all_articles, f, indent=2)

    def parse_article(self, response):
        """
        Extract article body from Finviz.com URLs and append it to the main JSON file.
        """
        item = response.meta['item']

        # Extract text from the article body
        article_body_block = response.css('div.text-justify')
        paragraphs_text = article_body_block.css('p::text, p strong::text').getall()
        paragraphs_text = [text.strip() for text in paragraphs_text if text.strip()]
        item['body'] = ' '.join(paragraphs_text)

        # Define output path
        output_dir = './data/raw_news'
        filepath = os.path.join(output_dir, 'raw_scraped_news.json')

        # Load existing articles
        existing_articles = []
        if os.path.exists(filepath):
            with open(filepath, 'r') as f:
                existing_articles = json.load(f)

        # Append new article and save
        existing_articles.append(dict(item))
        with open(filepath, 'w') as f:
            json.dump(existing_articles, f, indent=2)

        yield item

