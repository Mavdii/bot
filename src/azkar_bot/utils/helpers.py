"""
Helper functions and utilities for the Azkar Bot

This module contains common utility functions used throughout the application.
"""

import asyncio
import json
import random
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
import aiohttp
from functools import wraps

from .constants import TIME_FORMAT, DATETIME_FORMAT, MAX_RETRIES, RETRY_DELAY
from .logger import get_logger

logger = get_logger(__name__)


def timing_decorator(func):
    """Decorator to measure function execution time"""
    @wraps(func)
    async def async_wrapper(*args, **kwargs):
        start_time = time.time()
        try:
            result = await func(*args, **kwargs)
            duration = time.time() - start_time
            logger.debug(f"⏱️ {func.__name__} took {duration:.2f}s")
            return result
        except Exception as e:
            duration = time.time() - start_time
            logger.error(f"❌ {func.__name__} failed after {duration:.2f}s: {e}")
            raise
    
    @wraps(func)
    def sync_wrapper(*args, **kwargs):
        start_time = time.time()
        try:
            result = func(*args, **kwargs)
            duration = time.time() - start_time
            logger.debug(f"⏱️ {func.__name__} took {duration:.2f}s")
            return result
        except Exception as e:
            duration = time.time() - start_time
            logger.error(f"❌ {func.__name__} failed after {duration:.2f}s: {e}")
            raise
    
    return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper


def retry_on_failure(max_retries: int = MAX_RETRIES, delay: float = RETRY_DELAY):
    """Decorator to retry function on failure"""
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            last_exception = None
            for attempt in range(max_retries):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt < max_retries - 1:
                        wait_time = delay * (2 ** attempt)  # Exponential backoff
                        logger.warning(f"🔄 Attempt {attempt + 1} failed for {func.__name__}: {e}. Retrying in {wait_time}s...")
                        await asyncio.sleep(wait_time)
                    else:
                        logger.error(f"❌ All {max_retries} attempts failed for {func.__name__}")
            raise last_exception
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            last_exception = None
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt < max_retries - 1:
                        wait_time = delay * (2 ** attempt)
                        logger.warning(f"🔄 Attempt {attempt + 1} failed for {func.__name__}: {e}. Retrying in {wait_time}s...")
                        time.sleep(wait_time)
                    else:
                        logger.error(f"❌ All {max_retries} attempts failed for {func.__name__}")
            raise last_exception
        
        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper
    return decorator


