"""
Logging configuration for the Azkar Bot

This module provides centralized logging setup with:
- Arabic text support
- Structured logging
- File and console output
- Log rotation
"""

import logging
import logging.handlers
import sys
from pathlib import Path
from typing import Optional
import structlog


class AzkarBotException(Exception):
    """Base exception for all bot-related errors"""
    pass


class ConfigurationError(AzkarBotException):
    """Configuration-related errors"""
    pass


class ContentError(AzkarBotException):
    """Content management errors"""
    pass


class FileOperationError(AzkarBotException):
    """File operation errors"""
    pass


class TelegramAPIError(AzkarBotException):
    """Telegram API related errors"""
    pass


class SchedulerError(AzkarBotException):
    """Scheduler related errors"""
    pass


def setup_logging(
    log_level: str = "INFO",
    log_file: Optional[Path] = None,
    log_format: Optional[str] = None,
    enable_structlog: bool = True
) -> None:
    """
    Setup logging configuration for the bot
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Path to log file (optional)
        log_format: Custom log format string (optional)
        enable_structlog: Whether to enable structured logging
    """
    
    # Default format with Arabic support
    if not log_format:
        log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level.upper()))
    
    # Clear existing handlers
    root_logger.handlers.clear()
    
    # Create formatter
    formatter = logging.Formatter(
        log_format,
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    
    # Console handler with UTF-8 encoding for Arabic support
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, log_level.upper()))
    console_handler.setFormatter(formatter)
    
    # Ensure UTF-8 encoding for Arabic text
    if hasattr(console_handler.stream, 'reconfigure'):
        console_handler.stream.reconfigure(encoding='utf-8')
    
    root_logger.addHandler(console_handler)
    
    # File handler with rotation if log file is specified
    if log_file:
        # Ensure log directory exists
        log_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Rotating file handler (10MB max, keep 5 backups)
        file_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=5,
            encoding='utf-8'  # Support Arabic text
        )
        file_handler.setLevel(getattr(logging, log_level.upper()))
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)
    
    # Configure structlog if enabled
    if enable_structlog:
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
                structlog.processors.JSONRenderer(ensure_ascii=False)  # Support Arabic
            ],
            context_class=dict,
            logger_factory=structlog.stdlib.LoggerFactory(),
            wrapper_class=structlog.stdlib.BoundLogger,
            cache_logger_on_first_use=True,
        )
    
    # Set specific logger levels
    logging.getLogger("telegram").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("aiohttp").setLevel(logging.WARNING)
    logging.getLogger("apscheduler").setLevel(logging.INFO)
    
    # Log startup message
    logger = logging.getLogger(__name__)
    logger.info("🚀 تم تهيئة نظام السجلات بنجاح - Logging system initialized successfully")


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance with the specified name
    
    Args:
        name: Logger name (usually __name__)
        
    Returns:
        Configured logger instance
    """
    return logging.getLogger(name)


def log_exception(logger: logging.Logger, exception: Exception, context: str = "") -> None:
    """
    Log an exception with context information
    
    Args:
        logger: Logger instance to use
        exception: Exception to log
        context: Additional context information
    """
    error_msg = f"خطأ - Error: {str(exception)}"
    if context:
        error_msg = f"{context} - {error_msg}"
    
    logger.error(error_msg, exc_info=True)


def log_performance(logger: logging.Logger, operation: str, duration: float) -> None:
    """
    Log performance metrics
    
    Args:
        logger: Logger instance to use
        operation: Name of the operation
        duration: Duration in seconds
    """
    logger.info(f"⏱️ أداء العملية - Performance: {operation} took {duration:.2f}s")


class LoggerMixin:
    """Mixin class to add logging capabilities to any class"""
    
    @property
    def logger(self) -> logging.Logger:
        """Get logger for this class"""
        return get_logger(self.__class__.__module__ + "." + self.__class__.__name__)
    
    def log_info(self, message: str, **kwargs) -> None:
        """Log info message"""
        self.logger.info(message, **kwargs)
    
    def log_warning(self, message: str, **kwargs) -> None:
        """Log warning message"""
        self.logger.warning(message, **kwargs)
    
    def log_error(self, message: str, exception: Optional[Exception] = None, **kwargs) -> None:
        """Log error message"""
        if exception:
            log_exception(self.logger, exception, message)
        else:
            self.logger.error(message, **kwargs)
    
    def log_debug(self, message: str, **kwargs) -> None:
        """Log debug message"""
        self.logger.debug(message, **kwargs)