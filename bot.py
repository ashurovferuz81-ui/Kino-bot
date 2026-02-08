import os
import sqlite3
import nest_asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters
)

# --- Nest asyncio patch (Railway/Pydroid) ---
nest_asyncio.apply()

# --- Bot sozlamalari ---
TOKEN = "8426836407:AAHoXkQakddqyXZ_olNplG0_ov-3fhvrkSc"
ADMIN_ID = 5775388579
CHANNEL_USERNAME = "kinomandabor"  # Majburiy kanal username
DB_FILE = os.path.join(os.getcwd(), "kino.db")

# --- DB init ---
conn = sqlite3.connect(DB_FILE, check_same_thread=False)
c = conn.cursor()

# Kino jadvali
c.execute("""
CREATE TABLE IF NOT EXISTS kino(
    code TEXT PRIMARY KEY,
    file_id TEXT
)
""")
# Foydalanuvchilar jadvali
c.execute("""
CREATE TABLE IF NOT EXISTS users(
    user_id INTEGER PRIMARY KEY
)
""")
conn.commit()

# --- Admin panel tugmalari ---
def admin_panel():
    keyboard = [
        [InlineKeyboardButton("🎬 Kino qo‘shish", callback_data="add_kino")],
        [InlineKeyboardButton("🗑 Kino o‘chirish", callback_data="del_kino")],
        [InlineKeyboardButton("📊 Statistika", callback_data="stats")],
    ]
    return InlineKeyboardMarkup(keyboard)

# --- Inline tugma majburiy obuna ---
def subscription_button():
    link = f"https://t.me/{CHANNEL_USERNAME}"
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ Obuna buldim", callback_data="check_sub", url=link)]
    ])

# --- /start handler ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if user_id == ADMIN_ID:
        await update.message.reply_text(
            "🔥 Admin panelga xush kelibsiz!",
            reply_markup=admin_panel()
        )
        return

    # Foydalanuvchi uchun majburiy obuna
    await update.message.reply_text(
        f"❌ Botdan foydalanish uchun kanalga obuna bo‘ling: @{CHANNEL_USERNAME}",
        reply_markup=subscription_button()
    )

# --- Callback handler ---
async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id

    # Admin tugmalar
    if user_id == ADMIN_ID:
        if query.data == "add_kino":
            await query.edit_message_text("📥 Kino kodi kiriting:")
            context.user_data["action"] = "adding"
        elif query.data == "del_kino":
            await query.edit_message_text("🗑 O‘chirish kodi kiriting:")
            context.user_data["action"] = "deleting"
        elif query.data == "stats":
            c.execute("SELECT COUNT(*) FROM kino")
            total_kinos = c.fetchone()[0]
            c.execute("SELECT COUNT(*) FROM users")
            total_users = c.fetchone()[0]
            await query.edit_message_text(f"📊 Bazada kinolar: {total_kinos}\n👥 Foydalanuvchilar: {total_users}")
        return

    # Foydalanuvchi obuna tekshiruvi
    if query.data == "check_sub":
        try:
            member = await context.bot.get_chat_member(CHANNEL_USERNAME, user_id)
            if member.status in ["member", "creator", "administrator"]:
                await query.edit_message_text("✅ Obuna bo‘ldingiz! Endi kino kodi yuboring:")
                c.execute("INSERT OR IGNORE INTO users(user_id) VALUES(?)", (user_id,))
                conn.commit()
            else:
                await query.edit_message_text(f"❌ Siz kanalga obuna bo‘lmagansiz, obuna bo‘ling!")
        except:
            await query.edit_message_text("❌ Kanalga bog‘lanishda xatolik yuz berdi.")

# --- Message handler ---
async def message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text

    # Admin ishlar
    if user_id == ADMIN_ID:
        action = context.user_data.get("action")
        if action == "adding":
            context.user_data["new_code"] = text
            await update.message.reply_text("📥 Endi video yuboring:")
            context.user_data["action"] = "waiting_video"
            return
        elif action == "deleting":
            c.execute("DELETE FROM kino WHERE code=?", (text,))
            conn.commit()
            await update.message.reply_text(f"🗑 Kino {text} o‘chirildi!")
            context.user_data["action"] = None
            return
        elif action == "waiting_video":
            if update.message.video:
                file_id = update.message.video.file_id
                code = context.user_data.get("new_code")
                c.execute("INSERT OR REPLACE INTO kino(code,file_id) VALUES(?,?)", (code, file_id))
                conn.commit()
                await update.message.reply_text(f"✅ Kino {code} saqlandi!")
                context.user_data["action"] = None
            else:
                await update.message.reply_text("❌ Iltimos, video yuboring!")
            return

    # Foydalanuvchi kino kodi
    c.execute("SELECT file_id FROM kino WHERE code=?", (text,))
    row = c.fetchone()
    if row:
        file_id = row[0]
        await update.message.reply_video(file_id)
    else:
        await update.message.reply_text("❌ Kino topilmadi yoki obuna bo‘ling!")

# --- Main ---
app = ApplicationBuilder().token(TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CallbackQueryHandler(button))
app.add_handler(MessageHandler(filters.TEXT | filters.VIDEO, message))

# --- Run ---
app.run_polling()
