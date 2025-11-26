"""
Cleanup script to remove articles older than a specified number of days.

This script performs DELETION ONLY - no re-processing of kept articles:
1. Clean up backups older than 6 months
2. Create new backup of current data
3. Delete old articles from the vector database (selective deletion)
4. Filter raw news articles by date
5. Filter processed chunks by date (no re-chunking)
6. Complete (no re-embedding needed)
"""

import json
import shutil
from datetime import datetime, timedelta, timezone
from pathlib import Path

from langchain_chroma import Chroma

from finnews.common.config import ROOT, settings
from finnews.rag.embedder import delete_old_articles_from_chroma, get_embedding_model


def parse_date(date_str: str) -> datetime:
    """Parse date string to datetime object."""
    if not date_str:
        return datetime.min.replace(tzinfo=timezone.utc)

    try:
        # Try parsing ISO format with timezone
        if "+" in date_str or date_str.endswith("Z"):
            return datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        # Try parsing without timezone
        dt = datetime.fromisoformat(date_str)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except Exception as e:
        print(f"Warning: Could not parse date '{date_str}': {e}")
        return datetime.min.replace(tzinfo=timezone.utc)


def filter_articles_by_date(input_file: Path, output_file: Path, days_to_keep: int = 30) -> int:
    """
    Filter articles to keep only those from the last N days.

    Args:
        input_file: Path to raw news JSONL file
        output_file: Path to write filtered articles
        days_to_keep: Number of days to keep (default: 30)

    Returns:
        Number of articles kept
    """
    cutoff_date = datetime.now(timezone.utc) - timedelta(days=days_to_keep)

    kept_articles = []
    total_articles = 0

    print(f"Filtering articles to keep only last {days_to_keep} days...")
    print(f"Cutoff date: {cutoff_date.isoformat()}")

    if not input_file.exists():
        print(f"Warning: Input file {input_file} does not exist")
        return 0

    with open(input_file, "r", encoding="utf-8") as f:
        for line in f:
            total_articles += 1
            try:
                article = json.loads(line)
                published_date = article.get("published_date")

                # Skip articles without a published_date
                if not published_date or published_date == "null":
                    continue

                article_date = parse_date(published_date)

                # Keep only articles within the date range
                if article_date >= cutoff_date:
                    kept_articles.append(article)
            except json.JSONDecodeError as e:
                print(f"Warning: Skipping invalid JSON line: {e}")
                continue

    # Write filtered articles
    output_file.parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, "w", encoding="utf-8") as f:
        for article in kept_articles:
            f.write(json.dumps(article, ensure_ascii=False) + "\n")

    print(f"Kept {len(kept_articles)} out of {total_articles} articles")
    print(f"Removed {total_articles - len(kept_articles)} old articles")

    return len(kept_articles)