def safe_json_load(file_path: Union[str, Path], default: Any = None) -> Any:
    """
    Safely load JSON file with error handling
    
    Args:
        file_path: Path to JSON file
        default: Default value if file doesn't exist or is invalid
        
    Returns:
        Loaded JSON data or default value
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError, OSError) as e:
        logger.warning(f"⚠️ Could not load JSON file {file_path}: {e}")
        return default


def safe_json_save(data: Any, file_path: Union[str, Path]) -> bool:
    """
    Safely save data to JSON file
    
    Args:
        data: Data to save
        file_path: Path to save file
        
    Returns:
        True if successful, False otherwise
    """
    try:
        # Ensure directory exists
        Path(file_path).parent.mkdir(parents=True, exist_ok=True)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except (OSError, TypeError) as e:
        logger.error(f"❌ Could not save JSON file {file_path}: {e}")
        return False


def format_datetime(dt: datetime, format_str: str = DATETIME_FORMAT) -> str:
    """Format datetime to string"""
    return dt.strftime(format_str)


def parse_datetime(dt_str: str, format_str: str = DATETIME_FORMAT) -> Optional[datetime]:
    """Parse datetime string"""
    try:
        return datetime.strptime(dt_str, format_str)
    except ValueError:
        logger.warning(f"⚠️ Could not parse datetime: {dt_str}")
        return None


def format_time(hour: int, minute: int) -> str:
    """Format time as HH:MM string"""
    return f"{hour:02d}:{minute:02d}"


def parse_time(time_str: str) -> Optional[tuple]:
    """
    Parse time string to (hour, minute) tuple
    
    Args:
        time_str: Time string like "14:30"
        
    Returns:
        (hour, minute) tuple or None if invalid
    """
    try:
        hour, minute = map(int, time_str.split(':'))
        if 0 <= hour <= 23 and 0 <= minute <= 59:
            return (hour, minute)
    except (ValueError, AttributeError):
        pass
    return None


def get_random_item(items: List[Any]) -> Optional[Any]:
    """Get random item from list"""
    return random.choice(items) if items else None


def chunk_list(items: List[Any], chunk_size: int) -> List[List[Any]]:
    """Split list into chunks of specified size"""
    return [items[i:i + chunk_size] for i in range(0, len(items), chunk_size)]


def truncate_text(text: str, max_length: int, suffix: str = "...") -> str:
    """Truncate text to maximum length"""
    if len(text) <= max_length:
        return text
    return text[:max_length - len(suffix)] + suffix


def sanitize_filename(filename: str) -> str:
    """Sanitize filename by removing invalid characters"""
    invalid_chars = '<>:"/\\|?*'
    for char in invalid_chars:
        filename = filename.replace(char, '_')
    return filename.strip()


def get_file_extension(filename: str) -> str:
    """Get file extension from filename"""
    return Path(filename).suffix.lower()


def is_valid_file_extension(filename: str, valid_extensions: List[str]) -> bool:
    """Check if file has valid extension"""
    extension = get_file_extension(filename)
    return extension in [ext.lower() for ext in valid_extensions]


def format_file_size(size_bytes: int) -> str:
    """Format file size in human readable format"""
    if size_bytes == 0:
        return "0B"
    
    size_names = ["B", "KB", "MB", "GB"]
    i = 0
    while size_bytes >= 1024 and i < len(size_names) - 1:
        size_bytes /= 1024.0
        i += 1
    
    return f"{size_bytes:.1f}{size_names[i]}"


def generate_unique_id() -> str:
    """Generate unique ID based on timestamp"""
    return str(int(time.time() * 1000000))


def is_arabic_text(text: str) -> bool:
    """Check if text contains Arabic characters"""
    arabic_range = range(0x0600, 0x06FF + 1)
    return any(ord(char) in arabic_range for char in text)


def clean_text(text: str) -> str:
    """Clean and normalize text"""
    # Remove extra whitespace
    text = ' '.join(text.split())
    # Remove leading/trailing whitespace
    text = text.strip()
    return text


def validate_telegram_token(token: str) -> bool:
    """Validate Telegram bot token format"""
    if not token:
        return False
    
    parts = token.split(':')
    if len(parts) != 2:
        return False
    
    bot_id, auth_token = parts
    return bot_id.isdigit() and len(auth_token) == 35


def create_backup_filename(original_path: Union[str, Path]) -> Path:
    """Create backup filename with timestamp"""
    path = Path(original_path)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return path.parent / f"{path.stem}_backup_{timestamp}{path.suffix}"


async def safe_sleep(seconds: float) -> None:
    """Safe async sleep with error handling"""
    try:
        await asyncio.sleep(seconds)
    except asyncio.CancelledError:
        logger.debug("Sleep was cancelled")
        raise


def get_current_cairo_time() -> datetime:
    """Get current time in Cairo timezone"""
    import pytz
    cairo_tz = pytz.timezone('Africa/Cairo')
    return datetime.now(cairo_tz)


def is_time_in_range(current_time: datetime, start_hour: int, start_minute: int, 
                    end_hour: int, end_minute: int) -> bool:
    """Check if current time is within specified range"""
    current_minutes = current_time.hour * 60 + current_time.minute
    start_minutes = start_hour * 60 + start_minute
    end_minutes = end_hour * 60 + end_minute
    
    if start_minutes <= end_minutes:
        return start_minutes <= current_minutes <= end_minutes
    else:  # Range crosses midnight
        return current_minutes >= start_minutes or current_minutes <= end_minutes