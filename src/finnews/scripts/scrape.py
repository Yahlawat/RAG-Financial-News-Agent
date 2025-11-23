<<<<<<< HEAD
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
=======
﻿import subprocess
from finnews.common.config import settings
from finnews.common.paths import ensure_dirs

def main() -> int:
    ensure_dirs()
    cmd = ["scrapy", "-c", "config/scrapy.cfg", "crawl", "finviz_news", "-O", str(settings.RAW_NEWS_PATH)]
>>>>>>> 7af5a402772857b0c388489419e38a01f18be89d
    return subprocess.call(cmd)

if __name__ == "__main__":
    raise SystemExit(main())
 