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

    # Pipeline / Scraping Settings
    SCRAPE_TIMEOUT_PER_TICKER: int = 180  # seconds per ticker (3 minutes)
    SCRAPE_TIMEOUT_BUFFER: int = 300  # additional buffer in seconds (5 minutes)
    SCRAPE_MIN_TIMEOUT: int = 1800  # minimum timeout in seconds (30 minutes)
    AUTO_PROCESS_PIPELINE: bool = True  # automatically run chunking + embedding after scraping

    # Automated Scraping Scheduler
    SCRAPE_SCHEDULE_ENABLED: bool = True  # enable automated scheduled scraping
    SCRAPE_SCHEDULE_HOUR: int = 2  # hour (0-23) to run daily scrape (UTC)
    SCRAPE_SCHEDULE_MINUTE: int = 0  # minute (0-59) to run daily scrape
    SCRAPE_ON_NEW_TICKER: bool = True  # trigger scraping when new tickers are added

    # Data paths (directories)
    CHROMA_DIR: Path = ROOT / "data" / "chroma_store"
    CHAT_MEMORY_DIR: Path = ROOT / "data" / "chat_memory"
    PROCESSED_CHUNKS_DIR: Path = ROOT / "data" / "processed_chunks"
    TICKERS_DIR: Path = ROOT / "data" / "tickers"
    USER_PROFILES_DIR: Path = ROOT / "data" / "user_profiles"

    # Logging settings
    LOG_DIR: Path = ROOT / "logs"
    LOG_LEVEL: str = "INFO"  # Can be overridden via environment
    LOG_ROTATION_DAYS: int = 30  # Keep logs for 30 days
    LOG_ENABLE_UNIFIED: bool = True  # Enable combined.log

    # Files
    RAW_NEWS_PATH: Path = ROOT / "data" / "raw_news" / "articles.jsonl"
    PROCESSED_CHUNKS_PATH: Path = ROOT / "data" / "processed_chunks" / "chunked_articles.jsonl"
    CHAT_SESSIONS_FILE: Path = ROOT / "data" / "chat_sessions" / "chat_sessions.json"
    SCRAPE_METADATA_FILE: Path = ROOT / "data" / "scrape_metadata.json"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


settings = Settings()
