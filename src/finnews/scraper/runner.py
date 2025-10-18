from scrapy import cmdline


def main() -> None:
    cmdline.execute(["scrapy", "crawl", "finviz_news"]) 

