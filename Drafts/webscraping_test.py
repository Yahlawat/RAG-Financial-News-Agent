import requests
import pandas as pd
from scrapy.http import TextResponse
from finnews_scraper.items import NewsArticleItem
from datetime import datetime

# Step 1: Request and wrap response
url = "https://finviz.com/news/19041/3m-vs-griffon-which-industrial-conglomerate-stock-is-a-stronger-pick"
headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
html = requests.get(url, headers=headers).text
response = TextResponse(url=url, body=html, encoding='utf-8')

#------------------------------------------------------------------
# Extract article content
article_div = response.css('div.text-justify')
body_text = article_div.css('p::text, p strong::text').getall()
body_text = [text.strip() for text in body_text if text.strip()]  # Clean up whitespace

# Print the extracted text
print("\nExtracted Article Text:")
for text in body_text:
    print(text)

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


