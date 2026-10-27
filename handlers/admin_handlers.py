from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder
from states import AdminAdForm
from keyboards import main_menu, universal_post_keyboard
from database import approve_ad, get_ad_by_id

router = Router()

@router.callback_query(F.data.startswith("approve_"))
async def approve_ad_callback(call: CallbackQuery, bot: Bot):
    from bot import ADMIN_IDS, MAIN_CLAN_CHANNEL, SALE_CHANNEL, TRADE_CHANNEL, SELL_ACC_CHANNEL
    if call.from_user.id not in ADMIN_IDS: return
    
    ad_id = int(call.data.split("_")[1])
    approve_ad(ad_id)
    
    ad = get_ad_by_id(ad_id)
    if not ad: return
    
    # Собираем пост
    post_text = f"🔥 **НОВОЕ ОБЪЯВЛЕНИЕ** 🔥\n━━━━━━━━━━━━━━━━━━━━━━\n\n{ad[5]}\n{ad[6]}\n\n💰 **Цена:** {ad[7]}\n👤 **Продавец:** {ad[2]}\n📞 **Контакт:** {ad[9]}"
    markup = universal_post_keyboard()
    
    # Определяем канал
    target = SALE_CHANNEL
    if ad[4] == "car_trade": target = TRADE_CHANNEL
    elif ad[3] == "acc": target = SELL_ACC_CHANNEL
    
    for chat in {MAIN_CLAN_CHANNEL, target}:
        try:
            await bot.send_photo(chat, photo=ad[10], caption=post_text, reply_markup=markup, parse_mode="Markdown")
        except Exception as e:
            print(f"Ошибка: {e}")
            
    await call.message.edit_caption(caption=f"✅ **Объявление #{ad_id} ОДОБРЕНО и отправлено в каналы!**")
    await call.answer("Одобрено!")

@router.callback_query(F.data.startswith("reject_"))
async def reject_ad_callback(call: CallbackQuery):
    from bot import ADMIN_IDS
    if call.from_user.id not in ADMIN_IDS: return
    ad_id = int(call.data.split("_")[1])
    await call.message.edit_caption(caption=f"❌ **Объявление #{ad_id} ОТКЛОНЕНО.**")
    await call.answer("Отклонено")

@router.callback_query(F.data == "admin_panel")
async def admin_panel(call: CallbackQuery):
    from bot import ADMIN_IDS
    if call.from_user.id not in ADMIN_IDS:
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
    from bot import ADMIN_IDS
    if call.from_user.id not in ADMIN_IDS: return
    await state.set_state(AdminAdForm.photo)
    await call.message.edit_text("👑 **Реклама**\n\nОтправь фото/баннер:")
    await call.answer()

@router.message(AdminAdForm.photo, F.photo)
async def admin_ad_desc(message: Message, state: FSMContext):
    await state.update_data(photo=message.photo[-1].file_id)
    await state.set_state(AdminAdForm.description)
    await message.answer("📝 **Текст рекламы:**")

@router.message(AdminAdForm.description, F.text)
async def admin_ad_send(message: Message, state: FSMContext, bot: Bot):
    from bot import MAIN_CLAN_CHANNEL, SALE_CHANNEL, TRADE_CHANNEL, SELL_ACC_CHANNEL
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
