import json
import nest_asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, CallbackQueryHandler,
    MessageHandler, filters, ContextTypes
)

nest_asyncio.apply()  # asyncio patch (Railway / Pydroid)

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

# -------- CHECK SUBSCRIPTION --------
async def check_subscription(user_id, context):
    not_subscribed = []
    for ch in db["channels"]:
        try:
            member = await context.bot.get_chat_member(chat_id=ch, user_id=user_id)
            if member.status in ["left", "kicked"]:
                not_subscribed.append(ch)
        except:
            not_subscribed.append(ch)
    return not_subscribed

# -------- START --------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    username = update.effective_user.username or update.effective_user.full_name

    db["users"][str(user_id)] = {"username": username}
    save_db(db)

    buttons = []
    for ch in db["channels"]:
        if ch.startswith("@"):
            buttons.append([InlineKeyboardButton("📢 Kanalga kirish", url=f"https://t.me/{ch[1:]}")])
        elif ch.startswith("-100"):
            buttons.append([InlineKeyboardButton("📢 Kanalga kirish", url=f"https://t.me/c/{ch[4:]}/0")])
        elif ch.startswith("http"):
            buttons.append([InlineKeyboardButton("📢 Kanalga kirish", url=ch)])
        else:
            buttons.append([InlineKeyboardButton("📢 Kanalga kirish", url=ch)])

    buttons.append([InlineKeyboardButton("✅ Obuna buldim", callback_data="sub_done")])
    buttons.append([InlineKeyboardButton("⭐ VIP olish", callback_data="vip_info")])

    await update.message.reply_text(
        "📢 Shu kanallarga obuna bo‘ling va 'Obuna buldim' tugmasini bosing",
        reply_markup=InlineKeyboardMarkup(buttons)
    )

# -------- ADMIN PANEL --------
async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    keyboard = [
        [InlineKeyboardButton("🎬 Kino yuklash", callback_data="upload")],
        [InlineKeyboardButton("⭐ VIP qo‘shish", callback_data="vip_add")],
        [InlineKeyboardButton("📢 Kanal qo‘shish", callback_data="channel_add")],
        [InlineKeyboardButton("🗑 Kanal o‘chirish", callback_data="channel_del")],
        [InlineKeyboardButton("🗑 Kino o‘chirish", callback_data="delete_movie")],
        [InlineKeyboardButton("📊 Statistika", callback_data="stats")]
    ]
    await update.message.reply_text("👑 ADMIN PANEL", reply_markup=InlineKeyboardMarkup(keyboard))

# -------- CALLBACK HANDLER --------
async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    await query.answer()

    # ---------- FOYDALANUVCHI ----------
    if query.data == "vip_info":
        await query.message.reply_text("⭐ VIP olish uchun yozing: @Sardorbeko008")
        return

    if query.data == "sub_done":
        not_subscribed = await check_subscription(user_id, context)
        if not_subscribed:
            await query.message.reply_text(
                "❌ Hali barcha kanallarga obuna bo‘lmagansiz!\nQaysi kanallar: " + ", ".join(not_subscribed)
            )
        else:
            await query.message.reply_text("✅ Endi kino kodini yuboring.")
        return

    # ---------- ADMIN ----------
    if user_id != ADMIN_ID:
        return

    state = db["admin_state"].get(str(user_id), {})

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
    elif query.data == "delete_movie":
        db["admin_state"][str(user_id)] = {"step": "delete_movie"}
        save_db(db)
        await update.message.reply_text("O‘chiriladigan kino kodini yuboring")
    elif query.data == "stats":
        await update.message.reply_text(
            f"👥 Users: {len(db['users'])}\n🎬 Kinolar: {len(db['movies'])}\n⭐ VIP: {len(db['vip'])}\n📢 Kanallar: {len(db['channels'])}"
        )

# -------- MESSAGE HANDLER (ADMIN TEXT / VIDEO) --------
async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text.strip() if update.message.text else None

    if user_id != ADMIN_ID:
        return

    state = db["admin_state"].get(str(user_id), {})
    step = state.get("step")

    if step == "code":
        db["admin_state"][str(user_id)]["code"] = text
        db["admin_state"][str(user_id)]["step"] = "video"
        save_db(db)
        await update.message.reply_text("Endi video yuboring")
    elif step == "video":
        state = db["admin_state"].get(str(user_id), {})
        code = state.get("code")
        if update.message.video and code:
            db["movies"][code] = update.message.video.file_id
            save_db(db)
            db["admin_state"].pop(str(user_id), None)
            await update.message.reply_text(f"Kino saqlandi! Kod: {code}")
        else:
            await update.message.reply_text("❌ Iltimos video yuboring")
    elif step == "vip":
        db["vip"].append(text)
        save_db(db)
        db["admin_state"].pop(str(user_id), None)
        await update.message.reply_text(f"✅ VIP qo‘shildi: {text}")
    elif step == "channel_add":
        db["channels"].append(text)
        save_db(db)
        db["admin_state"].pop(str(user_id), None)
        await update.message.reply_text(f"✅ Kanal qo‘shildi: {text}")
    elif step == "channel_del":
        if text in db["channels"]:
            db["channels"].remove(text)
            save_db(db)
            await update.message.reply_text(f"🗑 Kanal o‘chirildi: {text}")
        db["admin_state"].pop(str(user_id), None)
    elif step == "delete_movie":
        if text in db["movies"]:
            db["movies"].pop(text)
            save_db(db)
            await update.message.reply_text(f"🗑 Kino o‘chirildi: {text}")
        db["admin_state"].pop(str(user_id), None)

# -------- USER SENDS KINO CODE --------
async def user_send_code(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text.strip() if update.message.text else None

    if not text:
        return

    not_subscribed = await check_subscription(user_id, context)
    if not not_subscribed:
        if text in db["movies"]:
            file_id = db["movies"][text]
            await update.message.reply_video(file_id)
        else:
            await update.message.reply_text("❌ Kino kodi topilmadi")
    else:
        await update.message.reply_text("❌ Avval kanallarga obuna bo‘ling!")

# -------- MAIN --------
def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("admin", admin_panel))
    app.add_handler(CallbackQueryHandler(button))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler))
    app.add_handler(MessageHandler(filters.VIDEO, message_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, user_send_code))

    print("Bot ishga tushdi...")
    app.run_polling()

if __name__ == "__main__":
    main()
