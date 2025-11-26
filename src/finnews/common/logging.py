import logging
import sys
from pathlib import Path
from typing import Optional


def setup_logging(
    level: int = logging.INFO,
    format_string: Optional[str] = None,
    log_file: Optional[Path] = None,
    console: bool = True,
) -> None:
    """Set up logging configuration.

    Args:
        level: Logging level (default: INFO)
        format_string: Custom format string for log messages
        log_file: Optional file path to write logs to
        console: Whether to log to console (default: True)
    """
    if format_string is None:
        format_string = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    handlers = []

    if console:
        handlers.append(logging.StreamHandler(sys.stdout))

    if log_file:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        handlers.append(logging.FileHandler(log_file))

    logging.basicConfig(level=level, format=format_string, handlers=handlers if handlers else None)


def get_logger(name: str = "finnews") -> logging.Logger:
    """Get a logger instance.

    Args:
        name: Logger name (default: 'finnews')

    Returns:
        Logger instance
    """
    return logging.getLogger(name)
