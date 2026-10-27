from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder
from states import AdminAdForm
from keyboards import main_menu, universal_post_keyboard
from bot import ADMIN_IDS, MAIN_CLAN_CHANNEL, SALE_CHANNEL, TRADE_CHANNEL, SELL_ACC_CHANNEL

router = Router()

def is_admin(user_id): return user_id in ADMIN_IDS

@router.callback_query(F.data == "admin_panel")
async def admin_panel(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        await call.answer("⛔ Нет прав!", show_alert=True)
        return
    kb = InlineKeyboardBuilder()
    kb.button(text="📢 Создать рекламу", callback_data="admin_create_ad")
    kb.button(text="⬅️ Назад", callback_data="back_main")
    kb.adjust(1, 1)
    await call.message.edit_text("👑 **Админ-панель:**", reply_markup=kb.as_markup())
    await call.answer()

@router.callback_query(F.data == "admin_create_ad")
async def admin_ad_photo(call: CallbackQuery, state: FSMContext):
    if not is_admin(call.from_user.id): return
    await state.set_state(AdminAdForm.photo)
    await call.message.edit_text("👑 **Реклама**\n\nОтправь фото/баннер:")
    await call.answer()

@router.message(AdminAdForm.photo, F.photo)
async def admin_ad_desc(message: Message, state: FSMContext):
    await state.update_data(photo=message.photo[-1].file_id)
    await state.set_state(AdminAdForm.description)
    await message.answer("📝 **Текст рекламы:**")

@router.message(AdminAdForm.description, F.text)
async def admin_ad_send(message: Message, state: FSMContext, bot):
    data = await state.get_data()
    ad_text = "🔥 **ОФИЦИАЛЬНОЕ СООБЩЕНИЕ** 🔥\n\n" + message.text
    markup = universal_post_keyboard()
    channels = [MAIN_CLAN_CHANNEL, SALE_CHANNEL, TRADE_CHANNEL, SELL_ACC_CHANNEL]
    success = 0
    for chat in channels:
        try:
            await bot.send_photo(chat, photo=data["photo"], caption=ad_text, reply_markup=markup, parse_mode="Markdown")
            success += 1
        except Exception as e:
            print(f"Ошибка: {e}")
    await state.clear()
    await message.answer(f"✅ **Реклама улетела в {success} канала!**", reply_markup=main_menu(True))
