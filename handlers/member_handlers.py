from aiogram import Router, Bot
from aiogram.types import ChatMemberUpdated
from aiogram.filters import ChatMemberUpdatedFilter, IS_NOT_MEMBER, IS_MEMBER
from bot import ADMIN_IDS

router = Router()

@router.chat_member(ChatMemberUpdatedFilter(IS_NOT_MEMBER >> IS_MEMBER))
async def on_user_join(event: ChatMemberUpdated, bot: Bot):
    if event.chat.type in ["group", "supergroup"]:
        user = event.new_chat_member.user
        username = f"@{user.username}" if user.username else "скрыт"
        text = f"🚪 **Новый участник!**\n━━━━━━━━━━━━━━━━━━━━━━\n👤 **Имя:** {user.first_name}\n🔗 **Юзернейм:** {username}\n🆔 **ID:** `{user.id}`\n💬 **Группа:** {event.chat.title}"
        for admin_id in ADMIN_IDS:
            try: await bot.send_message(admin_id, text, parse_mode="Markdown")
            except Exception: pass
