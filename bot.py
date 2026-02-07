import aiosqlite
import nest_asyncio
import asyncio
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

nest_asyncio.apply()

# =====================
# TOKEN VA ADMIN
# =====================
TOKEN = "7974172226:AAFOIPcl7LJmxJcV5rG9AnclbPqQlBvZNLo"
ADMIN_ID = 5775388579

DB = "kino_full.db"


# =====================
# DATABASE
# =====================
async def init_db():
    async with aiosqlite.connect(DB) as db:
        await db.execute("""
        CREATE TABLE IF NOT EXISTS movies(
            code TEXT PRIMARY KEY,
            file_id TEXT
        )
        """)

        await db.execute("""
        CREATE TABLE IF NOT EXISTS users(
            user_id INTEGER PRIMARY KEY
        )
        """)

        await db.execute("""
        CREATE TABLE IF NOT EXISTS channel(
            username TEXT
        )
        """)

        await db.commit()


# =====================
# ADMIN KEYBOARD
# =====================
def admin_panel():
    return ReplyKeyboardMarkup([
        ["🎬 Kino qo‘shish", "❌ Kino o‘chirish"],
        ["📊 Statistika", "📃 Kino ro‘yxati"],
        ["🔐 Majburiy kanal qo‘shish", "🚫 Kanalni o‘chirish"],
        ["📢 Xabar yuborish"]
    ], resize_keyboard=True)


# =====================
# KANAL TEKSHIRISH
# =====================
async def check_sub(bot, user_id):
    async with aiosqlite.connect(DB) as db:
        cur = await db.execute("SELECT username FROM channel")
        channels = await cur.fetchall()

    for ch in channels:
        try:
            member = await bot.get_chat_member(ch[0], user_id)
            if member.status in ["left", "kicked"]:
                return False, ch[0]
        except:
            pass

    return True, None


# =====================
# START
# =====================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    # user saqlash
    async with aiosqlite.connect(DB) as db:
        await db.execute("INSERT OR IGNORE INTO users VALUES(?)", (user_id,))
        await db.commit()

    if user_id == ADMIN_ID:
        await update.message.reply_text(
            "🔥 Admin panelga xush kelibsiz!",
            reply_markup=admin_panel()
        )
        return

    ok, ch = await check_sub(context.bot, user_id)

    if not ok:
        await update.message.reply_text(
            f"❗ Botdan foydalanish uchun kanalga obuna bo‘ling:\n👉 {ch}"
        )
        return

    await update.message.reply_text("🎬 Kino kodini yuboring!")


# =====================
# MESSAGE
# =====================
async def message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    msg = update.message


    # ========= ADMIN =========

    if user_id == ADMIN_ID:

        # kino qo‘shish
        if msg.text == "🎬 Kino qo‘shish":
            context.user_data["step"] = "code"
            await msg.reply_text("Kino kodini yuboring:")
            return

        if context.user_data.get("step") == "code":
            context.user_data["code"] = msg.text
            context.user_data["step"] = "video"
            await msg.reply_text("Endi kinoni VIDEO qilib yuboring:")
            return

        if msg.video and context.user_data.get("step") == "video":
            code = context.user_data["code"]
            file_id = msg.video.file_id

            async with aiosqlite.connect(DB) as db:
                await db.execute(
                    "INSERT OR REPLACE INTO movies VALUES(?,?)",
                    (code, file_id)
                )
                await db.commit()

            context.user_data.clear()

            await msg.reply_text("✅ Kino saqlandi!")
            return


        # kino o‘chirish
        if msg.text == "❌ Kino o‘chirish":
            context.user_data["delete"] = True
            await msg.reply_text("O‘chirmoqchi bo‘lgan kino kodini yuboring:")
            return

        if context.user_data.get("delete"):
            async with aiosqlite.connect(DB) as db:
                await db.execute(
                    "DELETE FROM movies WHERE code=?",
                    (msg.text,)
                )
                await db.commit()

            context.user_data.clear()
            await msg.reply_text("✅ Kino o‘chirildi!")
            return


        # statistika
        if msg.text == "📊 Statistika":
            async with aiosqlite.connect(DB) as db:
                u = await db.execute("SELECT COUNT(*) FROM users")
                users = (await u.fetchone())[0]

                m = await db.execute("SELECT COUNT(*) FROM movies")
                movies = (await m.fetchone())[0]

            await msg.reply_text(
                f"👥 Foydalanuvchilar: {users}\n🎬 Kinolar: {movies}"
            )
            return


        # kino ro‘yxati
        if msg.text == "📃 Kino ro‘yxati":
            async with aiosqlite.connect(DB) as db:
                cur = await db.execute("SELECT code FROM movies")
                rows = await cur.fetchall()

            if not rows:
                await msg.reply_text("Kino yo‘q.")
                return

            text = "\n".join([r[0] for r in rows])
            await msg.reply_text(f"🎬 Kinolar:\n{text}")
            return


        # kanal qo‘shish
        if msg.text == "🔐 Majburiy kanal qo‘shish":
            context.user_data["channel"] = True
            await msg.reply_text("Kanal username yuboring:\nMasalan: @kanalim")
            return

        if context.user_data.get("channel"):
            async with aiosqlite.connect(DB) as db:
                await db.execute("DELETE FROM channel")
                await db.execute("INSERT INTO channel VALUES(?)", (msg.text,))
                await db.commit()

            context.user_data.clear()
            await msg.reply_text("✅ Kanal qo‘shildi!")
            return


        # kanalni o‘chirish
        if msg.text == "🚫 Kanalni o‘chirish":
            async with aiosqlite.connect(DB) as db:
                await db.execute("DELETE FROM channel")
                await db.commit()

            await msg.reply_text("✅ Majburiy kanal o‘chirildi!")
            return


        # reklama
        if msg.text == "📢 Xabar yuborish":
            context.user_data["broadcast"] = True
            await msg.reply_text("Yubormoqchi bo‘lgan xabarni kiriting:")
            return

        if context.user_data.get("broadcast"):
            async with aiosqlite.connect(DB) as db:
                cur = await db.execute("SELECT user_id FROM users")
                users = await cur.fetchall()

            for u in users:
                try:
                    await context.bot.send_message(u[0], msg.text)
                except:
                    pass

            context.user_data.clear()
            await msg.reply_text("✅ Xabar yuborildi!")
            return


    # ========= FOYDALANUVCHI =========

    ok, ch = await check_sub(context.bot, user_id)

    if not ok:
        await msg.reply_text(
            f"❗ Kanalga obuna bo‘ling:\n👉 {ch}"
        )
        return

    if msg.text:
        async with aiosqlite.connect(DB) as db:
            cur = await db.execute(
                "SELECT file_id FROM movies WHERE code=?",
                (msg.text,)
            )
            movie = await cur.fetchone()

        if movie:
            await msg.reply_video(movie[0])
        else:
            await msg.reply_text("❌ Kino topilmadi.")


# =====================
# MAIN
# =====================
async def main():
    await init_db()

    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.ALL, message))

    print("🔥 Kino bot ishga tushdi!")
    await app.run_polling()


if __name__ == "__main__":
    asyncio.run(main())
