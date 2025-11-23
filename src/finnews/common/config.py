from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator


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

    # Add validation for ports
    @field_validator('API_PORT', 'STREAMLIT_PORT')
    @classmethod
    def validate_ports(cls, v):
        if not (1 <= v <= 65535):
            raise ValueError('Port must be between 1 and 65535')
        return v

    # Data paths (directories)
    CHROMA_DIR: Path = ROOT / "data" / "chroma_store"
    CHAT_MEMORY_DIR: Path = ROOT / "data" / "chat_memory"
    PROCESSED_CHUNKS_DIR: Path = ROOT / "data" / "processed_chunks"
    TICKERS_DIR: Path = ROOT / "data" / "tickers"
    USER_PROFILES_DIR: Path = ROOT / "data" / "user_profiles"

    # Files
    RAW_NEWS_PATH: Path = ROOT / "data" / "raw_news" / "articles.jsonl"
    PROCESSED_CHUNKS_PATH: Path = ROOT / "data" / "processed_chunks" / "chunked_articles.jsonl"
    CHAT_SESSIONS_FILE: Path = ROOT / "data" / "chat_sessions" / "chat_sessions.json"
    SCRAPE_METADATA_FILE: Path = ROOT / "data" / "scrape_metadata.json"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    # ---- Aliases to support both old/new names used across the codebase ----
    # Lowercase attribute aliases
    @property
    def openai_api_key(self) -> str | None:
        return self.OPENAI_API_KEY

    @property
    def llm_model(self) -> str:
        return self.LLM_MODEL

    @property
    def embedding_model(self) -> str:
        return self.EMBEDDING_MODEL

    @property
    def api_host(self) -> str:
        return self.API_HOST

    @property
    def api_port(self) -> int:
        return self.API_PORT

    @property
    def streamlit_port(self) -> int:
        return self.STREAMLIT_PORT

    @property
    def chroma_store(self) -> Path:
        return self.CHROMA_DIR

    @property
    def chat_memory(self) -> Path:
        return self.CHAT_MEMORY_DIR

    @property
    def raw_news(self) -> Path:
        return self.RAW_NEWS_PATH

    @property
    def processed_chunks(self) -> Path:
        return self.PROCESSED_CHUNKS_PATH

    @property
    def tickers_csv(self) -> Path:
        return self.TICKERS_DIR / "tickers.csv"

    @property
    def chat_sessions(self) -> Path:
        return self.CHAT_SESSIONS_FILE

    @property
    def user_profiles_dir(self) -> Path:
        return self.USER_PROFILES_DIR

    @property
    def scrape_metadata_file(self) -> Path:
        return self.SCRAPE_METADATA_FILE


settings = Settings()

