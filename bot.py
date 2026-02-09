import os
import sqlite3
import nest_asyncio
from telegram import Update, ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler

nest_asyncio.apply()

TOKEN = "8426836407:AAHoXkQakddqyXZ_olNplG0_ov-3fhvrkSc"
ADMIN_ID = 5775388579

# ---------- DATABASE ----------
conn = sqlite3.connect("elite_kino.db", check_same_thread=False)
cur = conn.cursor()

cur.execute("CREATE TABLE IF NOT EXISTS movies(code TEXT PRIMARY KEY, file_id TEXT, name TEXT)")
cur.execute("CREATE TABLE IF NOT EXISTS channels(channel TEXT)")
cur.execute("CREATE TABLE IF NOT EXISTS users(user_id TEXT)")
conn.commit()


# ---------- ADMIN KEYBOARD ----------
def admin_keyboard():
    keyboard = [
        ["🎬 Kino qo‘shish", "🗑 Kino o‘chirish"],
        ["📢 Kanal qo‘shish", "❌ Kanal o‘chirish"],
        ["👥 Userlar", "📊 Statistika"]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)


# ---------- USER START ----------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user_id = str(update.effective_user.id)

    cur.execute("INSERT OR IGNORE INTO users VALUES(?)", (user_id,))
    conn.commit()

    if update.effective_user.id == ADMIN_ID:
        await update.message.reply_text(
            "🔥 ADMIN PANEL",
            reply_markup=admin_keyboard()
        )
        return

    # CHANNEL CHECK
    cur.execute("SELECT channel FROM channels")
    channels = cur.fetchall()

    if channels:

        buttons = []

        not_joined = []

        for ch in channels:
            channel = ch[0]

            try:
                member = await context.bot.get_chat_member(channel, user_id)

                if member.status in ["left", "kicked"]:
                    not_joined.append(channel)

            except:
                not_joined.append(channel)

            buttons.append(
                [InlineKeyboardButton("📢 Kanalga kirish", url=f"https://t.me/{channel.replace('@','')}")]
            )

        if not_joined:

            buttons.append(
                [InlineKeyboardButton("✅ Obuna bo‘ldim", callback_data="check_sub")]
            )

            await update.message.reply_text(
                "📢 Kanallarga obuna bo‘ling:",
                reply_markup=InlineKeyboardMarkup(buttons)
            )
            return

    await update.message.reply_text("🎬 Kino kodini yuboring:")


# ---------- SUB CHECK ----------
async def check_sub(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    user_id = str(query.from_user.id)

    cur.execute("SELECT channel FROM channels")
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

    if not_joined:

        await query.answer("❌ Avval kanallarga obuna bo‘ling!", show_alert=True)
        return

    await query.message.edit_text("✅ Endi kino kodini yuboring.")


# ---------- MESSAGE HANDLER ----------
async def messages(update: Update, context: ContextTypes.DEFAULT_TYPE):

    text = update.message.text
    user_id = update.effective_user.id
    step = context.user_data.get("step")

    # ===== ADMIN =====
    if user_id == ADMIN_ID:

        # Kino qo‘shish
        if text == "🎬 Kino qo‘shish":
            context.user_data["step"] = "movie_code"
            await update.message.reply_text("🎥 Kino kodini yuboring:")
            return

        if step == "movie_code":
            context.user_data["code"] = text
            context.user_data["step"] = "movie_video"
            await update.message.reply_text("🎬 Endi kino VIDEOSINI yuboring:")
            return

        if step == "movie_name":
            code = context.user_data["code"]
            file_id = context.user_data["file"]

            cur.execute(
                "INSERT OR REPLACE INTO movies VALUES(?,?,?)",
                (code, file_id, text)
            )
            conn.commit()

            context.user_data.clear()

            await update.message.reply_text("✅ Kino saqlandi!", reply_markup=admin_keyboard())
            return

        # Kino o‘chirish
        if text == "🗑 Kino o‘chirish":
            context.user_data["step"] = "del_movie"
            await update.message.reply_text("O‘chirish uchun kino kodini yuboring:")
            return

        if step == "del_movie":
            cur.execute("DELETE FROM movies WHERE code=?", (text,))
            conn.commit()

            context.user_data.clear()

            await update.message.reply_text("✅ Kino o‘chirildi!", reply_markup=admin_keyboard())
            return

        # Kanal qo‘shish (AUTO)
        if text == "📢 Kanal qo‘shish":
            context.user_data["step"] = "channel"
            await update.message.reply_text(
                "Kanal yuboring:\n@username yoki link"
            )
            return

        if step == "channel":
            try:

                chat = await context.bot.get_chat(text)
                channel_id = str(chat.id)

                cur.execute(
                    "INSERT OR IGNORE INTO channels VALUES(?)",
                    (channel_id,)
                )
                conn.commit()

                context.user_data.clear()

                await update.message.reply_text(
                    "✅ Kanal qo‘shildi!",
                    reply_markup=admin_keyboard()
                )

            except:
                await update.message.reply_text(
                    "❌ Kanal topilmadi!\nBOTNI ADMIN QILING"
                )
            return

        # Kanal o‘chirish
        if text == "❌ Kanal o‘chirish":
            context.user_data["step"] = "del_channel"
            await update.message.reply_text("@kanal yoki ID yuboring:")
            return

        if step == "del_channel":
            cur.execute("DELETE FROM channels WHERE channel=?", (text,))
            conn.commit()

            context.user_data.clear()

            await update.message.reply_text(
                "✅ Kanal o‘chirildi!",
                reply_markup=admin_keyboard()
            )
            return

        # Users
        if text == "👥 Userlar":
            cur.execute("SELECT COUNT(*) FROM users")
            count = cur.fetchone()[0]

            await update.message.reply_text(
                f"👥 Jami foydalanuvchilar: {count}",
                reply_markup=admin_keyboard()
            )
            return

        # Stats
        if text == "📊 Statistika":
            cur.execute("SELECT COUNT(*) FROM movies")
            movies = cur.fetchone()[0]

            cur.execute("SELECT COUNT(*) FROM channels")
            channels = cur.fetchone()[0]

            await update.message.reply_text(
                f"""
📊 BOT STATISTIKASI

🎬 Kinolar: {movies}
📢 Kanallar: {channels}
""",
                reply_markup=admin_keyboard()
            )
            return

    # ===== USER =====
    cur.execute("SELECT file_id,name FROM movies WHERE code=?", (text,))
    movie = cur.fetchone()

    if movie:

        file_id, name = movie

        await update.message.reply_video(
            file_id,
            caption=f"🎬 {name}"
        )

    else:
        await update.message.reply_text("❌ Kino topilmadi!")


# ---------- VIDEO HANDLER ----------
async def video_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if update.effective_user.id != ADMIN_ID:
        return

    if context.user_data.get("step") == "movie_video":

        context.user_data["file"] = update.message.video.file_id
        context.user_data["step"] = "movie_name"

        await update.message.reply_text("🎬 Kino nomini yozing:")


# ---------- MAIN ----------
def main():

    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(check_sub, pattern="check_sub"))

    app.add_handler(MessageHandler(filters.VIDEO, video_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, messages))

    print("🚀 ELITE KINO BOT ISHLADI!")

    app.run_polling()


if __name__ == "__main__":
    main()
