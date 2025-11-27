import logging
import sys
from datetime import datetime
from logging.handlers import TimedRotatingFileHandler
from pathlib import Path


def setup_logging(
    component: str = "app",
    level: int | None = None,
    format_string: str | None = None,
    log_file: Path | None = None,
    console: bool = True,
    rotation: bool = True,
    retention_days: int | None = None,
    unified: bool | None = None,
) -> None:
    """Set up logging configuration with rotation support.

    Args:
        component: Component name (api, scraper, rag, ui, scripts)
        level: Logging level (default from settings.LOG_LEVEL)
        format_string: Custom format string for log messages
        log_file: Optional file path to write logs to (overrides component-based path)
        console: Whether to log to console (default: True)
        rotation: Enable daily log rotation (default: True)
        retention_days: Days to keep rotated logs (default from settings.LOG_ROTATION_DAYS)
        unified: Also write to combined.log (default from settings.LOG_ENABLE_UNIFIED)
    """
    from finnews.common.config import settings

    # Determine log level from settings or parameter
    if level is None:
        level_name = settings.LOG_LEVEL.upper()
        level = getattr(logging, level_name, logging.INFO)

    # Use settings defaults for retention and unified logging
    if retention_days is None:
        retention_days = settings.LOG_ROTATION_DAYS
    if unified is None:
        unified = settings.LOG_ENABLE_UNIFIED

    # Use enhanced format with file and line number
    if format_string is None:
        format_string = "%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s"

    # Get root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    # Clear existing handlers to avoid duplicates
    root_logger.handlers.clear()

    handlers = []
    formatter = logging.Formatter(format_string)

    # Console handler
    if console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        handlers.append(console_handler)

    # Determine log file path
    if log_file is None:
        # Get logs directory from settings
        log_dir = settings.LOG_DIR
        component_dir = log_dir / component
        component_dir.mkdir(parents=True, exist_ok=True)
        log_file = component_dir / f"{component}.log"
    else:
        log_file.parent.mkdir(parents=True, exist_ok=True)

    # File handler with rotation
    if rotation:
        file_handler = TimedRotatingFileHandler(
            log_file,
            when="midnight",
            interval=1,
            backupCount=retention_days,
            encoding="utf-8",
        )
        # Custom namer for rotated files (adds date suffix)
        file_handler.namer = lambda name: name.replace(".log", "") + f".{datetime.now().strftime('%Y-%m-%d')}.log"
    else:
        file_handler = logging.FileHandler(log_file, encoding="utf-8")

    file_handler.setFormatter(formatter)
    handlers.append(file_handler)

    # Unified log handler (optional)
    if unified:
        log_dir = settings.LOG_DIR
        combined_log = log_dir / "combined.log"
        combined_log.parent.mkdir(parents=True, exist_ok=True)

        if rotation:
            unified_handler = TimedRotatingFileHandler(
                combined_log,
                when="midnight",
                interval=1,
                backupCount=retention_days,
                encoding="utf-8",
            )
            unified_handler.namer = lambda name: name.replace(".log", "") + f".{datetime.now().strftime('%Y-%m-%d')}.log"
        else:
            unified_handler = logging.FileHandler(combined_log, encoding="utf-8")

        unified_handler.setFormatter(formatter)
        handlers.append(unified_handler)

    # Add all handlers to root logger
    for handler in handlers:
        root_logger.addHandler(handler)


def get_logger(name: str = "finnews") -> logging.Logger:
    """Get a logger instance.

    Args:
        name: Logger name (default: 'finnews')

    Returns:
        Logger instance
    """
    return logging.getLogger(name)
