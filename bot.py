import nest_asyncio
from telegram import Update, ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes
from utils import db_utils, sub_utils

nest_asyncio.apply()

TOKEN = "8426836407:AAHoXkQakddqyXZ_olNplG0_ov-3fhvrkSc"
ADMIN_ID = 5775388579

# ===== Admin panel keyboard =====
def admin_keyboard():
    keyboard = [
        ["🎬 Kino qo‘shish", "🗑 Kino o‘chirish"],
        ["📢 Kanal qo‘shish", "❌ Kanal o‘chirish"],
        ["👥 Userlar", "📊 Statistika"]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

# ===== START =====
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    username = update.effective_user.username or "NoName"
    db_utils.add_user(user_id, username)

    if user_id == ADMIN_ID:
        await update.message.reply_text("🔥 ADMIN PANEL", reply_markup=admin_keyboard())
        return

    missing = await sub_utils.not_subscribed(user_id, context.bot)

    # Majburiy obuna
    if missing:
        buttons = []
        for ch in db_utils.get_all_channels():
            if ch.startswith("@") or ch.startswith("https://"):
                if ch.startswith("@"):
                    url = f"https://t.me/{ch[1:]}"
                else:
                    url = ch
                buttons.append([InlineKeyboardButton("📢 Kanalga kirish", url=url)])
        buttons.append([InlineKeyboardButton("✅ Obuna bo‘ldim", callback_data="check_sub")])
        await update.message.reply_text("📢 Kanallarga obuna bo‘ling:", reply_markup=InlineKeyboardMarkup(buttons))
        return

    await update.message.reply_text("🎬 Kino kodini yuboring:")

# ===== BUTTON =====
async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    missing = await sub_utils.not_subscribed(query.from_user.id, context.bot)
    if missing:
        await query.answer("❌ Hali obuna bo‘lmagansiz!", show_alert=True)
        return
    await query.message.edit_text("✅ Endi kino kodini yuboring!")

# ===== VIDEO =====
async def video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    if context.user_data.get("step") == "video":
        context.user_data["file"] = update.message.video.file_id
        context.user_data["step"] = "name"
        await update.message.reply_text("🎬 Kino nomini yozing:")

# ===== TEXT MESSAGES =====
async def messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    user_id = update.effective_user.id
    step = context.user_data.get("step")

    # Admin logikasi
    if user_id == ADMIN_ID:
        if text == "🎬 Kino qo‘shish":
            context.user_data["step"] = "code"
            await update.message.reply_text("Kino kodini yuboring:")
            return
        if step == "code":
            context.user_data["code"] = text
            context.user_data["step"] = "video"
            await update.message.reply_text("Endi videoni yuboring:")
            return
        if step == "name":
            db_utils.add_movie(context.user_data["code"], context.user_data["file"], text)
            context.user_data.clear()
            await update.message.reply_text("✅ Kino saqlandi!", reply_markup=admin_keyboard())
            return
        if text == "🗑 Kino o‘chirish":
            context.user_data["step"] = "del_movie"
            await update.message.reply_text("O‘chirish uchun kod yuboring:")
            return
        if step == "del_movie":
            db_utils.del_movie(text)
            context.user_data.clear()
            await update.message.reply_text("✅ Kino o‘chirildi!", reply_markup=admin_keyboard())
            return
        if text == "📢 Kanal qo‘shish":
            context.user_data["step"] = "add_channel"
            await update.message.reply_text("@username yoki https:// link yuboring:")
            return
        if step == "add_channel":
            db_utils.add_channel(text)
            context.user_data.clear()
            await update.message.reply_text("✅ Kanal qo‘shildi!", reply_markup=admin_keyboard())
            return
        if text == "❌ Kanal o‘chirish":
            context.user_data["step"] = "del_channel"
            await update.message.reply_text("@username yoki https:// link yuboring:")
            return
        if step == "del_channel":
            db_utils.del_channel(text)
            context.user_data.clear()
            await update.message.reply_text("✅ Kanal o‘chirildi!", reply_markup=admin_keyboard())
            return
        if text == "👥 Userlar":
            users = db_utils.get_all_users()
            msg = "👥 Userlar:\n" + "\n".join([f"{u[1]} | {u[0]}" for u in users])
            await update.message.reply_text(msg, reply_markup=admin_keyboard())
            return
        if text == "📊 Statistika":
            await update.message.reply_text(
                f"🎬 Kinolar: {len(db_utils.get_all_channels())}\n📢 Kanallar: {len(db_utils.get_all_channels())}",
                reply_markup=admin_keyboard()
            )
            return

    # Foydalanuvchi logikasi
    missing = await sub_utils.not_subscribed(user_id, context.bot)
    if missing:
        await update.message.reply_text("❌ Avval majburiy kanallarga obuna bo‘ling! /start bosing.")
        return
    movie = db_utils.get_movie(text)
    if movie:
        await update.message.reply_video(movie[0], caption=f"🎬 {movie[1]}")
    else:
        await update.message.reply_text("❌ Kino topilmadi!")

# ===== MAIN =====
def main():
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button, pattern="check_sub"))
    app.add_handler(MessageHandler(filters.VIDEO, video))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, messages))
    print("🔥 ULTRA ELITE BOT ISHLADI!")
    app.run_polling()

if __name__ == "__main__":
    main()
