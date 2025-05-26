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
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.article_store = './data/raw_news/articles.jsonl'
        self.existing_urls = set()
        os.makedirs(os.path.dirname(self.article_store), exist_ok=True)

        # Load known URLs
        if os.path.exists(self.article_store):
            with open(self.article_store, 'r', encoding='utf-8') as f:
                for line in f:
                    try:
                        article = json.loads(line)
                        if 'url' in article:
                            self.existing_urls.add(article['url'])
                    except json.JSONDecodeError:
                        continue

        # Load tickers to scrape   
        with open("./data/tickers/tickers.csv", "r") as f:
            self.tickers = [line.strip() for line in f if line.strip()]

    def start_requests(self):
        """
        Initiate scraping requests for each ticker's Finviz page.
        """
        for ticker in self.tickers:
            url = f'https://finviz.com/quote.ashx?t={ticker}&p=d'
            yield scrapy.Request(url=url, callback=self.parse_main, meta={'ticker': ticker})

    def parse_main(self, response):
        """
        Extract news articles for a given ticker.
        Skip articles already saved in articles.jsonl.
        """
        ticker = response.meta['ticker']
        article_blocks = response.css('table.fullview-news-outer tr')

        for article in article_blocks:
            title = article.css('a::text').get()
            url = article.css('a::attr(href)').get()

            if url and url.startswith('/'):
                url = 'https://finviz.com' + url
            if not url or url in self.existing_urls:
                continue

            source = article.css('span::text').get()
            if source:
                source = re.sub(r'^\(|\)$', '', source.strip())

            item = NewsArticleItem(
                title=title,
                url=url,
                source=source,
                scraped_at=datetime.utcnow().isoformat(),
                published_date=None,
                body="",
                main_ticker=ticker,
                relevant_tickers=[]
            )

            if url.startswith('https://finviz.com/'):
                yield scrapy.Request(url=url, callback=self.parse_article, meta={'item': item})
            else:
                yield item


    def parse_article(self, response):
        """
        Extract article body and published date from Finviz.com URLs.
        """
        item = response.meta['item']
        
        # Extract relevant tickers
        relevant_tickers = response.css('div.ticker-badge_name::text').getall()
        item['relevant_tickers'] = list(set(ticker.strip() for ticker in relevant_tickers if ticker.strip()))

        # Extract published date
        published_texts = response.css('div.news-publish-info div::text').getall()
        if published_texts:
            raw_date = published_texts[1].strip() if len(published_texts) > 1 else published_texts[0].strip()
            raw_date = raw_date.lstrip('|').strip()
            try:
                item['published_date'] = datetime.strptime(raw_date, "%B %d, %Y, %I:%M %p").isoformat()
            except ValueError:
                pass

        # Extract article body
        article_body_block = response.css('div.text-justify')
        paragraphs = article_body_block.css('p::text, p strong::text').getall()
        item['body'] = ' '.join(p.strip() for p in paragraphs if p.strip())

        yield item
