from pathlib import Path

from finnews.common.config import settings


def test_config_aliases_exist_and_types():
    # Scalar aliases
    assert isinstance(settings.api_host, str)
    assert isinstance(settings.api_port, int)
    assert settings.llm_model

    # Path aliases
    assert isinstance(settings.chroma_store, Path)
    assert isinstance(settings.chat_memory, Path)
    assert isinstance(settings.raw_news, Path)
    assert isinstance(settings.processed_chunks, Path)
    assert isinstance(settings.tickers_csv, Path)
    assert isinstance(settings.chat_sessions, Path)

    # Specific filenames
    assert settings.processed_chunks.name == "chunked_articles.jsonl"
    assert settings.raw_news.name == "articles.jsonl"
