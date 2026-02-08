import json
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, CallbackQueryHandler,
    MessageHandler, filters, ContextTypes
)

# -------- CONFIG --------
TOKEN = "8426836407:AAHoXkQakddqyXZ_olNplG0_ov-3fhvrkSc"  # Test token
ADMIN_ID = 5775388579
DB_FILE = "elite_kino_db.json"

# -------- DATABASE --------
def load_db():
    try:
        with open(DB_FILE, "r") as f:
            return json.load(f)
    except:
        return {
            "users": {},
            "movies": {},
            "vip": [],
            "channels": [],
            "admin_state": {}
        }

def save_db(db):
    with open(DB_FILE, "w") as f:
        json.dump(db, f, indent=4)

db = load_db()

# -------- VIP --------
def is_vip(user_id):
    return str(user_id) in db["vip"]

# -------- OBUNA TEKSHIRUV --------
async def check_subscription(user_id, bot):
    if is_vip(user_id):
        return True
    for channel in db["channels"]:
        try:
            # Kanal username to'g'ri yuborilsin (hamisha @ bilan)
            ch = channel if channel.startswith("@") else f"@{channel}"
            member = await bot.get_chat_member(ch, user_id)
            if member.status in ["left", "kicked"]:
                return False
        except:
            return False
    return True

# -------- START --------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    db["users"][str(user_id)] = True
    save_db(db)

    vip_button = [InlineKeyboardButton("⭐ VIP olish", callback_data="vip_info")]

    if db["channels"] and not is_vip(user_id):
        buttons = []
        for ch in db["channels"]:
            buttons.append([InlineKeyboardButton("📢 Kanalga kirish", url=f"https://t.me/{ch.replace('@','')}")])
        buttons.append([InlineKeyboardButton("✅ Obuna buldim", callback_data="sub_done")])
        buttons.append(vip_button)

        await update.message.reply_text(
            "Botdan foydalanish uchun kanallarga obuna bo‘ling!",
            reply_markup=InlineKeyboardMarkup(buttons)
        )
        return

    await update.message.reply_text(
        "🎬 Kino kodini yuboring!",
        reply_markup=InlineKeyboardMarkup([[vip_button]])
    )

# -------- ADMIN PANEL --------
async def admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return

    keyboard = [
        [InlineKeyboardButton("🎬 Kino yuklash", callback_data="upload")],
        [InlineKeyboardButton("⭐ VIP qo‘shish", callback_data="vip_add")],
        [InlineKeyboardButton("📢 Kanal qo‘shish", callback_data="channel_add")],
        [InlineKeyboardButton("🗑 Kanalni o‘chirish", callback_data="channel_del")],
        [InlineKeyboardButton("📊 Statistika", callback_data="stats")]
    ]
    await update.message.reply_text(
        "👑 ADMIN PANEL",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# -------- BUTTON HANDLER --------
async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    await query.answer()

    # USER OBUNA BULDIM
    if query.data == "sub_done":
        await query.message.reply_text("✅ Endi kino kodini yuboring.")
        return

    # VIP info tugmasi
    if query.data == "vip_info":
        await query.message.reply_text("⭐ VIP olish uchun yozing: @Sardorbeko008")
        return

    # ADMIN TUGMALAR
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
        if len(db["channels"]) >= 7:
            await update.message.reply_text("7 tadan ortiq kanal qo‘shib bo‘lmaydi!")
            return
        db["admin_state"][str(user_id)] = {"step": "channel"}
        save_db(db)
        await update.message.reply_text("Kanal username yuboring (@kanal)")

    elif query.data == "channel_del":
        if not db["channels"]:
            await update.message.reply_text("Hech qanday kanal yo‘q!")
            return
        db["admin_state"][str(user_id)] = {"step": "channel_del"}
        save_db(db)
        await update.message.reply_text("O‘chiriladigan kanal username yuboring (@kanal)")

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

        # VIP qo‘shish
        if step == "vip":
            db["vip"].append(str(text))
            db["admin_state"].pop(str(user_id))
            save_db(db)
            await update.message.reply_text("User VIP qilindi ✅")
            return

        # Kanal qo‘shish
        if step == "channel":
            db["channels"].append(text if text.startswith("@") else f"@{text}")
            db["admin_state"].pop(str(user_id))
            save_db(db)
            await update.message.reply_text("Kanal qo‘shildi ✅")
            return

        # Kanal o‘chirish
        if step == "channel_del":
            ch = text if text.startswith("@") else f"@{text}"
            if ch in db["channels"]:
                db["channels"].remove(ch)
                save_db(db)
                await update.message.reply_text("Kanal o‘chirildi ✅")
            else:
                await update.message.reply_text("❌ Kanal topilmadi")
            db["admin_state"].pop(str(user_id))
            return

        # Kino kodi
        if step == "code":
            db["admin_state"][str(user_id)] = {"step": "video", "code": text}
            save_db(db)
            await update.message.reply_text("Endi kino videosini yuboring")
            return

        # Kino video
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
        # Foydalanuvchi kodi yubordi, kanalni tekshiramiz
        if not await check_subscription(user_id, context.bot):
            await update.message.reply_text("❌ Kanalga obuna bo‘lishingiz shart!")
            return
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
