import asyncio
import asyncpg
import nest_asyncio
from telegram import Update, ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler,
    ContextTypes, filters
)

nest_asyncio.apply()

TOKEN = "8426836407:AAHoXkQakddqyXZ_olNplG0_ov-3fhvrkSc"
ADMIN_ID = 5775388579

# ===== DATABASE CONFIG =====
DB_CONFIG = {
    "user": "postgres",
    "password": "fozEnbZYmphsRMKlZfsffKWPBZPRKgFR",
    "database": "railway",
    "host": "metro.proxy.rlwy.net",
    "port": 5432
}

# ===== ADMIN PANEL =====
def admin_keyboard():
    keyboard = [
        ["🎬 Kino qo‘shish", "🗑 Kino o‘chirish"],
        ["📢 Kanal qo‘shish", "❌ Kanal o‘chirish"],
        ["👥 Userlar", "📊 Statistika"],
        ["📣 Broadcast"]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

# ===== DATABASE INIT =====
async def init_db():
    conn = await asyncpg.connect(**DB_CONFIG)
    # Kinolar jadvali
    await conn.execute("""
        CREATE TABLE IF NOT EXISTS movies(
            code TEXT PRIMARY KEY,
            file_id TEXT,
            name TEXT
        )
    """)
    # Kanallar jadvali
    await conn.execute("""
        CREATE TABLE IF NOT EXISTS channels(
            channel TEXT PRIMARY KEY
        )
    """)
    # Foydalanuvchilar jadvali
    await conn.execute("""
        CREATE TABLE IF NOT EXISTS users(
            user_id BIGINT PRIMARY KEY,
            username TEXT
        )
    """)
    await conn.close()

# ===== DB FUNCTIONS =====
async def add_movie(code, file_id, name):
    conn = await asyncpg.connect(**DB_CONFIG)
    await conn.execute("INSERT INTO movies VALUES($1,$2,$3) ON CONFLICT (code) DO UPDATE SET file_id=$2, name=$3",
                       code, file_id, name)
    await conn.close()

async def del_movie(code):
    conn = await asyncpg.connect(**DB_CONFIG)
    await conn.execute("DELETE FROM movies WHERE code=$1", code)
    await conn.close()

async def get_movie(code):
    conn = await asyncpg.connect(**DB_CONFIG)
    row = await conn.fetchrow("SELECT file_id,name FROM movies WHERE code=$1", code)
    await conn.close()
    return row

async def add_channel(channel):
    conn = await asyncpg.connect(**DB_CONFIG)
    await conn.execute("INSERT INTO channels VALUES($1) ON CONFLICT DO NOTHING", channel)
    await conn.close()

async def del_channel(channel):
    conn = await asyncpg.connect(**DB_CONFIG)
    await conn.execute("DELETE FROM channels WHERE channel=$1", channel)
    await conn.close()

async def get_all_channels():
    conn = await asyncpg.connect(**DB_CONFIG)
    rows = await conn.fetch("SELECT channel FROM channels")
    await conn.close()
    return [r['channel'] for r in rows]

async def add_user(user_id, username):
    conn = await asyncpg.connect(**DB_CONFIG)
    await conn.execute("INSERT INTO users VALUES($1,$2) ON CONFLICT DO NOTHING", user_id, username)
    await conn.close()

async def get_all_users():
    conn = await asyncpg.connect(**DB_CONFIG)
    rows = await conn.fetch("SELECT user_id,username FROM users")
    await conn.close()
    return [(r['user_id'], r['username']) for r in rows]

# ===== CHECK SUB =====
async def not_subscribed(user_id, bot):
    channels = await get_all_channels()
    not_joined = []
    for ch in channels:
        if ch.startswith("@"):
            try:
                member = await bot.get_chat_member(ch, user_id)
                if member.status in ["left","kicked"]:
                    not_joined.append(ch)
            except:
                not_joined.append(ch)
        # https:// kanallar tekshirilmaydi
    return not_joined

# ===== START COMMAND =====
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    username = update.effective_user.username or "NoName"
    await add_user(user_id, username)

    if user_id == ADMIN_ID:
        await update.message.reply_text("🔥 ADMIN PANEL", reply_markup=admin_keyboard())
        return

    missing = await not_subscribed(user_id, context.bot)

    if missing:
        buttons = []
        for ch in await get_all_channels():
            url = f"https://t.me/{ch[1:]}" if ch.startswith("@") else ch
            buttons.append([InlineKeyboardButton("📢 Kanalga kirish", url=url)])
        buttons.append([InlineKeyboardButton("✅ Obuna bo‘ldim", callback_data="check_sub")])
        await update.message.reply_text("📢 Kanallarga obuna bo‘ling:", reply_markup=InlineKeyboardMarkup(buttons))
        return

    await update.message.reply_text("🎬 Kino kodini yuboring:")

# ===== BUTTON =====
async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    missing = await not_subscribed(query.from_user.id, context.bot)
    if missing:
        await query.answer("❌ Hali obuna bo‘lmagansiz!", show_alert=True)
        return
    await query.message.edit_text("✅ Endi kino kodini yuboring!")

# ===== VIDEO HANDLER =====
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
            await add_movie(context.user_data["code"], context.user_data["file"], text)
            context.user_data.clear()
            await update.message.reply_text("✅ Kino saqlandi!", reply_markup=admin_keyboard())
            return
        if text == "🗑 Kino o‘chirish":
            context.user_data["step"] = "del_movie"
            await update.message.reply_text("O‘chirish uchun kod yuboring:")
            return
        if step == "del_movie":
            await del_movie(text)
            context.user_data.clear()
            await update.message.reply_text("✅ Kino o‘chirildi!", reply_markup=admin_keyboard())
            return
        if text == "📢 Kanal qo‘shish":
            context.user_data["step"] = "add_channel"
            await update.message.reply_text("@username yoki https:// link yuboring:")
            return
        if step == "add_channel":
            await add_channel(text)
            context.user_data.clear()
            await update.message.reply_text("✅ Kanal qo‘shildi!", reply_markup=admin_keyboard())
            return
        if text == "❌ Kanal o‘chirish":
            context.user_data["step"] = "del_channel"
            await update.message.reply_text("@username yoki https:// link yuboring:")
            return
        if step == "del_channel":
            await del_channel(text)
            context.user_data.clear()
            await update.message.reply_text("✅ Kanal o‘chirildi!", reply_markup=admin_keyboard())
            return
        if text == "👥 Userlar":
            users = await get_all_users()
            msg = "👥 Userlar:\n" + "\n".join([f"{u[1]} | {u[0]}" for u in users])
            await update.message.reply_text(msg, reply_markup=admin_keyboard())
            return
        if text == "📊 Statistika":
            channels = await get_all_channels()
            movies_conn = await asyncpg.connect(**DB_CONFIG)
            total_movies = await movies_conn.fetchval("SELECT COUNT(*) FROM movies")
            await movies_conn.close()
            await update.message.reply_text(
                f"🎬 Kinolar: {total_movies}\n📢 Kanallar: {len(channels)}",
                reply_markup=admin_keyboard()
            )
            return
        # Broadcast
        if text == "📣 Broadcast":
            context.user_data["step"] = "broadcast"
            await update.message.reply_text("📣 Xabar matnini yuboring:")
            return
        if step == "broadcast":
            context.user_data["broadcast_msg"] = text
            context.user_data["step"] = "broadcast_count"
            await update.message.reply_text("Nechta foydalanuvchiga yuborilsin?")
            return
        if step == "broadcast_count":
            try:
                count = int(text)
            except:
                await update.message.reply_text("❌ Iltimos raqam kiriting!")
                return
            users = await get_all_users()
            for u in users[:count]:
                try:
                    await context.bot.send_message(u[0], context.user_data["broadcast_msg"])
                except:
                    continue
            context.user_data.clear()
            await update.message.reply_text(f"✅ Xabar {count} foydalanuvchiga yuborildi!", reply_markup=admin_keyboard())
            return

    # Foydalanuvchi logikasi
    missing = await not_subscribed(user_id, context.bot)
    if missing:
        await update.message.reply_text("❌ Avval majburiy kanallarga obuna bo‘ling! /start bosing.")
        return
    movie = await get_movie(text)
    if movie:
        await update.message.reply_video(movie['file_id'], caption=f"🎬 {movie['name']}")
    else:
        await update.message.reply_text("❌ Kino topilmadi!")

# ===== MAIN =====
async def main():
    await init_db()
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button, pattern="check_sub"))
    app.add_handler(MessageHandler(filters.VIDEO, video))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, messages))
    print("🔥 ULTRA ELITE PRO BOT ISHLADI!")
    await app.run_polling()

if __name__ == "__main__":
    asyncio.run(main())
