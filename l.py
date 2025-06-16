from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from supabase import create_client
from datetime import datetime, timedelta

API_ID = 22696039
API_HASH = "00f9cc1d3419e879013f7a9d2d9432e2"
BOT_TOKEN = "7788824693:AAGiawVus73If8IoAU8kOV3cT4ZUMhxoHtA"
SUPABASE_URL = "https://wqhmhwuqztdjglgqwkdw.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6IndxaG1od3VxenRkamdsZ3F3a2R3Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDk4OTMwNDgsImV4cCI6MjA2NTQ2OTA0OH0.8Cd1cQuXMOXkQwOVNYeX6RL2Fjw25JxY5DtbATIRQB8"

OWNER_ID = 7089656746
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

ADMIN_PRICES = {
    "1": {"days": 1, "coins": 2000},
    "2": {"days": 2, "coins": 4000},
    "3": {"days": 3, "coins": 6000}
}

# خيارات الاستبدال (Normal Exchange)
EXCHANGE_OPTIONS = [
    {"xp": 1000, "coins": 200},
    {"xp": 2000, "coins": 400},
    {"xp": 3000, "coins": 600},
    {"xp": 6000, "coins": 1000}
]

def xp_msg(name, level, level_name, xp, next_xp, coins, user_id, username):
    return (
        f"🪪 مستواك في الجروب:\n"
        f"👤 الاسم: <a href=\"tg://user?id={user_id}\">{username}</a>\n"
        f"🏅 المستوى: {level} - {level_name}\n"
        f"🧙‍♂️ الخبرة : {xp}/{next_xp}\n"
        f"💰 الكوينز: {coins}\n"
    )

async def get_or_create_user(user_id, group_id, username):
    res = supabase.table("group_members").select("*").eq("user_id", user_id).eq("group_id", group_id).execute()
    user = res.data[0] if res.data else None
    if user:
        return user
    else:
        # المستخدم غير موجود، أضفه
        new_user = {
            "user_id": user_id,
            "group_id": group_id,
            "username": username,
            "xp": 0,
            "coins": 0,
            "level": 1
        }
        supabase.table("group_members").insert(new_user).execute()
        return new_user

async def get_user_stats(user_id, group_id):
    res = supabase.table("group_members").select("*").eq("user_id", user_id).eq("group_id", group_id).execute()
    user = res.data[0] if res.data else None
    if user:
        lvl = user.get("level", 1)
        current_level_obj = supabase.table("levels").select("*").eq("id", lvl).execute().data
        level_name = current_level_obj[0]["name"] if current_level_obj else "بدون اسم"
        next_lvl = lvl + 1
        level_obj = supabase.table("levels").select("*").eq("id", next_lvl).execute().data
        next_xp = level_obj[0]["required_xp"] if level_obj else (user.get("xp", 0) + 100)
        return {
            "name": user.get("username", "بدون اسم"),
            "level": lvl,
            "level_name": level_name,
            "xp": user.get("xp", 0),
            "next_xp": next_xp,
            "coins": user.get("coins", 0)
        }
    else:
        return {
            "name": "بدون اسم",
            "level": 1,
            "level_name": "بدون اسم",
            "xp": 0,
            "next_xp": 100,
            "coins": 0
        }

async def update_user_xp(user_id, group_id, username, plus_xp=30, plus_coins=10):
    user = await get_or_create_user(user_id, group_id, username)
    new_xp = user.get("xp", 0) + plus_xp
    new_coins = user.get("coins", 0) + plus_coins
    lvl = user.get("level", 1)
    levels = supabase.table("levels").select("*").order("id").execute().data
    next_level = lvl + 1
    next_level_obj = next((l for l in levels if l["id"] == next_level), None)
    congrats = None
    if next_level_obj and new_xp >= next_level_obj["required_xp"]:
        lvl += 1
        level_congrats = next_level_obj.get("congratulation", "مبروك وصلت لمستوى جديد!")
        level_name = next_level_obj.get("name", "")
        congrats = f"🥳 تهانينا <a href=\"tg://user?id={user_id}\">{username}</a> وصلت للمستوى {lvl} - {level_name}!\n{level_congrats}"
        supabase.table("group_members").update(
            {"xp": new_xp, "coins": new_coins, "level": lvl}
        ).eq("user_id", user_id).eq("group_id", group_id).execute()
    else:
        supabase.table("group_members").update(
            {"xp": new_xp, "coins": new_coins}
        ).eq("user_id", user_id).eq("group_id", group_id).execute()
    return congrats

