from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder
from states import AdminAdForm, AdminBroadcast
from keyboards import main_menu, admin_panel_kb, custom_post_kb, AUTO_BUTTONS
from database import approve_ad, get_ad_by_id, get_all_users

router = Router()

def is_admin_check(user):
    from bot import ADMIN_USERNAMES, ADMIN_IDS
    if user.id in ADMIN_IDS: return True
    if user.username and user.username.lower() in ADMIN_USERNAMES: return True
    return False

@router.callback_query(F.data.startswith("approve_"))
async def approve_ad_callback(call: CallbackQuery, bot: Bot):
    from bot import ADMIN_IDS, MAIN_CLAN_CHANNEL, SALE_CHANNEL, TRADE_CHANNEL, SELL_ACC_CHANNEL
    if call.from_user.id not in ADMIN_IDS: return
    
    ad_id = int(call.data.split("_")[1])
    approve_ad(ad_id)
    ad = get_ad_by_id(ad_id)
    if not ad: return
    
    post_text = f"🔥 **НОВОЕ ОБЪЯВЛЕНИЕ** 🔥\n━━━━━━━━━━━━━━━━━━━━━━\n\n{ad[5]}\n{ad[6]}\n\n💰 **Цена:** {ad[7]}\n🆔 **ID:** `{ad[8]}`\n👤 **Продавец:** {ad[2]}\n📞 **Контакт:** {ad[9]}"
    
    kb = InlineKeyboardBuilder()
    kb.button(text="🌐 Наш сайт", url="https://www.metaimperiya.com/")
    kb.button(text="💬 Написать админу", url="https://t.me/metaimperiya")
    kb.adjust(1, 1)
    
    target = SALE_CHANNEL
    if ad[4] == "car_trade": target = TRADE_CHANNEL
    elif ad[3] == "acc": target = SELL_ACC_CHANNEL
    
    for chat in {MAIN_CLAN_CHANNEL, target}:
        try:
            await bot.send_photo(chat, photo=ad[10], caption=post_text, reply_markup=kb.as_markup(), parse_mode="Markdown")
        except Exception as e: print(f"Ошибка: {e}")
            
    await call.message.edit_caption(caption=f"✅ **Объявление #{ad_id} ОДОБРЕНО!**")
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
    if not is_admin_check(call.from_user):
        await call.answer("⛔ Нет прав!", show_alert=True)
        return
    await call.message.edit_text("👑 **Админ-панель:**", reply_markup=admin_panel_kb())
    await call.answer()

# --- РАССЫЛКА ---
@router.callback_query(F.data == "admin_broadcast")
async def admin_broadcast_start(call: CallbackQuery, state: FSMContext):
    if not is_admin_check(call.from_user): return
    await state.set_state(AdminBroadcast.message)
    await call.message.edit_text(
        "📢 **Рассылка по всем пользователям**\n\n"
        "Отправь сообщение (текст, фото или видео), которое улетит всем, кто нажимал /start в боте.\n\n"
        "Для отмены напиши /cancel",
        parse_mode="Markdown"
    )
    await call.answer()

