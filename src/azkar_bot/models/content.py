"""
Content data models for the Azkar Bot

This module defines data structures for different types of content
including text, images, audio, and other media files.
"""

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any
from enum import Enum

from ..utils.constants import ContentType
from ..utils.helpers import generate_unique_id, format_datetime


@dataclass
class Content:
    """
    Base content model for all types of content
    
    Attributes:
        id: Unique identifier for the content
        content_type: Type of content (text, image, voice, etc.)
        created_at: When the content was created
        caption: Optional caption or description
        metadata: Additional metadata dictionary
    """
    id: str = field(default_factory=generate_unique_id)
    content_type: ContentType = ContentType.TEXT
    created_at: datetime = field(default_factory=datetime.now)
    caption: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert content to dictionary"""
        return {
            'id': self.id,
            'content_type': self.content_type.value,
            'created_at': format_datetime(self.created_at),
            'caption': self.caption,
            'metadata': self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Content':
        """Create content from dictionary"""
        from ..utils.helpers import parse_datetime
        
        return cls(
            id=data.get('id', generate_unique_id()),
            content_type=ContentType(data.get('content_type', ContentType.TEXT.value)),
            created_at=parse_datetime(data.get('created_at')) or datetime.now(),
            caption=data.get('caption'),
            metadata=data.get('metadata', {})
        )


@dataclass
class TextContent(Content):
    """
    Text-based content model
    
    Attributes:
        text: The actual text content
        source: Source of the text (e.g., Quran, Hadith, Dua)
        reference: Reference information (e.g., verse number, hadith source)
    """
    text: str = ""
    source: Optional[str] = None
    reference: Optional[str] = None
    content_type: ContentType = field(default=ContentType.TEXT, init=False)
    
    def __post_init__(self):
        """Post-initialization processing"""
        if not self.text:
            raise ValueError("Text content cannot be empty")
        
        # Add text-specific metadata
        self.metadata.update({
            'word_count': len(self.text.split()),
            'character_count': len(self.text),
            'has_arabic': self._has_arabic_text(),
            'source': self.source,
            'reference': self.reference
        })
    
    def _has_arabic_text(self) -> bool:
        """Check if text contains Arabic characters"""
        from ..utils.helpers import is_arabic_text
        return is_arabic_text(self.text)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        data = super().to_dict()
        data.update({
            'text': self.text,
            'source': self.source,
            'reference': self.reference
        })
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TextContent':
        """Create from dictionary"""
        base_content = super().from_dict(data)
        return cls(
            id=base_content.id,
            created_at=base_content.created_at,
            caption=base_content.caption,
            metadata=base_content.metadata,
            text=data.get('text', ''),
            source=data.get('source'),
            reference=data.get('reference')
        )


@dataclass
class MediaContent(Content):
    """
    Media-based content model for files (images, audio, etc.)
    
    Attributes:
        file_path: Path to the media file
        file_name: Original filename
        file_size: File size in bytes
        mime_type: MIME type of the file
        duration: Duration for audio/video files (in seconds)
        dimensions: Image dimensions (width, height)
    """
    file_path: Path = field(default_factory=lambda: Path())
    file_name: str = ""
    file_size: int = 0
    mime_type: Optional[str] = None
    duration: Optional[float] = None
    dimensions: Optional[tuple] = None
    
    def __post_init__(self):
        """Post-initialization processing"""
        if not self.file_path or not self.file_path.exists():
            raise ValueError(f"Media file does not exist: {self.file_path}")
        
        # Auto-detect content type from file extension if not set
        if self.content_type == ContentType.TEXT:
            self.content_type = self._detect_content_type()
        
        # Update file information
        if self.file_path.exists():
            self.file_size = self.file_path.stat().st_size
            if not self.file_name:
                self.file_name = self.file_path.name
        
        # Add media-specific metadata
        self.metadata.update({
            'file_name': self.file_name,
            'file_size': self.file_size,
            'file_size_formatted': self._format_file_size(),
            'mime_type': self.mime_type,
            'duration': self.duration,
            'dimensions': self.dimensions
        })
    
    def _detect_content_type(self) -> ContentType:
        """Detect content type from file extension"""
        from ..utils.constants import FILE_EXTENSIONS
        
        extension = self.file_path.suffix.lower()
        for content_type, extensions in FILE_EXTENSIONS.items():
            if extension in extensions:
                return content_type
        return ContentType.DOCUMENT
    
    def _format_file_size(self) -> str:
        """Format file size in human readable format"""
        from ..utils.helpers import format_file_size
        return format_file_size(self.file_size)
    
    def get_file_info(self) -> Dict[str, Any]:
        """Get comprehensive file information"""
        return {
            'path': str(self.file_path),
            'name': self.file_name,
            'size': self.file_size,
            'size_formatted': self._format_file_size(),
            'type': self.content_type.value,
            'mime_type': self.mime_type,
            'exists': self.file_path.exists(),
            'duration': self.duration,
            'dimensions': self.dimensions
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        data = super().to_dict()
        data.update({
            'file_path': str(self.file_path),
            'file_name': self.file_name,
            'file_size': self.file_size,
            'mime_type': self.mime_type,
            'duration': self.duration,
            'dimensions': self.dimensions
        })
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MediaContent':
        """Create from dictionary"""
        base_content = super().from_dict(data)
        return cls(
            id=base_content.id,
            content_type=base_content.content_type,
            created_at=base_content.created_at,
            caption=base_content.caption,
            metadata=base_content.metadata,
            file_path=Path(data.get('file_path', '')),
            file_name=data.get('file_name', ''),
            file_size=data.get('file_size', 0),
            mime_type=data.get('mime_type'),
            duration=data.get('duration'),
            dimensions=data.get('dimensions')
        )


@dataclass
class ContentCollection:
    """
    Collection of content items with management capabilities
    
    Attributes:
        name: Name of the collection
        description: Description of the collection
        items: List of content items
        created_at: When the collection was created
        last_used: When content from this collection was last used
        usage_count: How many times content from this collection was used
    """
    name: str
    description: str = ""
    items: list = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    last_used: Optional[datetime] = None
    usage_count: int = 0
    
    def add_content(self, content: Content) -> None:
        """Add content to collection"""
        if content not in self.items:
            self.items.append(content)
    
    def remove_content(self, content_id: str) -> bool:
        """Remove content by ID"""
        for i, item in enumerate(self.items):
            if item.id == content_id:
                del self.items[i]
                return True
        return False
    
    def get_content_by_id(self, content_id: str) -> Optional[Content]:
        """Get content by ID"""
        for item in self.items:
            if item.id == content_id:
                return item
        return None
    
    def get_random_content(self) -> Optional[Content]:
        """Get random content from collection"""
        from ..utils.helpers import get_random_item
        
        if self.items:
            content = get_random_item(self.items)
            if content:
                self.last_used = datetime.now()
                self.usage_count += 1
            return content
        return None
    
    def get_content_by_type(self, content_type: ContentType) -> list:
        """Get all content of specific type"""
        return [item for item in self.items if item.content_type == content_type]
    
    def get_stats(self) -> Dict[str, Any]:
        """Get collection statistics"""
        type_counts = {}
        for content_type in ContentType:
            type_counts[content_type.value] = len(self.get_content_by_type(content_type))
        
        return {
            'name': self.name,
            'total_items': len(self.items),
            'type_counts': type_counts,
            'usage_count': self.usage_count,
            'last_used': format_datetime(self.last_used) if self.last_used else None,
            'created_at': format_datetime(self.created_at)
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'name': self.name,
            'description': self.description,
            'items': [item.to_dict() for item in self.items],
            'created_at': format_datetime(self.created_at),
            'last_used': format_datetime(self.last_used) if self.last_used else None,
            'usage_count': self.usage_count
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ContentCollection':
        """Create from dictionary"""
        from ..utils.helpers import parse_datetime
        
        collection = cls(
            name=data.get('name', ''),
            description=data.get('description', ''),
            created_at=parse_datetime(data.get('created_at')) or datetime.now(),
            last_used=parse_datetime(data.get('last_used')),
            usage_count=data.get('usage_count', 0)
        )
        
        # Load items
        for item_data in data.get('items', []):
            content_type = ContentType(item_data.get('content_type', ContentType.TEXT.value))
            if content_type == ContentType.TEXT:
                content = TextContent.from_dict(item_data)
            else:
                content = MediaContent.from_dict(item_data)
            collection.add_content(content)
        
        return collection