import os
from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder
from states import AdminAdForm

router = Router()

# ТВОЙ ID (замени на свой)
ADMINS = [123456789] 

def is_admin(user_id):
    return user_id in ADMINS

# --- АДМИН ПАНЕЛЬ ---
@router.callback_query(F.data == "admin_panel")
async def show_admin_panel(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        await call.answer("⛔ Нет прав!", show_alert=True)
        return
    
    kb = InlineKeyboardBuilder()
    kb.button(text="📢 Создать рекламный пост", callback_data="admin_create_ad")
    kb.button(text="⬅️ Назад", callback_data="back_main")
    kb.adjust(1, 1)
    
    await call.message.edit_text(
        "👑 **Админ-панель**\n\nВыбери действие:",
        reply_markup=kb.as_markup(),
        parse_mode="Markdown"
    )
    await call.answer()

# --- СОЗДАНИЕ РЕКЛАМЫ ---
@router.callback_query(F.data == "admin_create_ad")
async def admin_start_ad(call: CallbackQuery, state: FSMContext):
    if not is_admin(call.from_user.id):
        await call.answer("⛔ Нет прав!", show_alert=True)
        return
    await state.set_state(AdminAdForm.photo)
    await call.message.edit_text(
        "👑 **Создание рекламы**\n\nОтправь фото или баннер для поста:",
        parse_mode="Markdown"
    )
    await call.answer()

@router.message(AdminAdForm.photo, F.photo)
async def admin_process_photo(message: Message, state: FSMContext):
    await state.update_data(photo=message.photo[-1].file_id)
    await state.set_state(AdminAdForm.description)
    await message.answer("📝 **Напиши текст рекламного поста:**", parse_mode="Markdown")

@router.message(AdminAdForm.description, F.text)
async def admin_process_description(message: Message, state: FSMContext, bot: Bot):
    data = await state.get_data()
    photo_id = data["photo"]
    ad_text = "🔥 **ОФИЦИАЛЬНОЕ СООБЩЕНИЕ METAIMPERIYA** 🔥\n\n" + message.text
    
    # Твои каналы
    channels = ["@cpm_2_clan", "@cpm_2_sale", "@cpm_2_trade", "@Sell_CPM_2_accounts"]
    
    # Кнопки под постом
    kb = InlineKeyboardBuilder()
    kb.button(text="🌐 Наш сайт", url="https://www.metaimperiya.com/")
    kb.button(text="🛡️ Клан", url="https://t.me/cpm_2_clan")
    kb.adjust(1, 1)
    
    success = 0
    for chat in channels:
        try:
            await bot.send_photo(
                chat_id=chat,
                photo=photo_id,
                caption=ad_text,
                reply_markup=kb.as_markup(),
                parse_mode="Markdown"
            )
            success += 1
        except Exception as e:
            print(f"Ошибка отправки в {chat}: {e}")
    
    await state.clear()
    await message.answer(
        f"✅ **Реклама отправлена!**\n\nУспешно: {success} из {len(channels)} каналов.",
        reply_markup=main_menu(True) if 'main_menu' in globals() else None,
        parse_mode="Markdown"
    )
