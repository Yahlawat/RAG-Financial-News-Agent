from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT = Path(__file__).resolve().parents[3]


class Settings(BaseSettings):
    # Secrets / API
    OPENAI_API_KEY: str | None = None
    LLM_MODEL: str = "gpt-4o-mini"
    EMBEDDING_MODEL: str = "BAAI/bge-base-en-v1.5"

    # Network / Ports
    API_HOST: str = "127.0.0.1"
    API_PORT: int = 8000
    STREAMLIT_PORT: int = 8501

    # Scraping Settings
    SCRAPE_TIMEOUT: int = 1800  # seconds

    # Automated Scraping Scheduler
    SCRAPE_SCHEDULE_ENABLED: bool = False
    SCRAPE_SCHEDULE_HOUR: int = 2  # UTC, 0-23
    SCRAPE_SCHEDULE_MINUTE: int = 0  # 0-59

    # Data paths (directories)
    CHROMA_DIR: Path = ROOT / "data" / "chroma_store"
    CHAT_MEMORY_DIR: Path = ROOT / "data" / "chat_memory"
    PROCESSED_CHUNKS_DIR: Path = ROOT / "data" / "processed_chunks"
    TICKERS_DIR: Path = ROOT / "data" / "tickers"
    TICKERS_FILE: Path = ROOT / "data" / "tickers" / "tickers.txt"

    # Logging settings
    LOG_DIR: Path = ROOT / "logs"
    LOG_LEVEL: str = "INFO"
    LOG_ROTATION_DAYS: int = 30
    LOG_ENABLE_UNIFIED: bool = True

    # Files
    RAW_NEWS_PATH: Path = ROOT / "data" / "raw_news" / "articles.jsonl"
    PROCESSED_CHUNKS_PATH: Path = ROOT / "data" / "processed_chunks" / "chunked_articles.jsonl"
    CHAT_SESSIONS_FILE: Path = ROOT / "data" / "chat_sessions" / "chat_sessions.json"
    SCRAPE_METADATA_FILE: Path = ROOT / "data" / "scrape_metadata.json"

    # Single-user mode
    DEFAULT_USER_ID: str = "default"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


settings = Settings()
