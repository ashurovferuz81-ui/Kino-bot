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

    # VIP olish tugmasi
    vip_button = [InlineKeyboardButton("⭐ VIP olish", callback_data="vip_info")]

    if not await check_subscription(user_id, context.bot):
        buttons = []
        for ch in db["channels"]:
            buttons.append([InlineKeyboardButton("📢 Kanalga kirish", url=f"https://t.me/{ch.replace('@','')}")])
        buttons.append([InlineKeyboardButton("✅ Obuna bo‘ldim", callback_data="check_sub")])
        buttons.append(vip_button)  # VIP tugmasini ham qo‘shamiz

        await update.message.reply_text(
            "Botdan foydalanish uchun kanallarga obuna bo‘ling!",
            reply_markup=InlineKeyboardMarkup(buttons)
        )
        return

    # User obuna bo‘lgan yoki VIP bo‘lsa
    await update.message.reply_text(
        "🎬 Kino kodini yuboring!",
        reply_markup=InlineKeyboardMarkup([ [vip_button] ])
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

    # SUB CHECK
    if query.data == "check_sub":
        if await check_subscription(user_id, context.bot):
            await query.message.reply_text("✅ Obuna tasdiqlandi!\nKino kodini yuboring.")
        else:
            await 

    # VIP info tugmasi userga
    if query.data == "vip_info":
        await query.message.reply_text("⭐ VIP olish uchun yozing: @Sardorbeko008")
        return

    if user_id != ADMIN_ID:
        return

    # ADMIN BUTTONS
    if query.data == "upload":
        db["admin_state"][str(user_id)] = {"step": "code"}
        save_db(db)
        await query.message.reply_text("Kino kodini yuboring")
