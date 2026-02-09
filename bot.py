import sqlite3
import nest_asyncio
from telegram import Update, ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes

# --- Async patch ---
nest_asyncio.apply()

# --- BOT CONFIG ---
TOKEN = "8426836407:AAHoXkQakddqyXZ_olNplG0_ov-3fhvrkSc"
ADMIN_ID = 5775388579
DB_FILE = "super_elite_kino.db"

# --- DATABASE ---
conn = sqlite3.connect(DB_FILE, check_same_thread=False)
cur = conn.cursor()

# --- Tables ---
cur.execute("CREATE TABLE IF NOT EXISTS movies(code TEXT PRIMARY KEY, file_id TEXT, name TEXT)")
cur.execute("CREATE TABLE IF NOT EXISTS channels(channel_id TEXT PRIMARY KEY, type TEXT)")
cur.execute("CREATE TABLE IF NOT EXISTS users(user_id TEXT PRIMARY KEY)")
conn.commit()

# --- ADMIN KEYBOARD ---
def admin_keyboard():
    keyboard = [
        ["🎬 Kino qo‘shish", "🗑 Kino o‘chirish"],
        ["📢 Kanal qo‘shish", "❌ Kanal o‘chirish"],
        ["👥 Userlar", "📊 Statistika"]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

# --- CHECK SUBSCRIPTION ---
async def not_subscribed(user_id, context):
    cur.execute("SELECT channel_id,type FROM channels")
    channels = cur.fetchall()
    not_joined = []

    for ch_id, ch_type in channels:
        try:
            member = await context.bot.get_chat_member(ch_id, user_id)
            if member.status in ["left", "kicked"]:
                not_joined.append(ch_id)
        except:
            not_joined.append(ch_id)
    return not_joined

# --- START COMMAND ---
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
                if username:
                    url = f"https://t.me/{username}"
                else:
                    url = f"https://t.me/+{str(ch).replace('-100','')}"
                buttons.append([InlineKeyboardButton("📢 Kanalga kirish", url=url)])
            except:
                continue
        buttons.append([InlineKeyboardButton("✅ Obuna bo‘ldim", callback_data="check_sub")])
        await update.message.reply_text("📢 Kanallarga obuna bo‘ling:", reply_markup=InlineKeyboardMarkup(buttons))
        return

    await update.message.reply_text("🎬 Kino kodini yuboring:")

# --- BUTTON CALLBACK ---
async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    missing = await not_subscribed(query.from_user.id, context)
    if missing:
        await query.answer("❌ Hali obuna bo‘lmagansiz!", show_alert=True)
        return
    await query.message.edit_text("✅ Endi kino kodini yuboring!")

# --- VIDEO HANDLER ---
async def video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    step = context.user_data.get("step")
    if step == "video":
        context.user_data["file"] = update.message.video.file_id
        context.user_data["step"] = "name"
        await update.message.reply_text("🎬 Kino nomini yozing:")

# --- MESSAGE HANDLER ---
async def messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    user_id = update.effective_user.id
    step = context.user_data.get("step")

    # --- ADMIN ---
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

        # DELETE MOVIE
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

        # ADD CHANNEL
        if text == "📢 Kanal qo‘shish":
            context.user_data["step"] = "add_channel"
            await update.message.reply_text("@username yoki link yuboring / private kanal xabar yuboring:")
            return
        if step == "add_channel":
            try:
                chat = await context.bot.get_chat(text)
                cur.execute("INSERT OR IGNORE INTO channels VALUES(?,?)", (str(chat.id), "public"))
                conn.commit()
                context.user_data.clear()
                await update.message.reply_text("✅ Kanal qo‘shildi!", reply_markup=admin_keyboard())
            except:
                # Agar private kanal bo‘lsa admin xabar yuborsa
                if update.message.forward_from_chat:
                    fwd_chat = update.message.forward_from_chat
                    cur.execute("INSERT OR IGNORE INTO channels VALUES(?,?)", (str(fwd_chat.id), "private"))
                    conn.commit()
                    context.user_data.clear()
                    await update.message.reply_text("✅ Private kanal majburiy qo‘shildi!", reply_markup=admin_keyboard())
                else:
                    await update.message.reply_text("❌ Botni kanalga admin qiling yoki public username yuboring!")
            return

        # DELETE CHANNEL
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

        # USER STATS
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
            await update.message.reply_text(f"🎬 Kinolar: {movies}\n📢 Kanallar: {channels}", reply_markup=admin_keyboard())
            return

    # --- USER ---
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

# --- MAIN ---
def main():
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button, pattern="check_sub"))
    app.add_handler(MessageHandler(filters.VIDEO, video))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, messages))
    print("🔥 SUPER ELITE BOT ISHLADI!")
    app.run_polling()

if __name__ == "__main__":
    main()
