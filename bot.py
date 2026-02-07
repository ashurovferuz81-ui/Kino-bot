import os
import asyncio
import nest_asyncio
import psycopg2
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters

nest_asyncio.apply()

# --- Bot sozlamalari ---
TOKEN = "7974172226:AAFOIPcl7LJmxJcV5rG9AnclbPqQlBvZNLo"
ADMIN_ID = 5775388579
DATABASE_URL = os.environ.get("DATABASE_URL")  # Railway PostgreSQL URL

# --- DB init ---
conn = psycopg2.connect(DATABASE_URL)
c = conn.cursor()
c.execute("""
CREATE TABLE IF NOT EXISTS kino(
    code TEXT PRIMARY KEY,
    file_id TEXT
)
""")
conn.commit()

# --- Admin panel tugmalari ---
def admin_keyboard():
    keyboard = [
        [InlineKeyboardButton("🎬 Kino qo‘shish", callback_data="add_kino")],
        [InlineKeyboardButton("🗑 Kino o‘chirish", callback_data="del_kino")],
        [InlineKeyboardButton("💎 Premium sozlash", callback_data="premium")],
        [InlineKeyboardButton("📢 Majburiy kanal", callback_data="channel")],
        [InlineKeyboardButton("📊 Statistika", callback_data="stats")]
    ]
    return InlineKeyboardMarkup(keyboard)

# --- /start handler ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id == ADMIN_ID:
        await update.message.reply_text("⚡ Admin panelga xush kelibsiz!", reply_markup=admin_keyboard())
    else:
        await update.message.reply_text("🎬 Kino botga xush kelibsiz!\nKino kodi kiriting:")

# --- Callback handler ---
async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id

    if user_id != ADMIN_ID:
        await query.edit_message_text("❌ Faqat adminga!")
        return

    if query.data == "add_kino":
        await query.edit_message_text("📥 Kino qo‘shish kodi kiriting:")
        context.user_data["action"] = "adding"
    elif query.data == "del_kino":
        await query.edit_message_text("🗑 O‘chirish kodi kiriting:")
        context.user_data["action"] = "deleting"
    elif query.data == "premium":
        await query.edit_message_text("💎 Premium sozlash funksiyasi.")
    elif query.data == "stats":
        c.execute("SELECT COUNT(*) FROM kino")
        total = c.fetchone()[0]
        await query.edit_message_text(f"📊 Bazada jami kinolar: {total}")
    elif query.data == "channel":
        await query.edit_message_text("📢 Majburiy kanal sozlash.")

# --- Message handler ---
async def message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text

    # Admin kino qo‘shish / o‘chirish
    if user_id == ADMIN_ID:
        action = context.user_data.get("action")
        if action == "adding":
            context.user_data["new_code"] = text
            await update.message.reply_text("📥 Endi video yuboring:")
            context.user_data["action"] = "waiting_video"
            return
        elif action == "deleting":
            c.execute("DELETE FROM kino WHERE code=%s", (text,))
            conn.commit()
            await update.message.reply_text(f"🗑 Kino {text} o‘chirildi!")
            context.user_data["action"] = None
            return
        elif action == "waiting_video":
            if update.message.video:
                file_id = update.message.video.file_id
                code = context.user_data.get("new_code")
                c.execute("INSERT INTO kino(code,file_id) VALUES(%s,%s) ON CONFLICT (code) DO UPDATE SET file_id=EXCLUDED.file_id", (code, file_id))
                conn.commit()
                await update.message.reply_text(f"✅ Kino {code} saqlandi!")
                context.user_data["action"] = None
            else:
                await update.message.reply_text("❌ Iltimos, video yuboring!")
            return

    # Foydalanuvchi kino ko‘rish
    c.execute("SELECT file_id FROM kino WHERE code=%s", (text,))
    row = c.fetchone()
    if row:
        file_id = row[0]
        await update.message.reply_video(file_id)
    else:
        await update.message.reply_text("❌ Kino topilmadi!")

# --- Main ---
app = ApplicationBuilder().token(TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CallbackQueryHandler(button))
app.add_handler(MessageHandler(filters.TEXT | filters.VIDEO, message))

# --- Run ---
async def main():
    await app.initialize()
    await app.start()
    await app.updater.start_polling()
    await asyncio.Event().wait()

asyncio.run(main())
