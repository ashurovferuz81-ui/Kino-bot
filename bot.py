import logging
import sqlite3
import os
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
)

# ================== SOZLAMALAR ==================

TOKEN = "8426836407:AAHoXkQakddqyXZ_olNplG0_ov-3fhvrkSc"

ADMIN_ID = 5775388579  # <-- BU YERGA O'ZINGIZNI ADMIN ID QILING

FORCE_CHANNELS = [
    {
        "id": -1003803588211,
        "title": "Kinolar Olami",
        "link": "https://t.me/kinolarolami"
    }
]

DB_NAME = "elite_kino.db"

# ================== LOG ==================
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)

# ================== DATABASE ==================

def db():
    return sqlite3.connect(DB_NAME)

def init_db():
    con = db()
    cur = con.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS movies (
        code TEXT PRIMARY KEY,
        file_id TEXT,
        title TEXT
    )
    """)

    con.commit()
    con.close()

# ================== MAJBURIY OBUNA ==================

async def check_subscription(user_id: int, context):
    not_joined = []

    for ch in FORCE_CHANNELS:
        try:
            member = await context.bot.get_chat_member(ch["id"], user_id)
            if member.status not in ["member", "administrator", "creator"]:
                not_joined.append(ch)
        except:
            not_joined.append(ch)

    return not_joined

def sub_keyboard():
    buttons = []
    for ch in FORCE_CHANNELS:
        buttons.append([InlineKeyboardButton(f"➕ {ch['title']}", url=ch["link"])])
    buttons.append([InlineKeyboardButton("✅ Obuna bo‘ldim", callback_data="sub_done")])
    return InlineKeyboardMarkup(buttons)

# ================== START ==================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    con = db()
    cur = con.cursor()
    cur.execute("INSERT OR IGNORE INTO users VALUES (?)", (user_id,))
    con.commit()
    con.close()

    not_sub = await check_subscription(user_id, context)
    if not_sub:
        await update.message.reply_text(
            "❗ Botdan foydalanish uchun kanalga obuna bo‘ling:",
            reply_markup=sub_keyboard()
        )
        return

    await update.message.reply_text(
        "🎬 ULTRA ELITE KINO BOT\n\n"
        "🎥 Kino kodi yuboring:"
    )

# ================== OBUNA BOSILDI ==================

async def callbacks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "sub_done":
        not_sub = await check_subscription(query.from_user.id, context)
        if not_sub:
            await query.message.reply_text(
                "❌ Siz hali barcha kanallarga obuna bo‘lmadingiz!",
                reply_markup=sub_keyboard()
            )
        else:
            await query.message.reply_text(
                "✅ Obuna tasdiqlandi!\n🎬 Endi kino kodini yuboring."
            )

# ================== ADMIN PANEL ==================

async def admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return

    await update.message.reply_text(
        "👑 ADMIN PANEL\n\n"
        "📤 Kino yuklash:\n"
        "`/add kod`\n"
        "Keyin videoni yuboring",
        parse_mode="Markdown"
    )

# ================== KINO QO‘SHISH ==================

async def add_movie(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return

    if len(context.args) != 1:
        await update.message.reply_text("❌ To‘g‘ri format: /add 777")
        return

    code = context.args[0]
    context.user_data["add_code"] = code

    await update.message.reply_text("🎬 Endi kinoni video qilib yuboring")

async def save_movie(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return

    if "add_code" not in context.user_data:
        return

    if not update.message.video:
        return

    code = context.user_data["add_code"]
    file_id = update.message.video.file_id

    con = db()
    cur = con.cursor()
    cur.execute(
        "INSERT OR REPLACE INTO movies VALUES (?, ?, ?)",
        (code, file_id, f"Kino {code}")
    )
    con.commit()
    con.close()

    context.user_data.pop("add_code")

    await update.message.reply_text("✅ Kino saqlandi!")

# ================== KINO BERISH ==================

async def get_movie(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    not_sub = await check_subscription(user_id, context)
    if not_sub:
        await update.message.reply_text(
            "❗ Avval kanalga obuna bo‘ling:",
            reply_markup=sub_keyboard()
        )
        return

    code = update.message.text.strip()

    con = db()
    cur = con.cursor()
    cur.execute("SELECT file_id FROM movies WHERE code=?", (code,))
    row = cur.fetchone()
    con.close()

    if not row:
        await update.message.reply_text("❌ Kino topilmadi")
        return

    await update.message.reply_video(row[0])

# ================== MAIN ==================

def main():
    init_db()

    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("admin", admin))
    app.add_handler(CommandHandler("add", add_movie))
    app.add_handler(CallbackQueryHandler(callbacks))
    app.add_handler(MessageHandler(filters.VIDEO, save_movie))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, get_movie))

    print("🔥 ULTRA ELITE BOT ISHLADI")
    app.run_polling()

if __name__ == "__main__":
    main()
