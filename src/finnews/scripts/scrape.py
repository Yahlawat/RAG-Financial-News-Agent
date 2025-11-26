import subprocess

from finnews.common.config import settings
from finnews.common.paths import ensure_dirs


def main() -> int:
    """
    CLI entry point for the scraping step.

    Runs the Scrapy spider to scrape FinViz news articles for S&P 500 companies.
    Saves raw articles to data/raw_news/.
    """
    ensure_dirs()
    cmd = ["scrapy", "crawl", "finviz_news", "-O", str(settings.RAW_NEWS_PATH)]
    return subprocess.call(cmd)


if __name__ == "__main__":
    raise SystemExit(main())
