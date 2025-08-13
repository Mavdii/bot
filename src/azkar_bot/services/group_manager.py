"""
Group management service for the Azkar Bot

This service handles all group-related operations including:
- Group registration and persistence
- Group settings management
- Group statistics tracking
- Group activity monitoring
"""

from pathlib import Path
from typing import Dict, List, Optional, Set
from datetime import datetime, timedelta

from ..models.group import Group, GroupCollection, GroupType, GroupStatus, GroupSettings
from ..utils.logger import LoggerMixin
from ..utils.helpers import safe_json_load, safe_json_save, format_datetime


class GroupManager(LoggerMixin):
    """
    Manages all group operations for the bot
    
    This service provides functionality for:
    - Group registration and persistence
    - Group settings and preferences
    - Activity tracking and statistics
    - Group validation and cleanup
    """
    
    def __init__(self, groups_file: Path):
        """
        Initialize group manager
        
        Args:
            groups_file: Path to groups persistence file
        """
        self.groups_file = Path(groups_file)
        self.groups = GroupCollection()
        
        # Ensure groups file directory exists
        self.groups_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Load existing groups
        self._load_groups()
        
        self.log_info(f"👥 تم تهيئة مدير المجموعات - Group manager initialized with {len(self.groups.groups)} groups")
    
    def _load_groups(self) -> None:
        """Load groups from persistence file"""
        try:
            if self.groups_file.exists():
                data = safe_json_load(self.groups_file, {})
                if data:
                    self.groups = GroupCollection.from_dict(data)
                    self.log_info(f"📂 تم تحميل {len(self.groups.groups)} مجموعة - Loaded {len(self.groups.groups)} groups from file")
                else:
                    self.log_info("📂 ملف المجموعات فارغ - Groups file is empty, starting fresh")
            else:
                self.log_info("📂 لا يوجد ملف مجموعات، بدء جديد - No groups file found, starting fresh")
                
        except Exception as e:
            self.log_error("❌ خطأ في تحميل المجموعات - Error loading groups from file", e)
            # Start with empty collection on error
            self.groups = GroupCollection()
    
    def _save_groups(self) -> bool:
        """
        Save groups to persistence file
        
        Returns:
            True if saved successfully, False otherwise
        """
        try:
            data = self.groups.to_dict()
            if safe_json_save(data, self.groups_file):
                self.log_debug(f"💾 تم حفظ {len(self.groups.groups)} مجموعة - Saved {len(self.groups.groups)} groups to file")
                return True
            else:
                self.log_error("❌ فشل في حفظ المجموعات - Failed to save groups to file")
                return False
                
        except Exception as e:
            self.log_error("❌ خطأ في حفظ المجموعات - Error saving groups to file", e)
            return False
    
    def add_group(self, group_id: int, title: str = None, username: str = None, 
                  group_type: GroupType = GroupType.GROUP) -> Group:
        """
        Add or update a group
        
        Args:
            group_id: Telegram group ID
            title: Group title
            username: Group username
            group_type: Type of group
            
        Returns:
            Group object
        """
        existing_group = self.groups.get_group(group_id)
        
        if existing_group:
            # Update existing group
            existing_group.update_info(title, username, group_type)
            if existing_group.status != GroupStatus.ACTIVE:
                existing_group.activate()
            
            self.log_info(f"🔄 تم تحديث المجموعة - Updated group: {existing_group.get_display_name()}")
            group = existing_group
        else:
            # Create new group
            group = Group(
                id=group_id,
                title=title or f"Group {group_id}",
                username=username,
                group_type=group_type
            )
            
            self.groups.add_group(group)
            self.log_info(f"➕ تم إضافة مجموعة جديدة - Added new group: {group.get_display_name()}")
        
        # Save changes
        self._save_groups()
        return group
    
    def remove_group(self, group_id: int) -> bool:
        """
        Remove a group
        
        Args:
            group_id: Telegram group ID
            
        Returns:
            True if removed, False if not found
        """
        group = self.groups.get_group(group_id)
        if group:
            group.mark_left()
            self.log_info(f"➖ تم وضع علامة مغادرة للمجموعة - Marked group as left: {group.get_display_name()}")
            self._save_groups()
            return True
        
        return False
    
    def get_group(self, group_id: int) -> Optional[Group]:
        """
        Get group by ID
        
        Args:
            group_id: Telegram group ID
            
        Returns:
            Group object or None if not found
        """
        return self.groups.get_group(group_id)
    
    def get_active_groups(self) -> Dict[int, Group]:
        """
        Get all active groups
        
        Returns:
            Dictionary of active groups
        """
        return self.groups.get_active_groups()
    
    def get_active_group_ids(self) -> Set[int]:
        """
        Get set of active group IDs
        
        Returns:
            Set of active group IDs
        """
        return set(self.get_active_groups().keys())
    
    def activate_group(self, group_id: int) -> bool:
        """
        Activate a group
        
        Args:
            group_id: Telegram group ID
            
        Returns:
            True if activated, False if not found
        """
        group = self.groups.get_group(group_id)
        if group:
            group.activate()
            self.log_info(f"✅ تم تفعيل المجموعة - Activated group: {group.get_display_name()}")
            self._save_groups()
            return True
        
        return False
    
    def deactivate_group(self, group_id: int) -> bool:
        """
        Deactivate a group
        
        Args:
            group_id: Telegram group ID
            
        Returns:
            True if deactivated, False if not found
        """
        group = self.groups.get_group(group_id)
        if group:
            group.deactivate()
            self.log_info(f"⏸️ تم إلغاء تفعيل المجموعة - Deactivated group: {group.get_display_name()}")
            self._save_groups()
            return True
        
        return False
    
    def block_group(self, group_id: int) -> bool:
        """
        Block a group
        
        Args:
            group_id: Telegram group ID
            
        Returns:
            True if blocked, False if not found
        """
        group = self.groups.get_group(group_id)
        if group:
            group.block()
            self.log_info(f"🚫 تم حظر المجموعة - Blocked group: {group.get_display_name()}")
            self._save_groups()
            return True
        
        return False
    
    def update_group_activity(self, group_id: int) -> bool:
        """
        Update group activity timestamp
        
        Args:
            group_id: Telegram group ID
            
        Returns:
            True if updated, False if not found
        """
        group = self.groups.get_group(group_id)
        if group:
            group.update_activity()
            # Don't save on every activity update to avoid excessive I/O
            return True
        
        return False
    
    def increment_group_messages(self, group_id: int, is_azkar: bool = False, 
                               is_media: bool = False) -> bool:
        """
        Increment message count for a group
        
        Args:
            group_id: Telegram group ID
            is_azkar: Whether the message was azkar content
            is_media: Whether the message was media content
            
        Returns:
            True if updated, False if not found
        """
        group = self.groups.get_group(group_id)
        if group:
            if is_azkar:
                group.statistics.increment_azkar()
            elif is_media:
                group.statistics.increment_media()
            else:
                group.statistics.increment_messages()
            
            group.update_activity()
            return True
        
        return False
    
    def increment_group_errors(self, group_id: int) -> bool:
        """
        Increment error count for a group
        
        Args:
            group_id: Telegram group ID
            
        Returns:
            True if updated, False if not found
        """
        group = self.groups.get_group(group_id)
        if group:
            group.statistics.increment_errors()
            return True
        
        return False
    
    def update_group_settings(self, group_id: int, settings: Dict[str, any]) -> bool:
        """
        Update group settings
        
        Args:
            group_id: Telegram group ID
            settings: Settings dictionary
            
        Returns:
            True if updated, False if not found
        """
        group = self.groups.get_group(group_id)
        if group:
            # Update individual settings
            for key, value in settings.items():
                if hasattr(group.settings, key):
                    setattr(group.settings, key, value)
            
            group.update_activity()
            self._save_groups()
            self.log_info(f"⚙️ تم تحديث إعدادات المجموعة - Updated settings for group: {group.get_display_name()}")
            return True
        
        return False
    
    def get_group_settings(self, group_id: int) -> Optional[GroupSettings]:
        """
        Get group settings
        
        Args:
            group_id: Telegram group ID
            
        Returns:
            GroupSettings object or None if not found
        """
        group = self.groups.get_group(group_id)
        return group.settings if group else None
    
    def add_group_admin(self, group_id: int, user_id: int) -> bool:
        """
        Add admin to group
        
        Args:
            group_id: Telegram group ID
            user_id: User ID to add as admin
            
        Returns:
            True if added, False if not found
        """
        group = self.groups.get_group(group_id)
        if group:
            group.add_admin(user_id)
            self._save_groups()
            self.log_info(f"👑 تم إضافة مشرف للمجموعة - Added admin {user_id} to group: {group.get_display_name()}")
            return True
        
        return False
    
    def remove_group_admin(self, group_id: int, user_id: int) -> bool:
        """
        Remove admin from group
        
        Args:
            group_id: Telegram group ID
            user_id: User ID to remove as admin
            
        Returns:
            True if removed, False if not found
        """
        group = self.groups.get_group(group_id)
        if group:
            group.remove_admin(user_id)
            self._save_groups()
            self.log_info(f"👑 تم حذف مشرف من المجموعة - Removed admin {user_id} from group: {group.get_display_name()}")
            return True
        
        return False
    
    def is_group_admin(self, group_id: int, user_id: int) -> bool:
        """
        Check if user is admin in group
        
        Args:
            group_id: Telegram group ID
            user_id: User ID to check
            
        Returns:
            True if user is admin, False otherwise
        """
        group = self.groups.get_group(group_id)
        return group.is_admin(user_id) if group else False
    
    def get_groups_stats(self) -> Dict[str, any]:
        """
        Get comprehensive groups statistics
        
        Returns:
            Dictionary with statistics
        """
        return self.groups.get_stats()
    
    def get_inactive_groups(self, days: int = 30) -> List[Group]:
        """
        Get groups that have been inactive for specified days
        
        Args:
            days: Number of days to consider as inactive
            
        Returns:
            List of inactive groups
        """
        cutoff_date = datetime.now() - timedelta(days=days)
        inactive_groups = []
        
        for group in self.groups.groups.values():
            if (group.last_activity and 
                group.last_activity < cutoff_date and 
                group.is_active()):
                inactive_groups.append(group)
        
        return inactive_groups
    
    def cleanup_inactive_groups(self, days: int = 90) -> int:
        """
        Mark very old inactive groups as left
        
        Args:
            days: Number of days after which to mark as left
            
        Returns:
            Number of groups cleaned up
        """
        cutoff_date = datetime.now() - timedelta(days=days)
        cleaned_count = 0
        
        for group in self.groups.groups.values():
            if (group.last_activity and 
                group.last_activity < cutoff_date and 
                group.status == GroupStatus.ACTIVE):
                
                group.mark_left()
                cleaned_count += 1
                self.log_info(f"🧹 تم وضع علامة مغادرة للمجموعة غير النشطة - Marked inactive group as left: {group.get_display_name()}")
        
        if cleaned_count > 0:
            self._save_groups()
            self.log_info(f"🧹 تم تنظيف {cleaned_count} مجموعة غير نشطة - Cleaned up {cleaned_count} inactive groups")
        
        return cleaned_count
    
    def export_groups_data(self, export_path: Path = None) -> Path:
        """
        Export groups data to JSON file
        
        Args:
            export_path: Optional custom export path
            
        Returns:
            Path to exported file
        """
        if not export_path:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            export_path = self.groups_file.parent / f"groups_export_{timestamp}.json"
        
        try:
            data = self.groups.to_dict()
            if safe_json_save(data, export_path):
                self.log_info(f"📤 تم تصدير بيانات المجموعات - Exported groups data to: {export_path}")
                return export_path
            else:
                raise Exception("Failed to save export file")
                
        except Exception as e:
            self.log_error(f"❌ خطأ في تصدير بيانات المجموعات - Error exporting groups data", e)
            raise
    
    def import_groups_data(self, import_path: Path, merge: bool = True) -> int:
        """
        Import groups data from JSON file
        
        Args:
            import_path: Path to import file
            merge: Whether to merge with existing data or replace
            
        Returns:
            Number of groups imported
        """
        try:
            data = safe_json_load(import_path)
            if not data:
                raise Exception("Invalid or empty import file")
            
            imported_collection = GroupCollection.from_dict(data)
            
            if merge:
                # Merge with existing groups
                imported_count = 0
                for group_id, group in imported_collection.groups.items():
                    existing_group = self.groups.get_group(group_id)
                    if existing_group:
                        # Update existing group with imported data
                        existing_group.update_info(group.title, group.username, group.group_type)
                        existing_group.settings = group.settings
                        existing_group.statistics = group.statistics
                        existing_group.admins = group.admins
                        existing_group.metadata = group.metadata
                    else:
                        # Add new group
                        self.groups.add_group(group)
                    imported_count += 1
            else:
                # Replace existing groups
                self.groups = imported_collection
                imported_count = len(imported_collection.groups)
            
            self._save_groups()
            self.log_info(f"📥 تم استيراد {imported_count} مجموعة - Imported {imported_count} groups from: {import_path}")
            return imported_count
            
        except Exception as e:
            self.log_error(f"❌ خطأ في استيراد بيانات المجموعات - Error importing groups data from {import_path}", e)
            raise
    
    def validate_groups_data(self) -> Dict[str, List[str]]:
        """
        Validate groups data and return issues found
        
        Returns:
            Dictionary with validation issues
        """
        issues = {
            'duplicate_ids': [],
            'invalid_data': [],
            'missing_info': []
        }
        
        seen_ids = set()
        
        for group_id, group in self.groups.groups.items():
            # Check for duplicate IDs (shouldn't happen but good to check)
            if group_id in seen_ids:
                issues['duplicate_ids'].append(str(group_id))
            seen_ids.add(group_id)
            
            # Check for missing essential info
            if not group.title:
                issues['missing_info'].append(f"Group {group_id}: missing title")
            
            # Check for invalid data
            if group.statistics.messages_sent < 0:
                issues['invalid_data'].append(f"Group {group_id}: negative message count")
            
            if group.statistics.errors_count < 0:
                issues['invalid_data'].append(f"Group {group_id}: negative error count")
        
        return issues
    
    def force_save(self) -> bool:
        """
        Force save groups data (useful for periodic saves)
        
        Returns:
            True if saved successfully, False otherwise
        """
        return self._save_groups()