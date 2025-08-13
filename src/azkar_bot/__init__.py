"""
Islamic Azkar Telegram Bot

A professional Telegram bot for sending Islamic remembrances (Azkar) 
to groups with scheduled delivery and admin management features.

Author: Omar Mahdy (@Mavdiii)
Email: omarelmhdi@gmail.com
Repository: https://github.com/Mavdii/bot
"""

__version__ = "2.0.0"
__author__ = "Omar Mahdy"
__email__ = "omarelmhdi@gmail.com"

from .core.bot import AzkarBot
from .core.config import Config

__all__ = ["AzkarBot", "Config"]