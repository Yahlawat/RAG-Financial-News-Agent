"""
Cleanup script to remove articles older than a specified number of days.

This script removes old articles from:
- Raw news JSONL files
- Processed chunks

The ChromaDB vector store is synced to the chunks file on the next embedding run.
"""

import json
import logging
import shutil
from datetime import datetime, timedelta, timezone
from pathlib import Path

from finnews.common.config import ROOT, settings
from finnews.common.logging import setup_logging


def parse_date(date_str: str) -> datetime:
    """Parse date string to datetime object."""
    if not date_str:
        return datetime.min.replace(tzinfo=timezone.utc)

    try:
        if "+" in date_str or date_str.endswith("Z"):
            return datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        dt = datetime.fromisoformat(date_str)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except Exception as e:
        print(f"Warning: Could not parse date '{date_str}': {e}")
        return datetime.min.replace(tzinfo=timezone.utc)


def article_date(article: dict) -> datetime | None:
    """Date used for retention: the published date, or the scrape time for articles
    without one (e.g. links to external sites)."""
    for key in ("published_date", "scraped_at"):
        value = article.get(key)
        if value and value != "null":
            return parse_date(value)
    return None


def filter_articles_by_date(input_file: Path, output_file: Path, days_to_keep: int = 30) -> set[str]:
    """
    Filter articles to keep only those from the last N days.

    Args:
        input_file: Path to raw news JSONL file
        output_file: Path to write filtered articles
        days_to_keep: Number of days to keep (default: 30)

    Returns:
        URLs of the articles kept
    """
    cutoff_date = datetime.now(timezone.utc) - timedelta(days=days_to_keep)

    kept_articles = []
    total_articles = 0

    print(f"Filtering articles to keep only last {days_to_keep} days...")
    print(f"Cutoff date: {cutoff_date.isoformat()}")

    if not input_file.exists():
        print(f"Warning: Input file {input_file} does not exist")
        return set()

    with open(input_file, "r", encoding="utf-8") as f:
        for line in f:
            total_articles += 1
            try:
                article = json.loads(line)
            except json.JSONDecodeError as e:
                print(f"Warning: Skipping invalid JSON line: {e}")
                continue

            date = article_date(article)
            if date is not None and date >= cutoff_date:
                kept_articles.append(article)

    # Write filtered articles
    output_file.parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, "w", encoding="utf-8") as f:
        for article in kept_articles:
            f.write(json.dumps(article, ensure_ascii=False) + "\n")

    print(f"Kept {len(kept_articles)} out of {total_articles} articles")
    print(f"Removed {total_articles - len(kept_articles)} old articles")

    return {article.get("url") for article in kept_articles if article.get("url")}


def filter_chunks_by_url(input_file: Path, output_file: Path, kept_urls: set[str]) -> int:
    """
    Keep only chunks whose article was kept, so chunks always match the raw articles.

    Args:
        input_file: Path to processed chunks JSONL file
        output_file: Path to write filtered chunks
        kept_urls: URLs of the articles kept

    Returns:
        Number of chunks kept
    """
    kept_chunks = 0
    total_chunks = 0

    output_file.parent.mkdir(parents=True, exist_ok=True)
    with open(input_file, "r", encoding="utf-8") as f, open(output_file, "w", encoding="utf-8") as out:
        for line in f:
            total_chunks += 1
            try:
                chunk = json.loads(line)
            except json.JSONDecodeError as e:
                print(f"Warning: Skipping invalid JSON line: {e}")
                continue

            if chunk.get("metadata", {}).get("url") in kept_urls:
                out.write(json.dumps(chunk, ensure_ascii=False) + "\n")
                kept_chunks += 1

    print(f"Kept {kept_chunks} out of {total_chunks} chunks")
    return kept_chunks


def cleanup_old_backups(backup_base_dir: Path, max_age_days: int = 180) -> int:
    """
    Remove backups older than max_age_days.

    Args:
        backup_base_dir: Base directory containing dated backup folders
        max_age_days: Maximum age of backups to keep (default: 180 days)

    Returns:
        Number of old backups removed
    """
    if not backup_base_dir.exists():
        return 0

    cutoff_date = datetime.now() - timedelta(days=max_age_days)
    removed_count = 0

    for backup_dir in backup_base_dir.iterdir():
        if backup_dir.is_dir():
            try:
                # Parse timestamp from directory name (format: YYYYMMDD_HHMMSS)
                backup_timestamp = datetime.strptime(backup_dir.name, "%Y%m%d_%H%M%S")
                if backup_timestamp < cutoff_date:
                    shutil.rmtree(backup_dir)
                    print(f"  [OK] Deleted old backup: {backup_dir.name}")
                    removed_count += 1
            except ValueError:
                # Skip directories that don't match the expected format
                continue

    return removed_count


