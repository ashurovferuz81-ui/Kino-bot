from utils import db_utils

async def not_subscribed(user_id, bot):
    """
    Majburiy obuna tekshiruvi:
    - Faqat @username kanallar tekshiriladi
    - https:// kanallar tekshirilmaydi, lekin tugma ishlaydi
    """
    channels = db_utils.get_all_channels()
    not_joined = []

    for ch in channels:
        if ch.startswith("@"):  # faqat @ tekshirish
            try:
                member = await bot.get_chat_member(ch, user_id)
                if member.status in ["left", "kicked"]:
                    not_joined.append(ch)
            except:
                not_joined.append(ch)
        # https:// kanallar tekshirilmaydi

    return not_joined
