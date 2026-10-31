from aiogram import Router, Bot
from aiogram.filters import ChatMemberUpdatedFilter, IS_NOT_MEMBER, IS_MEMBER
from aiogram.types import ChatMemberUpdated

router = Router()

@router.chat_member(ChatMemberUpdatedFilter(IS_NOT_MEMBER >> IS_MEMBER))
async def on_user_join(event: ChatMemberUpdated, bot: Bot):
    from bot import ADMIN_IDS
    if event.chat.type not in ("group", "supergroup"):
        return
    user = event.new_chat_member.user
    username = f"@{user.username}" if user.username else "скрыт"
    text = (
        f"🚪 **Новый участник!**\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"👤 **Имя:** {user.first_name}\n"
        f"🔗 **Юзернейм:** {username}\n"
        f"🆔 **ID:** `{user.id}`\n"
        f"💬 **Группа:** {event.chat.title}"
    )
    for admin_id in ADMIN_IDS:
        try:
            await bot.send_message(admin_id, text, parse_mode="Markdown")
        except Exception:
            pass
