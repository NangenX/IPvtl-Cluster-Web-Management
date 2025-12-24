"""
Centralized logging configuration for the application.

This module provides a unified logging setup that reads configuration
from environment variables and ensures consistent logging across all modules.
"""
import logging
import sys
from app.config import settings


def setup_logging():
    """
    Initialize logging configuration for the entire application.
    
    Sets up:
    - Log level from LOG_LEVEL environment variable
    - Consistent log format with timestamp, module, level, and message
    - Output to stdout for container-friendly logging
    """
    # Map log level string to logging constants
    log_level_map = {
        "debug": logging.DEBUG,
        "info": logging.INFO,
        "warning": logging.WARNING,
        "error": logging.ERROR,
        "critical": logging.CRITICAL,
    }
    
    log_level = log_level_map.get(settings.LOG_LEVEL.lower(), logging.INFO)
    
    # Configure root logger
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=[logging.StreamHandler(sys.stdout)],
        force=True,  # Override any existing configuration
    )
    
    # Set level for httpx to WARNING to reduce noise
    logging.getLogger("httpx").setLevel(logging.WARNING)
    
    logger = logging.getLogger(__name__)
    logger.info(f"Logging initialized with level: {settings.LOG_LEVEL.upper()}")


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance for the specified module.
    
    Args:
        name: Module name (typically __name__)
    
    Returns:
        Configured logger instance
    """
    return logging.getLogger(name)
