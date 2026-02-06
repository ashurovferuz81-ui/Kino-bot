import aiosqlite
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
import nest_asyncio
import asyncio

# =======================
# TOKEN & ADMIN
# =======================
USER_BOT_TOKEN = "7974172226:AAFOIPcl7LJmxJcV5rG9AnclbPqQlBvZNLo"
USER_ADMIN_ID = 5775388579  # Sizning Telegram ID foydalanuvchi botida admin
DB = "user_kino_bot.db"

# =======================
# NEST ASYNCIO
# =======================
nest_asyncio.apply()

# =======================
# DATABASE INIT
# =======================
async def init_db():
    async with aiosqlite.connect(DB) as db:
        await db.execute("""CREATE TABLE IF NOT EXISTS movies (
            code TEXT,
            file_id TEXT
        )""")
        await db.commit()

# =======================
# ADMIN PANEL
# =======================
def admin_keyboard():
    keyboard = ReplyKeyboardMarkup([
        ["🎬 Kino qo‘shish", "🗑 Kino o‘chirish"],
        ["📊 Statistika", "📥 Qidirish"],
        ["🎞 Kino ro‘yxati", "🏷 Tag qo‘shish"],
        ["🔄 Kino tahrirlash", "💾 Obunachilar"],
        ["📢 Reklama", "🔔 Xabar yuborish"]
    ], resize_keyboard=True)
    return keyboard

# =======================
# START COMMAND
# =======================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id == USER_ADMIN_ID:
        await update.message.reply_text("✅ Admin panelga xush kelibsiz!", reply_markup=admin_keyboard())
    else:
        await update.message.reply_text("🎬 Kino kodi yuboring...")

# =======================
# MESSAGE HANDLER
# =======================
async def message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text

    # ===== Admin ishchi qismi =====
    if user_id == USER_ADMIN_ID:
        if text == "🎬 Kino qo‘shish":
            context.user_data["step"] = "code"
            await update.message.reply_text("Kino kodi yuboring:")
            return

        if context.user_data.get("step") == "code":
            context.user_data["movie_code"] = text
            context.user_data["step"] = "video"
            await update.message.reply_text("Endi kinoni VIDEO qilib yuboring:")
            return

    # ===== Video saqlash =====
    if update.message.video and user_id == USER_ADMIN_ID:
        code = context.user_data.get("movie_code")
        if not code:
            return
        file_id = update.message.video.file_id
        async with aiosqlite.connect(DB) as db:
            await db.execute("INSERT INTO movies VALUES (?, ?)", (code, file_id))
            await db.commit()
        context.user_data.clear()
        await update.message.reply_text("✅ Kino saqlandi!")
        return

    # ===== Kino berish =====
    if text:
        async with aiosqlite.connect(DB) as db:
            cursor = await db.execute("SELECT file_id FROM movies WHERE code=?", (text,))
            movie = await cursor.fetchone()
        if movie:
            await update.message.reply_video(movie[0])
        else:
            await update.message.reply_text("❌ Kino topilmadi")

# =======================
# MAIN FUNCTION
# =======================
async def main():
    await init_db()
    app = ApplicationBuilder().token(USER_BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.ALL, message))
    await app.run_polling()

# =======================
# RUN
# =======================
if __name__ == "__main__":
    asyncio.get_event_loop().run_until_complete(main())
