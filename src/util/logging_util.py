"""Logging utility for the PE compliance application."""

import logging
import sys
from typing import Optional


def setup_logging(
    level: int = logging.INFO,
    format_style: str = "simple",
    logger_name: Optional[str] = None
) -> logging.Logger:
    """Setup logging configuration for the application.
    
    Args:
        level: Logging level (default: INFO)
        format_style: Logging format style - "simple" or "detailed" (default: "simple")
        logger_name: Name of the logger. If None, uses root logger
        
    Returns:
        Configured logger instance
    """
    # Get logger
    logger = logging.getLogger(logger_name) if logger_name else logging.getLogger()
    
    # Avoid duplicate handlers
    if logger.handlers:
        return logger
    
    # Create console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    
    # Set format based on style
    if format_style == "detailed":
        formatter = logging.Formatter(
            fmt='%(asctime)s | %(name)s:%(lineno)d | %(funcName)s() | %(levelname)s | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
    else:  # simple
        formatter = logging.Formatter(
            fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
    
    console_handler.setFormatter(formatter)
    
    # Add handler to logger
    logger.addHandler(console_handler)
    logger.setLevel(level)
    
    return logger


def get_logger(name: str, level: int = logging.INFO, format_style: str = "simple") -> logging.Logger:
    """Get a configured logger instance.
    
    Args:
        name: Logger name (typically __name__)
        level: Logging level (default: INFO)
        format_style: Logging format style - "simple" or "detailed" (default: "simple")
        
    Returns:
        Configured logger instance
    """
    return setup_logging(level=level, format_style=format_style, logger_name=name) 