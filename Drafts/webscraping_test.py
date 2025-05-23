import requests
import pandas as pd
from scrapy.http import TextResponse
from finnews_scraper.finnews_scraper.items import NewsArticleItem
from datetime import datetime

# Step 1: Request and wrap response
url = "https://finviz.com/quote.ashx?t=MMM&p=d"
headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
html = requests.get(url, headers=headers).text
response = TextResponse(url=url, body=html, encoding='utf-8')

print(response.text[:1000])  # Show the first 1000 characters

#------------------------------------------------------------------
article_blocks = response.css('table.fullview-news-outer tr') 
print(article_blocks[0])  # Should be > 0 if news items were found

articles = []

for article in article_blocks:
    item = NewsArticleItem()
    item['title'] = article.css('a::text').get()
    item['url'] = article.css('a::attr(href)').get()
    item['source'] = article.css('span::text').get()
    item['scraped_at'] = datetime.utcnow().isoformat()
    articles.append(item)

for article in articles:
    print(article)


