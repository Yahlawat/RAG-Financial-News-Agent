import requests
import pandas as pd
from scrapy.http import TextResponse
from finnews_scraper.items import NewsArticleItem
from datetime import datetime

# Step 1: Request and wrap response
url = "https://finviz.com/news/65524/will-nvidia-stock-keep-rebounding-as-q1-earnings-approach"
headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
html = requests.get(url, headers=headers).text
response = TextResponse(url=url, body=html, encoding='utf-8')

#------------------------------------------------------------------
item = NewsArticleItem()

relevant_tickers = response.css('div.ticker-badge_name::text').getall()
item['relevant_tickers'] = list(set(ticker.strip() for ticker in relevant_tickers if ticker.strip()))

print(item['relevant_tickers'])


#------------------------------------------------------------------

published_texts = response.css('div.news-publish-info div::text').getall()

if published_texts:
    raw_date = published_texts[1].strip() if len(published_texts) > 1 else published_texts[0].strip()
    raw_date = raw_date.lstrip('|').strip()
    
    try:
        item['published_date'] = datetime.strptime(raw_date, "%B %d, %Y, %I:%M %p").isoformat()
    except ValueError:
                    pass
print(item['published_date'])

#------------------------------------------------------------------
article_blocks = response.css('table.fullview-news-outer tr') 
print("\nArticle blocks found:", len(article_blocks))  # Should be > 0 if news items were found

articles = []

for article in article_blocks:
    item = NewsArticleItem()
    item['title'] = article.css('a::text').get()
    item['url'] = article.css('a::attr(href)').get()
    item['source'] = article.css('span::text').get()
    item['scraped_at'] = datetime.utcnow().isoformat()
    articles.append(item)

print("\nExtracted Articles:")
for article in articles:
    print(article)


