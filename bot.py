import sqlite3
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters
import asyncio
import nest_asyncio

nest_asyncio.apply()

DB_FILE = "kino.db"
TOKEN = "7974172226:AAFOIPcl7LJmxJcV5rG9AnclbPqQlBvZNLo"
ADMIN_ID = 5775388579

# --- DB Init ---
conn = sqlite3.connect(DB_FILE)
c = conn.cursor()
c.execute("""CREATE TABLE IF NOT EXISTS kino(
            code TEXT PRIMARY KEY,
            file_id TEXT
            )""")
conn.commit()

# --- Start handler ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id == ADMIN_ID:
        keyboard = [
            [InlineKeyboardButton("🎬 Kino qo‘shish", callback_data="add_kino")],
            [InlineKeyboardButton("🗑 Kino o‘chirish", callback_data="del_kino")],
            [InlineKeyboardButton("💎 Premium sozlash", callback_data="premium")],
            [InlineKeyboardButton("📊 Statistika", callback_data="stats")],
            [InlineKeyboardButton("📢 Majburiy kanal", callback_data="channel")]
        ]
        await update.message.reply_text("⚡ Admin panelga xush kelibsiz!", reply_markup=InlineKeyboardMarkup(keyboard))
    else:
        await update.message.reply_text("🎬 Kino botga xush kelibsiz!\nKino kodini yozing:")

# --- Callback handler ---
async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id

    if user_id != ADMIN_ID:
        await query.edit_message_text("❌ Faqat adminga!")
        return

    if query.data == "add_kino":
        await query.edit_message_text("📥 Kino qo‘shish uchun kodi kiriting:")
        context.user_data["action"] = "adding"
    elif query.data == "del_kino":
        await query.edit_message_text("🗑 O‘chirish uchun kodi kiriting:")
        context.user_data["action"] = "deleting"
    elif query.data == "premium":
        await query.edit_message_text("💎 Premium sozlash funksiyasi hozir ishlayapti.")
    elif query.data == "stats":
        c.execute("SELECT COUNT(*) FROM kino")
        total = c.fetchone()[0]
        await query.edit_message_text(f"📊 Bazada jami kinolar: {total}")
    elif query.data == "channel":
        await query.edit_message_text("📢 Majburiy kanal sozlash hozir ishlayapti.")

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
        elif action == "deleting":
            c.execute("DELETE FROM kino WHERE code=?", (text,))
            conn.commit()
            await update.message.reply_text(f"🗑 Kino {text} o‘chirildi!")
            context.user_data["action"] = None
        elif action == "waiting_video":
            if update.message.video:
                file_id = update.message.video.file_id
                code = context.user_data.get("new_code")
                c.execute("INSERT OR REPLACE INTO kino(code,file_id) VALUES(?,?)", (code,file_id))
                conn.commit()
                await update.message.reply_text(f"✅ Kino {code} saqlandi!")
                context.user_data["action"] = None
            else:
                await update.message.reply_text("❌ Iltimos, video yuboring!")
        return

    # Foydalanuvchi kino ko‘rish
    c.execute("SELECT file_id FROM kino WHERE code=?", (text,))
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
