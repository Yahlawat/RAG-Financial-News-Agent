import subprocess
from finnews.common.config import settings
from finnews.common.paths import ensure_dirs

def main() -> int:
    ensure_dirs()
    cmd = ["scrapy", "-c", "config/scrapy.cfg", "crawl", "finviz_news", "-O", str(settings.RAW_NEWS_PATH)]
    return subprocess.call(cmd)

if __name__ == "__main__":
    raise SystemExit(main())
 