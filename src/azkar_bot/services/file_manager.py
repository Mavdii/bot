"""
File management service for the Azkar Bot

This service handles all file operations including:
- Downloading files from Telegram
- File validation and security checks
- Media file management
- File organization and cleanup
"""

import aiohttp
import asyncio
from pathlib import Path
from typing import Optional, Dict, Any, List
from datetime import datetime
import mimetypes
import hashlib

from ..utils.logger import LoggerMixin
from ..utils.helpers import (
    sanitize_filename, get_file_extension, is_valid_file_extension,
    format_file_size, safe_json_save, safe_json_load, retry_on_failure
)
from ..utils.constants import FILE_EXTENSIONS, MIME_TYPES, MAX_FILE_SIZE, ContentType


class FileManager(LoggerMixin):
    """
    Manages all file operations for the bot
    
    This service provides functionality for:
    - Downloading files from Telegram API
    - File validation and security checks
    - Media file organization
    - File metadata management
    """
    
    def __init__(self, bot_token: str, content_dir: Path):
        """
        Initialize file manager
        
        Args:
            bot_token: Telegram bot token for API access
            content_dir: Base directory for content storage
        """
        self.bot_token = bot_token
        self.content_dir = Path(content_dir)
        self.base_url = f"https://api.telegram.org/bot{bot_token}"
        self.file_url = f"https://api.telegram.org/file/bot{bot_token}"
        
        # Ensure content directories exist
        self._ensure_directories()
        
        self.log_info("📁 تم تهيئة مدير الملفات - File manager initialized")
    
    def _ensure_directories(self) -> None:
        """Ensure all necessary directories exist"""
        directories = [
            self.content_dir,
            self.content_dir / "images",
            self.content_dir / "voices", 
            self.content_dir / "audios",
            self.content_dir / "morning",
            self.content_dir / "evening",
            self.content_dir / "prayers",
            self.content_dir / "temp"
        ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
            self.log_debug(f"📂 تأكد من وجود المجلد - Ensured directory: {directory}")
    
    @retry_on_failure(max_retries=3)
    async def download_file(self, file_id: str, destination_folder: str, 
                          custom_filename: str = None) -> Optional[Path]:
        """
        Download file from Telegram
        
        Args:
            file_id: Telegram file ID
            destination_folder: Folder name within content directory
            custom_filename: Custom filename (optional)
            
        Returns:
            Path to downloaded file or None if failed
        """
        try:
            # Get file info from Telegram
            file_info = await self._get_file_info(file_id)
            if not file_info:
                return None
            
            file_path = file_info.get('file_path')
            file_size = file_info.get('file_size', 0)
            
            # Validate file size
            if file_size > MAX_FILE_SIZE:
                self.log_warning(f"⚠️ الملف كبير جداً - File too large: {format_file_size(file_size)}")
                return None
            
            # Determine file extension
            original_extension = get_file_extension(file_path) if file_path else ''
            if not original_extension:
                self.log_warning("⚠️ لا يمكن تحديد نوع الملف - Cannot determine file type")
                return None
            
            # Generate filename
            if custom_filename:
                filename = sanitize_filename(custom_filename)
                if not get_file_extension(filename):
                    filename += original_extension
            else:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"{timestamp}{original_extension}"
            
            # Determine destination directory
            dest_dir = self.content_dir / destination_folder
            dest_dir.mkdir(parents=True, exist_ok=True)
            
            # Full destination path
            dest_path = dest_dir / filename
            
            # Download the file
            download_url = f"{self.file_url}/{file_path}"
            
            async with aiohttp.ClientSession() as session:
                async with session.get(download_url) as response:
                    if response.status == 200:
                        # Read file content
                        file_content = await response.read()
                        
                        # Validate file content
                        if not self._validate_file_content(file_content, original_extension):
                            self.log_warning("⚠️ محتوى الملف غير صالح - Invalid file content")
                            return None
                        
                        # Save file
                        with open(dest_path, 'wb') as f:
                            f.write(file_content)
                        
                        # Verify file was saved correctly
                        if dest_path.exists() and dest_path.stat().st_size > 0:
                            self.log_info(f"✅ تم تحميل الملف - Downloaded file: {filename} ({format_file_size(len(file_content))})")
                            return dest_path
                        else:
                            self.log_error("❌ فشل في حفظ الملف - Failed to save file")
                            return None
                    else:
                        self.log_error(f"❌ فشل في تحميل الملف - Download failed with status: {response.status}")
                        return None
                        
        except Exception as e:
            self.log_error(f"❌ خطأ في تحميل الملف - Error downloading file {file_id}", e)
            return None
    
    async def _get_file_info(self, file_id: str) -> Optional[Dict[str, Any]]:
        """Get file information from Telegram API"""
        try:
            url = f"{self.base_url}/getFile"
            params = {'file_id': file_id}
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data.get('ok'):
                            return data.get('result')
                    
                    self.log_error(f"❌ فشل في الحصول على معلومات الملف - Failed to get file info: {response.status}")
                    return None
                    
        except Exception as e:
            self.log_error(f"❌ خطأ في الحصول على معلومات الملف - Error getting file info for {file_id}", e)
            return None
    
    def _validate_file_content(self, content: bytes, extension: str) -> bool:
        """
        Validate file content for security
        
        Args:
            content: File content bytes
            extension: File extension
            
        Returns:
            True if file is valid, False otherwise
        """
        if not content:
            return False
        
        # Check file size
        if len(content) > MAX_FILE_SIZE:
            return False
        
        # Basic file signature validation
        file_signatures = {
            '.jpg': [b'\xff\xd8\xff'],
            '.jpeg': [b'\xff\xd8\xff'],
            '.png': [b'\x89PNG\r\n\x1a\n'],
            '.gif': [b'GIF87a', b'GIF89a'],
            '.mp3': [b'ID3', b'\xff\xfb', b'\xff\xf3', b'\xff\xf2'],
            '.ogg': [b'OggS'],
            '.wav': [b'RIFF'],
            '.mp4': [b'\x00\x00\x00\x18ftypmp4', b'\x00\x00\x00\x20ftypmp4'],
        }
        
        if extension.lower() in file_signatures:
            signatures = file_signatures[extension.lower()]
            for signature in signatures:
                if content.startswith(signature):
                    return True
            
            self.log_warning(f"⚠️ توقيع الملف غير صحيح - Invalid file signature for {extension}")
            return False
        
        # For other file types, just check if not empty
        return len(content) > 0
    
    def save_media_info(self, file_path: Path, caption: str = None, 
                       media_type: str = None, additional_info: Dict[str, Any] = None) -> bool:
        """
        Save media file information
        
        Args:
            file_path: Path to media file
            caption: Optional caption
            media_type: Type of media
            additional_info: Additional metadata
            
        Returns:
            True if saved successfully, False otherwise
        """
        try:
            info_file = file_path.with_suffix(file_path.suffix + '.info')
            
            # Gather file information
            file_stats = file_path.stat()
            info_data = {
                'caption': caption or '',
                'type': media_type or self._detect_media_type(file_path),
                'created_at': datetime.now().isoformat(),
                'file_size': file_stats.st_size,
                'file_size_formatted': format_file_size(file_stats.st_size),
                'mime_type': mimetypes.guess_type(str(file_path))[0],
                'checksum': self._calculate_file_checksum(file_path)
            }
            
            # Add additional info if provided
            if additional_info:
                info_data.update(additional_info)
            
            # Save info file
            if safe_json_save(info_data, info_file):
                self.log_debug(f"💾 تم حفظ معلومات الملف - Saved media info for {file_path.name}")
                return True
            else:
                self.log_error(f"❌ فشل في حفظ معلومات الملف - Failed to save media info for {file_path.name}")
                return False
                
        except Exception as e:
            self.log_error(f"❌ خطأ في حفظ معلومات الملف - Error saving media info for {file_path}", e)
            return False
    
    def load_media_info(self, file_path: Path) -> Optional[Dict[str, Any]]:
        """
        Load media file information
        
        Args:
            file_path: Path to media file
            
        Returns:
            Media info dictionary or None if not found
        """
        info_file = file_path.with_suffix(file_path.suffix + '.info')
        return safe_json_load(info_file)
    
    def _detect_media_type(self, file_path: Path) -> str:
        """Detect media type from file extension"""
        extension = file_path.suffix.lower()
        
        for content_type, extensions in FILE_EXTENSIONS.items():
            if extension in extensions:
                return content_type.value
        
        return ContentType.DOCUMENT.value
    
    def _calculate_file_checksum(self, file_path: Path) -> str:
        """Calculate MD5 checksum of file"""
        try:
            hash_md5 = hashlib.md5()
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_md5.update(chunk)
            return hash_md5.hexdigest()
        except Exception:
            return ""
    
    def get_random_file(self, folder: str, extensions: List[str]) -> Optional[Path]:
        """
        Get random file from folder with specified extensions
        
        Args:
            folder: Folder name within content directory
            extensions: List of valid extensions
            
        Returns:
            Random file path or None if no files found
        """
        try:
            folder_path = self.content_dir / folder
            if not folder_path.exists():
                return None
            
            # Find all files with valid extensions
            valid_files = []
            for file_path in folder_path.iterdir():
                if (file_path.is_file() and 
                    file_path.suffix.lower() in [ext.lower() for ext in extensions] and
                    not file_path.name.endswith('.info')):
                    valid_files.append(file_path)
            
            if valid_files:
                import random
                selected_file = random.choice(valid_files)
                self.log_debug(f"🎲 تم اختيار ملف عشوائي - Selected random file: {selected_file.name}")
                return selected_file
            
            return None
            
        except Exception as e:
            self.log_error(f"❌ خطأ في اختيار ملف عشوائي - Error getting random file from {folder}", e)
            return None
    
    def validate_file_path(self, file_path: Path) -> bool:
        """
        Validate file path for security
        
        Args:
            file_path: Path to validate
            
        Returns:
            True if path is safe, False otherwise
        """
        try:
            # Resolve path to check for directory traversal
            resolved_path = file_path.resolve()
            content_dir_resolved = self.content_dir.resolve()
            
            # Check if file is within content directory
            try:
                resolved_path.relative_to(content_dir_resolved)
                return True
            except ValueError:
                self.log_warning(f"⚠️ مسار الملف خارج المجلد المسموح - File path outside allowed directory: {file_path}")
                return False
                
        except Exception as e:
            self.log_error(f"❌ خطأ في التحقق من مسار الملف - Error validating file path: {file_path}", e)
            return False
    
    def cleanup_temp_files(self) -> int:
        """
        Clean up temporary files
        
        Returns:
            Number of files cleaned up
        """
        try:
            temp_dir = self.content_dir / "temp"
            if not temp_dir.exists():
                return 0
            
            cleaned_count = 0
            cutoff_time = datetime.now().timestamp() - (24 * 60 * 60)  # 24 hours ago
            
            for file_path in temp_dir.iterdir():
                if file_path.is_file():
                    file_time = file_path.stat().st_mtime
                    if file_time < cutoff_time:
                        try:
                            file_path.unlink()
                            cleaned_count += 1
                        except OSError:
                            pass
            
            if cleaned_count > 0:
                self.log_info(f"🧹 تم حذف {cleaned_count} ملف مؤقت - Cleaned up {cleaned_count} temporary files")
            
            return cleaned_count
            
        except Exception as e:
            self.log_error("❌ خطأ في تنظيف الملفات المؤقتة - Error cleaning up temp files", e)
            return 0
    
    def get_folder_stats(self, folder: str) -> Dict[str, Any]:
        """
        Get statistics for a folder
        
        Args:
            folder: Folder name within content directory
            
        Returns:
            Dictionary with folder statistics
        """
        try:
            folder_path = self.content_dir / folder
            if not folder_path.exists():
                return {'exists': False}
            
            stats = {
                'exists': True,
                'total_files': 0,
                'total_size': 0,
                'file_types': {},
                'last_modified': None
            }
            
            latest_time = 0
            
            for file_path in folder_path.iterdir():
                if file_path.is_file() and not file_path.name.endswith('.info'):
                    stats['total_files'] += 1
                    
                    file_stats = file_path.stat()
                    stats['total_size'] += file_stats.st_size
                    
                    # Track file types
                    extension = file_path.suffix.lower()
                    stats['file_types'][extension] = stats['file_types'].get(extension, 0) + 1
                    
                    # Track latest modification
                    if file_stats.st_mtime > latest_time:
                        latest_time = file_stats.st_mtime
                        stats['last_modified'] = datetime.fromtimestamp(latest_time).isoformat()
            
            stats['total_size_formatted'] = format_file_size(stats['total_size'])
            
            return stats
            
        except Exception as e:
            self.log_error(f"❌ خطأ في الحصول على إحصائيات المجلد - Error getting folder stats for {folder}", e)
            return {'exists': False, 'error': str(e)}
    
    def verify_file_integrity(self, file_path: Path) -> bool:
        """
        Verify file integrity using checksum
        
        Args:
            file_path: Path to file to verify
            
        Returns:
            True if file is intact, False otherwise
        """
        try:
            if not file_path.exists():
                return False
            
            # Load stored checksum
            info = self.load_media_info(file_path)
            if not info or 'checksum' not in info:
                # No stored checksum, calculate and store it
                checksum = self._calculate_file_checksum(file_path)
                if checksum:
                    self.save_media_info(file_path, additional_info={'checksum': checksum})
                return True
            
            # Compare checksums
            stored_checksum = info['checksum']
            current_checksum = self._calculate_file_checksum(file_path)
            
            if stored_checksum == current_checksum:
                return True
            else:
                self.log_warning(f"⚠️ تلف في الملف - File integrity check failed: {file_path.name}")
                return False
                
        except Exception as e:
            self.log_error(f"❌ خطأ في التحقق من سلامة الملف - Error verifying file integrity: {file_path}", e)
            return False