import sqlite3
import logging
from telegram import (
    Update,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    ReplyKeyboardMarkup
)
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
)

TOKEN = "8426836407:AAHoXkQakddqyXZ_olNplG0_ov-3fhvrkSc"
ADMIN_ID = 5775388579
DB = "elite.db"

logging.basicConfig(level=logging.INFO)

# ================= DATABASE =================

def init_db():
    con = sqlite3.connect(DB)
    cur = con.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS users(
        id INTEGER PRIMARY KEY
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS movies(
        code TEXT PRIMARY KEY,
        name TEXT,
        file_id TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS channels(
        channel_id TEXT PRIMARY KEY,
        link TEXT
    )
    """)

    con.commit()
    con.close()

def db():
    return sqlite3.connect(DB)

# ================= ADMIN KEYBOARD =================

def admin_keyboard():
    return ReplyKeyboardMarkup([
        ["🎬 Kino qo‘shish", "🗑 Kino o‘chirish"],
        ["📢 Kanal qo‘shish", "❌ Kanal o‘chirish"],
        ["📊 Statistika"]
    ], resize_keyboard=True)

# ================= SUB CHECK =================

async def check_sub(user_id, context):
    con = db()
    cur = con.cursor()

    cur.execute("SELECT * FROM channels")
    channels = cur.fetchall()
    con.close()

    not_joined = []

    for ch_id, link in channels:
        try:
            member = await context.bot.get_chat_member(ch_id, user_id)
            if member.status not in ["member", "administrator", "creator"]:
                not_joined.append((ch_id, link))
        except:
            not_joined.append((ch_id, link))

    return not_joined


def sub_buttons(channels):
    btn = []

    for ch_id, link in channels:
        btn.append([InlineKeyboardButton("➕ Kanalga kirish", url=link)])

    btn.append([InlineKeyboardButton("✅ Obuna bo‘ldim", callback_data="sub")])

    return InlineKeyboardMarkup(btn)

# ================= START =================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user.id

    con = db()
    cur = con.cursor()
    cur.execute("INSERT OR IGNORE INTO users VALUES(?)", (user,))
    con.commit()
    con.close()

    not_sub = await check_sub(user, context)

    if not_sub:
        await update.message.reply_text(
            "❗ Botdan foydalanish uchun kanallarga obuna bo‘ling",
            reply_markup=sub_buttons(not_sub)
        )
        return

    if user == ADMIN_ID:
        await update.message.reply_text(
            "👑 ADMIN PANELGA XUSH KELIBSIZ",
            reply_markup=admin_keyboard()
        )
    else:
        await update.message.reply_text(
            "🎬 Kino kodini yuboring!"
        )

# ================= SUB BUTTON =================

async def sub_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user = query.from_user.id
    not_sub = await check_sub(user, context)

    if not_sub:
        await query.message.reply_text(
            "❌ Hali obuna bo‘lmadingiz!",
            reply_markup=sub_buttons(not_sub)
        )
    else:
        await query.message.reply_text("✅ Tasdiqlandi! Endi kino kodi yuboring.")

# ================= ADMIN LOGIC =================

async def admin_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return

    text = update.message.text

    if text == "🎬 Kino qo‘shish":
        context.user_data["step"] = "movie_code"
        await update.message.reply_text("🎥 Kino kodini yuboring:")

    elif text == "🗑 Kino o‘chirish":
        context.user_data["step"] = "delete_movie"
        await update.message.reply_text("❌ O‘chiriladigan kino kodini yuboring:")

    elif text == "📢 Kanal qo‘shish":
        context.user_data["step"] = "channel_add"
        await update.message.reply_text(
            "Kanal ID yuboring:\nMasalan: -100xxxx"
        )

    elif text == "❌ Kanal o‘chirish":
        context.user_data["step"] = "channel_del"
        await update.message.reply_text("O‘chiriladigan kanal ID ni yuboring:")

    elif text == "📊 Statistika":
        con = db()
        cur = con.cursor()

        cur.execute("SELECT COUNT(*) FROM users")
        users = cur.fetchone()[0]

        cur.execute("SELECT COUNT(*) FROM movies")
        movies = cur.fetchone()[0]

        con.close()

        await update.message.reply_text(
            f"👥 Userlar: {users}\n🎬 Kinolar: {movies}"
        )

# ================= STEPS =================

async def steps(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return

    step = context.user_data.get("step")
    text = update.message.text

    con = db()
    cur = con.cursor()

    if step == "movie_code":
        context.user_data["code"] = text
        context.user_data["step"] = "movie_name"
        await update.message.reply_text("🎬 Kino nomini yuboring:")

    elif step == "movie_name":
        context.user_data["name"] = text
        context.user_data["step"] = "movie_video"
        await update.message.reply_text("📥 Endi videoni yuboring:")

    elif step == "delete_movie":
        cur.execute("DELETE FROM movies WHERE code=?", (text,))
        con.commit()
        await update.message.reply_text("✅ Kino o‘chirildi!")
        context.user_data.clear()

    elif step == "channel_add":
        context.user_data["channel_id"] = text
        context.user_data["step"] = "channel_link"
        await update.message.reply_text("Kanal linkini yuboring:")

    elif step == "channel_link":
        cur.execute(
            "INSERT OR REPLACE INTO channels VALUES (?,?)",
            (context.user_data["channel_id"], text)
        )
        con.commit()
        await update.message.reply_text("✅ Kanal qo‘shildi!")
        context.user_data.clear()

    elif step == "channel_del":
        cur.execute("DELETE FROM channels WHERE channel_id=?", (text,))
        con.commit()
        await update.message.reply_text("✅ Kanal o‘chirildi!")
        context.user_data.clear()

    con.close()

# ================= VIDEO SAVE =================

async def video_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return

    if context.user_data.get("step") != "movie_video":
        return

    file_id = update.message.video.file_id
    code = context.user_data["code"]
    name = context.user_data["name"]

    con = db()
    cur = con.cursor()

    cur.execute(
        "INSERT OR REPLACE INTO movies VALUES(?,?,?)",
        (code, name, file_id)
    )
    con.commit()
    con.close()

    await update.message.reply_text("🔥 Kino saqlandi!")

    context.user_data.clear()

# ================= USER MOVIE =================

async def user_movie(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user.id

    not_sub = await check_sub(user, context)
    if not_sub:
        await update.message.reply_text(
            "❗ Avval obuna bo‘ling",
            reply_markup=sub_buttons(not_sub)
        )
        return

    code = update.message.text

    con = db()
    cur = con.cursor()

    cur.execute("SELECT file_id,name FROM movies WHERE code=?", (code,))
    movie = cur.fetchone()
    con.close()

    if not movie:
        return

    await update.message.reply_video(
        movie[0],
        caption=f"🎬 {movie[1]}"
    )

# ================= MAIN =================

def main():
    init_db()

    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(sub_callback))
    app.add_handler(MessageHandler(filters.TEXT & filters.User(ADMIN_ID), admin_text))
    app.add_handler(MessageHandler(filters.TEXT & filters.User(ADMIN_ID), steps))
    app.add_handler(MessageHandler(filters.VIDEO, video_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, user_movie))

    print("🔥 SUPER ELITE BOT ISHLADI")

    app.run_polling()

if __name__ == "__main__":
    main()
