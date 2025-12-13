"""File-based ticker management.

Tickers are stored in data/tickers.txt (one per line).
"""

import logging
from pathlib import Path

from finnews.common.config import settings

logger = logging.getLogger(__name__)

TICKERS_FILE = settings.TICKERS_FILE


def ensure_tickers_file() -> None:
    """Ensure the tickers file exists."""
    TICKERS_FILE.parent.mkdir(parents=True, exist_ok=True)
    if not TICKERS_FILE.exists():
        TICKERS_FILE.write_text("", encoding="utf-8")
        logger.info(f"Created tickers file at {TICKERS_FILE}")


def load_tickers() -> list[str]:
    """Load tickers from the tickers.txt file.

    Returns:
        List of unique, uppercase ticker symbols (sorted)
    """
    ensure_tickers_file()

    try:
        content = TICKERS_FILE.read_text(encoding="utf-8")
        tickers = [
            line.strip().upper()
            for line in content.splitlines()
            if line.strip() and not line.strip().startswith("#")
        ]
        # Return unique, sorted tickers
        return sorted(list(set(tickers)))
    except Exception as e:
        logger.error(f"Failed to load tickers from {TICKERS_FILE}: {e}")
        return []


def save_tickers(tickers: list[str]) -> None:
    """Save tickers to the tickers.txt file.

    Args:
        tickers: List of ticker symbols to save
    """
    ensure_tickers_file()

    # Normalize and sort
    normalized = sorted(list(set(t.strip().upper() for t in tickers if t.strip())))

    try:
        TICKERS_FILE.write_text("\n".join(normalized) + "\n", encoding="utf-8")
        logger.info(f"Saved {len(normalized)} tickers to {TICKERS_FILE}")
    except Exception as e:
        logger.error(f"Failed to save tickers to {TICKERS_FILE}: {e}")
        raise


def add_ticker(ticker: str) -> bool:
    """Add a single ticker to the file.

    Args:
        ticker: Ticker symbol to add

    Returns:
        True if ticker was added, False if already exists
    """
    current = load_tickers()
    ticker = ticker.strip().upper()

    if ticker in current:
        return False

    current.append(ticker)
    save_tickers(current)
    return True


def remove_ticker(ticker: str) -> bool:
    """Remove a ticker from the file.

    Args:
        ticker: Ticker symbol to remove

    Returns:
        True if ticker was removed, False if not found
    """
    current = load_tickers()
    ticker = ticker.strip().upper()

    if ticker not in current:
        return False

    current.remove(ticker)
    save_tickers(current)
    return True
