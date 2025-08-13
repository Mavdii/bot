"""
Constants and enums for the Azkar Bot

This module contains all constant values used throughout the application.
"""

from enum import Enum
from typing import Dict, List


class ContentType(Enum):
    """Content types supported by the bot"""
    TEXT = "text"
    IMAGE = "image"
    VOICE = "voice"
    AUDIO = "audio"
    DOCUMENT = "document"


class ScheduleType(Enum):
    """Types of scheduled content"""
    RANDOM = "random"
    MORNING = "morning"
    EVENING = "evening"
    PRAYER = "prayer"


class AdminAction(Enum):
    """Admin panel actions"""
    WAITING_FOR_TEXT = "waiting_for_text"
    WAITING_FOR_IMAGE = "waiting_for_image"
    WAITING_FOR_VOICE = "waiting_for_voice"
    WAITING_FOR_AUDIO = "waiting_for_audio"
    WAITING_FOR_DOCUMENT = "waiting_for_document"
    WAITING_FOR_CAPTION = "waiting_for_caption"


# File extensions mapping
FILE_EXTENSIONS: Dict[ContentType, List[str]] = {
    ContentType.IMAGE: ['.jpg', '.jpeg', '.png', '.gif', '.webp'],
    ContentType.VOICE: ['.ogg', '.mp3', '.wav'],
    ContentType.AUDIO: ['.mp3', '.mp4', '.wav', '.m4a', '.aac'],
    ContentType.DOCUMENT: ['.pdf', '.doc', '.docx', '.txt']
}

# MIME types mapping
MIME_TYPES: Dict[str, ContentType] = {
    'image/jpeg': ContentType.IMAGE,
    'image/png': ContentType.IMAGE,
    'image/gif': ContentType.IMAGE,
    'image/webp': ContentType.IMAGE,
    'audio/ogg': ContentType.VOICE,
    'audio/mpeg': ContentType.AUDIO,
    'audio/mp4': ContentType.AUDIO,
    'audio/wav': ContentType.AUDIO,
    'application/pdf': ContentType.DOCUMENT,
    'text/plain': ContentType.DOCUMENT,
}

# Bot messages in Arabic
MESSAGES = {
    'welcome_group': """
🕌 **أهلاً وسهلاً بكم في بوت الأذكار الإسلامية** 🕌

سيقوم البوت بإرسال:
📿 أذكار عشوائية كل 5 دقائق
🌅 أذكار الصباح في أوقات مختلفة
🌇 أذكار المساء في أوقات مختلفة
🕌 تذكير بأوقات الصلاة

📢 للمزيد من التلاوات: {channel_link}

بارك الله فيكم جميعاً 🤲
""",
    
    'start_private': """
🕌 **بوت الأذكار الإسلامية** 🕌

مرحباً بك! هذا البوت مخصص لإرسال الأذكار والتذكيرات الإسلامية للمجموعات.

لاستخدام البوت:
1️⃣ أضف البوت إلى مجموعتك
2️⃣ امنحه صلاحية إرسال الرسائل
3️⃣ سيبدأ البوت تلقائياً بإرسال الأذكار

📢 قناة التلاوات: {channel_link}

جعله الله في ميزان حسناتكم 🤲
""",
    
    'admin_panel': """
🔧 **لوحة تحكم المطور** 🔧

اختر الإجراء المطلوب:
""",
    
    'stats_template': """
📊 **إحصائيات البوت:**

👥 **المجموعات النشطة:** {groups_count}
📝 **النصوص:** {texts_count}
🖼️ **الصور:** {images_count}
🎙️ **الرسائل الصوتية:** {voices_count}
🎵 **الملفات الصوتية:** {audios_count}

⏰ **آخر تحديث:** {last_update}
""",
    
    'content_info_template': """
📋 **المحتوى المحفوظ:**

📝 **النصوص:** {texts_count}

📁 **الملفات:**
🖼️ **الصور العشوائية:** {images_count}
🎙️ **الرسائل الصوتية:** {voices_count}
🎵 **الملفات الصوتية:** {audios_count}
🌅 **صور الصباح:** {morning_count}
🌇 **صور المساء:** {evening_count}
🕌 **صور الصلاة:** {prayers_count}

📊 **إجمالي الملفات:** {total_files}
""",
    
    'file_uploaded': "✅ تم حفظ الملف بنجاح!\n📁 {filename}\n📝 {caption}",
    'text_added': "✅ تم إضافة النص بنجاح!",
    'error_file_upload': "❌ خطأ في حفظ الملف: {error}",
    'error_invalid_text': "❌ يرجى كتابة نص صحيح",
    'unauthorized': "❌ غير مخول لك!",
    'admin_panel_closed': "✅ تم إغلاق لوحة التحكم",
}

# Inline keyboard layouts
ADMIN_KEYBOARD = {
    "inline_keyboard": [
        [
            {"text": "📝 إضافة نص جديد", "callback_data": "admin_add_text"},
            {"text": "🖼️ إضافة صورة", "callback_data": "admin_add_image"}
        ],
        [
            {"text": "🎙️ إضافة رسالة صوتية", "callback_data": "admin_add_voice"},
            {"text": "🎵 إضافة ملف صوتي", "callback_data": "admin_add_audio"}
        ],
        [
            {"text": "📄 إضافة مستند", "callback_data": "admin_add_document"},
            {"text": "📊 إحصائيات البوت", "callback_data": "admin_stats"}
        ],
        [
            {"text": "📋 عرض المحتوى المحفوظ", "callback_data": "admin_view_content"},
            {"text": "❌ إغلاق", "callback_data": "admin_close"}
        ]
    ]
}

BACK_KEYBOARD = {
    "inline_keyboard": [[
        {"text": "🔙 العودة للقائمة", "callback_data": "admin_back"}
    ]]
}

SKIP_CAPTION_KEYBOARD = {
    "inline_keyboard": [[
        {"text": "تخطي الوصف", "callback_data": "skip_caption"}
    ]]
}

# Default content
DEFAULT_AZKAR = [
    "سبحان الله وبحمده، سبحان الله العظيم",
    "لا إله إلا الله وحده لا شريك له، له الملك وله الحمد وهو على كل شيء قدير",
    "اللهم صل وسلم على نبينا محمد",
    "أستغفر الله العظيم الذي لا إله إلا هو الحي القيوم وأتوب إليه",
    "الحمد لله رب العالمين",
]

# Prayer names in Arabic
PRAYER_NAMES = {
    'fajr': 'الفجر',
    'dhuhr': 'الظهر', 
    'asr': 'العصر',
    'maghrib': 'المغرب',
    'isha': 'العشاء'
}

# Time format
TIME_FORMAT = "%H:%M"
DATE_FORMAT = "%Y-%m-%d"
DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"

# API limits
MAX_MESSAGE_LENGTH = 4096
MAX_CAPTION_LENGTH = 1024
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB

# Retry settings
MAX_RETRIES = 3
RETRY_DELAY = 1.0  # seconds

# Content rotation settings
CONTENT_ROTATION_CYCLE = 4  # text, image, voice, audio