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
            member = await bot.get_chat_member(channel, user_id)
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

    if not db["channels"] and not is_vip(user_id):
        await update.message.reply_text("Bot hali sozlanmagan.")
        return

    if not await check_subscription(user_id, context.bot):
        buttons = []
        for ch in db["channels"]:
            buttons.append([InlineKeyboardButton("📢 Kanalga kirish", url=f"https://t.me/{ch.replace('@','')}")])
        buttons.append([InlineKeyboardButton("✅ Obuna bo‘ldim", callback_data="check_sub")])

        await update.message.reply_text(
            "Botdan foydalanish uchun kanallarga obuna bo‘ling!",
            reply_markup=InlineKeyboardMarkup(buttons)
        )
        return

    await update.message.reply_text("🎬 Kino kodini yuboring!")

# -------- ADMIN PANEL --------
async def admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return

    keyboard = [
        [InlineKeyboardButton("🎬 Kino yuklash", callback_data="upload")],
        [InlineKeyboardButton("⭐ VIP qo‘shish", callback_data="vip_add")],
        [InlineKeyboardButton("📢 Kanal qo‘shish", callback_data="channel_add")],
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

    # SUB CHECK
    if query.data == "check_sub":
        if await check_subscription(user_id, context.bot):
            await query.message.reply_text("✅ Obuna tasdiqlandi!\nKino kodini yuboring.")
        else:
            await query.message.reply_text("❌ Hali barcha kanallarga obuna bo‘lmagansiz!")
        return

    if user_id != ADMIN_ID:
        return

    if query.data == "upload":
        db["admin_state"][str(user_id)] = {"step": "code"}
        save_db(db)
        await query.message.reply_text("Kino kodini yuboring")

    elif query.data == "vip_add":
        db["admin_state"][str(user_id)] = {"step": "vip"}
        save_db(db)
        await query.message.reply_text("VIP qilinadigan user ID yuboring")

    elif query.data == "channel_add":
        if len(db["channels"]) >= 7:
            await query.message.reply_text("7 tadan ortiq kanal qo‘shib bo‘lmaydi!")
            return
        db["admin_state"][str(user_id)] = {"step": "channel"}
        save_db(db)
        await query.message.reply_text("Kanal username yuboring (@kanal)")

    elif query.data == "stats":
        await query.message.reply_text(
            f"👥 Users: {len(db['users'])}\n🎬 Kinolar: {len(db['movies'])}\n⭐ VIP: {len(db['vip'])}"
        )

# -------- MESSAGE HANDLER --------
async def messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text

    state = db["admin_state"].get(str(user_id))

    # ---------- ADMIN ----------
    if user_id == ADMIN_ID and state:
        step = state["step"]

        # VIP
        if step == "vip":
            db["vip"].append(str(text))
            db["admin_state"].pop(str(user_id))
            save_db(db)
            await update.message.reply_text("User VIP qilindi ✅")
            return

        # CHANNEL
        if step == "channel":
            db["channels"].append(text.replace("@",""))
            db["admin_state"].pop(str(user_id))
            save_db(db)
            await update.message.reply_text("Kanal qo‘shildi ✅")
            return

        # MOVIE CODE
        if step == "code":
            db["admin_state"][str(user_id)] = {
                "step": "video",
                "code": text
            }
            save_db(db)
            await update.message.reply_text("Endi kino videosini yuboring")
            return

        # VIDEO
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
    if not await check_subscription(user_id, context.bot):
        await update.message.reply_text("Avval kanallarga obuna bo‘ling!")
        return

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
