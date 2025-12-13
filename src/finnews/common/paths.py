from pathlib import Path

from .config import settings


def ensure_dirs() -> None:
    for p in [
        settings.CHROMA_DIR,
        settings.CHAT_MEMORY_DIR,
        settings.PROCESSED_CHUNKS_DIR,
        settings.RAW_NEWS_PATH.parent,
        settings.TICKERS_DIR,
        settings.CHAT_SESSIONS_FILE.parent,
        settings.LOG_DIR,
    ]:
        Path(p).mkdir(parents=True, exist_ok=True)
