"""
Content management service for the Azkar Bot

This service handles all content-related operations including:
- Loading and managing azkar texts
- Managing media content
- Content rotation and selection
- Content validation and processing
"""

import random
from pathlib import Path
from typing import List, Optional, Dict, Any, Union
from datetime import datetime

from ..models.content import Content, TextContent, MediaContent, ContentCollection, ContentType
from ..utils.logger import LoggerMixin
from ..utils.helpers import safe_json_load, safe_json_save, get_random_item, clean_text
from ..utils.constants import DEFAULT_AZKAR, CONTENT_ROTATION_CYCLE


class ContentManager(LoggerMixin):
    """
    Manages all content operations for the bot
    
    This service provides functionality for:
    - Loading azkar texts from files
    - Managing media content collections
    - Content rotation and random selection
    - Content validation and processing
    """
    
    def __init__(self, content_dir: Path, azkar_file: Path):
        """
        Initialize content manager
        
        Args:
            content_dir: Directory containing all content
            azkar_file: Path to azkar text file
        """
        self.content_dir = Path(content_dir)
        self.azkar_file = Path(azkar_file)
        
        # Content collections
        self.text_collection = ContentCollection("azkar_texts", "Islamic remembrances and prayers")
        self.media_collections: Dict[str, ContentCollection] = {}
        
        # Content rotation state
        self.rotation_index = 0
        
        # Initialize collections
        self._initialize_collections()
        
        self.log_info("📚 تم تهيئة مدير المحتوى - Content manager initialized")
    
    def _initialize_collections(self) -> None:
        """Initialize all content collections"""
        # Initialize media collections for different types
        collection_configs = [
            ("random", "Random images and media", self.content_dir / "images"),
            ("voices", "Voice messages", self.content_dir / "voices"),
            ("audios", "Audio files", self.content_dir / "audios"),
            ("morning", "Morning azkar images", self.content_dir / "morning"),
            ("evening", "Evening azkar images", self.content_dir / "evening"),
            ("prayers", "Prayer-related images", self.content_dir / "prayers"),
        ]
        
        for name, description, directory in collection_configs:
            self.media_collections[name] = ContentCollection(name, description)
            if directory.exists():
                self._load_media_from_directory(directory, name)
        
        # Load text content
        self._load_azkar_texts()
    
    def _load_azkar_texts(self) -> None:
        """Load azkar texts from file"""
        try:
            if self.azkar_file.exists():
                with open(self.azkar_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Split by separator and clean
                azkar_list = [clean_text(azkar) for azkar in content.split('---') if azkar.strip()]
                
                # Create TextContent objects
                for i, azkar_text in enumerate(azkar_list):
                    if azkar_text:
                        text_content = TextContent(
                            text=azkar_text,
                            source="Azkar Collection",
                            reference=f"Item {i+1}"
                        )
                        self.text_collection.add_content(text_content)
                
                self.log_info(f"📖 تم تحميل {len(azkar_list)} ذكر - Loaded {len(azkar_list)} azkar texts")
            else:
                # Use default azkar if file doesn't exist
                self.log_warning(f"⚠️ ملف الأذكار غير موجود، استخدام الأذكار الافتراضية - Azkar file not found, using defaults")
                for i, azkar_text in enumerate(DEFAULT_AZKAR):
                    text_content = TextContent(
                        text=azkar_text,
                        source="Default Collection",
                        reference=f"Default {i+1}"
                    )
                    self.text_collection.add_content(text_content)
                
        except Exception as e:
            self.log_error("❌ خطأ في تحميل الأذكار - Error loading azkar texts", e)
            # Fallback to default azkar
            for azkar_text in DEFAULT_AZKAR:
                text_content = TextContent(text=azkar_text, source="Fallback")
                self.text_collection.add_content(text_content)
    
    def _load_media_from_directory(self, directory: Path, collection_name: str) -> None:
        """Load media files from directory"""
        if not directory.exists():
            return
        
        collection = self.media_collections[collection_name]
        supported_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.mp3', '.ogg', '.wav', '.mp4']
        
        try:
            for file_path in directory.iterdir():
                if file_path.is_file() and file_path.suffix.lower() in supported_extensions:
                    # Skip .info files
                    if file_path.suffix == '.info':
                        continue
                    
                    # Load caption from .info file if exists
                    info_file = file_path.with_suffix(file_path.suffix + '.info')
                    caption = None
                    
                    if info_file.exists():
                        info_data = safe_json_load(info_file, {})
                        caption = info_data.get('caption', '')
                    
                    # Create media content
                    try:
                        media_content = MediaContent(
                            file_path=file_path,
                            caption=caption
                        )
                        collection.add_content(media_content)
                    except ValueError as e:
                        self.log_warning(f"⚠️ تخطي ملف غير صالح - Skipping invalid file {file_path}: {e}")
            
            self.log_info(f"📁 تم تحميل {len(collection.items)} ملف من {collection_name} - Loaded {len(collection.items)} files from {collection_name}")
            
        except Exception as e:
            self.log_error(f"❌ خطأ في تحميل الملفات من {directory} - Error loading files from {directory}", e)
    
    def get_random_azkar(self) -> Optional[TextContent]:
        """
        Get random azkar text
        
        Returns:
            Random TextContent or None if no content available
        """
        content = self.text_collection.get_random_content()
        if isinstance(content, TextContent):
            self.log_debug(f"🎲 تم اختيار ذكر عشوائي - Selected random azkar: {content.text[:50]}...")
            return content
        return None
    
    def get_random_media(self, media_type: str) -> Optional[MediaContent]:
        """
        Get random media content of specified type
        
        Args:
            media_type: Type of media (random, voices, audios, etc.)
            
        Returns:
            Random MediaContent or None if no content available
        """
        if media_type not in self.media_collections:
            self.log_warning(f"⚠️ نوع الوسائط غير معروف - Unknown media type: {media_type}")
            return None
        
        collection = self.media_collections[media_type]
        content = collection.get_random_content()
        
        if isinstance(content, MediaContent):
            self.log_debug(f"🎲 تم اختيار وسائط عشوائية - Selected random media from {media_type}: {content.file_name}")
            return content
        
        return None
    
    def get_rotated_content(self) -> Optional[Union[TextContent, MediaContent]]:
        """
        Get content using rotation system (text -> image -> voice -> audio)
        
        Returns:
            Content based on current rotation or None if no content available
        """
        content_types = ['text', 'random', 'voices', 'audios']
        current_type = content_types[self.rotation_index % len(content_types)]
        
        # Advance rotation
        self.rotation_index += 1
        
        if current_type == 'text':
            return self.get_random_azkar()
        else:
            return self.get_random_media(current_type)
    
    def add_text_content(self, text: str, source: str = None, reference: str = None) -> bool:
        """
        Add new text content
        
        Args:
            text: The azkar text
            source: Source of the text
            reference: Reference information
            
        Returns:
            True if added successfully, False otherwise
        """
        try:
            if not text or not text.strip():
                self.log_warning("⚠️ محاولة إضافة نص فارغ - Attempted to add empty text")
                return False
            
            text_content = TextContent(
                text=clean_text(text),
                source=source or "User Added",
                reference=reference
            )
            
            self.text_collection.add_content(text_content)
            
            # Save to file
            self._save_azkar_to_file()
            
            self.log_info(f"✅ تم إضافة نص جديد - Added new text: {text[:50]}...")
            return True
            
        except Exception as e:
            self.log_error("❌ خطأ في إضافة النص - Error adding text content", e)
            return False
    
    def add_media_content(self, file_path: Path, media_type: str, 
                         caption: str = None) -> bool:
        """
        Add new media content
        
        Args:
            file_path: Path to media file
            media_type: Type of media collection
            caption: Optional caption
            
        Returns:
            True if added successfully, False otherwise
        """
        try:
            if media_type not in self.media_collections:
                self.log_warning(f"⚠️ نوع الوسائط غير معروف - Unknown media type: {media_type}")
                return False
            
            media_content = MediaContent(
                file_path=file_path,
                caption=caption
            )
            
            collection = self.media_collections[media_type]
            collection.add_content(media_content)
            
            # Save caption info if provided
            if caption:
                self._save_media_info(file_path, caption, media_content.content_type.value)
            
            self.log_info(f"✅ تم إضافة ملف وسائط - Added media file: {file_path.name} to {media_type}")
            return True
            
        except Exception as e:
            self.log_error(f"❌ خطأ في إضافة الملف - Error adding media content: {file_path}", e)
            return False
    
    def _save_azkar_to_file(self) -> None:
        """Save current azkar texts to file"""
        try:
            # Ensure directory exists
            self.azkar_file.parent.mkdir(parents=True, exist_ok=True)
            
            # Collect all text content
            texts = []
            for content in self.text_collection.items:
                if isinstance(content, TextContent):
                    texts.append(content.text)
            
            # Write to file with separator
            with open(self.azkar_file, 'w', encoding='utf-8') as f:
                f.write('\n---\n'.join(texts))
            
            self.log_debug(f"💾 تم حفظ {len(texts)} ذكر في الملف - Saved {len(texts)} azkar to file")
            
        except Exception as e:
            self.log_error("❌ خطأ في حفظ الأذكار - Error saving azkar to file", e)
    
    def _save_media_info(self, file_path: Path, caption: str, media_type: str) -> None:
        """Save media information to .info file"""
        try:
            info_file = file_path.with_suffix(file_path.suffix + '.info')
            info_data = {
                'caption': caption,
                'type': media_type,
                'created_at': datetime.now().isoformat()
            }
            
            safe_json_save(info_data, info_file)
            self.log_debug(f"💾 تم حفظ معلومات الملف - Saved media info for {file_path.name}")
            
        except Exception as e:
            self.log_error(f"❌ خطأ في حفظ معلومات الملف - Error saving media info for {file_path}", e)
    
    def get_content_stats(self) -> Dict[str, Any]:
        """
        Get comprehensive content statistics
        
        Returns:
            Dictionary with content statistics
        """
        stats = {
            'text_content': self.text_collection.get_stats(),
            'media_collections': {},
            'total_content': len(self.text_collection.items),
            'rotation_index': self.rotation_index
        }
        
        total_media = 0
        for name, collection in self.media_collections.items():
            collection_stats = collection.get_stats()
            stats['media_collections'][name] = collection_stats
            total_media += collection_stats['total_items']
        
        stats['total_media'] = total_media
        stats['total_all_content'] = stats['total_content'] + total_media
        
        return stats
    
    def reload_content(self) -> None:
        """Reload all content from files"""
        self.log_info("🔄 إعادة تحميل المحتوى - Reloading all content")
        
        # Clear existing content
        self.text_collection.items.clear()
        for collection in self.media_collections.values():
            collection.items.clear()
        
        # Reload everything
        self._initialize_collections()
        
        self.log_info("✅ تم إعادة تحميل المحتوى بنجاح - Content reloaded successfully")
    
    def validate_content(self) -> Dict[str, List[str]]:
        """
        Validate all content and return issues found
        
        Returns:
            Dictionary with validation issues
        """
        issues = {
            'missing_files': [],
            'empty_content': [],
            'invalid_files': []
        }
        
        # Validate text content
        for content in self.text_collection.items:
            if isinstance(content, TextContent):
                if not content.text or not content.text.strip():
                    issues['empty_content'].append(f"Empty text content: {content.id}")
        
        # Validate media content
        for collection_name, collection in self.media_collections.items():
            for content in collection.items:
                if isinstance(content, MediaContent):
                    if not content.file_path.exists():
                        issues['missing_files'].append(f"{collection_name}: {content.file_path}")
                    elif content.file_size == 0:
                        issues['invalid_files'].append(f"{collection_name}: {content.file_path} (empty file)")
        
        return issues
    
    def cleanup_invalid_content(self) -> int:
        """
        Remove invalid content entries
        
        Returns:
            Number of items removed
        """
        removed_count = 0
        
        # Clean up media collections
        for collection in self.media_collections.values():
            items_to_remove = []
            for content in collection.items:
                if isinstance(content, MediaContent):
                    if not content.file_path.exists():
                        items_to_remove.append(content)
            
            for item in items_to_remove:
                collection.items.remove(item)
                removed_count += 1
        
        if removed_count > 0:
            self.log_info(f"🧹 تم حذف {removed_count} عنصر غير صالح - Removed {removed_count} invalid content items")
        
        return removed_count