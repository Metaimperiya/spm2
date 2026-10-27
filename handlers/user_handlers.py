from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder

from states import AdForm, RaceForm
from keyboards import main_menu, bottom_menu, cars_menu, accs_menu, money_menu, community_menu, custom_post_kb
from database import add_ad_to_db, get_approved_ads

router = Router()

@router.message(F.text == "/start")
async def start(message: Message, state: FSMContext):
    await state.clear()
    from bot import ADMIN_IDS
    is_admin = message.from_user.id in ADMIN_IDS
    text = f"🏁 **METAIMPERIYA | CPM 2 HUB** 🏁\n━━━━━━━━━━━━━━━━━━━━━━\n\nЗдарова, **{message.from_user.first_name}**!\n\n👇 *Жми кнопку «Подать объявление» внизу!*"
    await message.answer(text, reply_markup=bottom_menu(), parse_mode="Markdown")
    await message.answer("🚀 **Главное меню:**", reply_markup=main_menu(is_admin), parse_mode="Markdown")

@router.message(F.text == "🏠 В главное меню")
async def bottom_back(message: Message, state: FSMContext):
    await state.clear()
    from bot import ADMIN_IDS
    is_admin = message.from_user.id in ADMIN_IDS
    await message.answer("🚀 **Главное меню:**", reply_markup=main_menu(is_admin), parse_mode="Markdown")

@router.callback_query(F.data == "back_main")
async def back_main(call: CallbackQuery, state: FSMContext):
    await state.clear()
    from bot import ADMIN_IDS
    is_admin = call.from_user.id in ADMIN_IDS
    await call.message.edit_text("🚀 **Главное меню:**", reply_markup=main_menu(is_admin), parse_mode="Markdown")
    await call.answer()

@router.callback_query(F.data == "menu_cars")
async def show_cars(call: CallbackQuery):
    await call.message.edit_text("🚗 **Автомобили**", reply_markup=cars_menu())
    await call.answer()

@router.callback_query(F.data == "menu_accs")
async def show_accs(call: CallbackQuery):
    await call.message.edit_text("👤 **Аккаунты**", reply_markup=accs_menu())
    await call.answer()

@router.callback_query(F.data == "menu_money")
async def show_money(call: CallbackQuery):
    await call.message.edit_text("💵 **Монеты и Услуги**", reply_markup=money_menu())
    await call.answer()

@router.callback_query(F.data == "menu_community")
async def show_community(call: CallbackQuery):
    await call.message.edit_text("💬 **Наши каналы:**", reply_markup=community_menu())
    await call.answer()

# --- ПОДАЧА ОБЪЯВЛЕНИЯ ---
@router.message(F.text == "📢 Подать объявление")
async def bottom_create_ad(message: Message, state: FSMContext):
    await state.clear()
    kb = InlineKeyboardBuilder()
    kb.button(text="🚗 Продать машину", callback_data="car_sell")
    kb.button(text="🔄 Обменять машину", callback_data="car_trade")
    kb.button(text="👤 Продать аккаунт", callback_data="acc_sell")
    kb.button(text="⬅️ Назад", callback_data="back_main")
    kb.adjust(1, 1, 1, 1)
    await message.answer("📢 **Что выставляем?**", reply_markup=kb.as_markup())

@router.callback_query(F.data.in_({"car_sell", "car_trade", "acc_sell"}))
async def process_ad_type(call: CallbackQuery, state: FSMContext):
    action = call.data
    cat = "acc" if action == "acc_sell" else "car"
    await state.update_data(category=cat, ad_type=action, buttons=[])
    await state.set_state(AdForm.media)
    await call.message.edit_text("📸 **Отправь фото или видео:**", parse_mode="Markdown")
    await call.answer()

@router.message(AdForm.media, F.photo | F.video)
async def ad_media(message: Message, state: FSMContext):
    if message.photo:
        await state.update_data(media=message.photo[-1].file_id, media_type="photo")
    else:
        await state.update_data(media=message.video.file_id, media_type="video")
    await state.set_state(AdForm.title)
    await message.answer("📝 **Напиши заголовок:**", parse_mode="Markdown")

@router.message(AdForm.title, F.text)
async def ad_title(message: Message, state: FSMContext):
    await state.update_data(title=message.text)
    await state.set_state(AdForm.description)
    await message.answer("📝 **Напиши описание:**", parse_mode="Markdown")

@router.message(AdForm.description, F.text)
async def ad_desc(message: Message, state: FSMContext):
    await state.update_data(description=message.text)
    await state.set_state(AdForm.price)
    await message.answer("💰 **Укажи цену:**", parse_mode="Markdown")

@router.message(AdForm.price, F.text)
async def ad_price(message: Message, state: FSMContext):
    await state.update_data(price=message.text)
    await state.set_state(AdForm.game_id)
    await message.answer("🆔 **Введи свой игровой ID (только цифры!):**\n\n*Без ID пост не будет опубликован!*", parse_mode="Markdown")

@router.message(AdForm.game_id, F.text)
async def ad_game_id(message: Message, state: FSMContext):
    if not message.text.isdigit():
        await message.answer("⚠️ **Ошибка!** ID должен состоять только из цифр. Попробуй еще раз:")
        return
    await state.update_data(game_id=message.text)
    await state.set_state(AdForm.contact)
    await message.answer("📞 **Контакт для связи (@username):**", parse_mode="Markdown")