@router.message(AdminBroadcast.message, F.text == "/cancel")
async def admin_broadcast_cancel(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("❌ Рассылка отменена.", reply_markup=main_menu(True))

@router.message(AdminBroadcast.message)
async def admin_broadcast_send(message: Message, state: FSMContext, bot: Bot):
    users = get_all_users()
    await state.clear()
    
    await message.answer(f"⏳ **Начинаю рассылку для {len(users)} пользователей...**")
    
    success = 0
    fail = 0
    for user_id in users:
        try:
            await message.send_copy(chat_id=user_id)
            success += 1
        except Exception:
            fail += 1
    
    await message.answer(
        f"✅ **Рассылка завершена!**\n\n"
        f"Доставлено: {success}\n"
        f"Заблокировали бота: {fail}",
        reply_markup=main_menu(True)
    )

# --- СОЗДАНИЕ ПОСТА ---
@router.callback_query(F.data == "admin_post_simple")
async def admin_simple_post_start(call: CallbackQuery, state: FSMContext):
    if not is_admin_check(call.from_user): return
    await state.set_state(AdminAdForm.media)
    await call.message.edit_text("👑 **Просто объявление**\n\nОтправь фото/видео (или /skip):")
    await call.answer()

@router.message(AdminAdForm.media, F.photo | F.video)
async def admin_simple_media(message: Message, state: FSMContext):
    if message.photo:
        await state.update_data(media=message.photo[-1].file_id, media_type="photo")
    else:
        await state.update_data(media=message.video.file_id, media_type="video")
    await state.set_state(AdminAdForm.text)
    await message.answer("📝 **Текст поста:**")

@router.message(AdminAdForm.media, F.text == "/skip")
async def admin_simple_skip_media(message: Message, state: FSMContext):
    await state.update_data(media=None, media_type=None)
    await state.set_state(AdminAdForm.text)
    await message.answer("📝 **Текст поста:**")

@router.message(AdminAdForm.text, F.text)
async def admin_simple_get_text(message: Message, state: FSMContext):
    await state.update_data(text=message.text, buttons=[])
    await state.set_state(AdminAdForm.buttons)
    
    kb = InlineKeyboardBuilder()
    kb.button(text="✅ Добавить все кнопки автоматически", callback_data="auto_buttons")
    kb.adjust(1)
    
    await message.answer(
        "🔘 **Добавляем кнопки?**\n\n"
        "Нажми кнопку ниже, чтобы бот сам подставил все твои каналы и группы.\n"
        "Или напиши свои в формате `Название | ссылка`.\n\n"
        "Когда закончишь, напиши /done",
        reply_markup=kb.as_markup(),
        parse_mode="Markdown"
    )

@router.callback_query(F.data == "auto_buttons")
async def admin_auto_buttons(call: CallbackQuery, state: FSMContext):
    buttons = [f"{name} | {url}" for name, url in AUTO_BUTTONS]
    await state.update_data(buttons=buttons)
    await call.message.edit_text(
        "✅ **Все кнопки добавлены автоматически!**\n\n"
        "Теперь напиши /done, чтобы отправить пост во все каналы.",
        parse_mode="Markdown"
    )
    await call.answer()

@router.message(AdminAdForm.buttons, F.text == "/done")
async def admin_simple_finish(message: Message, state: FSMContext, bot: Bot):
    data = await state.get_data()
    from bot import MAIN_CLAN_CHANNEL, SALE_CHANNEL, TRADE_CHANNEL, SELL_ACC_CHANNEL
    
    buttons = data.get("buttons", [])
    if not buttons:
        buttons = ["🌐 Наш сайт | https://www.metaimperiya.com/", "💬 Написать админу | https://t.me/metaimperiya"]
        
    kb = custom_post_kb(buttons)
    channels = [MAIN_CLAN_CHANNEL, SALE_CHANNEL, TRADE_CHANNEL, SELL_ACC_CHANNEL]
    success = 0
    
    for chat in channels:
        try:
            if data.get("media_type") == "photo":
                await bot.send_photo(chat, photo=data["media"], caption=data["text"], reply_markup=kb, parse_mode="Markdown")
            elif data.get("media_type") == "video":
                await bot.send_video(chat, video=data["media"], caption=data["text"], reply_markup=kb, parse_mode="Markdown")
            else:
                await bot.send_message(chat, text=data["text"], reply_markup=kb, parse_mode="Markdown")
            success += 1
        except Exception as e: print(f"Ошибка: {e}")
            
    await state.clear()
    await message.answer(f"✅ **Пост отправлен в {success} каналов!**", reply_markup=main_menu(True))

@router.message(AdminAdForm.buttons, F.text)
async def admin_simple_add_button(message: Message, state: FSMContext):
    data = await state.get_data()
    buttons = data.get("buttons", [])
    if "|" not in message.text:
        await message.answer("⚠️ Ошибка! Формат: `Название | ссылка`", parse_mode="Markdown")
        return
    buttons.append(message.text)
    await state.update_data(buttons=buttons)
    await message.answer(f"✅ Кнопка добавлена. Отправь еще или напиши /done.")

@router.callback_query(F.data.in_({"admin_post_car", "admin_post_trade", "admin_post_acc"}))
async def admin_sell_start(call: CallbackQuery, state: FSMContext):
    if not is_admin_check(call.from_user): return
    await state.set_state(AdminAdForm.media)
    await call.message.edit_text("👑 **Админская продажа**\n\nОтправь фото/видео:")
    await call.answer()
