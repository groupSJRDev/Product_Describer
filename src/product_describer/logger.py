"""Logging configuration for product describer."""

import logging
import os
import sys
from typing import Optional


def setup_logger(name: str, level: Optional[str] = None) -> logging.Logger:
    """Configure and return a logger instance.

    Args:
        name: Name of the logger (typically __name__).
        level: Log level string (DEBUG, INFO, WARNING, ERROR).
               If None, reads from LOG_LEVEL environment variable or defaults to INFO.

    Returns:
        Configured logger instance.

    Examples:
        >>> logger = setup_logger(__name__)
        >>> logger.info("Application started")
        >>> logger = setup_logger(__name__, "DEBUG")
        >>> logger.debug("Detailed debug info")
    """
    logger = logging.getLogger(name)

    # Avoid adding handlers multiple times
    if logger.handlers:
        return logger

    # Get log level from environment or use INFO
    log_level_str = level or os.getenv("LOG_LEVEL", "INFO")
    log_level = getattr(logging, log_level_str.upper(), logging.INFO)
    logger.setLevel(log_level)

    # Create console handler with formatting
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(log_level)

    # Create formatter
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    handler.setFormatter(formatter)

    # Add handler to logger
    logger.addHandler(handler)

    return logger
