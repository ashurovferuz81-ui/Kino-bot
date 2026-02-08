import logging
import json
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    CallbackQueryHandler, ContextTypes, filters
)

# ---------------- CONFIG ----------------
TOKEN = "8426836407:AAHoXkQakddqyXZ_olNplG0_ov-3fhvrkSc"  # Sizning bot tokeningiz
ADMIN_ID = 5775388579  # Admin ID
CHANNEL_URL = "https://t.me/your_channel"  # Majburiy obuna kanali
DB_FILE = "kino_bot_db.json"

# ---------------- Logging ----------------
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# ---------------- DB Init ----------------
def load_db():
    try:
        with open(DB_FILE, "r") as f:
            return json.load(f)
    except:
        return {"users": {}, "movies": {}}

def save_db(db):
    with open(DB_FILE, "w") as f:
        json.dump(db, f, indent=4)

db = load_db()

# ---------------- Helpers ----------------
def is_subscribed(user_id):
    user = db["users"].get(str(user_id))
    if not user:
        return False
    return user.get("subscribed", False)

# ---------------- Commands ----------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    username = update.message.from_user.username or update.message.from_user.full_name

    db["users"][str(user_id)] = {"username": username, "subscribed": False}
    save_db(db)

    # Inline obuna tugmasi
    keyboard = [[InlineKeyboardButton("Obuna bo‘lish", url=CHANNEL_URL)],
                [InlineKeyboardButton("Obuna buldim ✅", callback_data="subscribed")]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        f"Salom {username}! 🎬\nBotni ishlatish uchun kanalimizga obuna bo‘ling va 'Obuna buldim' tugmasini bosing.",
        reply_markup=reply_markup
    )

# ---------------- Admin Panel ----------------
async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    if user_id != ADMIN_ID:
        await update.message.reply_text("Siz admin emassiz!")
        return

    keyboard = [
        [InlineKeyboardButton("Kino yuklash", callback_data="upload_movie")],
        [InlineKeyboardButton("Foydalanuvchilar ro'yxati", callback_data="list_users")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Admin panelga xush kelibsiz:", reply_markup=reply_markup)

# ---------------- Callback Handler ----------------
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    await query.answer()

    # Foydalanuvchi obuna bo‘ldim tugmasi
    if query.data == "subscribed":
        if str(user_id) in db["users"]:
            db["users"][str(user_id)]["subscribed"] = True
            save_db(db)
            await query.message.reply_text("Siz obuna bo‘ldingiz ✅\nEndi kodni yuboring, kino chiqarib beraman.")
        else:
            await query.message.reply_text("Avval /start bosing!")
        return

    # Admin tugmalari
    if user_id != ADMIN_ID:
        await query.answer("Siz admin emassiz!")
        return

    if query.data == "upload_movie":
        await query.message.reply_text("Kino kodi va video fayl yuboring (caption: kod)")
    elif query.data == "list_users":
        msg = "Foydalanuvchilar:\n\n"
        for uid, info in db["users"].items():
            status = "✅" if info.get("subscribed") else "❌"
            msg += f"{info['username']} ({uid}) - {status}\n"
        await query.message.reply_text(msg)

# ---------------- Kino Yuklash ----------------
async def receive_movie(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    if user_id != ADMIN_ID:
        return

    if update.message.video and update.message.caption:
        code = update.message.caption.strip()
        file_id = update.message.video.file_id
        db["movies"][code] = file_id
        save_db(db)
        await update.message.reply_text(f"Kino saqlandi! Kod: {code}")
    else:
        await update.message.reply_text("Iltimos, video faylni caption bilan yuboring.")

# ---------------- Foydalanuvchi kodi orqali kino olish ----------------
async def user_code_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    code = update.message.text.strip()

    if not is_subscribed(user_id):
        await update.message.reply_text("Kanalga obuna bo‘lishingiz shart! 🔒")
        return

    if code in db["movies"]:
        file_id = db["movies"][code]
        await update.message.reply_video(file_id)
    else:
        await update.message.reply_text("Kino kodi topilmadi ❌")

# ---------------- Main ----------------
def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("admin", admin_panel))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.VIDEO & filters.Caption, receive_movie))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, user_code_handler))

    print("Bot ishga tushdi...")
    app.run_polling()

if __name__ == "__main__":
    main()
