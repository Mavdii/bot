"""
Message and callback handlers for the Azkar Bot

This module contains all the handlers for processing:
- Admin commands and operations
- Regular user messages
- Callback queries from inline keyboards
"""

from .admin import AdminHandler
from .messages import MessageHandler
from .callbacks import CallbackHandler

__all__ = ["AdminHandler", "MessageHandler", "CallbackHandler"]