import sqlite3
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes

# ----------------------------
TOKEN = "8426836407:AAHoXkQakddqyXZ_olNplG0_ov-3fhvrkSc"
ADMIN_ID = 5775388579
# ----------------------------

# --- DATABASE ---
conn = sqlite3.connect("kino_pro.db", check_same_thread=False)
c = conn.cursor()

# Kinolar: code, file_id, type (normal/premium)
c.execute("CREATE TABLE IF NOT EXISTS movies(code TEXT PRIMARY KEY, file_id TEXT, type TEXT)")
# Foydalanuvchilar
c.execute("CREATE TABLE IF NOT EXISTS users(user_id INTEGER PRIMARY KEY)")
# Premium foydalanuvchilar
c.execute("CREATE TABLE IF NOT EXISTS premium(user_id INTEGER PRIMARY KEY)")
# Majburiy kanallar
c.execute("CREATE TABLE IF NOT EXISTS channels(username TEXT)")
conn.commit()

# --- ADMIN PANEL ---
def admin_panel():
    keyboard = [
        [InlineKeyboardButton("🎬 Kino qo‘shish", callback_data="add")],
        [InlineKeyboardButton("🗑 Kino o‘chirish", callback_data="delete")],
        [InlineKeyboardButton("💎 Premium obunachi", callback_data="premium")],
        [InlineKeyboardButton("📢 Majburiy kanal qo‘shish", callback_data="channel")],
        [InlineKeyboardButton("👥 Foydalanuvchilar", callback_data="users")],
        [InlineKeyboardButton("📊 Statistika", callback_data="stats")]
    ]
    return InlineKeyboardMarkup(keyboard)

# --- MAJBURIY OBUNA TEKSHIRISH ---
async def check_sub(bot, user_id):
    c.execute("SELECT username FROM channels")
    channels = c.fetchall()
    for ch in channels:
        try:
            member = await bot.get_chat_member(ch[0], user_id)
            if member.status not in ["member","administrator","creator"]:
                return ch[0]
        except:
            return ch[0]
    return None

# --- /START ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    c.execute("INSERT OR IGNORE INTO users VALUES(?)",(user_id,))
    conn.commit()
    if user_id == ADMIN_ID:
        await update.message.reply_text("🔥 Admin panelga xush kelibsiz!", reply_markup=admin_panel())
    else:
        channel = await check_sub(context.bot, user_id)
        if channel:
            await update.message.reply_text(f"❌ Botdan foydalanish uchun {channel} ga obuna bo‘ling!")
        else:
            await update.message.reply_text("🎬 Kino botga xush kelibsiz!\nKino kodi yuboring:")

# --- CALLBACK ---
async def buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.from_user.id != ADMIN_ID:
        await query.edit_message_text("❌ Faqat adminga!")
        return

    data = query.data
    if data == "add":
        context.user_data["step"] = "code"
        await query.message.reply_text("Kino kodi yuboring:")
    elif data == "delete":
        context.user_data["step"] = "delete"
        await query.message.reply_text("O‘chiriladigan kino kodi yuboring:")
    elif data == "channel":
        context.user_data["step"] = "channel"
        await query.message.reply_text("Majburiy kanal username yuboring (Masalan: @kinolar):")
    elif data == "premium":
        context.user_data["step"] = "premium"
        await query.message.reply_text("Premium foydalanuvchi ID kiriting:")
    elif data == "users":
        c.execute("SELECT user_id FROM users")
        users = c.fetchall()
        msg = f"👥 Jami foydalanuvchilar: {len(users)}\n"
        for u in users[:50]:
            msg += f"{u[0]}\n"
        await query.message.reply_text(msg)
    elif data == "stats":
        c.execute("SELECT COUNT(*) FROM movies")
        kino = c.fetchone()[0]
        c.execute("SELECT COUNT(*) FROM users")
        users = c.fetchone()[0]
        await query.message.reply_text(f"📊 Statistika\n👥 Users: {users}\n🎬 Kinolar: {kino}")

# --- MESSAGE HANDLER ---
async def messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text
    step = context.user_data.get("step")

    # --- ADMIN BOSQICHLARI ---
    if user_id == ADMIN_ID:
        if step == "code":
            context.user_data["code"] = text
            context.user_data["step"] = "video"
            await update.message.reply_text("Endi video yuboring:")
            return
        elif step == "delete":
            c.execute("DELETE FROM movies WHERE code=?",(text,))
            conn.commit()
            context.user_data.clear()
            await update.message.reply_text("🗑 Kino o‘chirildi.")
            return
        elif step == "channel":
            c.execute("INSERT INTO channels VALUES(?)",(text,))
            conn.commit()
            context.user_data.clear()
            await update.message.reply_text("✅ Majburiy kanal qo‘shildi.")
            return
        elif step == "premium":
            try:
                uid = int(text)
                c.execute("INSERT OR IGNORE INTO premium VALUES(?)",(uid,))
                conn.commit()
                context.user_data.clear()
                await update.message.reply_text(f"💎 Foydalanuvchi {uid} premium qilindi!")
            except:
                await update.message.reply_text("❌ ID raqam bo‘lishi kerak!")
            return
        elif step == "video":
            if update.message.video:
                file_id = update.message.video.file_id
                code = context.user_data.get("code")
                c.execute("INSERT OR REPLACE INTO movies VALUES(?,?,?)",(code,file_id,"normal"))
                conn.commit()
                context.user_data.clear()
                await update.message.reply_text("✅ Kino saqlandi!")
            else:
                await update.message.reply_text("❌ Iltimos, video yuboring!")
            return

    # --- USER KINO KO‘RISH ---
    channel = await check_sub(context.bot,user_id)
    if channel:
        await update.message.reply_text(f"❌ Botdan foydalanish uchun {channel} ga obuna bo‘ling!")
        return

    # Oddiy va premium kinolar
    c.execute("SELECT file_id,type FROM movies WHERE code=?",(text,))
    row = c.fetchone()
    if row:
        file_id, type_ = row
        if type_ == "premium":
            c.execute("SELECT 1 FROM premium WHERE user_id=?",(user_id,))
            if not c.fetchone():
                await update.message.reply_text("💎 Bu kino premium. Premium olish uchun @Sardorbeko008 ga yozing")
                return
        await update.message.reply_video(file_id)
    else:
        await update.message.reply_text("❌ Kino topilmadi!")

# --- VIDEO HANDLER ---
async def video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    if context.user_data.get("step")=="video" and update.message.video:
        file_id = update.message.video.file_id
        code = context.user_data.get("code")
        c.execute("INSERT OR REPLACE INTO movies VALUES(?,?,?)",(code,file_id,"normal"))
        conn.commit()
        context.user_data.clear()
        await update.message.reply_text("✅ Kino saqlandi!")

# --- APP ---
app = ApplicationBuilder().token(TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CallbackQueryHandler(buttons))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, messages))
app.add_handler(MessageHandler(filters.VIDEO, video))

print("🔥 PRO KINO BOT ISHLAYAPTI!")
app.run_polling()
