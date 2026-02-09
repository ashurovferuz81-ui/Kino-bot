import asyncio
import asyncpg
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, CallbackQueryHandler,
    MessageHandler, filters, ContextTypes
)

# -------- CONFIG --------
TOKEN = "8426836407:AAHoXkQakddqyXZ_olNplG0_ov-3fhvrkSc"
ADMIN_ID = 5775388579

# PostgreSQL config
DB_HOST = "localhost"        # yoki Railway/PostgreSQL host
DB_USER = "postgres"
DB_PASS = "password"
DB_NAME = "kino_bot"

# -------- HELPERS --------
async def get_db_pool():
    return await asyncpg.create_pool(
        host=DB_HOST, user=DB_USER, password=DB_PASS, database=DB_NAME
    )

async def init_db(pool):
    async with pool.acquire() as conn:
        await conn.execute("""
        CREATE TABLE IF NOT EXISTS users(
            user_id BIGINT PRIMARY KEY,
            username TEXT,
            is_vip BOOLEAN DEFAULT FALSE
        );
        CREATE TABLE IF NOT EXISTS movies(
            code TEXT PRIMARY KEY,
            file_id TEXT
        );
        CREATE TABLE IF NOT EXISTS channels(
            link TEXT PRIMARY KEY
        );
        """)
        
# -------- START --------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    username = update.effective_user.username or update.effective_user.full_name

    pool = context.bot_data["pool"]
    async with pool.acquire() as conn:
        await conn.execute(
            "INSERT INTO users(user_id, username) VALUES($1,$2) ON CONFLICT(user_id) DO UPDATE SET username=$2",
            user_id, username
        )
        # Majburiy kanallarni olish
        rows = await conn.fetch("SELECT link FROM channels")
        buttons = []
        for row in rows:
            link = row['link']
            if link.startswith("@"):
                buttons.append([InlineKeyboardButton("📢 Kanalga kirish", url=f"https://t.me/{link[1:]}")])
            else:
                buttons.append([InlineKeyboardButton("📢 Kanalga kirish", url=link)])
        buttons.append([InlineKeyboardButton("✅ Obuna buldim", callback_data="sub_done")])
        buttons.append([InlineKeyboardButton("⭐ VIP olish", callback_data="vip_info")])
        await update.message.reply_text(
            "📢 Shu kanallarga obuna bo‘ling va 'Obuna buldim' tugmasini bosing",
            reply_markup=InlineKeyboardMarkup(buttons)
        )

# -------- ADMIN PANEL --------
async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("❌ Siz admin emassiz!")
        return
    keyboard = [
        [InlineKeyboardButton("🎬 Kino yuklash", callback_data="upload")],
        [InlineKeyboardButton("🗑 Kino o‘chirish", callback_data="delete_movie")],
        [InlineKeyboardButton("📢 Kanal qo‘shish", callback_data="add_channel")],
        [InlineKeyboardButton("🗑 Kanal o‘chirish", callback_data="del_channel")],
        [InlineKeyboardButton("⭐ VIP berish", callback_data="vip_add")],
        [InlineKeyboardButton("📊 Statistika", callback_data="stats")]
    ]
    await update.message.reply_text("👑 ADMIN PANEL", reply_markup=InlineKeyboardMarkup(keyboard))

