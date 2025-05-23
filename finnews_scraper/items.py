import scrapy

class NewsArticleItem(scrapy.Item):
    ticker = scrapy.Field()
    title = scrapy.Field()
    body = scrapy.Field()
    url = scrapy.Field()
    source = scrapy.Field()
    published_date = scrapy.Field()
    scraped_at = scrapy.Field()
    