async def update_user_coins(user_id, group_id, plus_coins):
    user = await get_or_create_user(user_id, group_id, None)
    new_coins = user.get("coins", 0) + plus_coins
    supabase.table("group_members").update(
        {"coins": new_coins}
    ).eq("user_id", user_id).eq("group_id", group_id).execute()
    return new_coins

async def buy_admin(user_id, group_id, username, days, price):
    user = await get_or_create_user(user_id, group_id, username)
    if user.get("coins", 0) < price:
        return False, None, None
    expire_date = datetime.utcnow() + timedelta(days=days)
    supabase.table("group_members").update({
        "coins": user["coins"] - price,
        "is_admin": True,
        "admin_expiry": expire_date.isoformat()
    }).eq("user_id", user_id).eq("group_id", group_id).execute()
    supabase.table("purchases").insert({
        "user_id": user_id,
        "group_id": group_id,
        "item_type": "admin",
        "duration_days": days,
        "start_at": datetime.utcnow().isoformat(),
        "end_at": expire_date.isoformat(),
        "is_active": True
    }).execute()
    msg = (
        f"✅ تم الدفع بواسطة: <a href=\"tg://user?id={user_id}\">{username}</a>\n"
        f"💰 المبلغ: {price} كوينز\n"
        f"📅 تاريخ الشراء: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}\n"
        f"⏳ تاريخ الانتهاء: {expire_date.strftime('%Y-%m-%d %H:%M:%S')}\n"
        f"تواصل مع @Mavdiii وهو هيرفعك فورًا\n"
        f"💬 شكراً لتفاعلك!"
    )
    return True, f"🎉 مبروك! أصبحت أدمن لمدة {days} يوم. استخدم صلاحيتك بحكمة!", msg

app = Client(
    "mybot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

@app.on_message(filters.command("start"))
async def start_cmd(client, message):
    welcome_text = (
    "👋 أهلًا بيك في مجتمع المعرفة والتطوير!\n"
    "📚 هنا بنسأل، بنجاوب، ونتعلم من بعض بكل حب واحترام.\n\n"
    "💬 إسأل أي سؤال، شارك تجربة، أو قدّم نصيحة – كل مشاركة ليها قيمة.\n"
    "💡 كل تفاعل بيكسبك نقاط وكوينز تقدر تستخدمها في المتجر تشتري بيها حاجات مميزة زي أدمن فالجروب 🥷🏽!\n\n"
    "🔍 تابع تقدمك بـ الأمر : /XP\n"
    "🛒 افتح المتجر بـ : /SHOP\n\n"
    "🚀 وجودك معانا إضافة كبيرة، خليك دايمًا فعال وافتكر اننا كلنا فى ضهرك 💪\n\n"
    
)
    await message.reply_text(welcome_text)

@app.on_message(filters.command("xp") & filters.group)
async def xp_cmd(client, message):
    user = message.from_user
    stats = await get_user_stats(user.id, message.chat.id)
    await message.reply_text(
        xp_msg(
            name=user.first_name,
            level=stats["level"],
            level_name=stats["level_name"],
            xp=stats["xp"],
            next_xp=stats["next_xp"],
            coins=stats["coins"],
            user_id=user.id,
            username=user.first_name
        )
    )

@app.on_message(filters.command("coins") & filters.group)
async def coins_cmd(client, message):
    user = message.from_user
    res = supabase.table("group_members").select("coins").eq("user_id", user.id).eq("group_id", message.chat.id).execute()
    user_data = res.data[0] if res.data else None
    coins = user_data["coins"] if user_data else 0
    await message.reply_text(f"💰 عدد الكوينز معاك: {coins}")

@app.on_message(filters.command("shop") & filters.group)
async def shop_cmd(client, message):
    user_id = message.from_user.id
    username = message.from_user.first_name
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🛡 شراء أدمن", callback_data=f"shop_admin_{user_id}_{username}")],
        [InlineKeyboardButton("Exchange 🔁", callback_data=f"exchange_menu_{user_id}_{username}")]
    ])
    await message.reply_text(
        f"🛒 **أهلاً بيك يا** <a href=\"tg://user?id={user_id}\">{username}</a> **في المتجر بتاعنا!**\n\nدلوقتي تقدر تشتري **رتبة أدمن مؤقت** في الجروب باستخدام الكوينز 💰 اللي جمّعتها من نشاطك!\n\n🔄 **لو مش معاك كوينز كفاية، استبدل الـ XP بتوعك بكوينز عن طريق زر Exchange بالأسفل**\n👑 **ولما تجمع كوينز كفاية، اطلب الأدمن من هنا مباشرة.**",
        reply_markup=keyboard
    )

