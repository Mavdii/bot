import sqlite3
import random
import time
import threading
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes
from pyrogram import Client
from pyrogram.errors import FloodWait, BadRequest, Forbidden
from flask import Flask
import logging

# إعدادات البوت
TOKEN = "8050845867:AAFyvT9XUAcBPkfBcDhqjFPAPn5LKlqDTF4"  # غيّرها بتوكن بوتك
API_ID = 22696039  # من my.telegram.org
API_HASH = "00f9cc1d3419e879013f7a9d2d9432e2"  # من my.telegram.org
ADMIN_IDS = [7089656746]  # ضيف آي دي المشرفين
DB_FILE = "users_data.db"
COOLDOWN = 60  # ثواني بين كل رسالة
XP_RANGE = (10, 25)  # نطاق النقاط
COINS_PER_XP = 0.5  # كوينز لكل XP
ADMIN_COST_PER_DAY = 500  # تكلفة يوم واحد كأدمن
CHECK_EXPIRED_ADMINS_INTERVAL = 3600  # التحقق كل ساعة

# إعداد لوج
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# إعداد Pyrogram
pyro_client = Client("bot_session", api_id=API_ID, api_hash=API_HASH, bot_token=TOKEN)

# دالة رفع/تعديل صلاحيات المشرف باستخدام Pyrogram
async def promote_member(chat_id: str, user_id: int, permissions: dict, is_demote: bool = False):
    async with pyro_client:
        try:
            await pyro_client.promote_chat_member(
                chat_id=int(chat_id),
                user_id=user_id,
                can_change_info=permissions.get("can_change_info", False),
                can_post_messages=permissions.get("can_post_messages", is_demote),
                can_edit_messages=permissions.get("can_edit_messages", is_demote),
                can_delete_messages=permissions.get("can_delete_messages", is_demote),
                can_invite_users=permissions.get("can_invite_users", is_demote),
                can_restrict_members=permissions.get("can_restrict_members", False),
                can_pin_messages=permissions.get("can_pin_messages", is_demote),
                can_promote_members=permissions.get("can_promote_members", False),
                can_manage_topics=permissions.get("can_manage_topics", is_demote),
                can_manage_video_chats=permissions.get("can_manage_video_chats", is_demote),
                can_post_stories=permissions.get("can_post_stories", is_demote),
                can_edit_stories=permissions.get("can_edit_stories", is_demote),
                can_delete_stories=permissions.get("can_delete_stories", is_demote)
            )
            return True
        except Forbidden as e:
            logger.error(f"خطأ في رفع المشرف (Forbidden): {e}")
            return False
        except BadRequest as e:
            logger.error(f"خطأ في رفع المشرف (BadRequest): {e}")
            return False
        except FloodWait as e:
            logger.error(f"فلود ويت: انتظر {e.x} ثانية")
            await asyncio.sleep(e.x)
            return False
        except Exception as e:
            logger.error(f"خطأ غير متوقع في رفع المشرف: {e}")
            return False

# دالة التحقق من صلاحيات البوت
async def check_bot_permissions(context: ContextTypes.DEFAULT_TYPE, chat_id: str) -> bool:
    try:
        bot_member = await context.bot.get_chat_member(chat_id, context.bot.id)
        if bot_member.status in ["administrator"] and bot_member.can_promote_members:
            return True
        return False
    except Exception as e:
        logger.error(f"خطأ في التحقق من صلاحيات البوت: {e}")
        return False

# دالة تهجير قاعدة البيانات
def migrate_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    
    c.execute("PRAGMA table_info(users)")
    columns = [info[1] for info in c.fetchall()]
    
    if 'chat_id' not in columns:
        logger.info("يتم تهجير قاعدة البيانات لإضافة عمود chat_id...")
        
        c.execute('''CREATE TABLE users_temp (
            user_id TEXT,
            chat_id TEXT,
            username TEXT,
            xp INTEGER DEFAULT 0,
            coins INTEGER DEFAULT 0,
            level INTEGER DEFAULT 0,
            messages INTEGER DEFAULT 0,
            last_message REAL DEFAULT 0,
            daily_reward REAL DEFAULT 0,
            PRIMARY KEY (user_id, chat_id)
        )''')
        
        default_chat_id = "legacy_chat"
        c.execute('''INSERT INTO users_temp (user_id, chat_id, username, xp, coins, level, messages, last_message, daily_reward)
                     SELECT user_id, ?, username, xp, coins, level, messages, last_message, daily_reward
                     FROM users''', (default_chat_id,))
        
        c.execute('DROP TABLE users')
        c.execute('ALTER TABLE users_temp RENAME TO users')
        
        conn.commit()
        logger.info("تم تهجير قاعدة البيانات بنجاح!")
    
    conn.close()

