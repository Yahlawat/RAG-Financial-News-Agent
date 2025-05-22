import scrapy

class NewsItem(scrapy.Item):
    title = scrapy.Field()
    content = scrapy.Field()
    url = scrapy.Field()
    source = scrapy.Field()
    published_date = scrapy.Field()
    author = scrapy.Field()
    category = scrapy.Field()
    tickers = scrapy.Field()  # Related stock tickers
    sentiment = scrapy.Field()  # Optional: pre-computed sentiment 