@app.on_callback_query(filters.regex(r"shop_admin_(\d+)_(.+)"))
async def shop_admin_menu(client, callback_query):
    owner_id = int(callback_query.data.split("_")[2])
    owner_name = callback_query.data.split("_", 3)[3]
    user_id = callback_query.from_user.id
    user_name = callback_query.from_user.first_name
    
    if user_id != owner_id:
        await callback_query.answer(
            f"عذرا الامر مخصص فقط للمستخدم : {owner_name}",
            show_alert=True
        )
        return
    
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("1 يوم - 2000 كوينز", callback_data=f"buy_admin_1_{owner_id}_{owner_name}")],
        [InlineKeyboardButton("2 يوم - 4000 كوينز", callback_data=f"buy_admin_2_{owner_id}_{owner_name}")],
        [InlineKeyboardButton("3 أيام - 6000 كوينز", callback_data=f"buy_admin_3_{owner_id}_{owner_name}")]
    ])
    
    # تعديل الرسالة بدلاً من حذفها وإرسال رسالة جديدة
    await callback_query.edit_message_text(
        "اختر مدة الأدمن التي ترغب بها:",
        reply_markup=keyboard
    )

@app.on_callback_query(filters.regex(r"buy_admin_(\d+)_(\d+)_(.+)"))
async def buy_admin_cb(client, callback_query):
    data = callback_query.data.split("_")
    days = int(data[2])
    owner_id = int(data[3])
    owner_name = "_".join(data[4:])
    user_id = callback_query.from_user.id
    user_name = callback_query.from_user.first_name
    
    if user_id != owner_id:
        await callback_query.answer(
            f"عذرا الامر مخصص فقط للمستخدم : {owner_name}",
            show_alert=True
        )
        return
        
    price = ADMIN_PRICES[str(days)]["coins"]
    ok, msg, pay_msg = await buy_admin(
        user_id, callback_query.message.chat.id, user_name, days, price
    )
    
    if ok:
        # تعديل الرسالة أولاً لإزالة الأزرار
        await callback_query.edit_message_text(msg)
        # ثم إرسال رسالة الدفع
        await callback_query.message.reply_text(pay_msg)
    else:
        await callback_query.answer("معندكش كوينز كفاية!", show_alert=True)