# إعداد قاعدة البيانات
def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (
        user_id TEXT,
        chat_id TEXT,
        username TEXT,
        xp INTEGER DEFAULT 0,
        coins INTEGER DEFAULT 0,
        level INTEGER DEFAULT 0,
        messages INTEGER DEFAULT 0,
        last_message REAL DEFAULT 0,
        daily_reward REAL DEFAULT 0,
        PRIMARY KEY (user_id, chat_id)
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS settings (
        chat_id TEXT PRIMARY KEY,
        enabled INTEGER DEFAULT 1,
        xp_multiplier REAL DEFAULT 1.0,
        excluded_channels TEXT
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS shop (
        item_id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        price INTEGER,
        description TEXT
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS admin_roles (
        user_id TEXT,
        chat_id TEXT,
        expiry_date REAL,
        PRIMARY KEY (user_id, chat_id)
    )''')
    conn.commit()
    conn.close()
    migrate_db()

# تسجيل مستخدم جديد
def register_user(user_id, chat_id, username):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('INSERT OR IGNORE INTO users (user_id, chat_id, username, xp, coins, level, messages, last_message) VALUES (?, ?, ?, 0, 0, 0, 0, 0)', 
              (user_id, chat_id, username))
    conn.commit()
    conn.close()

# تحديث بيانات المستخدم
def update_user(user_id, chat_id, username, xp=0, coins=0, messages=0, last_message=0):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('INSERT OR IGNORE INTO users (user_id, chat_id, username, xp, coins, level, messages, last_message) VALUES (?, ?, ?, 0, 0, 0, 0, 0)', 
              (user_id, chat_id, username))
    c.execute('UPDATE users SET username = ?, xp = xp + ?, coins = coins + ?, messages = messages + ?, last_message = ? WHERE user_id = ? AND chat_id = ?', 
              (username, xp, coins, messages, last_message, user_id, chat_id))
    level = calculate_level(c.execute('SELECT xp FROM users WHERE user_id = ? AND chat_id = ?', (user_id, chat_id)).fetchone()[0])
    c.execute('UPDATE users SET level = ? WHERE user_id = ? AND chat_id = ?', (level, user_id, chat_id))
    conn.commit()
    conn.close()
    return level

# حساب المستوى
def calculate_level(xp):
    level = 0
    required_xp = 100
    while xp >= required_xp:
        xp -= required_xp
        level += 1
        required_xp = int(required_xp * 1.2)
    return level

# التحقق من إعدادات الجروب
def is_chat_enabled(chat_id):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('SELECT enabled FROM settings WHERE chat_id = ?', (str(chat_id),))
    result = c.fetchone()
    conn.close()
    return result[0] if result else True

# دالة بداية البوت
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if isinstance(update, Update) and update.callback_query:
        user_id = str(update.callback_query.from_user.id)
        username = update.callback_query.from_user.first_name
        chat_id = str(update.callback_query.message.chat.id)
        message = update.callback_query.message
    else:
        user_id = str(update.message.from_user.id)
        username = update.message.from_user.first_name
        chat_id = str(update.message.chat.id)
        message = update.message
    
    register_user(user_id, chat_id, username)
    
    keyboard = [
        [InlineKeyboardButton("إحصائياتي 📊", callback_data="mystats")],
        [InlineKeyboardButton("الليدربورد 🏆", callback_data="leaderboard")],
        [InlineKeyboardButton("المتجر 🛒", callback_data="shop")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await message.reply_text(
        "مرحبًا! أنا بوت الليفلينج الخارق! 🚀\n"
        "أرسل رسايل في الجروب عشان تجمع نقاط (XP) وكوينز، وترتفع مستواك!\n"
        "استخدم الأزرار تحت عشان تستكشف المزيد!",
        reply_markup=reply_markup
    )

# دالة عرض الإحصائيات (mystats/rank/levels)
async def mystats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if isinstance(update, Update) and update.callback_query:
        user_id = str(update.callback_query.from_user.id)
        username = update.callback_query.from_user.first_name
        chat_id = str(update.callback_query.message.chat.id)
        message = update.callback_query.message
    else:
        user_id = str(update.message.from_user.id)
        username = update.message.from_user.first_name
        chat_id = str(update.message.chat.id)
        message = update.message
    
    register_user(user_id, chat_id, username)
    
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('SELECT xp, coins, level, messages FROM users WHERE user_id = ? AND chat_id = ?', (user_id, chat_id))
    user_data = c.fetchone()
    conn.close()
    
    xp = user_data[0] if user_data else 0
    coins = user_data[1] if user_data else 0
    level = user_data[2] if user_data else 0
    messages = user_data[3] if user_data else 0
    required_xp = 100 * (1.2 ** level)
    
    await message.reply_text(
        f"👤 {username}\n"
        f"الرتبة: {get_rank_title(level)}\n"
        f"المستوى: {level}\n"
        f"النقاط: {xp}/{int(required_xp)} XP\n"
        f"الكوينز: {coins} 💰\n"
        f"عدد الرسايل: {messages} 📩"
    )

# دالة عرض الكوينز
async def coins(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if isinstance(update, Update) and update.callback_query:
        user_id = str(update.callback_query.from_user.id)
        username = update.callback_query.from_user.first_name
        chat_id = str(update.callback_query.message.chat.id)
        message = update.callback_query.message
    else:
        user_id = str(update.message.from_user.id)
        username = update.message.from_user.first_name
        chat_id = str(update.message.chat.id)
        message = update.message
    
    register_user(user_id, chat_id, username)
    
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('SELECT coins FROM users WHERE user_id = ? AND chat_id = ?', (user_id, chat_id))
    coins = c.fetchone()[0]
    conn.close()
    
    await message.reply_text(
        f"👤 {username}\n"
        f"الكوينز: {coins} 💰"
    )

# دالة الليدربورد
async def leaderboard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if isinstance(update, Update) and update.callback_query:
        chat_id = str(update.callback_query.message.chat.id)
        message = update.callback_query.message
    else:
        chat_id = str(update.message.chat.id)
        message = update.message

    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('SELECT user_id, username, xp, level FROM users WHERE chat_id = ? ORDER BY xp DESC LIMIT 10', (chat_id,))
    top_users = c.fetchall()
    conn.close()

    if not top_users:
        await message.reply_text("ما فيش أعضاء في الليدربورد لسه! 😊")
        return

    response = "🏆 الليدربورد:\n\n"
    for i, (user_id, username, xp, level) in enumerate(top_users, 1):
        response += f"{i}. {username}: المستوى {level} ({xp} XP) - {get_rank_title(level)}\n"

    await message.reply_text(response)

# دالة المتجر
async def shop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if isinstance(update, Update) and update.callback_query:
        message = update.callback_query.message
    else:
        message = update.message

    keyboard = [
        [InlineKeyboardButton("شراء رتبة أدمن 🛡️", callback_data="buy_admin")],
        [InlineKeyboardButton("عناصر أخرى 🛍️", callback_data="other_items")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await message.reply_text(
        "🛒 مرحبًا بك في المتجر!\n"
        "اختر من الخيارات تحت:\n"
        "- رتبة أدمن: 500 كوينز لكل يوم\n"
        "- عناصر أخرى: ألقاب وإيموجي حصرية",
        reply_markup=reply_markup
    )

# دالة شراء رتبة أدمن
async def buy_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if isinstance(update, Update) and update.callback_query:
        message = update.callback_query.message
    else:
        message = update.message

    keyboard = [
        [InlineKeyboardButton("شراء رتبة أدمن 🛡️", callback_data="buy_admin")],
        [InlineKeyboardButton("عناصر أخرى 🛍️", callback_data="other_items")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await message.reply_text(
        "🛒 مرحبًا بك في المتجر!\n"
        "اختر من الخيارات تحت:\n"
        "- رتبة أدمن: 500 كوينز لكل يوم\n"
        "- عناصر أخرى: ألقاب وإيموجي حصرية",
        reply_markup=reply_markup
    )
async def process_admin_purchase(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    user_id = str(query.from_user.id)
    chat_id = str(query.message.chat_id)
    coins_spent = int(query.data.split("_")[1])
    days = coins_spent // ADMIN_COST_PER_DAY
    
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('SELECT coins FROM users WHERE user_id = ? AND chat_id = ?', (user_id, chat_id))
    keyboard = [
        [InlineKeyboardButton("500 كوينز (يوم واحد)", callback_data="admin_500")],
        [InlineKeyboardButton("1000 كوينز (يومان)", callback_data="admin_1000")],
        [InlineKeyboardButton("1500 كوينز (3 أيام)", callback_data="admin_1500")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.message.reply_text(
        "🛡️ اختر عدد الكوينز لشراء رتبة الأدمن:\n"
        "كل 500 كوينز = يوم واحد كأدمن",
        reply_markup=reply_markup
    )
    
    # التحقق من أن المستخدم في الجروب
    try:
        member = await context.bot.get_chat_member(chat_id, int(user_id))
        if member.status in ["left", "kicked"]:
            await query.message.reply_text("لازم تكون في الجروب عشان تشتري رتبة أدمن! 🚫")
            conn.close()
            return
    except Exception:
        await query.message.reply_text("خطأ! تأكد إن البوت ليه صلاحيات في الجروب! 🚫")
        conn.close()
        return
    
    # التحقق من صلاحيات البوت
    if not await check_bot_permissions(context, chat_id):
        await query.message.reply_text("البوت ما عندوش صلاحية رفع مشرفين! اطلب من صاحب الجروب يفعل صلاحية 'تغيير صلاحيات الأعضاء' للبوت! 🚫")
        conn.close()
        return
    
    # خصم الكوينز
    c.execute('UPDATE users SET coins = coins - ? WHERE user_id = ? AND chat_id = ?', (coins_spent, user_id, chat_id))
    
    # إضافة رتبة الأدمن
    expiry_date = time.time() + (days * 86400)
    c.execute('INSERT OR REPLACE INTO admin_roles (user_id, chat_id, expiry_date) VALUES (?, ?, ?)', 
              (user_id, chat_id, expiry_date))
    conn.commit()
    conn.close()
    
    # صلاحيات الأدمن
    admin_permissions = {
        "can_change_info": False,
        "can_post_messages": True,
        "can_edit_messages": True,
        "can_delete_messages": True,
        "can_invite_users": True,
        "can_restrict_members": False,
        "can_pin_messages": True,
        "can_promote_members": False,
        "can_manage_topics": True,
        "can_manage_video_chats": True,
        "can_post_stories": True,
        "can_edit_stories": True,
        "can_delete_stories": True
    }
    
    # محاولة منح الصلاحيات باستخدام Pyrogram
    if await promote_member(chat_id, int(user_id), admin_permissions):
        await query.message.reply_text(
            f"🎉 مبروك! 🎉 اشتريت رتبة أدمن لمدة {days} يوم بـ {coins_spent} كوينز في هذا الجروب!"
        )
    else:
        await query.message.reply_text("خطأ في منح الرتبة! تأكد إن البوت ليه صلاحيات كافية أو إن الجروب ما فيهوش قيود على رفع المشرفين. 🚫")

# دالة التحقق من انتهاء رتب الأدمن
async def check_expired_admins(context: ContextTypes.DEFAULT_TYPE):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    current_time = time.time()
    c.execute('SELECT user_id, chat_id FROM admin_roles WHERE expiry_date < ?', (current_time,))
    expired_admins = c.fetchall()
    
    for user_id, chat_id in expired_admins:
        demote_permissions = {
            "can_change_info": False,
            "can_post_messages": False,
            "can_edit_messages": False,
            "can_delete_messages": False,
            "can_invite_users": False,
            "can_restrict_members": False,
            "can_pin_messages": False,
            "can_promote_members": False,
            "can_manage_topics": False,
            "can_manage_video_chats": False,
            "can_post_stories": False,
            "can_edit_stories": False,
            "can_delete_stories": False
        }
        try:
            if await promote_member(chat_id, int(user_id), demote_permissions, is_demote=True):
                await context.bot.send_message(
                    chat_id=chat_id,
                    text=f"🔔 انتهت رتبة الأدمن للمستخدم {user_id} في هذا الجروب."
                )
            c.execute('DELETE FROM admin_roles WHERE user_id = ? AND chat_id = ?', (user_id, chat_id))
        except Exception as e:
            logger.error(f"خطأ في إزالة رتبة الأدمن لـ{user_id} في {chat_id}: {e}")
        
    conn.commit()
    conn.close()

    
# دالة المكافأة يومية
async def daily(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if isinstance(update, Update) and update.callback_query:
        user_id = str(update.callback_query.from_user.id)
        username = update.callback_query.from_user.first_name
        chat_id = str(update.callback_query.message.chat_id)
        message = update.callback_query.message
    else:
        user_id = str(update.message.from_user.id)
        username = update.message.from_user.first_name
        chat_id = str(update.message.chat_id)
        message = update.message
    
    register_user((user_id, chat_id, username))
    
    current_time = time.time()
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('SELECT daily_reward FROM users WHERE user_id = ? AND chat_id = ?', (user_id, chat_id))
    last_daily = c.fetchone()
    
    if last_daily and current_time - last_daily[0] < 86400:
        remaining = int(time(86400 - (current_time - last_daily[0])))
        hours = remaining // 3600
        minutes = (remaining % 3600) // 60
        await message.reply_text(f"الاستني {hours} ساعة و{minutes} دقيقة عشان تاخد المكافأة اليومية تاني! ⏳️")
        conn.close()
        return
    
    reward_xp = random.randint(50, 100)
    reward_coins = random.randint(100, 200)
    c.execute('UPDATE users SET xp = xp + ?, coins = coins + ?, daily_reward = ? WHERE user_id = ? AND chat_id = ?', 
              (reward_xp, reward_coins, current_time, user_id, chat_id))
    conn.commit()
    conn.close()
    
    await message.reply_text(
            f"🎁 حصلت على مكافأتك اليومية في هذا الجروب!\n"
            f"+{reward_xp} XP\n"
            f"+{reward_coins} كوينز"
        )

# دالة تخصيص الرتب
def get_rank_title(level):
    ranks = {
        0: "🆕 عضو جديد",
        5: "🏅 عضو مبتدئ",
        10: "🌟 أسطورة الجروب",
        20: "👑 ملك التفاعل",
        40: "🦸‍♂️ البطل الخارق",
        70: "🎯 القناص",
        50: "🔥 المتفاعل المجنون",
        60: "🧠 العقل المدبر",
        80: "🗡️ فارس الظل",
        100: "🧙‍♂️ حكيم المجموعة",
        290: "💎 جوهرة الجروب",
        350: "🚖 منطلق بلا حدود",
        420: "🎖️ المخضرم",
        500: "📢 الصوت الأعلى",
        600: "⚔️ المحارب الحديدي",
        700: "💣 قنبلة التفاعل",
        820: "👨‍🏫 أستاذ الحوار",
        950: "💼 المدري العام",
1100: "🏆 سيد الجروب",
        1260: "🧨 صانع الضجة",
        1430: "🎮 لاعب أسطوري",
        1610: "👁️ عين المجموعة",
        1800: "🎬 نجم الشات",
        2000: "📡 المتصل الدائم",
        2210: "🔮 المتنبئ بالردود",
        2430: "👤 القائد الصامت",
        2660: "🧭 بوصلة النقاش",
        2900: "🛡️ حامي الجروب",
        3150: "🎩 الأسطوري",
        3410: "🦾 روبوت الردود",
        3680: "🛠️ المهندس الاجتماعي",
        3960: "🧃 العصير الفكري",
        4250: "📚 موسوعة الجروب",
        4550: "🪄 الساحر الذهبي",
        4860: "🌌 سيد الأكوان",
        5180: "🌀 دوامة الكلام",
        5510: "🌋 بركان التفاعل",
        5850: "🏹 رامي محترف",
        6200: "🔗 رابط الأرواح",
        6560: "🪱 حجر الأساس",
        6930: "🧬 DNA الجروب",
        7310: "🔊 المايك الذهبي",
        7700: "🎖 جامع النقاط",
        8100: "🔝 فوق الكل",
        8510: "🌈 طاقة إيجابية",
        8930: "💀 الشبح النشيط",
        9360: "⚡ كهرباء الجروب",
        9800: "🎆 الألعاب النارية",
        10250: "🧞‍♂️ الجني الخارق",
        10710: "🏛️ عميد الجروب",
        11200: "🌠 أسطورة لا تموت",
        11700: "👑🎖 الأسطورة النهائية"
    }
    for rank_level in sorted(ranks.keys(), reverse=True):
        if level >= rank_level:
            return ranks[rank_level]
    return "🆕 عضو جديد"

    

async def remove_coins(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.from_user.id not in ADMIN_IDS:
        await update.message.reply_text("مشرفين بس يقدروا يستخدموا الأمر ده! 🚫")
        return

    try:
        user_id = str(context.args[0])
        coins = int(context.args[1])
        chat_id = str(update.message.chat.id)
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute('SELECT coins FROM users WHERE user_id = ? AND chat_id = ?', (user_id, chat_id))
        user_coins = c.fetchone()
        if user_coins and user_coins[0] >= coins:
            c.execute('UPDATE users SET coins = coins - ? WHERE user_id = ? AND chat_id = ?', (coins, user_id, chat_id))
            conn.commit()
            await update.message.reply_text(f"تم خصم {coins} كوينز من {user_id} في هذا الجروب")
        else:
            await update.message.reply_text("ما عندوش كوينز كفاية! 😢")
        conn.close()
    except (IndexError, ValueError):
        await update.message.reply_text("استخدام خطأ! مثال: /removecoins 123456789 100")
        conn.close()
async def remove_xp(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.from_user.id not in ADMIN_IDS:
        await update.message.reply_text("مشرفين بس يقدروا يستخدموا الأمر ده! 🚫")
        return

    try:
        user_id = str(context.args[0])
        xp = int(context.args[1])
        chat_id = str(update.message.chat.id)
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute('SELECT xp FROM users WHERE user_id = ? AND chat_id = ?', (user_id, chat_id))
        user_xp = c.fetchone()
        if user_xp and user_xp[0] >= xp:
            c.execute('UPDATE users SET xp = xp - ? WHERE user_id = ? AND chat_id = ?', (xp, user_id, chat_id))
            level = calculate_level(c.execute('SELECT xp FROM users WHERE user_id = ? AND chat_id = ?', (user_id, chat_id)).fetchone()[0])
            c.execute('UPDATE users SET level = ? WHERE user_id = ? AND chat_id = ?', (level, user_id, chat_id))
            conn.commit()
            await update.message.reply_text(f"تم خصم {xp} XP من {user_id} في هذا الجروب")
        else:
            await update.message.reply_text("ما عندوش XP كفاية! 😢")
        conn.close()
    except (IndexError, ValueError):
        await update.message.reply_text("استخدام خطأ! مثال: /removexp 123456789 100")
        return
    
    if len(update.message.text or "") < 3:
        conn.close()
        return

    # Fetch user_data before using it
    c.execute('SELECT xp FROM users WHERE user_id = ? AND chat_id = ?', (user_id, chat_id))
    user_data = c.fetchone()

    xp_gained = random.randint(*XP_RANGE)
    coins_gained = int(xp_gained * COINS_PER_XP)
    old_level = calculate_level(user_data[0] if user_data else 0)
    current_time = time.time()
    # Ensure username is defined before use
    if isinstance(update, Update) and update.message:
        username = update.message.from_user.first_name
    elif isinstance(update, Update) and update.callback_query:
        username = update.callback_query.from_user.first_name
    else:
        username = "مستخدم"
    new_level = update_user(user_id, chat_id, username, xp_gained, coins_gained, 1, current_time)

    if new_level > old_level:
        await update.message.reply_text(
            f"🎉 مبروك يا {username}! !وصلت للمستوى {new_level} في هذا الجروب! 😊\n"
            f"الرتبة الجديدة: {get_rank_title(new_level)}"
        )

    conn.close()

    
# دالة معالجة الأزرار
async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if query.data == "mystats":
        await mystats(update, context)
    elif query.data == "leaderboard":
        await leaderboard(update, context)
    elif query.data == "shop":
        await shop(update, context)
    elif query.data == "buy_admin":
        await buy_admin(update, context)
    elif query.data.startswith("admin_"):
        await process_admin_purchase(update, context)
    elif query.data == "other_items":
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute('SELECT item_id, name, price, description FROM shop')
        items = c.fetchall()
        conn.close()
        
        if not items:
            await query.message.reply_text("ما فيش عناصر أخرى في المتجر لسه! 😢")
            return
        
        response = "🧍 العناصر الأخرى:\n"
        keyboard = []
        for item_id, name, price, description in items:
            response += f"{name} - {price} كوينز\n{description}\n\n"
            keyboard.append([InlineKeyboardButton(f"شراء {name}", callback_data=f"buy_{item_id}")])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.message.reply_text(response, reply_markup=reply_markup)
    elif query.data == "other_items":
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute('SELECT item_id, name, price, description FROM shop')
        items = c.fetchall()
        conn.close()

        if not items:
            await query.message.reply_text("ما فيش عناصر أخرى في المتجر لسه! 😢")
            return

        response = "🧍 العناصر الأخرى:\n"
        keyboard = []
        for item_id, name, price, description in items:
            response += f"{name} - {price} كوينز\n{description}\n\n"
            keyboard.append([InlineKeyboardButton(f"شراء {name}", callback_data=f"buy_{item_id}")])

        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.message.reply_text(response, reply_markup=reply_markup)

    elif query.data.startswith("buy_"):
        item_id = int(query.data.split("_")[1])
        user_id = str(query.from_user.id)
        chat_id = str(query.message.chat.id)

        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute('SELECT price FROM shop WHERE item_id = ?', (item_id,))
        price_row = c.fetchone()
        if not price_row:
            await query.message.reply_text("العنصر غير موجود!")
            conn.close()
            return
        price = price_row[0]
        c.execute('SELECT coins FROM users WHERE user_id = ? AND chat_id = ?', (user_id, chat_id))
        coins_row = c.fetchone()
        coins = coins_row[0] if coins_row else 0

        if coins >= price:
            c.execute('UPDATE users SET coins = coins - ? WHERE user_id = ? AND chat_id = ?', (price, user_id, chat_id))
            conn.commit()
            await query.message.reply_text("🎉 اشتريت العنصر بنجاح! 😊")
        else:
            await query.message.reply_text("ما عندك كوينز كفاية! 😢")

        conn.close()
    # The following HTML/CSS should be inside a string if used as a template, not as Python code.
    # Example:
    '''
    <style>
        th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
        th { background-color: #f2f2f2; }
    </style>
    </head>
    <body>
        <h1>لوحة تحكم البوت</h1>
        <h2>الأعضاء</h2>
        <table>
            <tr>
                <th>المستخدم</th>
                <th>الجروب</th>
                <th>النقاط</th>
                <th>المستوى</th>
                <th>الكوينز</th>
            </tr>
            {% for user in users %}
            <tr>
                <td>{{ user[2] }}</td>
                <td>{{ user[1] }}</td>
                <td>{{ user[3] }}</td>
                <td>{{ user[4] }}</td>
                <td>{{ user[5] }}</td>
            </tr>
            {% endfor %}
        </table>
        <h2>رتب الأدمن</h2>
        <table>
            <tr>
                <th>المستخدم</th>
                <th>الجروب</th>
                <th>تاريخ الانتهاء</th>
            </tr>
            {% for role in admin_roles %}
            <tr>
                <td>{{ role[0] }}</td>
                <td>{{ role[1] }}</td>
                <td>{{ role[2] | timestamp_to_date }}</td>
            </tr>
            {% endfor %}
        </table>
    </body>
    </html>
    '''
    # If you are using Flask's render_template_string, make sure the HTML is passed as a string argument.

def run_flask():
    app = Flask(__name__)
    app.run(host='0.0.0.0', port=5001)

async def main():
    init_db()
    
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('INSERT OR IGNORE INTO shop (name, price, description) VALUES (?, ?, ?)', 
              ("لقب مميز", 500, "لقب يظهر جنب اسمك"))
    c.execute('INSERT OR IGNORE INTO shop (name, price, description) VALUES (?, ?, ?)', 
              ("إيموجي حصري", 300, "إيموجي مخصص"))
    conn.commit()
    conn.close()
    
    flask_thread = threading.Thread(target=run_flask)
    flask_thread.daemon = True
    flask_thread.start()
    
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler(["rank", "levels", "mystats"], mystats))
    app.add_handler(CommandHandler("coins", coins))
    app.add_handler(CommandHandler(["leaderboard", "top"], leaderboard))
    app.add_handler(CommandHandler("shop", shop))
    app.add_handler(CommandHandler("daily", daily))
    # تعريف دالة set_xp لإعطاء XP للمستخدم (مشرفين فقط)
    async def set_xp(update: Update, context: ContextTypes.DEFAULT_TYPE):
        if update.message.from_user.id not in ADMIN_IDS:
            await update.message.reply_text("مشرفين فقط يمكنهم استخدام هذا الأمر! 🚫")
            return
        try:
            user_id = str(context.args[0])
            xp = int(context.args[1])
            chat_id = str(update.message.chat.id)
            conn = sqlite3.connect(DB_FILE)
            c = conn.cursor()
            c.execute('UPDATE users SET xp = ? WHERE user_id = ? AND chat_id = ?', (xp, user_id, chat_id))
            level = calculate_level(xp)
            c.execute('UPDATE users SET level = ? WHERE user_id = ? AND chat_id = ?', (level, user_id, chat_id))
            conn.commit()
            await update.message.reply_text(f"تم تعيين {xp} XP للمستخدم {user_id} في هذا الجروب.")
            conn.close()
        except (IndexError, ValueError):
            await update.message.reply_text("استخدام خطأ! مثال: /setxp 123456789 100")
            return

    app.add_handler(CommandHandler("setxp", set_xp))

    # تعريف دالة add_coins لإضافة كوينز للمستخدم (مشرفين فقط)
    async def add_coins(update: Update, context: ContextTypes.DEFAULT_TYPE):
        if update.message.from_user.id not in ADMIN_IDS:
            await update.message.reply_text("مشرفين فقط يمكنهم استخدام هذا الأمر! 🚫")
            return
        try:
            user_id = str(context.args[0])
            coins = int(context.args[1])
            chat_id = str(update.message.chat.id)
            conn = sqlite3.connect(DB_FILE)
            c = conn.cursor()
            c.execute('UPDATE users SET coins = coins + ? WHERE user_id = ? AND chat_id = ?', (coins, user_id, chat_id))
            conn.commit()
            await update.message.reply_text(f"تم إضافة {coins} كوينز للمستخدم {user_id} في هذا الجروب.")
            conn.close()
        except (IndexError, ValueError):
            await update.message.reply_text("استخدام خطأ! مثال: /addcoins 123456789 100")
            return

    app.add_handler(CommandHandler("addcoins", add_coins))
    app.add_handler(CommandHandler("removecoins", remove_coins))
    app.add_handler(CommandHandler("removexp", remove_xp))
    # تعريف دالة handle_message لمعالجة الرسائل النصية
    async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not update.message:
            return
        user_id = str(update.message.from_user.id)
        username = update.message.from_user.first_name
        chat_id = str(update.message.chat.id)
        current_time = time.time()

        # تحقق من تفعيل الجروب
        if not is_chat_enabled(chat_id):
            return

        # تسجيل المستخدم إذا لم يكن موجودًا
        register_user(user_id, chat_id, username)

        # تحقق من الكولداون
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute('SELECT last_message, xp FROM users WHERE user_id = ? AND chat_id = ?', (user_id, chat_id))
        user_data = c.fetchone()
        last_message_time = user_data[0] if user_data else 0
        if current_time - last_message_time < COOLDOWN:
            conn.close()
            return

        if len(update.message.text or "") < 3:
            conn.close()
            return

        xp_gained = random.randint(*XP_RANGE)
        coins_gained = int(xp_gained * COINS_PER_XP)
        old_level = calculate_level(user_data[1] if user_data else 0)

        new_level = update_user(user_id, chat_id, username, xp_gained, coins_gained, 1, current_time)

        if new_level > old_level:
            await update.message.reply_text(
                f"🎉 مبروك يا {username}! !وصلت للمستوى {new_level} في هذا الجروب! 😊\n"
                f"الرتبة الجديدة: {get_rank_title(new_level)}"
            )

        conn.close()

    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(CallbackQueryHandler(button))
    
    app.job_queue.run_repeating(check_expired_admins, interval=CHECK_EXPIRED_ADMINS_INTERVAL)
    
    logger.info("البوت شغال...")
    await pyro_client.start()
    await app.run_polling()

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
