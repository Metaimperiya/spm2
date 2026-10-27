from aiogram import Router, Bot
from aiogram.types import ChatMemberUpdated
from aiogram.filters import ChatMemberUpdatedFilter, IS_NOT_MEMBER, IS_MEMBER

router = Router()

# ТВОЙ ID
ADMIN_ID = 123456789

@router.chat_member(ChatMemberUpdatedFilter(IS_NOT_MEMBER >> IS_MEMBER))
async def on_user_join(event: ChatMemberUpdated, bot: Bot):
    # Проверяем, что это группа/супергруппа (не канал)
    if event.chat.type in ["group", "supergroup"]:
        user = event.new_chat_member.user
        username = f"@{user.username}" if user.username else "нет юзернейма"
        
        text = (
            "🚪 **Новый участник в группе!**\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n"
            f"👤 **Имя:** {user.first_name}\n"
            f"🔗 **Юзернейм:** {username}\n"
            f"🆔 **ID:** `{user.id}`\n"
            f"💬 **Группа:** {event.chat.title}"
        )
        
        try:
            await bot.send_message(chat_id=ADMIN_ID, text=text, parse_mode="Markdown")
        except Exception as e:
            print(f"Не удалось отправить уведомление админу: {e}")
