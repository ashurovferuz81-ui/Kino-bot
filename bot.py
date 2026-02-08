import asyncio
import base64
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters

# ================== SOZLAMALAR ==================
BOT_TOKEN = "8501918863:AAE6YCS4j3z0JM9RcpmNXVtk2Kh1qUfABRQ"  # Sening bot tokening
ADMIN_ID = 5775388579  # Sening ID
BOT_USERNAME = "Sardorbeko008_bot"  # Sening bot username (faqat info uchun)
KINO_CHANNEL = "@kino_channel"  # Kino kanali username

# In-memory saqlash (DB kerak emas)
users = {}  # {user_id: {"step":..., "ban":..., "lastmsg":...}}
kino_posts = {}  # {kino_code: {"file_id":..., "caption":...}}
kino_counter = 1
deleted_counter = 0

# ================== FUNKSIYALAR ==================
def get_time():
    now = datetime.now()
    return now.strftime("%d.%m.%Y | %H:%M")

def reply_keyboard(keyboard):
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def inline_keyboard(buttons):
    return InlineKeyboardMarkup(buttons)

async def send_message(update: Update, text, keyboard=None):
    await update.message.reply_text(text, reply_markup=keyboard, parse_mode="HTML")

async def send_video(update: Update, file_id, caption="", keyboard=None):
    await update.message.reply_video(file_id, caption=caption, reply_markup=keyboard, parse_mode="HTML")

async def send_photo(update: Update, file_id, caption="", keyboard=None):
    await update.message.reply_photo(file_id, caption=caption, reply_markup=keyboard, parse_mode="HTML")

# ================== BOT HANDLERLARI ==================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.chat.id
    users.setdefault(user_id, {"step": "0", "ban": 0, "lastmsg": "start"})
    await send_message(update, f"Salom <b>{update.message.from_user.first_name}</b>!\nBot ishga tayyor ✅")

async def panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.chat.id
    if user_id != ADMIN_ID:
        await send_message(update, "❌ Siz admin emassiz!")
        return
    keyboard = reply_keyboard([
        ["📊 Statistika", "🔍 Searching"],
        ["🎬 Kino qo'shish", "🗑️ Kino o'chirish"],
        ["👨‍💼 Adminlar", "📢 Kanallar"]
    ])
    await send_message(update, "👨🏻‍💻 Boshqaruv paneliga xush kelibsiz!", keyboard)

async def add_kino(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.chat.id
    if user_id != ADMIN_ID:
        return
    users[user_id]["step"] = "movie"
    await send_message(update, "🎬 Kinoni yuboring (video yoki foto):", reply_keyboard([["◀️ Orqaga"]]))

async def handle_media(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.chat.id
    step = users.get(user_id, {}).get("step", "0")
    if step == "movie":
        if update.message.video:
            file_id = update.message.video.file_id
            users[user_id]["file_id"] = file_id
            users[user_id]["step"] = "caption"
            await send_message(update, "🎬 Kino malumotini yuboring:", reply_keyboard([["◀️ Orqaga"]]))
        elif update.message.photo:
            file_id = update.message.photo[-1].file_id
            users[user_id]["file_id"] = file_id
            users[user_id]["step"] = "caption"
            await send_message(update, "🎬 Kino malumotini yuboring:", reply_keyboard([["◀️ Orqaga"]]))
        else:
            await send_message(update, "⚠️ Faqat video yoki rasm yuboring!")

    elif step == "caption":
        global kino_counter
        file_id = users[user_id].get("file_id")
        caption = update.message.text
        kino_posts[kino_counter] = {"file_id": file_id, "caption": caption}
        inline_kb = inline_keyboard([[InlineKeyboardButton("🎞️ Kanalga yuborish", callback_data=f"channel_{kino_counter}")]])
        await send_video(update, file_id, caption=f"<b>{caption}</b>", keyboard=inline_kb)
        kino_counter += 1
        users[user_id]["step"] = "0"

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    if data.startswith("channel_"):
        code = int(data.split("_")[1])
        kino = kino_posts.get(code)
        if kino:
            await context.bot.send_video(chat_id=KINO_CHANNEL, video=kino["file_id"],
                                         caption=f"🎬 <b>Kino kodi:</b> <code>{code}</code>\n\n✅ Botga joylandi!")
            await query.edit_message_text(f"✅ Kino kanalga yuborildi!\n🎬 Kino kodi: {code}")

async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.chat.id
    if user_id != ADMIN_ID:
        return
    total_users = len(users)
    active_users = len([u for u in users.values() if u["ban"] == 0])
    total_kino = len(kino_posts)
    await send_message(update, f"📊 Statistika:\n• Foydalanuvchilar: {total_users}\n• Faol: {active_users}\n• Kinolar: {total_kino}")

async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    user_id = update.message.chat.id
    if text == "/start":
        await start(update, context)
    elif text in ["📊 Statistika"]:
        await stats(update, context)
    elif text in ["🎬 Kino qo'shish"]:
        await add_kino(update, context)
    elif text in ["◀️ Orqaga"]:
        users[user_id]["step"] = "0"
        await send_message(update, "⏹️ Orqaga qaytdingiz.")

# ================== BOTNI ISHLATISH ==================
app = ApplicationBuilder().token(BOT_TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.TEXT | filters.VIDEO | filters.PHOTO, handle_media))
app.add_handler(MessageHandler(filters.TEXT, message_handler))
app.add_handler(CallbackQueryHandler(button_handler))

print("Bot ishga tushdi ✅")
app.run_polling()
