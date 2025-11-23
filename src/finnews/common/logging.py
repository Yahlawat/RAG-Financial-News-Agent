<<<<<<< HEAD
import logging
=======
﻿import logging
>>>>>>> 7af5a402772857b0c388489419e38a01f18be89d
import sys
from pathlib import Path
from typing import Optional


def setup_logging(
    level: int = logging.INFO,
    format_string: Optional[str] = None,
    log_file: Optional[Path] = None,
    console: bool = True
) -> None:
    """Set up logging configuration.
<<<<<<< HEAD

=======
    
>>>>>>> 7af5a402772857b0c388489419e38a01f18be89d
    Args:
        level: Logging level (default: INFO)
        format_string: Custom format string for log messages
        log_file: Optional file path to write logs to
        console: Whether to log to console (default: True)
    """
    if format_string is None:
        format_string = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
<<<<<<< HEAD

    handlers = []

    if console:
        handlers.append(logging.StreamHandler(sys.stdout))

    if log_file:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        handlers.append(logging.FileHandler(log_file))

=======
    
    handlers = []
    
    if console:
        handlers.append(logging.StreamHandler(sys.stdout))
    
    if log_file:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        handlers.append(logging.FileHandler(log_file))
    
>>>>>>> 7af5a402772857b0c388489419e38a01f18be89d
    logging.basicConfig(
        level=level,
        format=format_string,
        handlers=handlers if handlers else None
    )


def get_logger(name: str = 'finnews') -> logging.Logger:
    """Get a logger instance.
<<<<<<< HEAD

    Args:
        name: Logger name (default: 'finnews')

=======
    
    Args:
        name: Logger name (default: 'finnews')
        
>>>>>>> 7af5a402772857b0c388489419e38a01f18be89d
    Returns:
        Logger instance
    """
    return logging.getLogger(name)
