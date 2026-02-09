import sqlite3
import nest_asyncio
from telegram import Update, ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup, Chat
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes

nest_asyncio.apply()

# ===== CONFIG =====
TOKEN = "8426836407:AAHoXkQakddqyXZ_olNplG0_ov-3fhvrkSc"
ADMIN_ID = 5775388579

# ===== DATABASE =====
conn = sqlite3.connect("super_elite_kino.db", check_same_thread=False)
cur = conn.cursor()

# Kinolar
cur.execute("CREATE TABLE IF NOT EXISTS movies(code TEXT PRIMARY KEY, file_id TEXT, name TEXT)")
# Majburiy kanallar
cur.execute("CREATE TABLE IF NOT EXISTS channels(channel_id TEXT PRIMARY KEY)")
# Foydalanuvchilar
cur.execute("CREATE TABLE IF NOT EXISTS users(user_id TEXT PRIMARY KEY)")

conn.commit()

# ===== ADMIN KEYBOARD =====
def admin_keyboard():
    keyboard = [
        ["🎬 Kino qo‘shish", "🗑 Kino o‘chirish"],
        ["📢 Kanal qo‘shish", "❌ Kanal o‘chirish"],
        ["👥 Userlar", "📊 Statistika"]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

# ===== CHECK SUBSCRIPTION =====
async def not_subscribed(user_id, context):
    cur.execute("SELECT channel_id FROM channels")
    channels = cur.fetchall()
    not_joined = []

    for ch in channels:
        channel = ch[0]
        try:
            member = await context.bot.get_chat_member(channel, user_id)
            if member.status in ["left", "kicked"]:
                not_joined.append(channel)
        except:
            not_joined.append(channel)

    return not_joined

# ===== START =====
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    cur.execute("INSERT OR IGNORE INTO users VALUES(?)", (user_id,))
    conn.commit()

    if update.effective_user.id == ADMIN_ID:
        await update.message.reply_text("🔥 ADMIN PANEL", reply_markup=admin_keyboard())
        return

    missing = await not_subscribed(user_id, context)
    if missing:
        buttons = []
        for ch in missing:
            try:
                chat = await context.bot.get_chat(ch)
                username = chat.username
                url = f"https://t.me/{username}" if username else f"https://t.me/+{str(ch).replace('-100','')}"
            except:
                continue
            buttons.append([InlineKeyboardButton("📢 Kanalga kirish", url=url)])
        buttons.append([InlineKeyboardButton("✅ Obuna bo‘ldim", callback_data="check_sub")])
        await update.message.reply_text(
            "📢 Kanallarga obuna bo‘ling:",
            reply_markup=InlineKeyboardMarkup(buttons)
        )
        return

    await update.message.reply_text("🎬 Kino kodini yuboring:")

# ===== BUTTON CALLBACK =====
async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    missing = await not_subscribed(query.from_user.id, context)

    if missing:
        await query.answer("❌ Hali obuna bo‘lmagansiz!", show_alert=True)
        return

    await query.message.edit_text("✅ Endi kino kodini yuboring!")

# ===== VIDEO UPLOAD =====
async def video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return

    step = context.user_data.get("step")
    if step == "video":
        context.user_data["file"] = update.message.video.file_id
        context.user_data["step"] = "name"
        await update.message.reply_text("🎬 Kino nomini yozing:")

# ===== FORWARD CHANNEL ADD (PRIVATE/PUBLIC) =====
async def forward_channel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return

    if context.user_data.get("step") != "add_channel":
        return

    msg = update.message
    if msg.forward_from_chat and msg.forward_from_chat.type == Chat.CHANNEL:
        channel_id = str(msg.forward_from_chat.id)
        cur.execute("INSERT OR IGNORE INTO channels VALUES(?)", (channel_id,))
        conn.commit()
        context.user_data.clear()
        await update.message.reply_text(
            "✅ Private/Public kanal muvaffaqiyatli qo‘shildi!",
            reply_markup=admin_keyboard()
        )
    else:
        await update.message.reply_text("❌ Kanal postini forward qiling!")

# ===== MESSAGES HANDLER =====
async def messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    user_id = update.effective_user.id
    step = context.user_data.get("step")

    # ===== ADMIN =====
    if user_id == ADMIN_ID:
        if text == "🎬 Kino qo‘shish":
            context.user_data["step"] = "code"
            await update.message.reply_text("Kino kodini yuboring:")
            return

        if step == "code":
            context.user_data["code"] = text
            context.user_data["step"] = "video"
            await update.message.reply_text("Endi videoni yuboring:")
            return

        if step == "name":
            cur.execute(
                "INSERT OR REPLACE INTO movies VALUES(?,?,?)",
                (context.user_data["code"], context.user_data["file"], text)
            )
            conn.commit()
            context.user_data.clear()
            await update.message.reply_text("✅ Kino saqlandi!", reply_markup=admin_keyboard())
            return

        if text == "🗑 Kino o‘chirish":
            context.user_data["step"] = "del_movie"
            await update.message.reply_text("O‘chirish uchun kod yuboring:")
            return

        if step == "del_movie":
            cur.execute("DELETE FROM movies WHERE code=?", (text,))
            conn.commit()
            context.user_data.clear()
            await update.message.reply_text("✅ Kino o‘chirildi!", reply_markup=admin_keyboard())
            return

        if text == "📢 Kanal qo‘shish":
            context.user_data["step"] = "add_channel"
            await update.message.reply_text("📢 Kanal postini FORWARD qiling:")
            return

        if text == "❌ Kanal o‘chirish":
            context.user_data["step"] = "del_channel"
            await update.message.reply_text("@username / link / ID yuboring:")
            return

        if step == "del_channel":
            try:
                chat = await context.bot.get_chat(text)
                channel_id = str(chat.id)
            except:
                channel_id = text
            cur.execute("DELETE FROM channels WHERE channel_id=?", (channel_id,))
            conn.commit()
            context.user_data.clear()
            await update.message.reply_text("✅ Kanal o‘chirildi!", reply_markup=admin_keyboard())
            return

        if text == "👥 Userlar":
            cur.execute("SELECT COUNT(*) FROM users")
            count = cur.fetchone()[0]
            await update.message.reply_text(f"👥 Userlar: {count}", reply_markup=admin_keyboard())
            return

        if text == "📊 Statistika":
            cur.execute("SELECT COUNT(*) FROM movies")
            movies = cur.fetchone()[0]
            cur.execute("SELECT COUNT(*) FROM channels")
            channels = cur.fetchone()[0]
            await update.message.reply_text(
                f"🎬 Kinolar: {movies}\n📢 Kanallar: {channels}",
                reply_markup=admin_keyboard()
            )
            return

    # ===== USER =====
    missing = await not_subscribed(user_id, context)
    if missing:
        await update.message.reply_text("❌ Avval kanallarga obuna bo‘ling! /start bosing.")
        return

    cur.execute("SELECT file_id,name FROM movies WHERE code=?", (text,))
    movie = cur.fetchone()
    if movie:
        await update.message.reply_video(movie[0], caption=f"🎬 {movie[1]}")
    else:
        await update.message.reply_text("❌ Kino topilmadi!")

# ===== MAIN =====
def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button, pattern="check_sub"))
    app.add_handler(MessageHandler(filters.VIDEO, video))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, messages))
    app.add_handler(MessageHandler(filters.FORWARDED, forward_channel))

    print("🔥 SUPER ELITE 2026 BOT ISHLADI!")

    app.run_polling()

if __name__ == "__main__":
    main()
