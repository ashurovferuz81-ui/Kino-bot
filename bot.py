import os
import sqlite3
import nest_asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes

# --- Nest asyncio patch (Railway/Pydroid) ---
nest_asyncio.apply()

# --- Bot sozlamalari ---
TOKEN = "8426836407:AAHoXkQakddqyXZ_olNplG0_ov-3fhvrkSc"
ADMIN_ID = 5775388579
DB_FILE = os.path.join(os.getcwd(), "kino.db")

# --- DB init ---
conn = sqlite3.connect(DB_FILE, check_same_thread=False)
c = conn.cursor()

# Kino jadvali
c.execute("""
CREATE TABLE IF NOT EXISTS kino(
    code TEXT PRIMARY KEY,
    file_id TEXT,
    premium INTEGER DEFAULT 0
)
""")

# Foydalanuvchilar jadvali
c.execute("""
CREATE TABLE IF NOT EXISTS users(
    user_id INTEGER PRIMARY KEY,
    premium INTEGER DEFAULT 0
)
""")

# Majburiy kanal
c.execute("""
CREATE TABLE IF NOT EXISTS channels(
    username TEXT PRIMARY KEY
)
""")
conn.commit()

# --- Admin panel tugmalari ---
def admin_panel():
    keyboard = [
        [InlineKeyboardButton("🎬 Kino qo‘shish", callback_data="add_kino")],
        [InlineKeyboardButton("🗑 Kino o‘chirish", callback_data="del_kino")],
        [InlineKeyboardButton("💎 Premium obunachi", callback_data="premium")],
        [InlineKeyboardButton("📢 Majburiy kanal", callback_data="channel")],
        [InlineKeyboardButton("📊 Statistika", callback_data="stats")]
    ]
    return InlineKeyboardMarkup(keyboard)

# --- /start handler ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    c.execute("INSERT OR IGNORE INTO users(user_id) VALUES(?)",(user_id,))
    conn.commit()

    if user_id == ADMIN_ID:
        await update.message.reply_text("🔥 Admin panelga xush kelibsiz!", reply_markup=admin_panel())
        return

    # Majburiy kanalni tekshir
    c.execute("SELECT username FROM channels")
    channel = c.fetchone()
    if channel:
        channel_name = channel[0]
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("✅ Obuna buldim", callback_data="check_sub")]
        ])
        await update.message.reply_text(
            f"❌ Botdan foydalanish uchun {channel_name} ga obuna bo‘ling!",
            reply_markup=keyboard
        )
    else:
        await update.message.reply_text("🎬 Kino botga xush kelibsiz!\nKino kodi kiriting:")

# --- Callback handler ---
async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id

    # --- Obuna tugmasi tekshir ---
    if query.data == "check_sub":
        c.execute("SELECT username FROM channels")
        channel = c.fetchone()
        if not channel:
            await query.edit_message_text("❌ Kanal topilmadi! Adminga murojaat qiling.")
            return
        channel_name = channel[0]
        try:
            member = await context.bot.get_chat_member(channel_name, user_id)
            if member.status in ["member", "creator", "administrator"]:
                await query.edit_message_text("✅ Obuna bo‘ldingiz! Kino kodi yuboring:")
            else:
                await query.edit_message_text(f"❌ Siz hali {channel_name} ga obuna bo‘lmagansiz. Obuna bo‘ling!")
        except:
            await query.edit_message_text(f"❌ {channel_name} bilan bog‘lanishda xatolik. Adminga murojaat qiling.")
        return

    if user_id != ADMIN_ID:
        await query.edit_message_text("❌ Faqat adminga!")
        return

    # Admin tugmalar
    if query.data == "add_kino":
        await query.edit_message_text("📥 Kino qo‘shish kodi kiriting:")
        context.user_data["action"] = "adding"
    elif query.data == "del_kino":
        await query.edit_message_text("🗑 O‘chirish kodi kiriting:")
        context.user_data["action"] = "deleting"
    elif query.data == "premium":
        await query.edit_message_text("💎 Agar foydalanuvchi premium sotib olmoqchi bo‘lsa, unga yozing: @Sardorbeko008")
    elif query.data == "stats":
        c.execute("SELECT COUNT(*) FROM kino")
        total = c.fetchone()[0]
        c.execute("SELECT COUNT(*) FROM users")
        users = c.fetchone()[0]
        await query.edit_message_text(f"📊 Bazada jami kinolar: {total}\n👥 Foydalanuvchilar: {users}")
    elif query.data == "channel":
        await query.edit_message_text("📢 Majburiy kanal sozlash. Kanal username kiriting:")

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
app.run_polling()
