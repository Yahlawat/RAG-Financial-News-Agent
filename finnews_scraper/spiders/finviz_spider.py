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
        Read tickers from CSV and initiate scraping requests for each ticker's Finviz page.
        """
        ticker_file = './data/tickers/tickers.csv'
        tickers = pd.read_csv(ticker_file)['ticker_symbol'].tolist()

        for ticker in tickers:
            url = f'https://finviz.com/quote.ashx?t={ticker}&p=d'
            yield scrapy.Request(url=url, callback=self.parse_main, meta={'ticker': ticker})

    def load_existing_urls(self, ticker):
        """
        Load saved article URLs for a given ticker from the corresponding JSON file.
        """
        filepath = f'./data/raw_news/{ticker}.json'
        if os.path.exists(filepath):
            with open(filepath, 'r') as f:
                try:
                    articles = json.load(f)
                    return {a['url'] for a in articles if 'url' in a}
                except json.JSONDecodeError:
                    return set()
        return set()

    def parse_main(self, response):
        """
        Extract news articles for a given ticker.
        Skip articles already saved in ticker-specific JSON files.
        """
        ticker = response.meta['ticker']
        article_blocks = response.css('table.fullview-news-outer tr')

        saved_urls = self.load_existing_urls(ticker)

        for article in article_blocks:
            title = article.css('a::text').get()
            url = article.css('a::attr(href)').get()

            # Normalize relative URLs
            if url and url.startswith('/'):
                url = 'https://finviz.com' + url
            if not url or url in saved_urls:
                continue  # Skip if URL is already saved

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

            # Follow only Finviz-hosted links for full content scraping
            if url.startswith('https://finviz.com/'):
                yield scrapy.Request(url=url, callback=self.parse_article, meta={'item': item})
            else:
                yield item

    def parse_article(self, response):
        """
        Extract article body and published date from Finviz.com URLs.
        """
        item = response.meta['item']

        # Extract published date
        published_texts = response.css('div.news-publish-info div::text').getall()
        published_date = None

        if published_texts:
            # Prefer second element if available, else fallback to first
            raw_date = published_texts[1].strip() if len(published_texts) > 1 else published_texts[0].strip()   
            raw_date = raw_date.lstrip('|').strip()
            
            try:
                published_date = datetime.strptime(raw_date, "%B %d, %Y, %I:%M %p").isoformat()
            except ValueError:
                pass

        item['published_date'] = published_date

        # Extract article body
        article_body_block = response.css('div.text-justify')
        paragraphs = article_body_block.css('p::text, p strong::text').getall()
        paragraphs = [p.strip() for p in paragraphs if p.strip()]
        item['body'] = ' '.join(paragraphs)

        yield item
