from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT = Path(__file__).resolve().parents[2]

class Settings(BaseSettings):
    OPENAI_API_KEY: str | None = None
    CHROMA_DIR: Path = ROOT / "data" / "chroma_store"
    CHAT_MEMORY_DIR: Path = ROOT / "data" / "chat_memory"
    RAW_NEWS_PATH: Path = ROOT / "data" / "raw_news" / "articles.jsonl"
    PROCESSED_CHUNKS_PATH: Path = ROOT / "data" / "processed_chunks"
    TICKERS_DIR: Path = ROOT / "data" / "tickers"
    API_HOST: str = "127.0.0.1"
    API_PORT: int = 8000
    STREAMLIT_PORT: int = 8501
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

settings = Settings()
