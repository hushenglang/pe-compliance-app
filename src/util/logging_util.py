"""Logging utility for the PE compliance application."""

import logging
import sys
import json
from typing import Optional
from datetime import datetime
from pathlib import Path


class JSONFormatter(logging.Formatter):
    """Custom JSON formatter for structured logging in production."""
    
    def format(self, record):
        log_entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        
        # Add exception info if present
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)
            
        # Add extra fields if present
        if hasattr(record, 'user_id'):
            log_entry["user_id"] = record.user_id
        if hasattr(record, 'request_id'):
            log_entry["request_id"] = record.request_id
            
        return json.dumps(log_entry)


def setup_logging(
    level: int = logging.INFO,
    format_style: str = "simple",
    logger_name: Optional[str] = None,
    log_to_file: bool = False,
    log_file_path: Optional[str] = None,
    enable_json_logging: bool = False
) -> logging.Logger:
    """Setup logging configuration for the application.
    
    Args:
        level: Logging level (default: INFO)
        format_style: Logging format style - "simple", "detailed", or "json" (default: "simple")
        logger_name: Name of the logger. If None, uses root logger
        log_to_file: Whether to also log to a file
        log_file_path: Path to log file (default: logs/app.log)
        enable_json_logging: Whether to use JSON formatting (useful for ECS/CloudWatch)
        
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
    if enable_json_logging or format_style == "json":
        formatter = JSONFormatter()
    elif format_style == "detailed":
        formatter = logging.Formatter(
            fmt='%(asctime)s | %(name)s:%(lineno)d | %(funcName)s() | %(levelname)s | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
    else:  # simple
        formatter = logging.Formatter(
            fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
    
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # Add file handler if requested
    if log_to_file:
        if not log_file_path:
            log_file_path = "logs/app.log"
        
        # Create logs directory if it doesn't exist
        log_dir = Path(log_file_path).parent
        log_dir.mkdir(parents=True, exist_ok=True)
        
        # Create rotating file handler
        from logging.handlers import RotatingFileHandler
        file_handler = RotatingFileHandler(
            log_file_path,
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5
        )
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    logger.setLevel(level)
    return logger


def get_logger(
    name: str, 
    level: int = logging.INFO, 
    format_style: str = "simple",
    log_to_file: bool = False,
    enable_json_logging: bool = False
) -> logging.Logger:
    """Get a configured logger instance.
    
    Args:
        name: Logger name (typically __name__)
        level: Logging level (default: INFO)
        format_style: Logging format style - "simple", "detailed", or "json" (default: "simple")
        log_to_file: Whether to also log to a file
        enable_json_logging: Whether to use JSON formatting (useful for ECS/CloudWatch)
        
    Returns:
        Configured logger instance
    """
    return setup_logging(
        level=level, 
        format_style=format_style, 
        logger_name=name,
        log_to_file=log_to_file,
        enable_json_logging=enable_json_logging
    ) 