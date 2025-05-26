import scrapy

class NewsArticleItem(scrapy.Item):
    title = scrapy.Field()
    body = scrapy.Field()
    url = scrapy.Field()
    source = scrapy.Field()
    scraped_at = scrapy.Field()
    published_date = scrapy.Field()
    main_ticker = scrapy.Field()
    relevant_tickers = scrapy.Field()
