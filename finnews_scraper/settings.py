BOT_NAME = "finnews_scraper"

SPIDER_MODULES = ["finnews_scraper.spiders"]
NEWSPIDER_MODULE = "finnews_scraper.spiders"

# Obey robots.txt rules
ROBOTSTXT_OBEY = True

# Configure maximum concurrent requests
CONCURRENT_REQUESTS = 16

# Configure a delay for requests for the same website
DOWNLOAD_DELAY = 2

# Enable or disable downloader middlewares
DOWNLOADER_MIDDLEWARES = {
    "finnews_scraper.middlewares.FinnewsScraperDownloaderMiddleware": 543,
}

# Configure item pipelines
ITEM_PIPELINES = {
    "finnews_scraper.pipelines.FinnewsScraperPipeline": 300,
}

# Set settings whose default value is deprecated to a future-proof value
REQUEST_FINGERPRINTER_IMPLEMENTATION = "2.7"
TWISTED_REACTOR = "twisted.internet.asyncioreactor.AsyncioSelectorReactor"
FEED_EXPORT_ENCODING = "utf-8" 