def cleanup_and_rebuild(days_to_keep: int = 30, backup: bool = True):
    """
    Remove articles older than days_to_keep from the raw news and chunks files.

    The vector database is not modified here: the next embedding run
    (finnews-embed or finnews-pipeline) removes documents whose chunks are gone.

    Args:
        days_to_keep: Number of days of articles to keep (default: 30)
        backup: Whether to backup existing data before cleanup (default: True)
    """
    print("=" * 80)
    print("ARTICLE CLEANUP")
    print("=" * 80)

    raw_news_path = settings.RAW_NEWS_PATH
    processed_chunks_path = settings.PROCESSED_CHUNKS_PATH

    # Step 1: Clean up old backups (keep only last 6 months)
    if backup:
        print("\n[1/5] Cleaning up old backups...")
        backup_base_dir = ROOT / "data" / "backups"
        removed = cleanup_old_backups(backup_base_dir, max_age_days=180)
        if removed > 0:
            print(f"  [OK] Removed {removed} backups older than 6 months")
        else:
            print("  [OK] No old backups to remove")

    # Step 2: Create new backup before cleanup. The vector DB isn't backed up:
    # it is rebuilt from the chunks file by the embedding step.
    if backup:
        print("\n[2/5] Creating backups...")
        backup_dir = ROOT / "data" / "backups" / datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_dir.mkdir(parents=True, exist_ok=True)

        if raw_news_path.exists():
            shutil.copy2(raw_news_path, backup_dir / raw_news_path.name)
            print(f"  [OK] Backed up raw news to {backup_dir / raw_news_path.name}")

        if processed_chunks_path.exists():
            shutil.copy2(processed_chunks_path, backup_dir / processed_chunks_path.name)
            print(f"  [OK] Backed up chunks to {backup_dir / processed_chunks_path.name}")

    # Step 3: Filter raw articles by date (written to a temp file until all filtering succeeds)
    print(f"\n[3/5] Filtering raw articles (keeping last {days_to_keep} days)...")
    temp_raw = raw_news_path.parent / "articles_filtered.jsonl"
    kept_urls = filter_articles_by_date(raw_news_path, temp_raw, days_to_keep)

    if not kept_urls:
        print("  [ERROR] No articles found in date range. Aborting cleanup.")
        temp_raw.unlink(missing_ok=True)
        return

    # Step 4: Keep only chunks of the kept articles
    print("\n[4/5] Filtering processed chunks...")
    kept_chunks = 0
    temp_chunks = processed_chunks_path.parent / "chunked_articles_filtered.jsonl"
    if processed_chunks_path.exists():
        kept_chunks = filter_chunks_by_url(processed_chunks_path, temp_chunks, kept_urls)
    else:
        print("  [WARNING] No existing chunks file found")

    shutil.move(str(temp_raw), str(raw_news_path))
    print(f"  [OK] Updated raw news file with {len(kept_urls)} recent articles")
    if processed_chunks_path.exists():
        shutil.move(str(temp_chunks), str(processed_chunks_path))
        print(f"  [OK] Updated chunks file with {kept_chunks} chunks")

    print("\n[5/5] Cleanup complete!")
    print("=" * 80)
    print("SUMMARY:")
    print(f"  - Articles kept: {len(kept_urls)}")
    print(f"  - Chunks kept: {kept_chunks}")
    print(f"  - Days of data: {days_to_keep}")
    print("  - Vector DB: synced on the next embedding run")
    if backup:
        print(f"  - Backup location: {backup_dir}")
    print("=" * 80)


def main():
    """CLI entry point."""
    import argparse

    setup_logging(component="scripts", level=logging.INFO, console=True)

    parser = argparse.ArgumentParser(
        description="Remove articles older than the given number of days"
    )
    parser.add_argument(
        "--days", type=int, default=30, help="Number of days of articles to keep (default: 30)"
    )
    parser.add_argument(
        "--no-backup", action="store_true", help="Skip creating backups before cleanup"
    )

    args = parser.parse_args()

    cleanup_and_rebuild(days_to_keep=args.days, backup=not args.no_backup)


if __name__ == "__main__":
    main()
