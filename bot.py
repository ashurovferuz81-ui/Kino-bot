import sqlite3
import nest_asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, CallbackQueryHandler,
    MessageHandler, filters, ContextTypes
)

nest_asyncio.apply()

TOKEN = "8426836407:AAHoXkQakddqyXZ_olNplG0_ov-3fhvrkSc"
ADMIN_ID = 5775388579

# -------- DATABASE --------
conn = sqlite3.connect("elite_kino.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS users(
    user_id INTEGER PRIMARY KEY
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS movies(
    code TEXT PRIMARY KEY,
    file_id TEXT
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS settings(
    id INTEGER PRIMARY KEY,
    channel TEXT
)
""")

conn.commit()

admin_state = {}

# -------- MAJBURIY OBUNA TEKSHIRUV --------
async def check_sub(user_id, context):
    cursor.execute("SELECT channel FROM settings WHERE id=1")
    row = cursor.fetchone()

    if not row:
        return True

    channel = row[0].replace("https://t.me/", "").replace("@", "")

    try:
        member = await context.bot.get_chat_member(channel, user_id)
        return member.status in ["member", "administrator", "creator"]
    except:
        return False


# -------- START --------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    cursor.execute("INSERT OR IGNORE INTO users VALUES(?)", (user_id,))
    conn.commit()

    if not await check_sub(user_id, context):
        cursor.execute("SELECT channel FROM settings WHERE id=1")
        channel = cursor.fetchone()[0]

        keyboard = [
            [InlineKeyboardButton("📢 Obuna bo‘lish", url=channel)],
            [InlineKeyboardButton("✅ Obuna bo‘ldim", callback_data="check_sub")]
        ]

        await update.message.reply_text(
            "Botdan foydalanish uchun kanalga obuna bo‘ling!",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return

    await update.message.reply_text("🎬 Kino kodini yuboring!")


# -------- ADMIN PANEL --------
async def admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return

    keyboard = [
        [InlineKeyboardButton("🎬 Kino yuklash", callback_data="upload")],
        [InlineKeyboardButton("📊 Statistika", callback_data="stats")],
        [InlineKeyboardButton("📢 Broadcast", callback_data="broadcast")],
        [InlineKeyboardButton("🔒 Majburiy kanal", callback_data="channel")]
    ]

    await update.message.reply_text(
        "👑 ELITE ADMIN PANEL",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


# -------- BUTTONS --------
async def buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    await query.answer()

    # obuna qayta tekshirish
    if query.data == "check_sub":
        if await check_sub(user_id, context):
            await query.edit_message_text("✅ Obuna tasdiqlandi!\nEndi kino kodi yuboring.")
        else:
            await query.answer("❌ Hali obuna bo‘lmadingiz!", show_alert=True)
        return

    if user_id != ADMIN_ID:
        return

    if query.data == "upload":
        admin_state[user_id] = "code"
        await query.message.reply_text("🎬 Kino kodini yuboring:")

    elif query.data == "stats":
        cursor.execute("SELECT COUNT(*) FROM users")
        users = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM movies")
        movies = cursor.fetchone()[0]

        await query.message.reply_text(
            f"📊 Statistika:\n👥 Users: {users}\n🎬 Kinolar: {movies}"
        )

    elif query.data == "broadcast":
        admin_state[user_id] = "broadcast"
        await query.message.reply_text("📢 Yuboriladigan xabarni kiriting:")

    elif query.data == "channel":
        admin_state[user_id] = "channel"
        await query.message.reply_text("📢 Kanal linkini yuboring:\nMasalan https://t.me/kanal")


# -------- MESSAGE HANDLER --------
async def messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    msg = update.message

    # ----- ADMIN -----
    if user_id == ADMIN_ID:

        state = admin_state.get(user_id)

        # kanal sozlash
        if state == "channel" and msg.text:
            cursor.execute("INSERT OR REPLACE INTO settings VALUES(1,?)", (msg.text,))
            conn.commit()

            admin_state.pop(user_id)
            await msg.reply_text("✅ Kanal saqlandi!")
            return

        # kino kodi
        if state == "code" and msg.text:
            admin_state[user_id] = {"step": "video", "code": msg.text}
            await msg.reply_text("📥 Endi kino videosini yuboring:")
            return

        # kino video
        if isinstance(state, dict) and state.get("step") == "video":

            file_id = None

            if msg.video:
                file_id = msg.video.file_id

            elif msg.document and msg.document.mime_type.startswith("video"):
                file_id = msg.document.file_id

            if file_id:
                code = state["code"]

                cursor.execute(
                    "INSERT OR REPLACE INTO movies VALUES(?,?)",
                    (code, file_id)
                )
                conn.commit()

                admin_state.pop(user_id)

                await msg.reply_text(f"✅ Kino saqlandi!\nKodi: {code}")
            else:
                await msg.reply_text("❌ Video yuboring!")
            return

        # broadcast
        if state == "broadcast":
            cursor.execute("SELECT user_id FROM users")
            users = cursor.fetchall()

            sent = 0

            for u in users:
                try:
                    await context.bot.send_message(u[0], msg.text)
                    sent += 1
                except:
                    pass

            admin_state.pop(user_id)

            await msg.reply_text(f"✅ Yuborildi: {sent} ta userga")
            return

    # ----- USER -----
    if not await check_sub(user_id, context):

        cursor.execute("SELECT channel FROM settings WHERE id=1")
        channel = cursor.fetchone()[0]

        keyboard = [
            [InlineKeyboardButton("📢 Obuna bo‘lish", url=channel)],
            [InlineKeyboardButton("✅ Obuna bo‘ldim", callback_data="check_sub")]
        ]

        await msg.reply_text(
            "❌ Avval kanalga obuna bo‘ling!",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return

    if msg.text:
        cursor.execute("SELECT file_id FROM movies WHERE code=?", (msg.text,))
        movie = cursor.fetchone()

        if movie:
            await msg.reply_video(movie[0])
        else:
            await msg.reply_text("❌ Kino topilmadi.")


# -------- RUN --------
def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("admin", admin))
    app.add_handler(CallbackQueryHandler(buttons))
    app.add_handler(MessageHandler(filters.ALL, messages))

    print("ELITE BOT ISHGA TUSHDI 🚀")
    app.run_polling()


if __name__ == "__main__":
    main()
