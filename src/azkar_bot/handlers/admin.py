"""
Admin handler for the Azkar Bot

This module handles all admin-related operations including:
- Admin panel management
- Content upload and management
- Bot statistics and monitoring
- Admin command processing
"""

from typing import Dict, Any, Optional
from pathlib import Path
import asyncio

from ..services.content_manager import ContentManager
from ..services.file_manager import FileManager
from ..services.group_manager import GroupManager
from ..utils.logger import LoggerMixin
from ..utils.constants import (
    MESSAGES, ADMIN_KEYBOARD, BACK_KEYBOARD, SKIP_CAPTION_KEYBOARD,
    AdminAction, ContentType
)
from ..utils.helpers import format_datetime


class AdminHandler(LoggerMixin):
    """
    Handles all admin-related operations
    
    This handler provides functionality for:
    - Admin panel interface
    - Content management operations
    - File upload handling
    - Statistics and monitoring
    """
    
    def __init__(self, admin_id: int, content_manager: ContentManager,
                 file_manager: FileManager, group_manager: GroupManager):
        """
        Initialize admin handler
        
        Args:
            admin_id: Telegram ID of the admin user
            content_manager: Content management service
            file_manager: File management service
            group_manager: Group management service
        """
        self.admin_id = admin_id
        self.content_manager = content_manager
        self.file_manager = file_manager
        self.group_manager = group_manager
        
        # Admin states for multi-step operations
        self.admin_states: Dict[int, Dict[str, Any]] = {}
        
        self.log_info("👑 تم تهيئة معالج المشرف - Admin handler initialized")
    
    def is_admin(self, user_id: int) -> bool:
        """
        Check if user is admin
        
        Args:
            user_id: Telegram user ID
            
        Returns:
            True if user is admin, False otherwise
        """
        return user_id == self.admin_id
    
    async def handle_admin_command(self, user_id: int, chat_id: int, 
                                 command: str, args: str = None) -> Dict[str, Any]:
        """
        Handle admin commands
        
        Args:
            user_id: User ID who sent the command
            chat_id: Chat ID where command was sent
            command: Command name
            args: Command arguments
            
        Returns:
            Response dictionary with message and keyboard
        """
        if not self.is_admin(user_id):
            return {
                'text': MESSAGES['unauthorized'],
                'keyboard': None
            }
        
        if command == '/admin':
            return await self.show_admin_panel(chat_id)
        elif command == '/stats':
            return await self.get_bot_stats(chat_id)
        elif command.startswith('/add_text'):
            text_content = args or command.replace('/add_text', '').strip()
            return await self.add_text_content(chat_id, text_content)
        else:
            return {
                'text': f"❌ أمر غير معروف - Unknown command: {command}",
                'keyboard': None
            }
    
    async def show_admin_panel(self, chat_id: int) -> Dict[str, Any]:
        """
        Show admin panel with available options
        
        Args:
            chat_id: Chat ID to send panel to
            
        Returns:
            Response dictionary with admin panel
        """
        self.log_info("🔧 عرض لوحة تحكم المشرف - Showing admin panel")
        
        return {
            'text': MESSAGES['admin_panel'],
            'keyboard': ADMIN_KEYBOARD
        }
    
    async def handle_callback_query(self, user_id: int, chat_id: int, 
                                  message_id: int, callback_data: str) -> Dict[str, Any]:
        """
        Handle callback queries from admin panel
        
        Args:
            user_id: User ID who clicked the button
            chat_id: Chat ID
            message_id: Message ID to edit
            callback_data: Callback data from button
            
        Returns:
            Response dictionary with action to take
        """
        if not self.is_admin(user_id):
            return {
                'action': 'answer_callback',
                'text': MESSAGES['unauthorized']
            }
        
        self.log_debug(f"🔘 معالجة استعلام المشرف - Processing admin callback: {callback_data}")
        
        if callback_data == "admin_add_text":
            return await self._handle_add_text_callback(chat_id, message_id)
        elif callback_data == "admin_add_image":
            return await self._handle_add_media_callback(chat_id, message_id, "image")
        elif callback_data == "admin_add_voice":
            return await self._handle_add_media_callback(chat_id, message_id, "voice")
        elif callback_data == "admin_add_audio":
            return await self._handle_add_media_callback(chat_id, message_id, "audio")
        elif callback_data == "admin_add_document":
            return await self._handle_add_media_callback(chat_id, message_id, "document")
        elif callback_data == "admin_stats":
            return await self._handle_stats_callback(chat_id, message_id)
        elif callback_data == "admin_view_content":
            return await self._handle_view_content_callback(chat_id, message_id)
        elif callback_data == "admin_back":
            return await self._handle_back_callback(chat_id, message_id)
        elif callback_data == "admin_close":
            return await self._handle_close_callback(chat_id, message_id)
        elif callback_data == "skip_caption":
            return await self._handle_skip_caption_callback(user_id, chat_id, message_id)
        else:
            return {
                'action': 'answer_callback',
                'text': f"❌ إجراء غير معروف - Unknown action: {callback_data}"
            }
    
    async def _handle_add_text_callback(self, chat_id: int, message_id: int) -> Dict[str, Any]:
        """Handle add text callback"""
        self.admin_states[self.admin_id] = {'action': AdminAction.WAITING_FOR_TEXT.value}
        
        return {
            'action': 'edit_message',
            'message_id': message_id,
            'text': "📝 **إضافة نص جديد**\n\nاكتب النص الذي تريد إضافته:",
            'keyboard': None
        }
    
    async def _handle_add_media_callback(self, chat_id: int, message_id: int, 
                                       media_type: str) -> Dict[str, Any]:
        """Handle add media callback"""
        action_map = {
            'image': AdminAction.WAITING_FOR_IMAGE,
            'voice': AdminAction.WAITING_FOR_VOICE,
            'audio': AdminAction.WAITING_FOR_AUDIO,
            'document': AdminAction.WAITING_FOR_DOCUMENT
        }
        
        self.admin_states[self.admin_id] = {'action': action_map[media_type].value}
        
        media_names = {
            'image': 'صورة',
            'voice': 'رسالة صوتية',
            'audio': 'ملف صوتي',
            'document': 'مستند'
        }
        
        return {
            'action': 'edit_message',
            'message_id': message_id,
            'text': f"📁 **إضافة {media_names[media_type]}**\n\nأرسل {media_names[media_type]} التي تريد إضافتها:",
            'keyboard': None
        }
    
    async def _handle_stats_callback(self, chat_id: int, message_id: int) -> Dict[str, Any]:
        """Handle stats callback"""
        stats = await self.get_bot_stats(chat_id)
        
        return {
            'action': 'edit_message',
            'message_id': message_id,
            'text': stats['text'],
            'keyboard': BACK_KEYBOARD
        }
    
    async def _handle_view_content_callback(self, chat_id: int, message_id: int) -> Dict[str, Any]:
        """Handle view content callback"""
        content_info = await self.get_content_info(chat_id)
        
        return {
            'action': 'edit_message',
            'message_id': message_id,
            'text': content_info['text'],
            'keyboard': BACK_KEYBOARD
        }
    
    async def _handle_back_callback(self, chat_id: int, message_id: int) -> Dict[str, Any]:
        """Handle back button callback"""
        return {
            'action': 'delete_and_send',
            'message_id': message_id,
            'text': MESSAGES['admin_panel'],
            'keyboard': ADMIN_KEYBOARD
        }
    
    async def _handle_close_callback(self, chat_id: int, message_id: int) -> Dict[str, Any]:
        """Handle close button callback"""
        return {
            'action': 'delete_and_send',
            'message_id': message_id,
            'text': MESSAGES['admin_panel_closed'],
            'keyboard': None
        }
    
    async def _handle_skip_caption_callback(self, user_id: int, chat_id: int, 
                                          message_id: int) -> Dict[str, Any]:
        """Handle skip caption callback"""
        state = self.admin_states.get(user_id, {})
        file_path = state.get('file_path')
        file_type = state.get('file_type')
        
        if file_path and file_type:
            # Save file without caption
            success = self.content_manager.add_media_content(
                Path(file_path), 
                file_type, 
                caption=""
            )
            
            if success:
                file_name = Path(file_path).name
                response_text = MESSAGES['file_uploaded'].format(
                    filename=file_name,
                    caption="بدون وصف نصي"
                )
            else:
                response_text = MESSAGES['error_file_upload'].format(error="فشل في حفظ الملف")
            
            # Clear admin state
            if user_id in self.admin_states:
                del self.admin_states[user_id]
            
            return {
                'action': 'edit_and_delay_panel',
                'message_id': message_id,
                'text': response_text,
                'delay': 2
            }
        
        return {
            'action': 'answer_callback',
            'text': "❌ لا يوجد ملف للحفظ - No file to save"
        }
    
    async def handle_message(self, user_id: int, chat_id: int, 
                           message: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Handle messages from admin
        
        Args:
            user_id: User ID who sent the message
            chat_id: Chat ID
            message: Message data
            
        Returns:
            Response dictionary or None if no response needed
        """
        if not self.is_admin(user_id):
            return None
        
        # Check if admin is in a state
        state = self.admin_states.get(user_id, {})
        if not state:
            return None
        
        action = state.get('action')
        
        if action == AdminAction.WAITING_FOR_TEXT.value:
            return await self._handle_text_input(user_id, chat_id, message)
        elif action == AdminAction.WAITING_FOR_CAPTION.value:
            return await self._handle_caption_input(user_id, chat_id, message)
        elif action in [AdminAction.WAITING_FOR_IMAGE.value, 
                       AdminAction.WAITING_FOR_VOICE.value,
                       AdminAction.WAITING_FOR_AUDIO.value,
                       AdminAction.WAITING_FOR_DOCUMENT.value]:
            return await self._handle_media_input(user_id, chat_id, message)
        
        return None
    
    async def _handle_text_input(self, user_id: int, chat_id: int, 
                                message: Dict[str, Any]) -> Dict[str, Any]:
        """Handle text input from admin"""
        text = message.get('text', '').strip()
        
        if text:
            success = self.content_manager.add_text_content(text)
            if success:
                response_text = MESSAGES['text_added']
            else:
                response_text = MESSAGES['error_file_upload'].format(error="فشل في إضافة النص")
        else:
            response_text = MESSAGES['error_invalid_text']
        
        # Clear admin state
        if user_id in self.admin_states:
            del self.admin_states[user_id]
        
        return {
            'text': response_text,
            'keyboard': None,
            'show_panel_after': True
        }
    
    async def _handle_caption_input(self, user_id: int, chat_id: int, 
                                  message: Dict[str, Any]) -> Dict[str, Any]:
        """Handle caption input from admin"""
        caption = message.get('text', '').strip()
        state = self.admin_states.get(user_id, {})
        
        file_path = state.get('file_path')
        file_type = state.get('file_type')
        
        if file_path and file_type:
            success = self.content_manager.add_media_content(
                Path(file_path), 
                file_type, 
                caption=caption
            )
            
            if success:
                file_name = Path(file_path).name
                caption_text = caption if caption else "بدون وصف نصي"
                response_text = MESSAGES['file_uploaded'].format(
                    filename=file_name,
                    caption=caption_text
                )
            else:
                response_text = MESSAGES['error_file_upload'].format(error="فشل في حفظ الملف")
        else:
            response_text = "❌ خطأ في معلومات الملف - File information error"
        
        # Clear admin state
        if user_id in self.admin_states:
            del self.admin_states[user_id]
        
        return {
            'text': response_text,
            'keyboard': None,
            'show_panel_after': True
        }
    
    async def _handle_media_input(self, user_id: int, chat_id: int, 
                                message: Dict[str, Any]) -> Dict[str, Any]:
        """Handle media input from admin"""
        state = self.admin_states.get(user_id, {})
        action = state.get('action')
        
        # Determine expected media type and file info
        file_info = None
        destination_folder = "random"
        
        if action == AdminAction.WAITING_FOR_IMAGE.value and message.get('photo'):
            file_info = message['photo'][-1]  # Highest quality
            destination_folder = "images"
        elif action == AdminAction.WAITING_FOR_VOICE.value and message.get('voice'):
            file_info = message['voice']
            destination_folder = "voices"
        elif action == AdminAction.WAITING_FOR_AUDIO.value and message.get('audio'):
            file_info = message['audio']
            destination_folder = "audios"
        elif action == AdminAction.WAITING_FOR_DOCUMENT.value and message.get('document'):
            file_info = message['document']
            file_name = file_info.get('file_name', 'document')
            
            # Determine folder based on file type
            if any(ext in file_name.lower() for ext in ['.jpg', '.jpeg', '.png']):
                destination_folder = "images"
            elif any(ext in file_name.lower() for ext in ['.mp3', '.mp4', '.wav']):
                destination_folder = "audios"
            else:
                destination_folder = "random"
        
        if not file_info:
            return {
                'text': "❌ نوع الملف غير صحيح - Invalid file type for this operation",
                'keyboard': None
            }
        
        # Download the file
        file_id = file_info['file_id']
        file_path = await self.file_manager.download_file(file_id, destination_folder)
        
        if file_path:
            # Update admin state to wait for caption
            self.admin_states[user_id] = {
                'action': AdminAction.WAITING_FOR_CAPTION.value,
                'file_path': str(file_path),
                'file_type': destination_folder
            }
            
            return {
                'text': "✅ تم تحميل الملف بنجاح!\n\n📝 اكتب وصفاً للملف أو اضغط تخطي:",
                'keyboard': SKIP_CAPTION_KEYBOARD
            }
        else:
            # Clear admin state on failure
            if user_id in self.admin_states:
                del self.admin_states[user_id]
            
            return {
                'text': MESSAGES['error_file_upload'].format(error="فشل في تحميل الملف"),
                'keyboard': None,
                'show_panel_after': True
            }
    
    async def add_text_content(self, chat_id: int, text: str) -> Dict[str, Any]:
        """
        Add text content directly
        
        Args:
            chat_id: Chat ID
            text: Text content to add
            
        Returns:
            Response dictionary
        """
        if not text or not text.strip():
            return {
                'text': MESSAGES['error_invalid_text'],
                'keyboard': None
            }
        
        success = self.content_manager.add_text_content(text.strip())
        
        if success:
            return {
                'text': MESSAGES['text_added'],
                'keyboard': None
            }
        else:
            return {
                'text': MESSAGES['error_file_upload'].format(error="فشل في إضافة النص"),
                'keyboard': None
            }
    
    async def get_bot_stats(self, chat_id: int) -> Dict[str, Any]:
        """
        Get comprehensive bot statistics
        
        Args:
            chat_id: Chat ID
            
        Returns:
            Response dictionary with statistics
        """
        try:
            # Get group statistics
            group_stats = self.group_manager.get_groups_stats()
            
            # Get content statistics
            content_stats = self.content_manager.get_content_stats()
            
            # Format statistics
            stats_text = MESSAGES['stats_template'].format(
                groups_count=group_stats['active_groups'],
                texts_count=content_stats['text_content']['total_items'],
                images_count=content_stats['media_collections'].get('random', {}).get('total_items', 0),
                voices_count=content_stats['media_collections'].get('voices', {}).get('total_items', 0),
                audios_count=content_stats['media_collections'].get('audios', {}).get('total_items', 0),
                last_update=format_datetime(group_stats.get('last_updated'))
            )
            
            return {
                'text': stats_text,
                'keyboard': None
            }
            
        except Exception as e:
            self.log_error("❌ خطأ في جلب الإحصائيات - Error getting bot stats", e)
            return {
                'text': f"❌ خطأ في جلب الإحصائيات: {str(e)}",
                'keyboard': None
            }
    
    async def get_content_info(self, chat_id: int) -> Dict[str, Any]:
        """
        Get content information
        
        Args:
            chat_id: Chat ID
            
        Returns:
            Response dictionary with content info
        """
        try:
            content_stats = self.content_manager.get_content_stats()
            
            # Calculate totals
            media_collections = content_stats['media_collections']
            total_files = sum(collection.get('total_items', 0) for collection in media_collections.values())
            
            content_text = MESSAGES['content_info_template'].format(
                texts_count=content_stats['text_content']['total_items'],
                images_count=media_collections.get('random', {}).get('total_items', 0),
                voices_count=media_collections.get('voices', {}).get('total_items', 0),
                audios_count=media_collections.get('audios', {}).get('total_items', 0),
                morning_count=media_collections.get('morning', {}).get('total_items', 0),
                evening_count=media_collections.get('evening', {}).get('total_items', 0),
                prayers_count=media_collections.get('prayers', {}).get('total_items', 0),
                total_files=total_files
            )
            
            return {
                'text': content_text,
                'keyboard': None
            }
            
        except Exception as e:
            self.log_error("❌ خطأ في جلب معلومات المحتوى - Error getting content info", e)
            return {
                'text': f"❌ خطأ في جلب معلومات المحتوى: {str(e)}",
                'keyboard': None
            }
    
    def clear_admin_state(self, user_id: int) -> None:
        """
        Clear admin state for user
        
        Args:
            user_id: User ID to clear state for
        """
        if user_id in self.admin_states:
            del self.admin_states[user_id]
            self.log_debug(f"🧹 تم مسح حالة المشرف - Cleared admin state for user {user_id}")
    
    def get_admin_state(self, user_id: int) -> Optional[Dict[str, Any]]:
        """
        Get current admin state for user
        
        Args:
            user_id: User ID
            
        Returns:
            Admin state dictionary or None
        """
        return self.admin_states.get(user_id)