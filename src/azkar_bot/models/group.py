"""
Group data models for the Azkar Bot

This module defines data structures for managing Telegram groups
and their associated settings and statistics.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict, Any, Set
from enum import Enum

from ..utils.helpers import format_datetime, parse_datetime


class GroupType(Enum):
    """Types of Telegram groups"""
    GROUP = "group"
    SUPERGROUP = "supergroup"
    CHANNEL = "channel"


class GroupStatus(Enum):
    """Status of group in the bot"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    BLOCKED = "blocked"
    LEFT = "left"


@dataclass
class GroupSettings:
    """
    Settings for a specific group
    
    Attributes:
        enable_random_azkar: Whether to send random azkar
        enable_morning_azkar: Whether to send morning azkar
        enable_evening_azkar: Whether to send evening azkar
        enable_prayer_reminders: Whether to send prayer reminders
        custom_schedule: Custom schedule settings
        language: Preferred language for messages
        timezone: Group's timezone
    """
    enable_random_azkar: bool = True
    enable_morning_azkar: bool = True
    enable_evening_azkar: bool = True
    enable_prayer_reminders: bool = True
    custom_schedule: Dict[str, Any] = field(default_factory=dict)
    language: str = "ar"  # Arabic by default
    timezone: str = "Africa/Cairo"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert settings to dictionary"""
        return {
            'enable_random_azkar': self.enable_random_azkar,
            'enable_morning_azkar': self.enable_morning_azkar,
            'enable_evening_azkar': self.enable_evening_azkar,
            'enable_prayer_reminders': self.enable_prayer_reminders,
            'custom_schedule': self.custom_schedule,
            'language': self.language,
            'timezone': self.timezone
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'GroupSettings':
        """Create settings from dictionary"""
        return cls(
            enable_random_azkar=data.get('enable_random_azkar', True),
            enable_morning_azkar=data.get('enable_morning_azkar', True),
            enable_evening_azkar=data.get('enable_evening_azkar', True),
            enable_prayer_reminders=data.get('enable_prayer_reminders', True),
            custom_schedule=data.get('custom_schedule', {}),
            language=data.get('language', 'ar'),
            timezone=data.get('timezone', 'Africa/Cairo')
        )


@dataclass
class GroupStatistics:
    """
    Statistics for a group
    
    Attributes:
        messages_sent: Total messages sent to this group
        last_message_sent: When the last message was sent
        azkar_sent: Number of azkar messages sent
        media_sent: Number of media files sent
        errors_count: Number of errors encountered
        member_count: Approximate member count (if available)
    """
    messages_sent: int = 0
    last_message_sent: Optional[datetime] = None
    azkar_sent: int = 0
    media_sent: int = 0
    errors_count: int = 0
    member_count: Optional[int] = None
    
    def increment_messages(self) -> None:
        """Increment message count and update timestamp"""
        self.messages_sent += 1
        self.last_message_sent = datetime.now()
    
    def increment_azkar(self) -> None:
        """Increment azkar count"""
        self.azkar_sent += 1
        self.increment_messages()
    
    def increment_media(self) -> None:
        """Increment media count"""
        self.media_sent += 1
        self.increment_messages()
    
    def increment_errors(self) -> None:
        """Increment error count"""
        self.errors_count += 1
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert statistics to dictionary"""
        return {
            'messages_sent': self.messages_sent,
            'last_message_sent': format_datetime(self.last_message_sent) if self.last_message_sent else None,
            'azkar_sent': self.azkar_sent,
            'media_sent': self.media_sent,
            'errors_count': self.errors_count,
            'member_count': self.member_count
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'GroupStatistics':
        """Create statistics from dictionary"""
        return cls(
            messages_sent=data.get('messages_sent', 0),
            last_message_sent=parse_datetime(data.get('last_message_sent')),
            azkar_sent=data.get('azkar_sent', 0),
            media_sent=data.get('media_sent', 0),
            errors_count=data.get('errors_count', 0),
            member_count=data.get('member_count')
        )


@dataclass
class Group:
    """
    Telegram group model
    
    Attributes:
        id: Telegram group ID
        title: Group title/name
        username: Group username (if any)
        group_type: Type of group (group, supergroup, channel)
        status: Current status in the bot
        added_at: When the group was added to the bot
        last_activity: Last activity timestamp
        settings: Group-specific settings
        statistics: Group statistics
        admins: Set of admin user IDs
        metadata: Additional metadata
    """
    id: int
    title: str = ""
    username: Optional[str] = None
    group_type: GroupType = GroupType.GROUP
    status: GroupStatus = GroupStatus.ACTIVE
    added_at: datetime = field(default_factory=datetime.now)
    last_activity: Optional[datetime] = None
    settings: GroupSettings = field(default_factory=GroupSettings)
    statistics: GroupStatistics = field(default_factory=GroupStatistics)
    admins: Set[int] = field(default_factory=set)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Post-initialization processing"""
        if not self.title:
            self.title = f"Group {self.id}"
        
        # Update last activity
        self.update_activity()
    
    def update_activity(self) -> None:
        """Update last activity timestamp"""
        self.last_activity = datetime.now()
    
    def is_active(self) -> bool:
        """Check if group is active"""
        return self.status == GroupStatus.ACTIVE
    
    def activate(self) -> None:
        """Activate the group"""
        self.status = GroupStatus.ACTIVE
        self.update_activity()
    
    def deactivate(self) -> None:
        """Deactivate the group"""
        self.status = GroupStatus.INACTIVE
        self.update_activity()
    
    def block(self) -> None:
        """Block the group"""
        self.status = GroupStatus.BLOCKED
        self.update_activity()
    
    def mark_left(self) -> None:
        """Mark as left the group"""
        self.status = GroupStatus.LEFT
        self.update_activity()
    
    def add_admin(self, user_id: int) -> None:
        """Add admin to the group"""
        self.admins.add(user_id)
    
    def remove_admin(self, user_id: int) -> None:
        """Remove admin from the group"""
        self.admins.discard(user_id)
    
    def is_admin(self, user_id: int) -> bool:
        """Check if user is admin"""
        return user_id in self.admins
    
    def update_info(self, title: str = None, username: str = None, 
                   group_type: GroupType = None) -> None:
        """Update group information"""
        if title:
            self.title = title
        if username is not None:  # Allow setting to None
            self.username = username
        if group_type:
            self.group_type = group_type
        self.update_activity()
    
    def get_display_name(self) -> str:
        """Get display name for the group"""
        if self.username:
            return f"@{self.username}"
        return self.title or f"Group {self.id}"
    
    def get_summary(self) -> Dict[str, Any]:
        """Get group summary information"""
        return {
            'id': self.id,
            'display_name': self.get_display_name(),
            'title': self.title,
            'username': self.username,
            'type': self.group_type.value,
            'status': self.status.value,
            'is_active': self.is_active(),
            'added_at': format_datetime(self.added_at),
            'last_activity': format_datetime(self.last_activity) if self.last_activity else None,
            'messages_sent': self.statistics.messages_sent,
            'member_count': self.statistics.member_count,
            'admin_count': len(self.admins)
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert group to dictionary"""
        return {
            'id': self.id,
            'title': self.title,
            'username': self.username,
            'group_type': self.group_type.value,
            'status': self.status.value,
            'added_at': format_datetime(self.added_at),
            'last_activity': format_datetime(self.last_activity) if self.last_activity else None,
            'settings': self.settings.to_dict(),
            'statistics': self.statistics.to_dict(),
            'admins': list(self.admins),
            'metadata': self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Group':
        """Create group from dictionary"""
        group = cls(
            id=data['id'],
            title=data.get('title', ''),
            username=data.get('username'),
            group_type=GroupType(data.get('group_type', GroupType.GROUP.value)),
            status=GroupStatus(data.get('status', GroupStatus.ACTIVE.value)),
            added_at=parse_datetime(data.get('added_at')) or datetime.now(),
            last_activity=parse_datetime(data.get('last_activity')),
            settings=GroupSettings.from_dict(data.get('settings', {})),
            statistics=GroupStatistics.from_dict(data.get('statistics', {})),
            admins=set(data.get('admins', [])),
            metadata=data.get('metadata', {})
        )
        return group


@dataclass
class GroupCollection:
    """
    Collection of groups with management capabilities
    
    Attributes:
        groups: Dictionary of group ID to Group objects
        last_updated: When the collection was last updated
    """
    groups: Dict[int, Group] = field(default_factory=dict)
    last_updated: datetime = field(default_factory=datetime.now)
    
    def add_group(self, group: Group) -> None:
        """Add group to collection"""
        self.groups[group.id] = group
        self.last_updated = datetime.now()
    
    def remove_group(self, group_id: int) -> bool:
        """Remove group from collection"""
        if group_id in self.groups:
            del self.groups[group_id]
            self.last_updated = datetime.now()
            return True
        return False
    
    def get_group(self, group_id: int) -> Optional[Group]:
        """Get group by ID"""
        return self.groups.get(group_id)
    
    def get_active_groups(self) -> Dict[int, Group]:
        """Get all active groups"""
        return {gid: group for gid, group in self.groups.items() if group.is_active()}
    
    def get_groups_by_status(self, status: GroupStatus) -> Dict[int, Group]:
        """Get groups by status"""
        return {gid: group for gid, group in self.groups.items() if group.status == status}
    
    def get_stats(self) -> Dict[str, Any]:
        """Get collection statistics"""
        active_count = len(self.get_active_groups())
        total_messages = sum(group.statistics.messages_sent for group in self.groups.values())
        total_members = sum(group.statistics.member_count or 0 for group in self.groups.values())
        
        status_counts = {}
        for status in GroupStatus:
            status_counts[status.value] = len(self.get_groups_by_status(status))
        
        return {
            'total_groups': len(self.groups),
            'active_groups': active_count,
            'status_counts': status_counts,
            'total_messages_sent': total_messages,
            'total_members': total_members,
            'last_updated': format_datetime(self.last_updated)
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert collection to dictionary"""
        return {
            'groups': {str(gid): group.to_dict() for gid, group in self.groups.items()},
            'last_updated': format_datetime(self.last_updated)
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'GroupCollection':
        """Create collection from dictionary"""
        collection = cls(
            last_updated=parse_datetime(data.get('last_updated')) or datetime.now()
        )
        
        for gid_str, group_data in data.get('groups', {}).items():
            group = Group.from_dict(group_data)
            collection.add_group(group)
        
        return collection