def cleanup_old_backups(backup_base_dir: Path, max_age_days: int = 180) -> int:
    """
    Remove backups older than max_age_days (default: 6 months).

    Args:
        backup_base_dir: Base directory containing dated backup folders
        max_age_days: Maximum age of backups to keep (default: 180 days = 6 months)

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
                # Skip directories that don't match timestamp format
                continue

    return removed_count


def cleanup_and_rebuild(days_to_keep: int = 30, backup: bool = True):
    """
    Clean up old articles from the database using selective deletion.

    Args:
        days_to_keep: Number of days of articles to keep (default: 30)
        backup: Whether to backup existing data before cleanup (default: True)
    """
    print("=" * 80)
    print("ARTICLE CLEANUP (SELECTIVE DELETION)")
    print("=" * 80)

    raw_news_path = settings.RAW_NEWS_PATH
    processed_chunks_path = settings.PROCESSED_CHUNKS_PATH
    chroma_store_path = settings.CHROMA_DIR

    # Clean up old backups (keep only 6 months)
    if backup:
        print("\n[1/6] Cleaning up old backups...")
        backup_base_dir = ROOT / "data" / "backups"
        removed = cleanup_old_backups(backup_base_dir, max_age_days=180)
        if removed > 0:
            print(f"  [OK] Removed {removed} backups older than 6 months")
        else:
            print("  [OK] No old backups to remove")

    # Backup existing data if requested
    if backup:
        print("\n[2/6] Creating backups...")
        backup_dir = ROOT / "data" / "backups" / datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_dir.mkdir(parents=True, exist_ok=True)

        if raw_news_path.exists():
            shutil.copy2(raw_news_path, backup_dir / raw_news_path.name)
            print(f"  [OK] Backed up raw news to {backup_dir / raw_news_path.name}")

        if processed_chunks_path.exists():
            shutil.copy2(processed_chunks_path, backup_dir / processed_chunks_path.name)
            print(f"  [OK] Backed up chunks to {backup_dir / processed_chunks_path.name}")

        if chroma_store_path.exists():
            shutil.copytree(chroma_store_path, backup_dir / "chroma_store", dirs_exist_ok=True)
            print(f"  [OK] Backed up vector DB to {backup_dir / 'chroma_store'}")

    # Delete old articles from vector database first
    print("\n[3/6] Deleting old articles from vector database...")

    cutoff_date = datetime.now(timezone.utc) - timedelta(days=days_to_keep)
    cutoff_date_str = cutoff_date.date().isoformat()

    deleted_count = 0
    if chroma_store_path.exists():
        # Selectively delete old articles from existing vector store
        embedding_model = get_embedding_model()
        vectorstore = Chroma(
            embedding_function=embedding_model,
            persist_directory=str(chroma_store_path),
        )
        deleted_count = delete_old_articles_from_chroma(vectorstore, cutoff_date_str)
        print(f"  [OK] Deleted {deleted_count} old documents from vector database")
    else:
        print("  [INFO] No existing vector database found")

    # Filter raw articles
    print(f"\n[4/6] Filtering raw articles (keeping last {days_to_keep} days)...")
    temp_file = raw_news_path.parent / "articles_filtered.jsonl"
    kept_count = filter_articles_by_date(raw_news_path, temp_file, days_to_keep)

    if kept_count == 0:
        print("  [ERROR] No articles found in date range. Aborting cleanup.")
        temp_file.unlink(missing_ok=True)
        return

    # Replace original with filtered
    shutil.move(str(temp_file), str(raw_news_path))
    print(f"  [OK] Updated raw news file with {kept_count} recent articles")

    # Filter chunks (no re-chunking needed)
    print(f"\n[5/6] Filtering processed chunks (keeping last {days_to_keep} days)...")

    kept_chunks = []
    total_chunks = 0

    if processed_chunks_path.exists():
        with open(processed_chunks_path, "r", encoding="utf-8") as f:
            for line in f:
                total_chunks += 1
                try:
                    chunk = json.loads(line)
                    metadata = chunk.get("metadata", {})
                    published_date = metadata.get("published_date", "")

                    # Skip chunks without a published_date
                    if not published_date or published_date == "null":
                        continue

                    # Keep chunks from articles within the date range
                    if published_date >= cutoff_date_str:
                        kept_chunks.append(chunk)
                except json.JSONDecodeError as e:
                    print(f"Warning: Skipping invalid JSON line: {e}")
                    continue

        # Write filtered chunks back
        processed_chunks_path.parent.mkdir(parents=True, exist_ok=True)
        with open(processed_chunks_path, "w", encoding="utf-8") as f:
            for chunk in kept_chunks:
                f.write(json.dumps(chunk, ensure_ascii=False) + "\n")

        print(f"  [OK] Kept {len(kept_chunks)} out of {total_chunks} chunks")
        print(f"  [OK] Removed {total_chunks - len(kept_chunks)} old chunks")
    else:
        print("  [WARNING] No existing chunks file found")
        kept_chunks = []

    # Summary
    print("\n[6/6] Cleanup complete!")
    print("=" * 80)
    print("SUMMARY:")
    print(f"  - Articles kept: {kept_count}")
    print(f"  - Chunks kept: {len(kept_chunks)}")
    print(f"  - Old documents deleted from vector DB: {deleted_count}")
    print(f"  - Days of data: {days_to_keep}")
    if backup:
        print(f"  - Backup location: {backup_dir}")
    print("  - NO RE-CHUNKING or RE-EMBEDDING performed (deletion only)")
    print("=" * 80)


def main():
    """CLI entry point."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Clean up old articles using selective deletion (no full rebuild)"
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
