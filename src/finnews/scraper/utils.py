"""Common scraper utilities."""

import os
import json
import logging
from typing import Set

logger = logging.getLogger(__name__)


def load_existing_urls(file_path: str) -> Set[str]:
    """Load existing article URLs from JSONL file.

    Args:
        file_path: Path to the JSONL file containing articles

    Returns:
        Set of URLs found in the file
    """
    if not os.path.exists(file_path):
        return set()

    urls = set()
    with open(file_path, "r", encoding="utf-8") as f:
        for line_num, line in enumerate(f, 1):
            try:
                article = json.loads(line)
                if "url" in article:
                    urls.add(article["url"])
            except json.JSONDecodeError as e:
                logger.warning(f"Skipping invalid JSON on line {line_num} in {file_path}: {e}")
                continue

    return urls
