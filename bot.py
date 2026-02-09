import sqlite3, nest_asyncio, datetime
from telegram import (
    Update, ReplyKeyboardMarkup,
    InlineKeyboardButton, InlineKeyboardMarkup
)
from telegram.ext import (
    ApplicationBuilder, CommandHandler,
    MessageHandler, CallbackQueryHandler,
    ContextTypes, filters
)

nest_asyncio.apply()

TOKEN = "8426836407:AAHoXkQakddqyXZ_olNplG0_ov-3fhvrkSc"
ADMIN_ID = 5775388579

# ===== DB =====
db = sqlite3.connect("god_bot.db", check_same_thread=False)
cur = db.cursor()

cur.execute("""CREATE TABLE IF NOT EXISTS movies(
    code TEXT PRIMARY KEY,
    file_id TEXT,
    name TEXT
)""")

cur.execute("""CREATE TABLE IF NOT EXISTS channels(
    channel TEXT PRIMARY KEY
)""")

cur.execute("""CREATE TABLE IF NOT EXISTS users(
    user_id INTEGER PRIMARY KEY,
    username TEXT,
    joined_at TEXT,
    movies_taken INTEGER DEFAULT 0
)""")

db.commit()

# ===== KEYBOARDS =====
def admin_kb():
    return ReplyKeyboardMarkup([
        ["🎬 Kino qo‘shish", "✏️ Kino tahrirlash"],
        ["🗑 Kino o‘chirish", "📢 Kanal qo‘shish"],
        ["❌ Kanal o‘chirish", "📂 Kinolar"],
        ["📢 Broadcast", "👥 Userlar"],
        ["📊 Statistika"]
    ], resize_keyboard=True)

# ===== SUB CHECK =====
async def check_sub(user_id, bot):
    cur.execute("SELECT channel FROM channels")
    chans = [c[0] for c in cur.fetchall()]
    missing = []

    for ch in chans:
        if ch.startswith("@"):
            try:
                m = await bot.get_chat_member(ch, user_id)
                if m.status in ("left", "kicked"):
                    missing.append(ch)
            except:
                missing.append(ch)
    return missing

def sub_buttons():
    cur.execute("SELECT channel FROM channels")
    buttons = []
    for c in cur.fetchall():
        ch = c[0]
        if ch.startswith("@"):
            url = f"https://t.me/{ch[1:]}"
        elif ch.startswith("https://"):
            url = ch
        else:
            continue
        buttons.append([InlineKeyboardButton("📢 Kanalga kirish", url=url)])
    buttons.append([InlineKeyboardButton("✅ Obuna bo‘ldim", callback_data="check")])
    return InlineKeyboardMarkup(buttons)

# ===== START =====
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    u = update.effective_user
    cur.execute(
        "INSERT OR IGNORE INTO users VALUES(?,?,?,0)",
        (u.id, u.username, str(datetime.date.today()))
    )
    db.commit()

    if u.id == ADMIN_ID:
        await update.message.reply_text("🔥 ADMIN PANEL", reply_markup=admin_kb())
        return

    miss = await check_sub(u.id, context.bot)
    if miss:
        await update.message.reply_text(
            "📢 Majburiy obuna:",
            reply_markup=sub_buttons()
        )
        return

    await update.message.reply_text("🎬 Kino kodi yoki nomini yozing:")

# ===== BUTTON =====
async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    miss = await check_sub(q.from_user.id, context.bot)
    if miss:
        await q.answer("❌ Obuna bo‘lmagansiz", show_alert=True)
        return
    await q.message.edit_text("✅ Endi kino yozing")

# ===== VIDEO =====
async def video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    if context.user_data.get("step") == "video":
        context.user_data["file"] = update.message.video.file_id
        context.user_data["step"] = "name"
        await update.message.reply_text("🎬 Kino nomini yozing:")

# ===== TEXT =====
async def text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    t = update.message.text
    uid = update.effective_user.id
    step = context.user_data.get("step")

    # ===== ADMIN =====
    if uid == ADMIN_ID:

        if t == "🎬 Kino qo‘shish":
            context.user_data["step"] = "code"
            await update.message.reply_text("Kino kodi:")
            return

        if step == "code":
            context.user_data["code"] = t
            context.user_data["step"] = "video"
            await update.message.reply_text("Videoni yuboring:")
            return

        if step == "name":
            cur.execute(
                "INSERT OR REPLACE INTO movies VALUES(?,?,?)",
                (context.user_data["code"], context.user_data["file"], t)
            )
            db.commit()
            context.user_data.clear()
            await update.message.reply_text("✅ Kino saqlandi", reply_markup=admin_kb())
            return

        if t == "🗑 Kino o‘chirish":
            context.user_data["step"] = "del"
            await update.message.reply_text("Kino kodi:")
            return

        if step == "del":
            cur.execute("DELETE FROM movies WHERE code=?", (t,))
            db.commit()
            context.user_data.clear()
            await update.message.reply_text("✅ O‘chirildi", reply_markup=admin_kb())
            return

        if t == "📢 Kanal qo‘shish":
            context.user_data["step"] = "add_ch"
            await update.message.reply_text("@kanal yoki https link:")
            return

        if step == "add_ch":
            cur.execute("INSERT OR IGNORE INTO channels VALUES(?)", (t,))
            db.commit()
            context.user_data.clear()
            await update.message.reply_text("✅ Kanal qo‘shildi", reply_markup=admin_kb())
            return

        if t == "❌ Kanal o‘chirish":
            context.user_data["step"] = "del_ch"
            await update.message.reply_text("Kanalni yozing:")
            return

        if step == "del_ch":
            cur.execute("DELETE FROM channels WHERE channel=?", (t,))
            db.commit()
            context.user_data.clear()
            await update.message.reply_text("✅ Kanal o‘chirildi", reply_markup=admin_kb())
            return

        if t == "📊 Statistika":
            cur.execute("SELECT COUNT(*) FROM movies")
            m = cur.fetchone()[0]
            cur.execute("SELECT COUNT(*) FROM users")
            u = cur.fetchone()[0]
            await update.message.reply_text(
                f"🎬 Kinolar: {m}\n👥 Userlar: {u}",
                reply_markup=admin_kb()
            )
            return

    # ===== USER =====
    miss = await check_sub(uid, context.bot)
    if miss:
        await update.message.reply_text("❌ Avval obuna bo‘ling", reply_markup=sub_buttons())
        return

    # SEARCH BY CODE OR NAME
    cur.execute(
        "SELECT file_id,name FROM movies WHERE code=? OR name LIKE ?",
        (t, f"%{t}%")
    )
    m = cur.fetchone()

    if m:
        await update.message.reply_video(m[0], caption=f"🎬 {m[1]}")
        cur.execute("UPDATE users SET movies_taken=movies_taken+1 WHERE user_id=?", (uid,))
        db.commit()
    else:
        await update.message.reply_text("❌ Topilmadi")

# ===== MAIN =====
def main():
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button, pattern="check"))
    app.add_handler(MessageHandler(filters.VIDEO, video))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text))
    print("🔥 GOD LEVEL BOT ISHLADI")
    app.run_polling()

if __name__ == "__main__":
    main()
