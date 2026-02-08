import json
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler,
    filters, ContextTypes
)

# ---------------- CONFIG ----------------
TOKEN = "8426836407:AAHoXkQakddqyXZ_olNplG0_ov-3fhvrkSc"
ADMIN_ID = 5775388579
DB_FILE = "kino_bot_db.json"

# ---------------- DB ----------------
def load_db():
    try:
        with open(DB_FILE, "r") as f:
            return json.load(f)
    except:
        return {"users": {}, "movies": {}, "settings": {"channel_url": ""}, "admin_state": {}}

def save_db(db):
    with open(DB_FILE, "w") as f:
        json.dump(db, f, indent=4)

db = load_db()

# ---------------- HELPERS ----------------
def is_subscribed(user_id):
    user = db["users"].get(str(user_id))
    return user.get("subscribed", False) if user else False

def get_admin_state(user_id):
    return db["admin_state"].get(str(user_id), None)

def set_admin_state(user_id, state):
    if state:
        db["admin_state"][str(user_id)] = state
    else:
        db["admin_state"].pop(str(user_id), None)
    save_db(db)

# ---------------- START ----------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    username = update.message.from_user.username or update.message.from_user.full_name

    db["users"][str(user_id)] = {"username": username, "subscribed": False}
    save_db(db)

    channel_url = db["settings"].get("channel_url")
    if not channel_url:
        await update.message.reply_text("Bot hali admin tomonidan sozlanmagan. Iltimos, keyinroq qayta urinib ko‘ring.")
        return

    message_text = "Salom! Shu kanalga obuna buling va 'Obuna buldim' tugmasini bosing"
    keyboard = [
        [InlineKeyboardButton("Obuna bo‘lish", url=channel_url)],
        [InlineKeyboardButton("Obuna buldim ✅", callback_data="subscribed")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(message_text, reply_markup=reply_markup)

# ---------------- ADMIN PANEL ----------------
async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.from_user.id != ADMIN_ID:
        await update.message.reply_text("Siz admin emassiz!")
        return

    keyboard = [
        [InlineKeyboardButton("Kino yuklash", callback_data="upload_movie")],
        [InlineKeyboardButton("Kino ro'yxati", callback_data="list_movies")],
        [InlineKeyboardButton("Foydalanuvchilar ro'yxati", callback_data="list_users")],
        [InlineKeyboardButton("Bot statistikasi", callback_data="stats")],
        [InlineKeyboardButton("Majburiy obuna kanalini sozlash", callback_data="set_channel")]
    ]
    await update.message.reply_text("Admin panelga xush kelibsiz 👑", reply_markup=InlineKeyboardMarkup(keyboard))

# ---------------- CALLBACK HANDLER ----------------
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    await query.answer()

    # Foydalanuvchi obuna tugmasi
    if query.data == "subscribed":
        if str(user_id) in db["users"]:
            db["users"][str(user_id)]["subscribed"] = True
            save_db(db)
            await query.message.reply_text("Siz obuna bo‘ldingiz ✅\nEndi kino kodi yuboring.")
        return

    # Admin tugmalari
    if user_id != ADMIN_ID:
        await query.answer("Siz admin emassiz!")
        return

    if query.data == "upload_movie":
        set_admin_state(user_id, "awaiting_code")
        await query.message.reply_text("Kino kodini yuboring")
    elif query.data == "list_users":
        msg = "Foydalanuvchilar:\n"
        for uid, info in db["users"].items():
            status = "✅" if info.get("subscribed") else "❌"
            msg += f"{info['username']} ({uid}) - {status}\n"
        await query.message.reply_text(msg)
    elif query.data == "list_movies":
        if not db["movies"]:
            await query.message.reply_text("Hozircha kino yo‘q 🎬")
            return
        msg = "Saqlangan kinolar:\n"
        for code in db["movies"]:
            msg += f"- {code}\n"
        await query.message.reply_text(msg)
    elif query.data == "stats":
        users_count = len(db["users"])
        movies_count = len(db["movies"])
        await query.message.reply_text(f"📊 Statistika:\nFoydalanuvchilar: {users_count}\nKinolar: {movies_count}")
    elif query.data == "set_channel":
        await query.message.reply_text("Iltimos kanal URL sini yuboring (https://t.me/…)")

# ---------------- ADMIN TEXT HANDLER ----------------
async def admin_text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    text = update.message.text.strip()

    # Admin kanal URL sozlash
    if user_id == ADMIN_ID and text.startswith("https://t.me/"):
        db["settings"]["channel_url"] = text
        save_db(db)
        await update.message.reply_text(f"Majburiy obuna kanali sozlandi: {text}")
        return

    # Admin kino yuklash
    state = get_admin_state(user_id)
    if state == "awaiting_code":
        # admin kodi yubordi
        db["admin_state"]["current_code"] = text
        set_admin_state(user_id, "awaiting_video")
        await update.message.reply_text("Kino videosini yuboring")
    elif state == "awaiting_video":
        if update.message.video:
            code = db["admin_state"].get("current_code")
            file_id = update.message.video.file_id
            db["movies"][code] = file_id
            save_db(db)
            set_admin_state(user_id, None)
            db["admin_state"].pop("current_code", None)
            await update.message.reply_text(f"Kino saqlandi! Kod: {code}")
        else:
            await update.message.reply_text("Iltimos video yuboring")

# ---------------- FOYDALANUVCHI KODI ----------------
async def user_code_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    code = update.message.text.strip()
    channel_url = db["settings"].get("channel_url")

    if not channel_url:
        await update.message.reply_text("Bot hali admin tomonidan sozlanmagan.")
        return

    if not is_subscribed(user_id):
        await update.message.reply_text(f"Kanalga obuna bo‘lishingiz shart! 🔒")
        return

    if code in db["movies"]:
        file_id = db["movies"][code]
        await update.message.reply_video(file_id)
    else:
        await update.message.reply_text("Kino kodi topilmadi ❌")

# ---------------- MAIN ----------------
def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("admin", admin_panel))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, admin_text_handler))
    app.add_handler(MessageHandler(filters.VIDEO, admin_text_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, user_code_handler))

    print("Bot ishga tushdi...")
    app.run_polling()

if __name__ == "__main__":
    main()
