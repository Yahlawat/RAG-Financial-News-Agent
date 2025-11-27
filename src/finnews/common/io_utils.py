"""Common I/O utilities for reading and writing files."""

import json
import logging
import os
from pathlib import Path
from typing import Any, Iterator

logger = logging.getLogger(__name__)


def read_jsonl(file_path: str) -> Iterator[dict[str, Any]]:
    """Read JSONL file line by line with error handling.

    Args:
        file_path: Path to the JSONL file

    Yields:
        Parsed JSON objects from each line
    """
    if not os.path.exists(file_path):
        logger.warning(f"File not found: {file_path}")
        return

    with open(file_path, "r", encoding="utf-8") as f:
        for idx, line in enumerate(f):
            try:
                yield json.loads(line)
            except json.JSONDecodeError as e:
                logger.warning(f"Skipping invalid JSON on line {idx + 1} in {file_path}: {e}")
                continue


def write_jsonl(file_path: str, items: Iterator[dict[str, Any]]) -> None:
    """Write items to JSONL file.

    Args:
        file_path: Path to write the JSONL file
        items: Iterator of dictionaries to write
    """
    ensure_file_dir(file_path)
    with open(file_path, "w", encoding="utf-8") as f:
        for item in items:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")


def append_jsonl(file_path: str, item: dict[str, Any]) -> None:
    """Append a single item to a JSONL file.

    Args:
        file_path: Path to the JSONL file
        item: Dictionary to append
    """
    ensure_file_dir(file_path)
    with open(file_path, "a", encoding="utf-8") as f:
        f.write(json.dumps(item, ensure_ascii=False) + "\n")


def ensure_file_dir(file_path: str) -> None:
    """Ensure the parent directory of a file exists.

    Args:
        file_path: Path to a file
    """
    parent_dir = os.path.dirname(file_path)
    if parent_dir:
        Path(parent_dir).mkdir(parents=True, exist_ok=True)


def read_json(file_path: str) -> dict[str, Any]:
    """Read JSON file with error handling.

    Args:
        file_path: Path to the JSON file

    Returns:
        Parsed JSON object, or empty dict if file doesn't exist or is invalid
    """
    if not os.path.exists(file_path):
        return {}

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        logger.warning(f"Error reading JSON from {file_path}: {e}")
        return {}


def write_json(file_path: str, data: dict[str, Any], indent: int = 2) -> None:
    """Write data to JSON file with error handling.

    Args:
        file_path: Path to the JSON file
        data: Dictionary to write
        indent: JSON indentation (default: 2)
    """
    ensure_file_dir(file_path)
    try:
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=indent, ensure_ascii=False)
    except IOError as e:
        logger.warning(f"Error writing JSON to {file_path}: {e}")
