import os
import sqlite3
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

# --- TOKEN va ADMIN ---
TOKEN = "7974172226:AAFOIPcl7LJmxJcV5rG9AnclbPqQlBvZNLo"
ADMIN_ID = 5775388579
PREMIUM_ADMIN = "@Sardorbeko008"

# --- BAZA ---
db_path = os.path.join(os.getcwd(), "kino.db")  # Railway ishchi papkasi
db = sqlite3.connect(db_path, check_same_thread=False)
cursor = db.cursor()

cursor.execute("CREATE TABLE IF NOT EXISTS movies (code TEXT, file_id TEXT)")
cursor.execute("CREATE TABLE IF NOT EXISTS users (user_id INTEGER, premium INTEGER DEFAULT 0)")
cursor.execute("CREATE TABLE IF NOT EXISTS channels (username TEXT)")
cursor.execute("CREATE TABLE IF NOT EXISTS vip (user_id INTEGER)")
db.commit()

# --- Admin Panel ---
admin_panel = ReplyKeyboardMarkup([
    ["🎬 Kino qo‘shish", "🗑 Kino o‘chirish"],
    ["📊 Statistika", "📢 Reklama"],
    ["➕ Kanal", "➖ Kanal"],
    ["⭐ VIP qo‘shish", "❌ VIP o‘chirish"],
    ["🔒 Majburiy Obuna"]
], resize_keyboard=True)

# --- Obuna tekshirish ---
async def check_sub(user_id, bot):
    cursor.execute("SELECT username FROM channels")
    channels = cursor.fetchall()
    for ch in channels:
        try:
            member = await bot.get_chat_member(ch[0], user_id)
            if member.status in ["left", "kicked"]:
                return False, ch[0]
        except:
            return False, ch[0]
    return True, None

# --- START ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    cursor.execute("INSERT OR IGNORE INTO users VALUES (?,0)", (user_id,))
    db.commit()

    if user_id == ADMIN_ID:
        await update.message.reply_text("🔥 ADMIN PANEL", reply_markup=admin_panel)
        return

    ok, ch = await check_sub(user_id, context.bot)
    if not ok:
        await update.message.reply_text(f"❗ Avval {ch} kanaliga obuna bo‘ling!")
        return

    await update.message.reply_text(
        f"🎬 Kino kodini yuboring yoki nomini yozing!\n\n💎 Premium olish uchun {PREMIUM_ADMIN} ga yozing."
    )

# --- MESSAGE HANDLER ---
async def msg(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text

    # --- ADMIN ---
    if user_id == ADMIN_ID:
        # Kino qo‘shish
        if text == "🎬 Kino qo‘shish":
            context.user_data["state"] = "code"
            await update.message.reply_text("Kino kodini yuboring:")
            return

        if context.user_data.get("state") == "code":
            context.user_data["code"] = text
            context.user_data["state"] = "video"
            await update.message.reply_text("Videoni yuboring:")
            return

        if update.message.video and context.user_data.get("state") == "video":
            file_id = update.message.video.file_id
            code = context.user_data["code"]
            cursor.execute("INSERT INTO movies VALUES (?,?)", (code, file_id))
            db.commit()
            await update.message.reply_text("✅ Kino saqlandi!")
            context.user_data.clear()
            return

        # Kino o‘chirish
        if text == "🗑 Kino o‘chirish":
            context.user_data["state"] = "del"
            await update.message.reply_text("Kod yuboring:")
            return

        if context.user_data.get("state") == "del":
            cursor.execute("DELETE FROM movies WHERE code=?", (text,))
            db.commit()
            await update.message.reply_text("✅ O‘chirildi!")
            context.user_data.clear()
            return

        # Statistika
        if text == "📊 Statistika":
            cursor.execute("SELECT COUNT(*) FROM users")
            u = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM movies")
            m = cursor.fetchone()[0]
            await update.message.reply_text(f"👥 Users: {u}\n🎬 Kinolar: {m}")
            return

        # Reklama
        if text == "📢 Reklama":
            context.user_data["state"] = "ad"
            await update.message.reply_text("Xabar yuboring:")
            return

        if context.user_data.get("state") == "ad":
            cursor.execute("SELECT user_id FROM users")
            users = cursor.fetchall()
            for u in users:
                try:
                    await context.bot.send_message(u[0], text)
                except:
                    pass
            await update.message.reply_text("✅ Yuborildi!")
            context.user_data.clear()
            return

        # Kanal qo‘shish
        if text == "➕ Kanal":
            context.user_data["state"] = "addch"
            await update.message.reply_text("@kanal yuboring:")
            return

        if context.user_data.get("state") == "addch":
            cursor.execute("INSERT INTO channels VALUES (?)", (text,))
            db.commit()
            await update.message.reply_text("✅ Qo‘shildi!")
            context.user_data.clear()
            return

        # Kanal o‘chirish
        if text == "➖ Kanal":
            context.user_data["state"] = "delch"
            await update.message.reply_text("Kanal yuboring:")
            return

        if context.user_data.get("state") == "delch":
            cursor.execute("DELETE FROM channels WHERE username=?", (text,))
            db.commit()
            await update.message.reply_text("✅ O‘chirildi!")
            context.user_data.clear()
            return

        # VIP qo‘shish
        if text == "⭐ VIP qo‘shish":
            context.user_data["state"] = "vipadd"
            await update.message.reply_text("User ID yuboring:")
            return

        if context.user_data.get("state") == "vipadd":
            cursor.execute("INSERT INTO vip VALUES (?)", (text,))
            db.commit()
            await update.message.reply_text("✅ VIP qo‘shildi!")
            context.user_data.clear()
            return

        # Majburiy obuna
        if text == "🔒 Majburiy Obuna":
            context.user_data["state"] = "subch"
            await update.message.reply_text("Kanal username yuboring:")
            return

        if context.user_data.get("state") == "subch":
            cursor.execute("INSERT INTO channels VALUES (?)", (text,))
            db.commit()
            await update.message.reply_text("✅ Majburiy kanal qo‘shildi!")
            context.user_data.clear()
            return

    # --- FOYDALANUVCHI ---
    ok, ch = await check_sub(user_id, context.bot)
    if not ok:
        await update.message.reply_text(f"❗ Avval {ch} kanaliga obuna bo‘ling!")
        return

    cursor.execute("SELECT file_id FROM movies WHERE code LIKE ?", ('%'+text+'%',))
    movie = cursor.fetchone()

    if movie:
        await update.message.reply_video(movie[0])
    else:
        await update.message.reply_text("❌ Kino topilmadi.")


# --- MAIN ---
def main():
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.ALL, msg))

    print("🔥 SUPER ULTRA BOT ISHGA TUSHDI!")
    app.run_polling()


if __name__ == "__main__":
    main()