@router.message(AdForm.contact, F.text)
async def ad_contact(message: Message, state: FSMContext):
    await state.update_data(contact=message.text)
    await state.set_state(AdForm.buttons)
    await message.answer(
        "🔘 **Хочешь добавить свои кнопки под пост?**\n\n"
        "Отправь кнопку в формате: `Название | ссылка`\n"
        "Например: `🌐 Мой сайт | https://metaimperiya.com`\n\n"
        "Если кнопки не нужны, напиши /skip",
        parse_mode="Markdown"
    )

@router.message(AdForm.buttons, F.text == "/skip")
async def ad_skip_buttons(message: Message, state: FSMContext, bot: Bot):
    data = await state.get_data()
    from bot import ADMIN_IDS
    from keyboards import admin_approve_kb
    
    ad_id = add_ad_to_db(
        message.from_user.id, f"@{message.from_user.username}", data['category'], data['ad_type'], 
        data['title'], data['description'], data['price'], data['game_id'], data['contact'], data['media']
    )
    
    mod_text = f"🚨 **НОВОЕ ОБЪЯВЛЕНИЕ #{ad_id}** 🚨\n━━━━━━━━━━━━━━━━━━━━━━\n👤 **Автор:** @{message.from_user.username}\n📦 **Тип:** {data['ad_type']}\n📝 **Заголовок:** {data['title']}\n💰 **Цена:** {data['price']}\n🆔 **Игровой ID:** `{data['game_id']}`"
    
    for admin_id in ADMIN_IDS:
        try:
            await bot.send_photo(admin_id, photo=data['media'], caption=mod_text, reply_markup=admin_approve_kb(ad_id), parse_mode="Markdown")
        except: pass
        
    await state.clear()
    await message.answer(f"✅ **Объявление #{ad_id} отправлено на модерацию!**", reply_markup=main_menu(False), parse_mode="Markdown")

@router.message(AdForm.buttons, F.text)
async def ad_add_button(message: Message, state: FSMContext):
    data = await state.get_data()
    buttons = data.get("buttons", [])
    if "|" not in message.text:
        await message.answer("⚠️ Ошибка! Формат: `Название | ссылка`", parse_mode="Markdown")
        return
    buttons.append(message.text)
    await state.update_data(buttons=buttons)
    await message.answer(f"✅ Кнопка добавлена. Отправь еще или напиши /skip для отправки.")

# --- ОСТАЛЬНОЕ (ГОНКИ, КАТАЛОГ) ---
@router.callback_query(F.data == "join_race")
async def start_race(call: CallbackQuery, state: FSMContext):
    kb = InlineKeyboardBuilder()
    kb.button(text="🏎️ Дрэг", callback_data="race_drag")
    kb.button(text="🌪️ Дрифт", callback_data="race_drift")
    kb.button(text="⬅️ Назад", callback_data="back_main")
    kb.adjust(1, 1, 1)
    await state.set_state(RaceForm.race_type)
    await call.message.edit_text("🏁 **Выбери тип гонки:**", reply_markup=kb.as_markup())
    await call.answer()

@router.callback_query(RaceForm.race_type, F.data.startswith("race_"))
async def race_type(call: CallbackQuery, state: FSMContext):
    r_type = "Дрэг" if call.data == "race_drag" else "Дрифт"
    await state.update_data(race_type=r_type)
    await state.set_state(RaceForm.game_id)
    await call.message.edit_text(f"🏎️ **{r_type}**\n\n🆔 **Введи свой игровой ID (только цифры):**")
    await call.answer()

@router.message(RaceForm.game_id, F.text)
async def race_id(message: Message, state: FSMContext):
    if not message.text.isdigit():
        await message.answer("⚠️ **Ошибка!** ID должен быть числом. Попробуй еще раз:")
        return
    await state.update_data(game_id=message.text)
    await state.set_state(RaceForm.car)
    await message.answer("🚗 **На какой машине едешь?**")

@router.message(RaceForm.car, F.text)
async def race_car(message: Message, state: FSMContext, bot: Bot):
    data = await state.get_data()
    from bot import ADMIN_IDS
    username = f"@{message.from_user.username}" if message.from_user.username else message.from_user.first_name
    admin_text = f"🚨 **ЗАЯВКА НА ГОНКУ!** 🚨\n━━━━━━━━━━━━━━━━━━━━━━\n👤 **ТГ:** {username}\n🏁 **Тип:** {data['race_type']}\n🆔 **ID:** `{data['game_id']}`\n🚗 **Машина:** {message.text}"
    for admin_id in ADMIN_IDS:
        try: await bot.send_message(admin_id, admin_text, parse_mode="Markdown")
        except: pass
    await state.clear()
    await message.answer("✅ **Заявка принята!** Ожидай.", reply_markup=main_menu(False))

@router.callback_query(F.data.in_({"buy_car_catalog", "buy_acc_catalog"}))
async def show_catalog(call: CallbackQuery):
    cat = "car" if call.data == "buy_car_catalog" else "acc"
    ads = get_approved_ads(cat, "sale")
    if not ads:
        await call.message.edit_text("🛒 **Каталог пуст.**", reply_markup=main_menu(False))
        await call.answer()
        return
    ad = ads[0]
    text = f"🚗 **{ad[5]}**\n\n{ad[6]}\n\n💰 **Цена:** {ad[7]}\n🆔 **Игровой ID:** `{ad[8]}`\n📞 **Контакт:** {ad[9]}"
    kb = InlineKeyboardBuilder()
    kb.button(text="💬 Написать продавцу", url=f"https://t.me/{ad[9].replace('@', '')}")
    kb.button(text="⬅️ Назад", callback_data="back_main")
    kb.adjust(1, 1)
    await call.message.answer_photo(photo=ad[10], caption=text, reply_markup=kb.as_markup(), parse_mode="Markdown")
    await call.answer()
