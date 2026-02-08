import json
import os
import base64
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes

# ================== CONFIG ==================
API_KEY = "8426836407:AAHoXkQakddqyXZ_olNplG0_ov-3fhvrkSc"
ADMIN_ID = 5775388579
BOT_USERNAME = "YourBotUsername"  # Telegram bot username
KINO_CHANNEL = "kinomandabor"  # Kino kanali username

# Data storage (DB o‘rniga JSON)
DATA_FILE = "data.json"
SETTINGS_FILE = "settings.json"

# ================== HELPER FUNCTIONS ==================

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def load_settings():
    if os.path.exists(SETTINGS_FILE):
        with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"last_kino_id": 0, "reklama": ""}

def save_settings(settings):
    with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
        json.dump(settings, f, ensure_ascii=False, indent=2)

def join_check(user_id: int):
    """
    Foydalanuvchi majburiy kanalga obuna bo‘lganini tekshiradi.
    """
    # Inline tugma
    key = [
        [InlineKeyboardButton(f"📢 Obuna bo'ling: @{KINO_CHANNEL}", url=f"https://t.me/{KINO_CHANNEL}")],
        [InlineKeyboardButton("✅ Obuna bo'ldim", callback_data="check_subscription")]
    ]
    return InlineKeyboardMarkup(key)

# ================== HANDLERS ==================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    chat_id = update.effective_chat.id

    data = load_data()
    if str(chat_id) not in data:
        data[str(chat_id)] = {"last_msg": "start", "ban": False}
        save_data(data)

    now = datetime.now().strftime("%d.%m.%Y | %H:%M")
    text = f"Salom, {user.first_name}! 🎬\n\nBotimizga xush kelibsiz.\n\nSoat: {now}"
    await context.bot.send_message(chat_id, text, reply_markup=join_check(chat_id))

async def check_subscription(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    chat_id = query.from_user.id
    # Foydalanuvchi obuna bo‘lsa kino kodini yuborish
    member = await context.bot.get_chat_member(chat_id=f"@{KINO_CHANNEL}", user_id=chat_id)
    if member.status in ["member", "administrator", "creator"]:
        # Foydalanuvchi obuna bo‘lgan
        data = load_data()
        last_kino_id = load_settings().get("last_kino_id", 0)
        if last_kino_id > 0:
            # Kino kodi
            kino_data = load_data().get(str(last_kino_id), {})
            fname = kino_data.get("name", "No name")
            f_id = kino_data.get("file_id")
            reklama = load_settings().get("reklama", "")
            if f_id:
                await context.bot.send_video(chat_id=chat_id, video=f_id, caption=f"<b>{fname}</b>\n\n{reklama}")
            else:
                await context.bot.send_message(chat_id, "Kino hali mavjud emas.")
        else:
            await context.bot.send_message(chat_id, "Hozircha kino kodi mavjud emas.")
    else:
        await context.bot.send_message(chat_id, "❌ Siz hali kanalga obuna bo‘lmadingiz!", reply_markup=join_check(chat_id))

# ================== ADMIN HANDLERS ==================

async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    if chat_id != ADMIN_ID:
        return
    keyboard = [
        ["🎬 Kino qo'shish", "🗑️ Kino o'chirish"],
        ["📢 Kanal sozlash", "📈 Reklama"],
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await context.bot.send_message(chat_id, "👨‍💻 Admin panel:", reply_markup=reply_markup)

async def add_movie(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    if chat_id != ADMIN_ID:
        return
    await context.bot.send_message(chat_id, "🎬 Videoni yuboring:")
    context.user_data["step"] = "add_movie"

async def receive_movie(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    if chat_id != ADMIN_ID:
        return
    if context.user_data.get("step") == "add_movie":
        video = update.message.video
        if video:
            f_id = video.file_id
            context.user_data["video_id"] = f_id
            await context.bot.send_message(chat_id, "🎬 Kino nomini yuboring:")
            context.user_data["step"] = "add_movie_name"
        else:
            await context.bot.send_message(chat_id, "⚠️ Video yuboring!")

async def receive_movie_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    if chat_id != ADMIN_ID:
        return
    if context.user_data.get("step") == "add_movie_name":
        name = update.message.text
        f_id = context.user_data.get("video_id")
        settings = load_settings()
        last_kino_id = settings.get("last_kino_id", 0) + 1
        settings["last_kino_id"] = last_kino_id
        save_settings(settings)

        data = load_data()
        data[str(last_kino_id)] = {"file_id": f_id, "name": name}
        save_data(data)

        await context.bot.send_message(chat_id, f"✅ Kino qo‘shildi! Kod: {last_kino_id}")
        context.user_data.clear()

# ================== MAIN ==================

def main():
    app = ApplicationBuilder().token(API_KEY).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("panel", admin_panel))
    app.add_handler(CallbackQueryHandler(check_subscription, pattern="check_subscription"))
    app.add_handler(MessageHandler(filters.Video.ALL, receive_movie))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), receive_movie_name))

    print("Bot ishlayapti...")
    app.run_polling()

if __name__ == "__main__":
    main()
