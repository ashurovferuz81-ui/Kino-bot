from utils import db_utils

async def not_subscribed(user_id, bot):
    channels = db_utils.get_all_channels()
    not_joined = []

    for ch in channels:
        try:
            member = await bot.get_chat_member(ch, user_id)
            if member.status in ["left", "kicked"]:
                not_joined.append(ch)
        except:
            not_joined.append(ch)

    return not_joined
