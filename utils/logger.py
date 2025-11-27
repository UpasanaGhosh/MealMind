"""Structured logging configuration for MealMind."""
import logging
import structlog
from pathlib import Path
from config import config

def setup_logging():
    """Configure structured logging for the application."""
    
    # Ensure logs directory exists
    logs_dir = Path(__file__).parent.parent / "logs"
    logs_dir.mkdir(exist_ok=True)
    
    # Configure standard logging
    logging.basicConfig(
        format="%(message)s",
        level=getattr(logging, config.LOG_LEVEL),
        handlers=[
            logging.FileHandler(logs_dir / "mealmind.log"),
            logging.StreamHandler()
        ]
    )
    
    # Configure structlog
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer()
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )

def get_logger(name: str):
    """Get a structured logger instance.
    
    Args:
        name: Name of the logger (typically module name)
    
    Returns:
        Structured logger instance
    """
    return structlog.get_logger(name)

# Initialize logging on module import
setup_logging()
