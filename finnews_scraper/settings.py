BOT_NAME = "finnews_scraper"

SPIDER_MODULES = ["finnews_scraper.spiders"]
NEWSPIDER_MODULE = "finnews_scraper.spiders"

# Obey robots.txt rules
ROBOTSTXT_OBEY = True

# Custom user-agent to mimic a browser
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"

# Crawl respectfully
CONCURRENT_REQUESTS = 8
DOWNLOAD_DELAY = 2

# Enable AutoThrottle to avoid bans
AUTOTHROTTLE_ENABLED = True
AUTOTHROTTLE_START_DELAY = 2
AUTOTHROTTLE_MAX_DELAY = 10
AUTOTHROTTLE_TARGET_CONCURRENCY = 1.0

# Retry failed requests
RETRY_ENABLED = True
RETRY_TIMES = 3
RETRY_HTTP_CODES = [500, 502, 503, 504, 522, 524, 408]

# Pipeline for saving articles
ITEM_PIPELINES = {
    "finnews_scraper.pipelines.SaveToTickerJsonPipeline": 300,
}

# Compatibility settings
REQUEST_FINGERPRINTER_IMPLEMENTATION = "2.7"
TWISTED_REACTOR = "twisted.internet.asyncioreactor.AsyncioSelectorReactor"
FEED_EXPORT_ENCODING = "utf-8"
