"""
Configuration management for the Azkar Bot

This module handles all configuration settings including:
- Environment variables loading
- Configuration validation
- Default values management
- Secure credential handling
"""

import os
from typing import List, Optional
from pathlib import Path
from dotenv import load_dotenv
import logging

logger = logging.getLogger(__name__)


class ConfigurationError(Exception):
    """Raised when configuration is invalid or missing"""
    pass


class Config:
    """
    Configuration manager for the Azkar Bot
    
    Loads configuration from environment variables with validation
    and provides secure access to sensitive settings.
    """
    
    def __init__(self, env_file: Optional[str] = None):
        """
        Initialize configuration
        
        Args:
            env_file: Optional path to .env file
        """
        # Load environment variables from .env file if provided
        if env_file and os.path.exists(env_file):
            load_dotenv(env_file)
        elif os.path.exists('.env'):
            load_dotenv('.env')
            
        self._load_config()
        self.validate()
    
    def _load_config(self) -> None:
        """Load all configuration values from environment variables"""
        
        # Bot Configuration
        self.bot_token = os.getenv('BOT_TOKEN', '')
        self.admin_id = self._get_int_env('ADMIN_ID', 0)
        self.channel_link = os.getenv('CHANNEL_LINK', 'https://t.me/Telawat_Quran_0')
        
        # Paths Configuration
        self.data_dir = Path(os.getenv('DATA_DIR', './data'))
        self.content_dir = Path(os.getenv('CONTENT_DIR', './data/content'))
        self.groups_file = Path(os.getenv('GROUPS_FILE', './data/groups/active_groups.json'))
        
        # Scheduling Configuration
        self.timezone = os.getenv('TIMEZONE', 'Africa/Cairo')
        self.random_content_interval = self._get_int_env('RANDOM_CONTENT_INTERVAL', 5)
        self.morning_azkar_times = self._parse_time_list(
            os.getenv('MORNING_AZKAR_TIMES', '05:30,07:00,08:00')
        )
        self.evening_azkar_times = self._parse_time_list(
            os.getenv('EVENING_AZKAR_TIMES', '18:00,19:00,20:00')
        )
        
        # Logging Configuration
        self.log_level = os.getenv('LOG_LEVEL', 'INFO').upper()
        self.log_file = Path(os.getenv('LOG_FILE', './logs/azkar_bot.log'))
        self.log_format = os.getenv(
            'LOG_FORMAT', 
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        # Development Settings
        self.debug = self._get_bool_env('DEBUG', False)
        self.development_mode = self._get_bool_env('DEVELOPMENT_MODE', False)
        
        # Content paths
        self.azkar_file = self.content_dir / 'azkar.txt'
        self.images_dir = self.content_dir / 'images'
        self.voices_dir = self.content_dir / 'voices'
        self.audios_dir = self.content_dir / 'audios'
        self.morning_dir = self.content_dir / 'morning'
        self.evening_dir = self.content_dir / 'evening'
        self.prayers_dir = self.content_dir / 'prayers'
    
    def _get_int_env(self, key: str, default: int) -> int:
        """Get integer value from environment variable"""
        try:
            value = os.getenv(key)
            return int(value) if value else default
        except (ValueError, TypeError):
            logger.warning(f"Invalid integer value for {key}, using default: {default}")
            return default
    
    def _get_bool_env(self, key: str, default: bool) -> bool:
        """Get boolean value from environment variable"""
        value = os.getenv(key, '').lower()
        if value in ('true', '1', 'yes', 'on'):
            return True
        elif value in ('false', '0', 'no', 'off'):
            return False
        return default
    
    def _parse_time_list(self, time_string: str) -> List[tuple]:
        """
        Parse comma-separated time string into list of (hour, minute) tuples
        
        Args:
            time_string: String like "05:30,07:00,08:00"
            
        Returns:
            List of (hour, minute) tuples
        """
        times = []
        for time_str in time_string.split(','):
            time_str = time_str.strip()
            try:
                hour, minute = map(int, time_str.split(':'))
                if 0 <= hour <= 23 and 0 <= minute <= 59:
                    times.append((hour, minute))
                else:
                    logger.warning(f"Invalid time format: {time_str}")
            except ValueError:
                logger.warning(f"Could not parse time: {time_str}")
        return times
    
    def validate(self) -> None:
        """
        Validate configuration settings
        
        Raises:
            ConfigurationError: If required settings are missing or invalid
        """
        errors = []
        
        # Validate required settings
        if not self.bot_token:
            errors.append("BOT_TOKEN is required")
        
        if not self.admin_id:
            errors.append("ADMIN_ID is required")
        
        # Validate log level
        valid_log_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        if self.log_level not in valid_log_levels:
            errors.append(f"LOG_LEVEL must be one of: {', '.join(valid_log_levels)}")
        
        # Validate interval
        if self.random_content_interval <= 0:
            errors.append("RANDOM_CONTENT_INTERVAL must be positive")
        
        # Validate time lists
        if not self.morning_azkar_times:
            errors.append("MORNING_AZKAR_TIMES must contain at least one valid time")
        
        if not self.evening_azkar_times:
            errors.append("EVENING_AZKAR_TIMES must contain at least one valid time")
        
        if errors:
            raise ConfigurationError(f"Configuration errors: {'; '.join(errors)}")
    
    def ensure_directories(self) -> None:
        """Create necessary directories if they don't exist"""
        directories = [
            self.data_dir,
            self.content_dir,
            self.groups_file.parent,
            self.log_file.parent,
            self.images_dir,
            self.voices_dir,
            self.audios_dir,
            self.morning_dir,
            self.evening_dir,
            self.prayers_dir,
        ]
        
        for directory in directories:
            try:
                directory.mkdir(parents=True, exist_ok=True)
                logger.debug(f"Ensured directory exists: {directory}")
            except OSError as e:
                logger.error(f"Failed to create directory {directory}: {e}")
                raise ConfigurationError(f"Cannot create directory: {directory}")
    
    def get_content_directories(self) -> dict:
        """Get mapping of content types to their directories"""
        return {
            'images': self.images_dir,
            'voices': self.voices_dir,
            'audios': self.audios_dir,
            'morning': self.morning_dir,
            'evening': self.evening_dir,
            'prayers': self.prayers_dir,
        }
    
    def __repr__(self) -> str:
        """String representation of config (without sensitive data)"""
        return (
            f"Config("
            f"admin_id={self.admin_id}, "
            f"timezone={self.timezone}, "
            f"debug={self.debug}, "
            f"log_level={self.log_level}"
            f")"
        )