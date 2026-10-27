from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

router = Router()

# Сюда мы будем складывать айдишники админов (пока для теста)
ADMINS = [123456789] 

def is_admin(user_id):
    return user_id in ADMINS

@router.callback_query(F.data == "admin_panel")
async def show_admin_panel(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        await call.answer("⛔ Нет прав!", show_alert=True)
        return
    await call.message.edit_text("👑 **Админ-панель** (в разработке)")
    await call.answer()
