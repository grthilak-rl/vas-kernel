"""
Logging configuration using Loguru.
"""
from loguru import logger
import sys
import os

# Add parent directory to Python path
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from config.settings import settings


def setup_logging():
    """Configure structured logging."""
    
    # Remove default handler
    logger.remove()
    
    # Configure log format
    if settings.log_format == "json":
        format_string = "{time} | {level} | {message}"
        logger.add(
            sys.stdout,
            format=format_string,
            level=settings.log_level,
            serialize=True,  # JSON output
            backtrace=True,
            diagnose=True,
        )
    else:
        format_string = "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan> - <level>{message}</level>"
        logger.add(
            sys.stdout,
            format=format_string,
            level=settings.log_level,
            colorize=True,
            backtrace=True,
            diagnose=True,
        )
    
    # Add file logging
    logger.add(
        "logs/app_{time}.log",
        rotation="1 day",
        retention="30 days",
        compression="zip",
        level=settings.log_level,
        serialize=(settings.log_format == "json"),
    )
    
    logger.info("Logging configured successfully")
    return logger


def get_logger(name: str):
    """Get a logger instance with a specific name."""
    return logger.bind(name=name)


