import scrapy
import pandas as pd
from datetime import datetime
import os
import json

from finnews_scraper.items import NewsArticleItem


class FinVizSpider(scrapy.Spider):
    name = 'finviz_news'
    allowed_domains = ['finviz.com']
    
    def start_requests(self):
        """Starts requests for each ticker in the tickers.csv file"""
        
        with open('./data/tickers/tickers.csv', 'r') as ticker_csv:
            tickers = pd.read_csv(ticker_csv)['ticker_symbol'].tolist()
        for ticker in tickers:
            url = f'https://finviz.com/quote.ashx?t={ticker}&p=d'
            yield scrapy.Request(url=url, callback=self.parse_main, meta={'ticker': ticker})

    def parse_main(self, response):
        """Parses the main page for each ticker"""
        
        ticker = response.meta['ticker']
        article_blocks = response.css('table.fullview-news-outer tr')  
        
        # Create a list to store all articles for this ticker
        articles = []
        
        for article in article_blocks:
            item = NewsArticleItem()
            item['title'] = article.css('a::text').get()
            item['url'] = article.css('a::attr(href)').get()
            item['source'] = article.css('span::text').get()
            item['scraped_at'] = datetime.utcnow().isoformat()
            item['ticker'] = ticker
            articles.append(dict(item))
            yield item
        
        # Save all articles to a single JSON file
        if articles:
            output_dir = './data/raw_news'
            os.makedirs(output_dir, exist_ok=True)
            filepath = f'{output_dir}/raw_scraped_news.json'
            
            # Load existing articles if file exists
            existing_articles = []
            if os.path.exists(filepath):
                with open(filepath, 'r') as f:
                    existing_articles = json.load(f)
            
            # Append new articles and save
            all_articles = existing_articles + articles
            with open(filepath, 'w') as f:
                json.dump(all_articles, f, indent=2)

