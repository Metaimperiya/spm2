from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder

from states import AdForm, RaceForm
from keyboards import main_menu, bottom_menu, cars_menu, accs_menu, money_menu, community_menu
from database import add_ad_to_db, get_approved_ads, add_user_to_db

router = Router()

def is_admin_check(user):
    from bot import ADMIN_USERNAMES, ADMIN_IDS
    if user.id in ADMIN_IDS:
        return True
    if user.username and user.username.lower() in [u.lower() for u in ADMIN_USERNAMES]:
        return True
    return False

@router.message(F.text == "/start")
async def start(message: Message, state: FSMContext):
    await state.clear()
    username = f"@{message.from_user.username}" if message.from_user.username else "скрыт"
    add_user_to_db(message.from_user.id, username, message.from_user.first_name)
    is_admin = is_admin_check(message.from_user)
    text = (
        f"🏁 **METAIMPERIYA | CPM 2 HUB** 🏁\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"Здарова, **{message.from_user.first_name}**!\n\n"
        f"👇 *Жми кнопку внизу:*"
    )
    await message.answer(text, reply_markup=bottom_menu(), parse_mode="Markdown")
    await message.answer("🚀 **Главное меню:**", reply_markup=main_menu(is_admin), parse_mode="Markdown")

@router.message(F.text == "🏠 В главное меню")
async def bottom_back(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("🚀 **Главное меню:**", reply_markup=main_menu(is_admin_check(message.from_user)), parse_mode="Markdown")

@router.callback_query(F.data == "back_main")
async def back_main(call: CallbackQuery, state: FSMContext):
    await state.clear()
    await call.message.edit_text("🚀 **Главное меню:**", reply_markup=main_menu(is_admin_check(call.from_user)), parse_mode="Markdown")
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
    await call.message.edit_text("💬 **Наши каналы и группы:**", reply_markup=community_menu())
    await call.answer()

@router.message(F.text == "📢 Подать объявление")
async def bottom_create_ad(message: Message, state: FSMContext):
    await state.clear()
    is_admin = is_admin_check(message.from_user)
    kb = InlineKeyboardBuilder()
    if is_admin:
        kb.button(text="🚗 Продать машину (Админ)", callback_data="admin_post_car")
        kb.button(text="🔄 Обменять машину (Админ)", callback_data="admin_post_trade")
        kb.button(text="👤 Продать аккаунт (Админ)", callback_data="admin_post_acc")
        kb.button(text="📝 ПРОСТО ОБЪЯВЛЕНИЕ (С кнопками)", callback_data="admin_post_simple")
        kb.button(text="⬅️ Назад", callback_data="back_main")
        kb.adjust(1, 1, 1, 1, 1)
        await message.answer("👑 **Админ-меню подачи:**", reply_markup=kb.as_markup())
    else:
        kb.button(text="🚗 Продать машину", callback_data="car_sell")
        kb.button(text="🔄 Обменять машину", callback_data="car_trade")
        kb.button(text="👤 Продать аккаунт", callback_data="acc_sell")
        kb.button(text="⬅️ Назад", callback_data="back_main")
        kb.adjust(1, 1, 1, 1)
        await message.answer("📢 **Что выставляем?**", reply_markup=kb.as_markup())

@router.callback_query(F.data.in_({"car_sell", "car_trade", "acc_sell"}))
async def process_ad_type(call: CallbackQuery, state: FSMContext):
    cat = "acc" if call.data == "acc_sell" else "car"
    await state.update_data(category=cat, ad_type=call.data)
    await state.set_state(AdForm.media)
    await call.message.edit_text("📸 **Отправь фото или видео:**")
    await call.answer()

@router.message(AdForm.media, F.photo | F.video)
async def ad_media(message: Message, state: FSMContext):
    if message.photo:
        await state.update_data(media=message.photo[-1].file_id, media_type="photo")
    else:
        await state.update_data(media=message.video.file_id, media_type="video")
    await state.set_state(AdForm.title)
    await message.answer("📝 **Напиши заголовок:**")

@router.message(AdForm.title, F.text)
async def ad_title(message: Message, state: FSMContext):
    await state.update_data(title=message.text)
    await state.set_state(AdForm.description)
    await message.answer("📝 **Напиши описание:**")

@router.message(AdForm.description, F.text)
async def ad_desc(message: Message, state: FSMContext):
    await state.update_data(description=message.text)
    await state.set_state(AdForm.price)
    await message.answer("💰 **Укажи цену:**")

@router.message(AdForm.price, F.text)
async def ad_price(message: Message, state: FSMContext):
    await state.update_data(price=message.text)
    await state.set_state(AdForm.game_id)
    await message.answer("🆔 **Введи свой игровой ID (только цифры!):**")

@router.message(AdForm.game_id, F.text)
async def ad_game_id(message: Message, state: FSMContext):
    if not message.text.isdigit():
        await message.answer("⚠️ **Ошибка!** ID должен быть числом. Попробуй еще раз:")
        return
    await state.update_data(game_id=message.text)
    await state.set_state(AdForm.contact)
    await message.answer("📞 **Контакт для связи (@username):**")

@router.message(AdForm.contact, F.text)
async def ad_contact(message: Message, state: FSMContext):
    await state.update_data(contact=message.text)
    data = await state.get_data()
    ad_id = add_ad_to_db(
        message.from_user.id, f"@{message.from_user.username}", data['category'], data['ad_type'],
        data['title'], data['description'], data['price'], data['game_id'], data['contact'], data['media'],
    )
    mod_text = (
        f"🚨 **НОВОЕ ОБЪЯВЛЕНИЕ #{ad_id}** 🚨\n━━━━━━━━━━━━━━━━━━━━━━\n"
        f"👤 **Автор:** @{message.from_user.username}\n"
        f"📦 **Тип:** {data['ad_type']}\n"
        f"📝 **Заголовок:** {data['title']}\n"
        f"💰 **Цена:** {data['price']}\n"
        f"🆔 **Игровой ID:** `{data['game_id']}`"
    )
    from bot import ADMIN_IDS
    from keyboards import admin_approve_kb
    for admin_id in ADMIN_IDS:
        try:
            if data.get('media_type') == "photo":
                await message.bot.send_photo(admin_id, photo=data['media'], caption=mod_text, reply_markup=admin_approve_kb(ad_id), parse_mode="Markdown")
            else:
                await message.bot.send_video(admin_id, video=data['media'], caption=mod_text, reply_markup=admin_approve_kb(ad_id), parse_mode="Markdown")
        except Exception:
            pass
    await state.clear()
    await message.answer(f"✅ **Объявление #{ad_id} отправлено на модерацию!**", reply_markup=main_menu(False))

# ================== ГОНКИ ==================
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
    await call.message.edit_text(f"🏎️ **{r_type}**\n\n🆔 **Введи свой игровой ID:**")
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
async def race_car(message: Message, state: FSMContext):
    data = await state.get_data()
    username = f"@{message.from_user.username}" if message.from_user.username else message.from_user.first_name
    admin_text = (
        f"🚨 **ЗАЯВКА НА ГОНКУ!** 🚨\n━━━━━━━━━━━━━━━━━━━━━━\n"
        f"👤 **ТГ:** {username}\n"
        f"🏁 **Тип:** {data['race_type']}\n"
        f"🆔 **ID:** `{data['game_id']}`\n"
        f"🚗 **Машина:** {message.text}"
    )
    from bot import ADMIN_IDS
    for admin_id in ADMIN_IDS:
        try:
            await message.bot.send_message(admin_id, admin_text, parse_mode="Markdown")
        except Exception:
            pass
    await state.clear()
    await message.answer("✅ **Заявка принята!** Ожидай.", reply_markup=main_menu(False))

# ================== КАТАЛОГ ==================
@router.callback_query(F.data.in_({"buy_car_catalog", "buy_acc_catalog"}))
async def show_catalog(call: CallbackQuery):
    cat = "car" if call.data == "buy_car_catalog" else "acc"
    ads = get_approved_ads(cat, "car_sell" if cat == "car" else "acc_sell")
    if not ads:
        await call.message.edit_text("🛒 **Каталог пуст.**", reply_markup=main_menu(False))
        await call.answer()
        return
    for ad in ads[:5]:
        text = (
            f"🚗 **{ad[5]}**\n\n{ad[6]}\n\n"
            f"💰 **Цена:** {ad[7]}\n🆔 **Игровой ID:** `{ad[8]}`\n📞 **Контакт:** {ad[9]}"
        )
        kb = InlineKeyboardBuilder()
        contact = ad[9].replace('@', '') if ad[9] else ""
        if contact:
            kb.button(text="💬 Написать продавцу", url=f"https://t.me/{contact}")
        kb.button(text="⬅️ Назад", callback_data="back_main")
        kb.adjust(1, 1)
        try:
            await call.message.answer_photo(photo=ad[10], caption=text, reply_markup=kb.as_markup(), parse_mode="Markdown")
        except Exception:
            await call.message.answer(text, reply_markup=kb.as_markup(), parse_mode="Markdown")
    await call.answer()
