from telegram import InlineKeyboardButton

async def check_sub(bot, user_id, channels):
    """
    Foydalanuvchining majburiy obunalarini tekshiradi.
    @ bilan boshlangan kanallar tekshiriladi, https bilan boshlanuvchilar tekshirilmaydi.
    """
    not_joined = []
    for ch in channels:
        if ch.startswith("@"):
            try:
                member = await bot.get_chat_member(ch, user_id)
                if member.status in ["left", "kicked"]:
                    not_joined.append(ch)
            except:
                not_joined.append(ch)
        # https:// kanallar tekshirilmaydi
    return not_joined

def generate_buttons(channels):
    """
    Kanalga kirish tugmalari.
    """
    buttons = []
    for ch in channels:
        if ch.startswith("@"):
            url = f"https://t.me/{ch[1:]}"
        else:
            url = ch
        buttons.append([InlineKeyboardButton("📢 Kanalga kirish", url=url)])
    buttons.append([InlineKeyboardButton("✅ Obuna bo‘ldim", callback_data="check_sub")])
    return buttons
