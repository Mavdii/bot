import os
import random
import asyncio
import logging
from datetime import datetime, timedelta
import pytz
import requests
import json
import aiohttp
from apscheduler.schedulers.asyncio import AsyncIOScheduler
import shutil

# إعداد نظام السجلات
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

class AzkarBot:
    def __init__(self):
        self.bot_token = 
        self.base_url = f"https://api.telegram.org/bot{self.bot_token}"
        self.admin_id = 
        
        self.scheduler = AsyncIOScheduler()
        self.cairo_tz = pytz.timezone('Africa/Cairo')
        self.active_groups = set()
        self.last_message_ids = {}
        self.content_turn = 0  # 0=text, 1=image, 2=voice, 3=audio
        self.offset = 0
        self.session = None
        
        # ملف حفظ المجموعات
        self.groups_file = 'active_groups.json'
        
        # رابط القناة
        self.channel_link = "https://t.me/Telawat_Quran_0"
        
        # إدارة حالات الـ admin
        self.admin_states = {}  # {user_id: {'action': 'waiting_for_caption', 'file_path': '...', 'file_type': '...'}}
        
        # إنشاء المجلدات المطلوبة وتحميل المجموعات المحفوظة
        self.ensure_directories()
        self.load_active_groups()
        
    def ensure_directories(self):
        """إنشاء المجلدات المطلوبة"""
        directories = ['random', 'morning', 'evening', 'prayers', 'voices', 'audios']
        for directory in directories:
            if not os.path.exists(directory):
                os.makedirs(directory)
                logger.info(f"تم إنشاء مجلد: {directory}")

    def save_active_groups(self):
        """حفظ المجموعات النشطة في ملف"""
        try:
            groups_data = {
                'groups': list(self.active_groups),
                'last_updated': datetime.now().isoformat()
            }
            with open(self.groups_file, 'w', encoding='utf-8') as f:
                json.dump(groups_data, f, ensure_ascii=False, indent=2)
            logger.info(f"تم حفظ {len(self.active_groups)} مجموعة نشطة")
        except Exception as e:
            logger.error(f"خطأ في حفظ المجموعات: {e}")

    def load_active_groups(self):
        """تحميل المجموعات النشطة من الملف"""
        try:
            if os.path.exists(self.groups_file):
                with open(self.groups_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    saved_groups = data.get('groups', [])
                    self.active_groups = set(saved_groups)
                    logger.info(f"تم تحميل {len(self.active_groups)} مجموعة نشطة من الملف المحفوظ")
                    if self.active_groups:
                        logger.info(f"المجموعات النشطة: {list(self.active_groups)}")
            else:
                logger.info("لا يوجد ملف مجموعات محفوظ، سيتم إنشاؤه عند إضافة مجموعات جديدة")
        except Exception as e:
            logger.error(f"خطأ في تحميل المجموعات المحفوظة: {e}")
            self.active_groups = set()

    async def start_bot(self):
        """تشغيل البوت"""
        logger.info("🚀 بدء تشغيل بوت الأذكار الإسلامية...")
        
        try:
            self.session = aiohttp.ClientSession()
            
            # إعداد الجدولة
            self.setup_scheduler()
            self.scheduler.start()
            
            logger.info(f"✅ البوت يعمل الآن مع {len(self.active_groups)} مجموعة نشطة")
            if self.active_groups:
                logger.info("📋 المجموعات المُفعلة:")
                for group_id in self.active_groups:
                    logger.info(f"   • {group_id}")
            else:
                logger.info("⚠️  لا توجد مجموعات مُفعلة حالياً، في انتظار إضافة البوت للمجموعات")
            
            logger.info("🔄 بدء معالجة الرسائل والتحديثات...")
            
            # بدء معالجة الرسائل
            await self.process_updates()
            
        except Exception as e:
            logger.error(f"❌ خطأ في تشغيل البوت: {e}")
        finally:
            if self.session:
                await self.session.close()
                logger.info("🛑 تم إغلاق جلسة البوت")

    def setup_scheduler(self):
        """إعداد جدولة المهام"""
        # أذكار عشوائية كل 5 دقائق - تبدأ فوراً
        self.scheduler.add_job(
            self.send_random_content,
            'interval',
            minutes=5,
            timezone=self.cairo_tz
        )
        
        # إرسال المحتوى الأول فوراً بعد 30 ثانية من التشغيل
        self.scheduler.add_job(
            self.send_random_content,
            'date',
            run_date=datetime.now(self.cairo_tz) + timedelta(seconds=30),
            timezone=self.cairo_tz,
            id='first_content_send'
        )
        
        # إرسال المحتوى الثاني بعد دقيقتين للتأكد من أن النظام يعمل
        self.scheduler.add_job(
            self.send_random_content,
            'date',
            run_date=datetime.now(self.cairo_tz) + timedelta(minutes=2),
            timezone=self.cairo_tz,
            id='second_content_send'
        )
        
        # أذكار الصباح - 5:30, 7:00, 8:00
        for hour, minute in [(5, 30), (7, 0), (8, 0)]:
            self.scheduler.add_job(
                self.send_morning_azkar,
                'cron',
                hour=hour,
                minute=minute,
                timezone=self.cairo_tz
            )
        
        # أذكار المساء - 6:00, 7:00, 8:00 مساءً
        for hour in [18, 19, 20]:
            self.scheduler.add_job(
                self.send_evening_azkar,
                'cron',
                hour=hour,
                minute=0,
                timezone=self.cairo_tz
            )
        
        # جدولة تنبيهات الصلاة يومياً
        self.scheduler.add_job(
            self.schedule_prayer_notifications,
            'cron',
            hour=0,
            minute=0,
            timezone=self.cairo_tz
        )
        
        # تشغيل جدولة الصلاة للمرة الأولى
        self.scheduler.add_job(
            self.schedule_prayer_notifications,
            'date',
            run_date=datetime.now(self.cairo_tz) + timedelta(seconds=10)
        )

    async def process_updates(self):
        """معالجة التحديثات من التيليجرام"""
        error_count = 0
        while True:
            try:
                url = f"{self.base_url}/getUpdates"
                params = {
                    'offset': self.offset,
                    'limit': 100,
                    'timeout': 10
                }
                
                async with self.session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data.get('ok'):
                            updates = data.get('result', [])
                            for update in updates:
                                await self.handle_update(update)
                                self.offset = update['update_id'] + 1
                            error_count = 0
                    elif response.status == 409:
                        error_count += 1
                        if error_count > 5:
                            logger.error("عدد كبير من الأخطاء، إعادة تشغيل...")
                            await asyncio.sleep(30)
                            error_count = 0
                    
                await asyncio.sleep(2)
                
            except Exception as e:
                logger.error(f"خطأ في معالجة التحديثات: {e}")
                await asyncio.sleep(5)

    async def handle_update(self, update):
        """معالجة تحديث واحد"""
        if 'message' in update:
            message = update['message']
            chat = message.get('chat', {})
            text = message.get('text', '')
            user_id = message.get('from', {}).get('id')
            
            # معالجة أوامر الـ admin
            if user_id == self.admin_id:
                # التحقق من حالة الـ admin
                if user_id in self.admin_states:
                    await self.handle_admin_state(message)
                    return
                
                if text == '/admin':
                    await self.show_admin_panel(chat['id'])
                    return
                elif message.get('photo') or message.get('voice') or message.get('audio') or message.get('document'):
                    await self.handle_admin_media(message)
                    return
            
            # معالجة أمر /start
            if text == '/start':
                await self.send_start_message(chat['id'])
                return
            
            # إضافة المجموعات
            if chat.get('type') in ['group', 'supergroup']:
                chat_id = chat['id']
                if chat_id not in self.active_groups:
                    self.active_groups.add(chat_id)
                    self.save_active_groups()  # حفظ المجموعات فوراً
                    logger.info(f"تم إضافة مجموعة جديدة: {chat_id}")
                    logger.info(f"إجمالي المجموعات النشطة: {len(self.active_groups)}")
                    
                    # إرسال رسالة ترحيب للمجموعة الجديدة
                    await self.send_welcome_to_new_group(chat_id)
        
        elif 'callback_query' in update:
            # معالجة الأزرار
            await self.handle_callback_query(update['callback_query'])

    async def show_admin_panel(self, chat_id):
        """عرض لوحة التحكم الرئيسية للمطور"""
        text = """🔧 **لوحة تحكم المطور** 🔧

اختر الإجراء المطلوب:"""
        
        keyboard = {
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
        
        await self.send_message(chat_id, text, keyboard)

    async def handle_callback_query(self, callback_query):
        """معالجة النقر على الأزرار"""
        user_id = callback_query['from']['id']
        chat_id = callback_query['message']['chat']['id']
        data = callback_query['data']
        message_id = callback_query['message']['message_id']
        
        if user_id != self.admin_id:
            await self.answer_callback_query(callback_query['id'], "❌ غير مخول لك!")
            return
        
        # الإجابة على الاستعلام
        await self.answer_callback_query(callback_query['id'])
        
        if data == "admin_add_text":
            await self.edit_message(chat_id, message_id, "📝 **إضافة نص جديد**\n\nاكتب النص الذي تريد إضافته:")
            self.admin_states[user_id] = {'action': 'waiting_for_text'}
            
        elif data == "admin_add_image":
            await self.edit_message(chat_id, message_id, "🖼️ **إضافة صورة**\n\nأرسل الصورة التي تريد إضافتها:")
            self.admin_states[user_id] = {'action': 'waiting_for_image'}
            
        elif data == "admin_add_voice":
            await self.edit_message(chat_id, message_id, "🎙️ **إضافة رسالة صوتية**\n\nأرسل الرسالة الصوتية:")
            self.admin_states[user_id] = {'action': 'waiting_for_voice'}
            
        elif data == "admin_add_audio":
            await self.edit_message(chat_id, message_id, "🎵 **إضافة ملف صوتي**\n\nأرسل الملف الصوتي:")
            self.admin_states[user_id] = {'action': 'waiting_for_audio'}
            
        elif data == "admin_add_document":
            await self.edit_message(chat_id, message_id, "📄 **إضافة مستند**\n\nأرسل المستند (PDF أو أي ملف):")
            self.admin_states[user_id] = {'action': 'waiting_for_document'}
            
        elif data == "admin_stats":
            stats = await self.get_bot_stats()
            keyboard = {"inline_keyboard": [[{"text": "🔙 العودة للقائمة", "callback_data": "admin_back"}]]}
            await self.edit_message(chat_id, message_id, stats, keyboard)
            
        elif data == "admin_view_content":
            content_info = await self.get_content_info()
            keyboard = {"inline_keyboard": [[{"text": "🔙 العودة للقائمة", "callback_data": "admin_back"}]]}
            await self.edit_message(chat_id, message_id, content_info, keyboard)
            
        elif data == "admin_back":
            await self.delete_message(chat_id, message_id)
            await self.show_admin_panel(chat_id)
            
        elif data == "admin_close":
            await self.delete_message(chat_id, message_id)
            await self.send_message(chat_id, "✅ تم إغلاق لوحة التحكم")
            
        elif data == "skip_caption":
            # تخطي الوصف وحفظ الملف بوصف افتراضي
            state = self.admin_states.get(user_id, {})
            file_path = state.get('file_path')
            file_type = state.get('file_type')
            
            if file_path and file_type:
                default_caption = ""  # وصف فارغ للتخطي
                await self.save_media_info(file_path, default_caption, file_type)
                
                file_name = os.path.basename(file_path)
                await self.edit_message(chat_id, message_id, f"✅ تم حفظ الملف بنجاح!\n📁 {file_name}\n📝 بدون وصف نصي")
                
                del self.admin_states[user_id]
                await asyncio.sleep(2)
                await self.delete_message(chat_id, message_id)
                await self.show_admin_panel(chat_id)

    async def handle_admin_state(self, message):
        """معالجة حالات المطور"""
        user_id = message['from']['id']
        chat_id = message['chat']['id']
        text = message.get('text', '')
        state = self.admin_states.get(user_id, {})
        
        if state.get('action') == 'waiting_for_text':
            # إضافة نص جديد
            if text.strip():
                await self.add_azkar_text(text)
                await self.send_message(chat_id, "✅ تم إضافة النص بنجاح!")
                del self.admin_states[user_id]
                await self.show_admin_panel(chat_id)
            else:
                await self.send_message(chat_id, "❌ يرجى كتابة نص صحيح")
                
        elif state.get('action') == 'waiting_for_caption':
            # إضافة وصف للملف
            file_path = state.get('file_path')
            file_type = state.get('file_type')
            
            if file_path and file_type:
                caption = text.strip() if text.strip() else ""
                await self.save_media_info(file_path, caption, file_type)
                
                file_name = os.path.basename(file_path)
                if caption:
                    await self.send_message(chat_id, f"✅ تم حفظ الملف بنجاح!\n📁 {file_name}\n📝 الوصف: {caption}")
                else:
                    await self.send_message(chat_id, f"✅ تم حفظ الملف بنجاح!\n📁 {file_name}\n📝 بدون وصف نصي")
                
                del self.admin_states[user_id]
                await self.show_admin_panel(chat_id)
        
        elif state.get('action') in ['waiting_for_image', 'waiting_for_voice', 'waiting_for_audio', 'waiting_for_document']:
            # معالجة الملفات
            await self.handle_admin_media_with_state(message)

    async def handle_admin_media_with_state(self, message):
        """معالجة الملفات مع حالات الـ admin"""
        user_id = message['from']['id']
        chat_id = message['chat']['id']
        state = self.admin_states.get(user_id, {})
        action = state.get('action')
        
        file_path = None
        file_type = None
        
        try:
            if action == 'waiting_for_image' and message.get('photo'):
                photo = message['photo'][-1]
                file_id = photo['file_id']
                file_path = await self.download_file(file_id, 'random', 'jpg')
                file_type = 'image'
                
            elif action == 'waiting_for_voice' and message.get('voice'):
                voice = message['voice']
                file_id = voice['file_id']
                file_path = await self.download_file(file_id, 'voices', 'ogg')
                file_type = 'voice'
                
            elif action == 'waiting_for_audio' and message.get('audio'):
                audio = message['audio']
                file_id = audio['file_id']
                file_extension = 'mp3'
                if audio.get('mime_type'):
                    if 'mp3' in audio['mime_type']:
                        file_extension = 'mp3'
                    elif 'mp4' in audio['mime_type']:
                        file_extension = 'mp4'
                
                file_path = await self.download_file(file_id, 'audios', file_extension)
                file_type = 'audio'
                
            elif action == 'waiting_for_document' and message.get('document'):
                document = message['document']
                file_id = document['file_id']
                file_name = document.get('file_name', 'document')
                
                if any(ext in file_name.lower() for ext in ['.jpg', '.jpeg', '.png']):
                    folder = 'random'
                    file_type = 'image'
                elif any(ext in file_name.lower() for ext in ['.mp3', '.mp4', '.wav']):
                    folder = 'audios'
                    file_type = 'audio'
                else:
                    folder = 'random'
                    file_type = 'document'
                
                file_extension = file_name.split('.')[-1] if '.' in file_name else 'unknown'
                file_path = await self.download_file(file_id, folder, file_extension)
            
            if file_path:
                # طلب الوصف
                self.admin_states[user_id] = {
                    'action': 'waiting_for_caption',
                    'file_path': file_path,
                    'file_type': file_type
                }
                
                keyboard = {
                    "inline_keyboard": [[
                        {"text": "تخطي الوصف", "callback_data": "skip_caption"}
                    ]]
                }
                
                await self.send_message(
                    chat_id, 
                    f"✅ تم تحميل الملف بنجاح!\n\n📝 اكتب وصفاً للملف أو اضغط تخطي:",
                    keyboard
                )
            else:
                await self.send_message(chat_id, "❌ فشل في تحميل الملف. حاول مرة أخرى.")
                
        except Exception as e:
            logger.error(f"خطأ في معالجة الملف: {e}")
            await self.send_message(chat_id, f"❌ خطأ في معالجة الملف: {str(e)}")

    async def get_content_info(self):
        """الحصول على معلومات المحتوى المحفوظ"""
        try:
            # عدد النصوص
            texts_count = 0
            try:
                with open('Azkar.txt', 'r', encoding='utf-8') as f:
                    content = f.read()
                    texts_count = len([t for t in content.split('---') if t.strip()])
            except:
                pass
            
            # عدد الملفات في كل مجلد
            folders_info = {}
            for folder in ['random', 'voices', 'audios', 'morning', 'evening', 'prayers']:
                if os.path.exists(folder):
                    files = [f for f in os.listdir(folder) if not f.endswith('.info')]
                    folders_info[folder] = len(files)
                else:
                    folders_info[folder] = 0
            
            content_text = f"""📋 **المحتوى المحفوظ:**

📝 **النصوص:** {texts_count}

📁 **الملفات:**
🖼️ **الصور العشوائية:** {folders_info['random']}
🎙️ **الرسائل الصوتية:** {folders_info['voices']}
🎵 **الملفات الصوتية:** {folders_info['audios']}
🌅 **صور الصباح:** {folders_info['morning']}
🌇 **صور المساء:** {folders_info['evening']}
🕌 **صور الصلاة:** {folders_info['prayers']}

📊 **إجمالي الملفات:** {sum(folders_info.values())}"""
            
            return content_text
            
        except Exception as e:
            return f"❌ خطأ في جلب معلومات المحتوى: {str(e)}"

    async def handle_admin_command(self, message):
        """معالجة أوامر الـ admin"""
        text = message.get('text', '')
        chat_id = message['chat']['id']
        
        if text.startswith('/admin add_text '):
            # إضافة نص جديد
            new_text = text.replace('/admin add_text ', '').strip()
            if new_text:
                await self.add_azkar_text(new_text)
                await self.send_message(chat_id, "✅ تم إضافة النص بنجاح!")
            else:
                await self.send_message(chat_id, "❌ يرجى كتابة النص بعد الأمر")
        
        elif text == '/admin stats':
            # إحصائيات البوت
            stats = await self.get_bot_stats()
            await self.send_message(chat_id, stats)
        
        elif text == '/admin help':
            # مساعدة الـ admin
            help_text = """🔧 **أوامر المطور:**

📝 **إضافة محتوى:**
• `/admin add_text [النص]` - إضافة نص جديد
• أرسل صورة مع وصف لإضافتها للأذكار العشوائية
• أرسل رسالة صوتية مع وصف لإضافتها للقائمة
• أرسل ملف صوتي مع وصف لإضافته للقائمة

📊 **معلومات:**
• `/admin stats` - إحصائيات البوت
• `/admin help` - هذه المساعدة

ℹ️ **ملاحظة:** الوصف اختياري وسيستخدم كتعليق للمحتوى"""
            
            await self.send_message(chat_id, help_text)

    async def handle_admin_media(self, message):
        """معالجة الملفات المرسلة من الـ admin"""
        chat_id = message['chat']['id']
        caption = message.get('caption', '')
        
        try:
            if message.get('photo'):
                # معالجة الصور
                photo = message['photo'][-1]  # أعلى جودة
                file_id = photo['file_id']
                file_path = await self.download_file(file_id, 'random', 'jpg')
                if file_path:
                    await self.save_media_info(file_path, caption, 'image')
                    await self.send_message(chat_id, f"✅ تم حفظ الصورة: {os.path.basename(file_path)}")
                
            elif message.get('voice'):
                # معالجة الرسائل الصوتية
                voice = message['voice']
                file_id = voice['file_id']
                file_path = await self.download_file(file_id, 'voices', 'ogg')
                if file_path:
                    await self.save_media_info(file_path, caption, 'voice')
                    await self.send_message(chat_id, f"✅ تم حفظ الرسالة الصوتية: {os.path.basename(file_path)}")
                
            elif message.get('audio'):
                # معالجة الملفات الصوتية
                audio = message['audio']
                file_id = audio['file_id']
                file_extension = 'mp3'
                if audio.get('mime_type'):
                    if 'mp3' in audio['mime_type']:
                        file_extension = 'mp3'
                    elif 'mp4' in audio['mime_type']:
                        file_extension = 'mp4'
                
                file_path = await self.download_file(file_id, 'audios', file_extension)
                if file_path:
                    await self.save_media_info(file_path, caption, 'audio')
                    await self.send_message(chat_id, f"✅ تم حفظ الملف الصوتي: {os.path.basename(file_path)}")
                
            elif message.get('document'):
                # معالجة المستندات (PDF، صور، إلخ)
                document = message['document']
                file_id = document['file_id']
                file_name = document.get('file_name', 'document')
                
                # تحديد نوع الملف والمجلد المناسب
                if any(ext in file_name.lower() for ext in ['.jpg', '.jpeg', '.png']):
                    folder = 'random'
                elif any(ext in file_name.lower() for ext in ['.mp3', '.mp4', '.wav']):
                    folder = 'audios'
                else:
                    folder = 'random'  # افتراضي
                
                file_extension = file_name.split('.')[-1] if '.' in file_name else 'unknown'
                file_path = await self.download_file(file_id, folder, file_extension)
                
                if file_path:
                    await self.save_media_info(file_path, caption, 'document')
                    await self.send_message(chat_id, f"✅ تم حفظ المستند: {os.path.basename(file_path)}")
        
        except Exception as e:
            logger.error(f"خطأ في معالجة الملف: {e}")
            await self.send_message(chat_id, f"❌ خطأ في حفظ الملف: {str(e)}")

    async def download_file(self, file_id, folder, extension):
        """تحميل ملف من تيليجرام"""
        try:
            # الحصول على مسار الملف
            url = f"{self.base_url}/getFile?file_id={file_id}"
            async with self.session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    if data.get('ok'):
                        file_path = data['result']['file_path']
                        
                        # تحميل الملف
                        download_url = f"https://api.telegram.org/file/bot{self.bot_token}/{file_path}"
                        async with self.session.get(download_url) as file_response:
                            if file_response.status == 200:
                                # إنشاء اسم ملف فريد
                                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                                filename = f"{timestamp}.{extension}"
                                local_path = os.path.join(folder, filename)
                                
                                # حفظ الملف
                                with open(local_path, 'wb') as f:
                                    f.write(await file_response.read())
                                
                                return local_path
        except Exception as e:
            logger.error(f"خطأ في تحميل الملف: {e}")
        return None

    async def save_media_info(self, file_path, caption, media_type):
        """حفظ معلومات الملف مع الوصف"""
        info_file = f"{file_path}.info"
        info_data = {
            'caption': caption,
            'type': media_type,
            'created_at': datetime.now().isoformat()
        }
        
        with open(info_file, 'w', encoding='utf-8') as f:
            json.dump(info_data, f, ensure_ascii=False, indent=2)

    async def add_azkar_text(self, text):
        """إضافة نص جديد لملف الأذكار"""
        try:
            with open('Azkar.txt', 'a', encoding='utf-8') as f:
                f.write(f"\n---\n{text}")
            logger.info(f"تم إضافة نص جديد: {text[:50]}...")
        except Exception as e:
            logger.error(f"خطأ في إضافة النص: {e}")

    async def get_bot_stats(self):
        """الحصول على إحصائيات البوت"""
        try:
            # عدد المجموعات النشطة
            groups_count = len(self.active_groups)
            
            # عدد النصوص
            texts_count = 0
            try:
                with open('Azkar.txt', 'r', encoding='utf-8') as f:
                    content = f.read()
                    texts_count = len([t for t in content.split('---') if t.strip()])
            except:
                pass
            
            # عدد الصور
            images_count = len([f for f in os.listdir('random') if f.lower().endswith(('.png', '.jpg', '.jpeg'))])
            
            # عدد الرسائل الصوتية
            voices_count = len([f for f in os.listdir('voices') if f.lower().endswith(('.ogg', '.mp3'))])
            
            # عدد الملفات الصوتية
            audios_count = len([f for f in os.listdir('audios') if f.lower().endswith(('.mp3', '.mp4', '.wav'))])
            
            stats_text = f"""📊 **إحصائيات البوت:**

👥 **المجموعات النشطة:** {groups_count}
📝 **النصوص:** {texts_count}
🖼️ **الصور:** {images_count}
🎙️ **الرسائل الصوتية:** {voices_count}
🎵 **الملفات الصوتية:** {audios_count}

⏰ **آخر تحديث:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"""
            
            return stats_text
        except Exception as e:
            return f"❌ خطأ في جلب الإحصائيات: {str(e)}"

    def load_azkar_texts(self):
        """تحميل نصوص الأذكار من الملف"""
        try:
            with open('Azkar.txt', 'r', encoding='utf-8') as file:
                content = file.read()
                azkar_list = [azkar.strip() for azkar in content.split('---') if azkar.strip()]
                return azkar_list
        except FileNotFoundError:
            logger.error("ملف Azkar.txt غير موجود")
            return ["سبحان الله وبحمده، سبحان الله العظيم"]

    def get_random_file(self, folder, extensions):
        """الحصول على ملف عشوائي من المجلد"""
        try:
            if os.path.exists(folder):
                files = [f for f in os.listdir(folder) if f.lower().endswith(extensions)]
                if files:
                    selected_file = random.choice(files)
                    file_path = os.path.join(folder, selected_file)
                    
                    # محاولة قراءة الوصف
                    info_file = f"{file_path}.info"
                    caption = None
                    
                    if os.path.exists(info_file):
                        try:
                            with open(info_file, 'r', encoding='utf-8') as f:
                                info_data = json.load(f)
                                user_caption = info_data.get('caption', '').strip()
                                # إذا كان هناك وصف من المطور، استخدمه
                                if user_caption:
                                    caption = f" **{user_caption}** "
                        except Exception as e:
                            logger.error(f"خطأ في قراءة ملف المعلومات {info_file}: {e}")
                    
                    return file_path, caption
        except Exception as e:
            logger.error(f"خطأ في قراءة المجلد {folder}: {e}")
        return None, None

    def create_inline_keyboard(self):
        """إنشاء لوحة مفاتيح مضمنة للرسائل العادية"""
        return {
            "inline_keyboard": [[{
                "text": "📿 تلاوات قرانية - أجر",
                "url": self.channel_link
            }]]
        }

    def create_start_keyboard(self):
        """إنشاء لوحة مفاتيح خاصة برسالة البداية"""
        return {
            "inline_keyboard": [
                [
                    {"text": "👨‍💻 مطور البوت", "url": "https://t.me/mavdiii"},
                    {"text": "📂 Source code", "url": "https://github.com/Mavdii/bot"}
                ],
                [
                    {"text": "➕ اضافة البوت الى مجموعتك", "url": "https://t.me/Mouslim_alarm_bot?startgroup=inpvbtn"}
                ]
            ]
        }

    async def send_start_message(self, chat_id):
        """إرسال رسالة البداية"""
        start_text = """**🌿 مرحبًا بك في بوت الأذكار 🌿**

**قال تعالى: "فاذكروني أذكركم واشكروا لي ولا تكفرون"**

**وقال رسول الله ﷺ: "ألا أنبئكم بخير أعمالكم، وأزكاها عند مليككم، وأرفعها في درجاتكم...؟ ذكر الله"**

**هذا البوت وُجد ليكون رفيقك في طريق الطمأنينة، ومُعينك على ذكر الله في زحمة الحياة.**

**ستجد هنا: أذكار يومية، تسبيحات، أدعية نبوية، وتذكير بقراءة القرآن الكريم.**

**📌 قم بإضافة البوت الى مجموعتك واجعل لسانك رطبًا بذكر الله**

**✨ نسأل الله أن يجعلنا وإياكم من الذاكرين الله كثيرًا والذاكرات، وأن يكتب لنا الأجر والثواب.**"""
        
        reply_markup = self.create_start_keyboard()
        await self.send_message(chat_id, start_text, reply_markup)

    async def send_message(self, chat_id, text, reply_markup=None):
        """إرسال رسالة نصية"""
        try:
            url = f"{self.base_url}/sendMessage"
            data = {
                'chat_id': chat_id,
                'text': text,
                'parse_mode': 'Markdown'
            }
            if reply_markup:
                data['reply_markup'] = json.dumps(reply_markup)
            
            async with self.session.post(url, data=data) as response:
                if response.status == 200:
                    result = await response.json()
                    if result.get('ok'):
                        return result['result']['message_id']
        except Exception as e:
            logger.error(f"خطأ في إرسال الرسالة: {e}")
        return None

    async def edit_message(self, chat_id, message_id, text, reply_markup=None):
        """تحرير رسالة موجودة"""
        try:
            url = f"{self.base_url}/editMessageText"
            data = {
                'chat_id': chat_id,
                'message_id': message_id,
                'text': text,
                'parse_mode': 'Markdown'
            }
            if reply_markup:
                data['reply_markup'] = json.dumps(reply_markup)
            
            async with self.session.post(url, data=data) as response:
                if response.status == 200:
                    result = await response.json()
                    return result.get('ok', False)
        except Exception as e:
            logger.error(f"خطأ في تحرير الرسالة: {e}")
        return False

    async def answer_callback_query(self, callback_query_id, text=None):
        """الرد على callback query"""
        try:
            url = f"{self.base_url}/answerCallbackQuery"
            data = {'callback_query_id': callback_query_id}
            if text:
                data['text'] = text
            
            async with self.session.post(url, data=data) as response:
                return response.status == 200
        except Exception as e:
            logger.error(f"خطأ في الرد على callback query: {e}")
        return False

    async def send_photo(self, chat_id, photo_path, caption, reply_markup=None):
        """إرسال صورة"""
        try:
            url = f"{self.base_url}/sendPhoto"
            
            data = aiohttp.FormData()
            data.add_field('chat_id', str(chat_id))
            data.add_field('caption', caption)
            data.add_field('parse_mode', 'Markdown')
            if reply_markup:
                data.add_field('reply_markup', json.dumps(reply_markup))
            
            with open(photo_path, 'rb') as photo_file:
                data.add_field('photo', photo_file)
                
                async with self.session.post(url, data=data) as response:
                    if response.status == 200:
                        result = await response.json()
                        if result.get('ok'):
                            return result['result']['message_id']
        except Exception as e:
            logger.error(f"خطأ في إرسال الصورة: {e}")
        return None

    async def send_voice(self, chat_id, voice_path, caption, reply_markup=None):
        """إرسال رسالة صوتية"""
        try:
            url = f"{self.base_url}/sendVoice"
            
            data = aiohttp.FormData()
            data.add_field('chat_id', str(chat_id))
            data.add_field('caption', caption)
            data.add_field('parse_mode', 'Markdown')
            if reply_markup:
                data.add_field('reply_markup', json.dumps(reply_markup))
            
            with open(voice_path, 'rb') as voice_file:
                data.add_field('voice', voice_file)
                
                async with self.session.post(url, data=data) as response:
                    if response.status == 200:
                        result = await response.json()
                        if result.get('ok'):
                            return result['result']['message_id']
        except Exception as e:
            logger.error(f"خطأ في إرسال الرسالة الصوتية: {e}")
        return None

    async def send_audio(self, chat_id, audio_path, caption, reply_markup=None):
        """إرسال ملف صوتي"""
        try:
            url = f"{self.base_url}/sendAudio"
            
            data = aiohttp.FormData()
            data.add_field('chat_id', str(chat_id))
            data.add_field('caption', caption)
            data.add_field('parse_mode', 'Markdown')
            if reply_markup:
                data.add_field('reply_markup', json.dumps(reply_markup))
            
            with open(audio_path, 'rb') as audio_file:
                data.add_field('audio', audio_file)
                
                async with self.session.post(url, data=data) as response:
                    if response.status == 200:
                        result = await response.json()
                        if result.get('ok'):
                            return result['result']['message_id']
        except Exception as e:
            logger.error(f"خطأ في إرسال الملف الصوتي: {e}")
        return None

    async def send_photo_without_caption(self, chat_id, photo_path, reply_markup=None):
        """إرسال صورة بدون نص"""
        try:
            url = f"{self.base_url}/sendPhoto"
            
            data = aiohttp.FormData()
            data.add_field('chat_id', str(chat_id))
            if reply_markup:
                data.add_field('reply_markup', json.dumps(reply_markup))
            
            with open(photo_path, 'rb') as photo_file:
                data.add_field('photo', photo_file)
                
                async with self.session.post(url, data=data) as response:
                    if response.status == 200:
                        result = await response.json()
                        if result.get('ok'):
                            return result['result']['message_id']
        except Exception as e:
            logger.error(f"خطأ في إرسال الصورة: {e}")
        return None

    async def send_voice_without_caption(self, chat_id, voice_path, reply_markup=None):
        """إرسال رسالة صوتية بدون نص"""
        try:
            url = f"{self.base_url}/sendVoice"
            
            data = aiohttp.FormData()
            data.add_field('chat_id', str(chat_id))
            if reply_markup:
                data.add_field('reply_markup', json.dumps(reply_markup))
            
            with open(voice_path, 'rb') as voice_file:
                data.add_field('voice', voice_file)
                
                async with self.session.post(url, data=data) as response:
                    if response.status == 200:
                        result = await response.json()
                        if result.get('ok'):
                            return result['result']['message_id']
        except Exception as e:
            logger.error(f"خطأ في إرسال الرسالة الصوتية: {e}")
        return None

    async def send_audio_without_caption(self, chat_id, audio_path, reply_markup=None):
        """إرسال ملف صوتي بدون نص"""
        try:
            url = f"{self.base_url}/sendAudio"
            
            data = aiohttp.FormData()
            data.add_field('chat_id', str(chat_id))
            if reply_markup:
                data.add_field('reply_markup', json.dumps(reply_markup))
            
            with open(audio_path, 'rb') as audio_file:
                data.add_field('audio', audio_file)
                
                async with self.session.post(url, data=data) as response:
                    if response.status == 200:
                        result = await response.json()
                        if result.get('ok'):
                            return result['result']['message_id']
        except Exception as e:
            logger.error(f"خطأ في إرسال الملف الصوتي: {e}")
        return None

    async def delete_message(self, chat_id, message_id):
        """حذف رسالة"""
        try:
            url = f"{self.base_url}/deleteMessage"
            data = {
                'chat_id': chat_id,
                'message_id': message_id
            }
            async with self.session.post(url, data=data) as response:
                return response.status == 200
        except Exception as e:
            logger.warning(f"لم يتم حذف الرسالة: {e}")
        return False

    async def send_random_content(self):
        """إرسال محتوى عشوائي (نص، صورة، صوت، أو ملف صوتي)"""
        if not self.active_groups:
            logger.warning("لا توجد مجموعات نشطة لإرسال المحتوى إليها")
            return
        
        logger.info(f"بدء إرسال المحتوى العشوائي إلى {len(self.active_groups)} مجموعة (نوع المحتوى: {self.content_turn})")
            
        for chat_id in self.active_groups.copy():
            try:
                reply_markup = self.create_inline_keyboard()
                message_id = None
                
                # تحديد نوع المحتوى بالتناوب
                if self.content_turn == 0:
                    # إرسال نص
                    azkar_list = self.load_azkar_texts()
                    azkar_text = random.choice(azkar_list)
                    text = f" **{azkar_text}** "
                    message_id = await self.send_message(chat_id, text, reply_markup)
                
                elif self.content_turn == 1:
                    # إرسال صورة
                    image_path, caption = self.get_random_file('random', ('.png', '.jpg', '.jpeg'))
                    if image_path:
                        if caption:
                            message_id = await self.send_photo(chat_id, image_path, caption, reply_markup)
                        else:
                            # إرسال الصورة بدون نص
                            message_id = await self.send_photo_without_caption(chat_id, image_path, reply_markup)
                    else:
                        # نص بديل
                        azkar_list = self.load_azkar_texts()
                        azkar_text = random.choice(azkar_list)
                        text = f" **{azkar_text}** "
                        message_id = await self.send_message(chat_id, text, reply_markup)
                
                elif self.content_turn == 2:
                    # إرسال رسالة صوتية
                    voice_path, caption = self.get_random_file('voices', ('.ogg', '.mp3'))
                    if voice_path:
                        if caption:
                            message_id = await self.send_voice(chat_id, voice_path, caption, reply_markup)
                        else:
                            # إرسال الرسالة الصوتية بدون نص
                            message_id = await self.send_voice_without_caption(chat_id, voice_path, reply_markup)
                    else:
                        # نص بديل
                        azkar_list = self.load_azkar_texts()
                        azkar_text = random.choice(azkar_list)
                        text = f" **{azkar_text}** "
                        message_id = await self.send_message(chat_id, text, reply_markup)
                
                elif self.content_turn == 3:
                    # إرسال ملف صوتي
                    audio_path, caption = self.get_random_file('audios', ('.mp3', '.mp4', '.wav'))
                    if audio_path:
                        if caption:
                            message_id = await self.send_audio(chat_id, audio_path, caption, reply_markup)
                        else:
                            # إرسال الملف الصوتي بدون نص
                            message_id = await self.send_audio_without_caption(chat_id, audio_path, reply_markup)
                    else:
                        # نص بديل
                        azkar_list = self.load_azkar_texts()
                        azkar_text = random.choice(azkar_list)
                        text = f" **{azkar_text}** "
                        message_id = await self.send_message(chat_id, text, reply_markup)
                
            except Exception as e:
                logger.error(f"خطأ في إرسال المحتوى للمجموعة {chat_id}: {e}")
        
        # تحديث دورة المحتوى
        self.content_turn = (self.content_turn + 1) % 4
        logger.info(f"تم إرسال المحتوى بنجاح، المحتوى التالي سيكون نوع: {self.content_turn}")

    async def send_welcome_to_new_group(self, chat_id):
        """إرسال رسالة ترحيب للمجموعة الجديدة"""
        try:
            welcome_text = """🌿 **أهلاً وسهلاً بكم في بوت الأذكار الإسلامية** 🌿

✅ **تم تفعيل البوت بنجاح في هذه المجموعة**

📿 **سيقوم البوت بإرسال:**
• أذكار وتسبيحات عشوائية كل 5 دقائق
• تذكير بأذكار الصباح والمساء
• تنبيهات مواقيت الصلاة لمحافظة القاهرة
• أذكار ما بعد الصلاة

 **نسأل الله أن يبارك فيكم ويجعل هذا البوت سبباً في تذكيركم بالله عز وجل**

⚡️ **سيبدأ البوت في العمل خلال دقائق قليلة...**"""

            reply_markup = self.create_inline_keyboard()
            await self.send_message(chat_id, welcome_text, reply_markup)
            logger.info(f"تم إرسال رسالة الترحيب للمجموعة الجديدة: {chat_id}")
        except Exception as e:
            logger.error(f"خطأ في إرسال رسالة الترحيب للمجموعة {chat_id}: {e}")

    async def send_morning_azkar(self):
        """إرسال أذكار الصباح"""
        if not self.active_groups:
            return
            
        for chat_id in self.active_groups.copy():
            try:
                image_path, _ = self.get_random_file('morning', ('.png', '.jpg', '.jpeg'))
                reply_markup = self.create_inline_keyboard()
                
                if image_path:
                    caption = "🌅 **لا تنس قراءة أذكار الصباح** 🌅"
                    await self.send_photo(chat_id, image_path, caption, reply_markup)
                else:
                    text = "🌅 **لا تنس قراءة أذكار الصباح** 🌅"
                    await self.send_message(chat_id, text, reply_markup)
                    
            except Exception as e:
                logger.error(f"خطأ في إرسال أذكار الصباح للمجموعة {chat_id}: {e}")

    async def send_evening_azkar(self):
        """إرسال أذكار المساء"""
        if not self.active_groups:
            return
            
        for chat_id in self.active_groups.copy():
            try:
                image_path, _ = self.get_random_file('evening', ('.png', '.jpg', '.jpeg'))
                reply_markup = self.create_inline_keyboard()
                
                if image_path:
                    caption = "🌇 **لا تنس قراءة أذكار المساء** 🌇"
                    await self.send_photo(chat_id, image_path, caption, reply_markup)
                else:
                    text = "🌇 **لا تنس قراءة أذكار المساء** 🌇"
                    await self.send_message(chat_id, text, reply_markup)
                    
            except Exception as e:
                logger.error(f"خطأ في إرسال أذكار المساء للمجموعة {chat_id}: {e}")

    async def get_prayer_times(self):
        """جلب مواقيت الصلاة من API"""
        try:
            today = datetime.now(self.cairo_tz).strftime('%d-%m-%Y')
            url = f"https://api.aladhan.com/v1/timingsByCity/{today}?city=cairo&country=egypt&method=8"
            
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                data = response.json()
                if data.get('code') == 200:
                    timings = data['data']['timings']
                    return {
                        'Fajr': timings['Fajr'],
                        'Dhuhr': timings['Dhuhr'],
                        'Asr': timings['Asr'],
                        'Maghrib': timings['Maghrib'],
                        'Isha': timings['Isha']
                    }
        except Exception as e:
            logger.error(f"خطأ في جلب مواقيت الصلاة: {e}")
        return None

    async def schedule_prayer_notifications(self):
        """جدولة تنبيهات الصلاة - محسن لتجنب المهام المتأخرة"""
        prayer_times = await self.get_prayer_times()
        if not prayer_times:
            logger.error("لم يتم الحصول على مواقيت الصلاة")
            return

        # إزالة الوظائف القديمة أولاً
        current_jobs = self.scheduler.get_jobs()
        for job in current_jobs:
            if 'prayer' in job.id:
                self.scheduler.remove_job(job.id)

        prayer_messages = {
            'Fajr': """🌅 **تنبيه مهم لصلاة الفجر** 🌅

⏰ **تبقّى 5 دقائق على أذان الفجر** ⏰

📢 **أيها الإخوة، هذا وقت عظيم من أوقات الطاعة، اتركوا أعمالكم وتهيأوا للصلاة، فإنها عهد الله الذي لا يُضيّعه إلا غافل.**

☝️ **تارك الصلاة عمدًا - بلا عذر ولا توبة - على خطرٍ عظيم، فقد أفتى جمع من العلماء بأنه يُعد كافرًا مرتدًا عن الإسلام، ويُقام عليه الحد الشرعي إن لم يتب ويُصلِّ.**

🕌 **صلاة الفجر نور في الوجه، وبركة في الرزق، وحفظ في اليوم كله.**""",

            'Dhuhr': """☀️ **تنبيه مهم لصلاة الظهر** ☀️

⏰ **تبقّى 5 دقائق على أذان الظهر** ⏰

📢 **أيها المسلمون، هذا وقت عبادةٍ من أعظم أوقات اليوم، فتوقفوا قليلًا عن الانشغال بالدنيا، وتهيأوا للقاء ربكم بالصلاة.**

☝️ **تارك الصلاة عمدًا بلا عذر على خطرٍ عظيم، فقد أفتى كثير من أهل العلم أنه كافر كفرًا أكبر مخرجًا من الملة، ويُدعى للتوبة، فإن لم يتب وأصرّ، يُقام عليه الحد الشرعي.**

🕌 **الصلاة راحةٌ للروح، وطمأنينةٌ للقلب، وتجديدٌ للعهد مع الله.**""",

            'Asr': """🌤️ **تنبيه مهم لصلاة العصر** 🌤️

⏰ **تبقّى 5 دقائق على أذان العصر** ⏰

⚠️ **هذه الصلاة حذّرنا الله من التفريط فيها، فهي من الصلوات التي يجب تعظيمها وعدم تأخيرها.**

🌟 **من فاته العصر كأنما وُتِرَ أهله وماله، كما جاء في الحديث الشريف.**""",

            'Maghrib': """🌅 **تنبيه مهم لصلاة المغرب** 🌅

⏰ **تبقّى 5 دقائق على أذان المغرب** ⏰

🌇 **الشمس تغرب الآن، وهذا وقتٌ تُستجاب فيه الدعوات.**""",

            'Isha': """🌙 **تنبيه مهم لصلاة العشاء** 🌙

⏰ **تبقّى 5 دقائق على أذان العشاء** ⏰

🌟 **هذه آخر صلاة في اليوم، فاجعلوها ختامًا مباركًا.**"""
        }

        current_time = datetime.now(self.cairo_tz)
        
        for prayer, time_str in prayer_times.items():
            try:
                prayer_time = datetime.strptime(time_str, '%H:%M').time()
                prayer_datetime = datetime.combine(current_time.date(), prayer_time)
                prayer_datetime = self.cairo_tz.localize(prayer_datetime)
                
                # إذا كان الوقت قد فات اليوم، جدوله للغد
                if prayer_datetime <= current_time:
                    prayer_datetime += timedelta(days=1)
                
                # تنبيه قبل 5 دقائق
                notification_time = prayer_datetime - timedelta(minutes=5)
                
                # التأكد من أن وقت التنبيه لم يفت
                if notification_time > current_time:
                    self.scheduler.add_job(
                        self.send_prayer_notification,
                        'date',
                        run_date=notification_time,
                        args=[prayer_messages[prayer]],
                        id=f"prayer_notification_{prayer}_{current_time.strftime('%Y%m%d')}",
                        replace_existing=True,
                        misfire_grace_time=300  # 5 دقائق grace time
                    )
                    
                    # صورة ما بعد الصلاة (بعد 25 دقيقة)
                    after_prayer_time = prayer_datetime + timedelta(minutes=25)
                    self.scheduler.add_job(
                        self.send_after_prayer_image,
                        'date',
                        run_date=after_prayer_time,
                        id=f"after_prayer_{prayer}_{current_time.strftime('%Y%m%d')}",
                        replace_existing=True,
                        misfire_grace_time=300
                    )
                    
                    logger.info(f"تم جدولة تنبيه صلاة {prayer} في {notification_time}")
                else:
                    logger.info(f"تم تخطي صلاة {prayer} لأن وقتها فات اليوم")
                
            except Exception as e:
                logger.error(f"خطأ في جدولة صلاة {prayer}: {e}")

    async def send_prayer_notification(self, message_text):
        """إرسال تنبيه الصلاة"""
        if not self.active_groups:
            return
            
        reply_markup = self.create_inline_keyboard()
        
        for chat_id in self.active_groups.copy():
            try:
                await self.send_message(chat_id, message_text, reply_markup)
            except Exception as e:
                logger.error(f"خطأ في إرسال تنبيه الصلاة للمجموعة {chat_id}: {e}")

    async def send_after_prayer_image(self):
        """إرسال صورة ما بعد الصلاة"""
        if not self.active_groups:
            return
            
        for chat_id in self.active_groups.copy():
            try:
                image_path, _ = self.get_random_file('prayers', ('.png', '.jpg', '.jpeg'))
                reply_markup = self.create_inline_keyboard()
                
                if image_path:
                    caption = "🕌 **لا تنس قراءة أذكار ما بعد الصلاة** 🕌"
                    await self.send_photo(chat_id, image_path, caption, reply_markup)
                else:
                    text = "🕌 **لا تنس قراءة أذكار ما بعد الصلاة** 🕌"
                    await self.send_message(chat_id, text, reply_markup)
                    
            except Exception as e:
                logger.error(f"خطأ في إرسال صورة ما بعد الصلاة للمجموعة {chat_id}: {e}")

# تشغيل البوت
async def main():
    bot = AzkarBot()
    try:
        await bot.start_bot()
    except KeyboardInterrupt:
        logger.info("تم إيقاف البوت")
    except Exception as e:
        logger.error(f"خطأ في تشغيل البوت: {e}")

if __name__ == "__main__":
    asyncio.run(main())
