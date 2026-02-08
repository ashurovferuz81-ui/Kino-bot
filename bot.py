import json
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, CallbackQueryHandler,
    MessageHandler, filters, ContextTypes
)

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

# -------- VIP CHECK --------
def is_vip(user_id):
    return str(user_id) in db["vip"]

# -------- SUBSCRIPTION CHECK --------
async def check_subscription(user_id, bot):
    if is_vip(user_id):
        return True

    for channel in db["channels"]:
        try:
            member = await bot.get_chat_member(channel, user_id)
            if member.status in ["creator", "administrator", "member"]:
                continue
            else:
                return False
        except:
            return False
    return True

# -------- START COMMAND --------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    db["users"][str(user_id)] = True
    save_db(db)

    if not db["channels"] and not is_vip(user_id):
        await update.message.reply_text("Bot hali sozlanmagan.")
        return

    vip_button = InlineKeyboardButton("⭐ VIP olish", callback_data="vip_info")

    # Agar foydalanuvchi VIP emas va barcha kanallarga obuna bo‘lmagan bo‘lsa
    if not await check_subscription(user_id, context.bot):
        buttons = []
        for ch in db["channels"]:
            buttons.append([InlineKeyboardButton("📢 Kanalga kirish", url=f"https://t.me/{ch.replace('@','')}")])
        buttons.append([InlineKeyboardButton("✅ Obuna bo‘ldim", callback_data="check_sub")])
        buttons.append([vip_button])

        await update.message.reply_text(
            "Botdan foydalanish uchun kanallarga obuna bo‘ling!",
            reply_markup=InlineKeyboardMarkup(buttons)
        )
        return

    # Agar foydalanuvchi VIP yoki barcha kanallarga obuna bo‘lgan bo‘lsa
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

    # Foydalanuvchi obuna tekshiruvi
    if query.data == "check_sub":
        if await check_subscription(user_id, context.bot):
            await query.message.reply_text("✅ Obuna tasdiqlandi!\nKino kodini yuboring.")
        else:
            await query.message.reply_text("❌ Hali barcha kanallarga obuna bo‘lmagansiz!")
        return

    # VIP olish tugmasi
    if query.data == "vip_info":
        await query.message.reply_text("⭐ VIP olish uchun yozing: @Sardorbeko008")
        return

    # ADMIN tugmalari
    if user_id != ADMIN_ID:
        return

    if query.data == "upload":
        db["admin_state"][str(user_id)] = {"step": "code"}
        save_db(db)
        await query.message.reply_text("Kino kodini yuboring")

    elif query.data == "vip_add":
        db["admin_state"][str(user_id)] = {"step": "vip_add"}
        save_db(db)
        await query.message.reply_text("Foydalanuvchi ID sini yuboring VIP qo‘shish uchun:")

    elif query.data == "channel_add":
        db["admin_state"][str(user_id)] = {"step": "channel_add"}
        save_db(db)
        await query.message.reply_text("Kanal username sini yuboring (@username)")

    elif query.data == "channel_del":
        db["admin_state"][str(user_id)] = {"step": "channel_del"}
        save_db(db)
        await query.message.reply_text("O‘chirmoqchi bo‘lgan kanal username sini yuboring (@username)")

    elif query.data == "stats":
        total_users = len(db["users"])
        total_vip = len(db["vip"])
        total_channels = len(db["channels"])
        await query.message.reply_text(
            f"📊 Statistika:\n\nFoydalanuvchilar: {total_users}\nVIP: {total_vip}\nKanallar: {total_channels}"
        )

# -------- MESSAGE HANDLER (ADMIN) --------
async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text

    if user_id != ADMIN_ID:
        return

    state = db["admin_state"].get(str(user_id))
    if not state:
        return

    step = state.get("step")

    if step == "vip_add":
        db["vip"].append(str(text))
        db["admin_state"].pop(str(user_id))
        save_db(db)
        await update.message.reply_text(f"✅ {text} VIP ga qo‘shildi!")

    elif step == "channel_add":
        if text not in db["channels"]:
            db["channels"].append(text)
            save_db(db)
            await update.message.reply_text(f"✅ {text} kanali qo‘shildi!")
        else:
            await update.message.reply_text("⚠ Kanal allaqachon mavjud.")
        db["admin_state"].pop(str(user_id))

    elif step == "channel_del":
        if text in db["channels"]:
            db["channels"].remove(text)
            save_db(db)
            await update.message.reply_text(f"✅ {text} kanali o‘chirildi!")
        else:
            await update.message.reply_text("⚠ Kanal topilmadi.")
        db["admin_state"].pop(str(user_id])

    elif step == "code":
        # Kino kodi qo‘shish logikasi
        movie_code = text
        db["movies"][movie_code] = {"added_by": str(user_id)}
        db["admin_state"].pop(str(user_id))
        save_db(db)
        await update.message.reply_text(f"🎬 Kino kodi qo‘shildi: {movie_code}")

# -------- MAIN --------
async def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("admin", admin))
    app.add_handler(CallbackQueryHandler(button))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), message_handler))

    print("Bot ishlayapti...")
    await app.run_polling()

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
