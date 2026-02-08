await query.message.reply_text("Kino kodini yuboring")
    elif query.data == "vip_add":
        db["admin_state"][str(user_id)] = {"step": "vip"}
        save_db(db)
        await query.message.reply_text("VIP qilinadigan user ID yuboring")
    elif query.data == "channel_add":
        db["admin_state"][str(user_id)] = {"step": "channel_add"}
        save_db(db)
        await query.message.reply_text("Kanal username yoki link yuboring")
    elif query.data == "channel_del":
        db["admin_state"][str(user_id)] = {"step": "channel_del"}
        save_db(db)
        await query.message.reply_text("O‘chiriladigan kanal username yoki link yuboring")
    elif query.data == "delete_movie":
        db["admin_state"][str(user_id)] = {"step": "delete_movie"}
        save_db(db)
        await query.message.reply_text("O‘chiriladigan kino kodini yuboring")
    elif query.data == "stats":
        await query.message.reply_text(
            f"👥 Users: {len(db['users'])}\n🎬 Kinolar: {len(db['movies'])}\n⭐ VIP: {len(db['vip'])}\n📢 Kanallar: {len(db['channels'])}"
        )

# -------- MESSAGE HANDLER (ADMIN TEXT) --------
async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text.strip()

    if user_id != ADMIN_ID:
        return  # Faqat admin ishlaydi

    state = db["admin_state"].get(str(user_id), {})
    step = state.get("step")

    if step == "code":
        db["admin_state"][str(user_id)]["code"] = text
        db["admin_state"][str(user_id)]["step"] = "video"
        save_db(db)
        await update.message.reply_text("Endi video yuboring")
    elif step == "video":
        if update.message.video:
            code = state.get("code")
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
    text = update.message.text.strip()

    # Obuna tekshirish
    not_subscribed = await check_subscription(user_id, context)
    if not not_subscribed:
        # Foydalanuvchi barcha kanallarga obuna bo‘lgan
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
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, user_send_code))
    app.add_handler(MessageHandler(filters.VIDEO, message_handler))

    print("Bot ishga tushdi...")
    app.run_polling()

if name == "main":
    main()