@app.on_callback_query(filters.regex(r"exchange_menu_(\d+)_(.+)"))
async def exchange_menu(client, callback_query):
    user_id = int(callback_query.data.split("_")[2])
    user_name = callback_query.data.split("_", 3)[3]
    from_user = callback_query.from_user
    
    if from_user.id != user_id:
        await callback_query.answer(
            f"عذرا الامر مخصص فقط للمستخدم : {user_name}",
            show_alert=True
        )
        return
    
    # قائمة أزرار خيارات الاستبدال
    exchange_buttons = [
        [InlineKeyboardButton(f"{opt['xp']} XP ➡️ {opt['coins']} Coins", callback_data=f"exchange_xp_{opt['xp']}_{opt['coins']}_{user_id}_{user_name}")]
        for opt in EXCHANGE_OPTIONS
    ]
    
    # تعديل الرسالة بدلاً من حذفها وإرسال رسالة جديدة
    await callback_query.edit_message_text(
        "💱 اختر كمية XP التي تريد استبدالها بكوينز ",
        reply_markup=InlineKeyboardMarkup(exchange_buttons)
    )

@app.on_callback_query(filters.regex(r"exchange_xp_(\d+)_(\d+)_(\d+)_(.+)"))
async def exchange_xp_to_coins(client, callback_query):
    parts = callback_query.data.split("_")
    xp_needed = int(parts[2])
    coins_reward = int(parts[3])
    user_id = int(parts[4])
    user_name = "_".join(parts[5:])
    from_user = callback_query.from_user

    if from_user.id != user_id:
        await callback_query.answer(
            f"عذرا الامر مخصص فقط للمستخدم : {user_name}",
            show_alert=True
        )
        return

    res = supabase.table("group_members").select("*").eq("user_id", user_id).eq("group_id", callback_query.message.chat.id).execute()
    user_data = res.data[0] if res.data else None
    if not user_data:
        await callback_query.answer("لم يتم العثور على بياناتك!", show_alert=True)
        return

    xp = user_data.get("xp", 0)
    coins = user_data.get("coins", 0)

    if xp < xp_needed:
        await callback_query.answer(f"رصيدك من XP غير كافي! لازم {xp_needed} XP على الأقل.", show_alert=True)
        return

    # تحديث البيانات في قاعدة البيانات
    supabase.table("group_members").update(
        {"xp": xp - xp_needed, "coins": coins + coins_reward}
    ).eq("user_id", user_id).eq("group_id", callback_query.message.chat.id).execute()

    # تعديل الرسالة لإظهار نتيجة الاستبدال
    success_msg = (
        f"✅ تم استبدال {xp_needed} XP بـ {coins_reward} كوينز بنجاح!\n\n"
        f"💰 رصيدك الجديد:\n"
        f"🪙 الكوينز: {coins + coins_reward}\n"
        f"⭐ الخبرة: {xp - xp_needed}"
    )
    
    await callback_query.edit_message_text(success_msg)

@app.on_message(filters.group & ~filters.command(["xp", "shop", "coins"]))
async def add_xp(client, message):
    if message.from_user and not message.from_user.is_bot:
        user_id = message.from_user.id
        user_name = message.from_user.first_name
        if message.text and len(message.text) > 50:
            xp = 40
            coins = 20
        else:
            xp = 30
            coins = 10
        congrats = await update_user_xp(
            user_id, message.chat.id, user_name,
            plus_xp=xp, plus_coins=coins
        )
        if congrats:
            await message.reply_text(congrats)

@app.on_message(filters.command("addcoins") & filters.user(OWNER_ID) & filters.group)
async def owner_add_coins(client, message):
    try:
        if message.reply_to_message:
            user_id = message.reply_to_message.from_user.id
            amount = int(message.command[1]) if len(message.command) > 1 else None
        else:
            if len(message.command) < 3:
                await message.reply_text("استعمال الأمر: /addcoins <user_id> <amount> أو ريبلاي + /addcoins <amount>")
                return
            user_id = int(message.command[1])
            amount = int(message.command[2])
        await update_user_coins(user_id, message.chat.id, amount)
        await message.reply_text(f"✅ تمت إضافة {amount} كوينز لعضو ID: {user_id}")
    except Exception as e:
        await message.reply_text(f"❌ خطأ: {e}")

if __name__ == "__main__":
    print("Bot is running...")
    app.run()