import json
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes

# -------- CONFIG --------
TOKEN = "8426836407:AAHoXkQakddqyXZ_olNplG0_ov-3fhvrkSc"
ADMIN_ID = 5775388579
DB_FILE = "elite_kino_db.json"

# -------- DATABASE --------
def load_db():
    try:
        with open(DB_FILE, "r") as f:
            return json.load(f)
    except:
        return {"users": {}, "movies": {}, "vip": [], "channels": [], "admin_state": {}}

def save_db(db):
    with open(DB_FILE, "w") as f:
        json.dump(db, f, indent=4)

db = load_db()

# -------- VIP CHECK --------
def is_vip(user_id):
    return str(user_id) in db["vip"]

# -------- START --------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    username = update.effective_user.username or update.effective_user.full_name
    db["users"][str(user_id)] = {"username": username}
    save_db(db)

    # Inline tugmalar
    buttons = []
    for ch in db["channels"]:
        if ch.startswith("@"):
            buttons.append([InlineKeyboardButton("📢 Kanalga kirish", url=f"https://t.me/{ch[1:]}")])
        else:
            buttons.append([InlineKeyboardButton("📢 Kanalga kirish", url=ch)])

    buttons.append([InlineKeyboardButton("✅ Obuna buldim", callback_data="sub_done")])
    buttons.append([InlineKeyboardButton("⭐ VIP olish", callback_data="vip_info")])

    await update.message.reply_text(
        "📢 Shu kanallarga obuna bo‘ling va 'Obuna buldim' tugmasini bosing",
        reply_markup=InlineKeyboardMarkup(buttons)
    )

# -------- ADMIN PANEL --------
async def admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    keyboard = [
        [InlineKeyboardButton("🎬 Kino yuklash", callback_data="upload")],
        [InlineKeyboardButton("⭐ VIP qo‘shish", callback_data="vip_add")],
        [InlineKeyboardButton("📊 Statistika", callback_data="stats")],
        [InlineKeyboardButton("📢 Kanal qo‘shish", callback_data="channel_add")],
        [InlineKeyboardButton("🗑 Kanal o‘chirish", callback_data="channel_del")]
    ]
    await update.message.reply_text("👑 ADMIN PANEL", reply_markup=InlineKeyboardMarkup(keyboard))

# -------- BUTTON HANDLER --------
async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    await query.answer()

    # VIP info
    if query.data == "vip_info":
        await query.message.reply_text("⭐ VIP olish uchun yozing: @Sardorbeko008")
        return

    # Obuna buldim
    if query.data == "sub_done":
        await query.message.reply_text("✅ Endi kino kodini yuboring.")
        return

    # Admin tugmalar
    if user_id != ADMIN_ID:
        return

    if query.data == "upload":
        db["admin_state"][str(user_id)] = {"step": "code"}
        save_db(db)
        await query.message.reply_text("Kino kodini yuboring")
    elif query.data == "vip_add":
        db["admin_state"][str(user_id)] = {"step": "vip"}
        save_db(db)
        await update.message.reply_text("VIP qilinadigan user ID yuboring")
    elif query.data == "channel_add":
        db["admin_state"][str(user_id)] = {"step": "channel_add"}
        save_db(db)
        await update.message.reply_text("Kanal username yoki link yuboring")
    elif query.data == "channel_del":
        db["admin_state"][str(user_id)] = {"step": "channel_del"}
        save_db(db)
        await update.message.reply_text("O‘chiriladigan kanal username yoki link yuboring")
    elif query.data == "stats":
        await update.message.reply_text(
            f"👥 Users: {len(db['users'])}\n🎬 Kinolar: {len(db['movies'])}\n⭐ VIP: {len(db['vip'])}\n📢 Kanallar: {len(db['channels'])}"
        )

# -------- MESSAGE HANDLER --------
async def messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text
    state = db["admin_state"].get(str(user_id))

    # ---------- ADMIN ----------
    if user_id == ADMIN_ID and state:
        step = state["step"]

        if step == "vip":
            db["vip"].append(str(text))
            db["admin_state"].pop(str(user_id))
            save_db(db)
            await update.message.reply_text("User VIP qilindi ✅")
            return

        if step == "channel_add":
            db["channels"].append(text)
            db["admin_state"].pop(str(user_id))
            save_db(db)
            await update.message.reply_text("Kanal qo‘shildi ✅")
            return

        if step == "channel_del":
            if text in db["channels"]:
                db["channels"].remove(text)
                db["admin_state"].pop(str(user_id))
                save_db(db)
                await update.message.reply_text("Kanal o‘chirildi ✅")
            else:
                await update.message.reply_text("❌ Kanal topilmadi")
                db["admin_state"].pop(str(user_id))
            return

        if step == "code":
            db["admin_state"][str(user_id)] = {"step": "video", "code": text}
            save_db(db)
            await update.message.reply_text("Endi kino videosini yuboring")
            return

        if step == "video":
            if update.message.video or update.message.document:
                file_id = update.message.video.file_id if update.message.video else update.message.document.file_id
                code = state["code"]
                db["movies"][code] = file_id
                db["admin_state"].pop(str(user_id))
                save_db(db)
                await update.message.reply_text(f"✅ Kino saqlandi! Kod: {code}")
                return
            else:
                await update.message.reply_text("Video yoki file yuboring!")
            return

    # ---------- USER ----------
    if text in db["movies"]:
        await update.message.reply_video(db["movies"][text])
    else:
        await update.message.reply_text("❌ Kino topilmadi")

# -------- MAIN --------
def main():
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("admin", admin))
    app.add_handler(CallbackQueryHandler(button))
    app.add_handler(MessageHandler(filters.ALL, messages))
    print("ELITE BOT ISHGA TUSHDI 🔥")
    app.run_polling()

if __name__ == "__main__":
    main()
