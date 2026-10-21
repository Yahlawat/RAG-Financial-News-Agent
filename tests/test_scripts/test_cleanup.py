"""Tests for old-article cleanup."""

import json
from datetime import datetime, timedelta, timezone
from unittest.mock import patch

from finnews.scripts.cleanup_old_articles import cleanup_and_rebuild, filter_articles_by_date


def write_jsonl(path, items):
    path.write_text("".join(json.dumps(item) + "\n" for item in items), encoding="utf-8")


def read_jsonl(path):
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


def days_ago(days):
    return (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()


def test_filter_articles_uses_scraped_at_when_unpublished(tmp_path):
    raw = tmp_path / "articles.jsonl"
    write_jsonl(raw, [
        {"url": "recent", "published_date": days_ago(1)},
        {"url": "old", "published_date": days_ago(60)},
        {"url": "external-recent", "published_date": None, "scraped_at": days_ago(2)},
        {"url": "external-old", "published_date": None, "scraped_at": days_ago(60)},
        {"url": "undated"},
    ])

    kept = filter_articles_by_date(raw, tmp_path / "out.jsonl", days_to_keep=30)

    assert kept == {"recent", "external-recent"}


def test_cleanup_filters_chunks_by_kept_articles(tmp_path):
    raw = tmp_path / "raw" / "articles.jsonl"
    chunks = tmp_path / "chunks" / "chunked_articles.jsonl"
    raw.parent.mkdir()
    chunks.parent.mkdir()
    write_jsonl(raw, [
        {"url": "recent", "published_date": days_ago(1)},
        {"url": "old", "published_date": days_ago(60)},
    ])
    write_jsonl(chunks, [
        {"content": "a", "metadata": {"url": "recent"}},
        {"content": "b", "metadata": {"url": "old"}},
    ])

    with patch("finnews.scripts.cleanup_old_articles.settings") as mock_settings:
        mock_settings.RAW_NEWS_PATH = raw
        mock_settings.PROCESSED_CHUNKS_PATH = chunks
        cleanup_and_rebuild(days_to_keep=30, backup=False)

    assert [a["url"] for a in read_jsonl(raw)] == ["recent"]
    assert [c["metadata"]["url"] for c in read_jsonl(chunks)] == ["recent"]


def test_cleanup_aborts_without_changes_when_nothing_is_recent(tmp_path):
    raw = tmp_path / "articles.jsonl"
    chunks = tmp_path / "chunked_articles.jsonl"
    write_jsonl(raw, [{"url": "old", "published_date": days_ago(60)}])
    write_jsonl(chunks, [{"content": "b", "metadata": {"url": "old"}}])

    with patch("finnews.scripts.cleanup_old_articles.settings") as mock_settings:
        mock_settings.RAW_NEWS_PATH = raw
        mock_settings.PROCESSED_CHUNKS_PATH = chunks
        cleanup_and_rebuild(days_to_keep=30, backup=False)

    assert len(read_jsonl(raw)) == 1
    assert len(read_jsonl(chunks)) == 1
    assert sorted(p.name for p in tmp_path.iterdir()) == ["articles.jsonl", "chunked_articles.jsonl"]