# -------- CALLBACK HANDLER --------
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    await query.answer()
    pool = context.bot_data["pool"]

    # VIP info
    if query.data == "vip_info":
        await query.message.reply_text("⭐ VIP olish uchun yozing: @Sardorbeko008")
        return

    # Obuna buldim
    if query.data == "sub_done":
        # Majburiy kanallarni tekshirish
        async with pool.acquire() as conn:
            rows = await conn.fetch("SELECT link FROM channels")
        not_subscribed = []  # Hozir demo, haqiqiy tekshiruv uchun bot admin tokeni va get_chat_member kerak
        if not not_subscribed:
            await query.message.reply_text("✅ Endi kino kodini yuboring.")
        else:
            await query.message.reply_text(
                "❌ Hali barcha kanallarga obuna bo‘lmagansiz!\nQaysi kanallar: " + ", ".join(not_subscribed)
            )
        return

    # Admin tugmalar
    if user_id != ADMIN_ID:
        return

    async with pool.acquire() as conn:
        if query.data == "upload":
            context.user_data["admin_step"] = "await_code"
            await query.message.reply_text("🎬 Kino kodini yuboring:")
        elif query.data == "delete_movie":
            context.user_data["admin_step"] = "del_movie"
            await query.message.reply_text("🗑 O‘chirish uchun kino kodini yuboring:")
        elif query.data == "add_channel":
            context.user_data["admin_step"] = "add_channel"
            await query.message.reply_text("📢 Kanal username yoki link yuboring:")
        elif query.data == "del_channel":
            context.user_data["admin_step"] = "del_channel"
            await query.message.reply_text("🗑 Kanal username yoki link yuboring:")
        elif query.data == "vip_add":
            context.user_data["admin_step"] = "vip_add"
            await query.message.reply_text("⭐ VIP beriladigan user ID yuboring:")
        elif query.data == "stats":
            user_count = await conn.fetchval("SELECT COUNT(*) FROM users")
            movie_count = await conn.fetchval("SELECT COUNT(*) FROM movies")
            channel_count = await conn.fetchval("SELECT COUNT(*) FROM channels")
            await query.message.reply_text(
                f"📊 Statistika:\nFoydalanuvchilar: {user_count}\nKinolar: {movie_count}\nKanallar: {channel_count}"
            )

# -------- MESSAGE HANDLER --------
async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    pool = context.bot_data["pool"]
    text = update.message.text

    if user_id == ADMIN_ID:
        step = context.user_data.get("admin_step")
        if step == "await_code":
            context.user_data["new_code"] = text
            context.user_data["admin_step"] = "await_video"
            await update.message.reply_text("🎥 Endi kino videosini yuboring:")
        elif step == "await_video":
            if update.message.video:
                code = context.user_data.get("new_code")
                file_id = update.message.video.file_id
                async with pool.acquire() as conn:
                    await conn.execute(
                        "INSERT INTO movies(code, file_id) VALUES($1,$2) ON CONFLICT(code) DO UPDATE SET file_id=$2",
                        code, file_id
                    )
                await update.message.reply_text(f"✅ Kino {code} saqlandi!")
                context.user_data["admin_step"] = None
            else:
                await update.message.reply_text("❌ Iltimos, video yuboring!")
        elif step == "del_movie":
            async with pool.acquire() as conn:
                await conn.execute("DELETE FROM movies WHERE code=$1", text)
            await update.message.reply_text(f"🗑 Kino {text} o‘chirildi!")
            context.user_data["admin_step"] = None
        elif step == "add_channel":
            async with pool.acquire() as conn:
                await conn.execute("INSERT INTO channels(link) VALUES($1) ON CONFLICT DO NOTHING", text)
            await update.message.reply_text(f"📢 Kanal qo‘shildi: {text}")
            context.user_data["admin_step"] = None
        elif step == "del_channel":
            async with pool.acquire() as conn:
                await conn.execute("DELETE FROM channels WHERE link=$1", text)
            await update.message.reply_text(f"🗑 Kanal o‘chirildi: {text}")
            context.user_data["admin_step"] = None
        elif step == "vip_add":
            async with pool.acquire() as conn:
                await conn.execute("UPDATE users SET is_vip=TRUE WHERE user_id=$1", int(text))
            await update.message.reply_text(f"⭐ VIP berildi: {text}")
            context.user_data["admin_step"] = None
        return

    # Foydalanuvchi kino kodi
    async with pool.acquire() as conn:
        row = await conn.fetchrow("SELECT file_id FROM movies WHERE code=$1", text)
    if row:
        file_id = row["file_id"]
        await update.message.reply_video(file_id)
    else:
        await update.message.reply_text("❌ Kino kodi topilmadi!")

# -------- MAIN --------
async def main():
    pool = await get_db_pool()
    await init_db(pool)

    app = ApplicationBuilder().token(TOKEN).build()
    app.bot_data["pool"] = pool

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("admin", admin_panel))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler))
    app.add_handler(MessageHandler(filters.VIDEO, message_handler))

    print("🚀 GOD LEVEL KINO BOT ishga tushdi...")
    await app.run_polling()

if __name__ == "__main__":
    asyncio.run(main())
