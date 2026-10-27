from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder

from states import AdForm, RaceForm
from keyboards import main_menu, bottom_menu, cars_menu, accs_menu, money_menu, community_menu
from database import add_ad_to_db, get_approved_ads

router = Router()

@router.message(F.text == "/start")
async def start(message: Message, state: FSMContext):
    await state.clear()
    from bot import ADMIN_IDS
    is_admin = message.from_user.id in ADMIN_IDS
    text = f"🏁 **METAIMPERIYA | CPM 2 HUB** 🏁\n━━━━━━━━━━━━━━━━━━━━━━\n\nЗдарова, **{message.from_user.first_name}**!\n\n👇 *Жми кнопку внизу или выбирай раздел!*"
    await message.answer(text, reply_markup=bottom_menu(), parse_mode="Markdown")
    await message.answer("🚀 **Главное меню:**", reply_markup=main_menu(is_admin), parse_mode="Markdown")

@router.message(F.text == "🏠 В главное меню")
async def bottom_back(message: Message, state: FSMContext):
    await state.clear()
    from bot import ADMIN_IDS
    is_admin = message.from_user.id in ADMIN_IDS
    await message.answer("🚀 **Главное меню:**", reply_markup=main_menu(is_admin), parse_mode="Markdown")

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

# --- ПРОДАЖА ---
@router.callback_query(F.data.in_({"car_sell", "car_trade", "acc_sell"}))
async def process_ad_type(call: CallbackQuery, state: FSMContext):
    action = call.data
    cat = "acc" if action == "acc_sell" else "car"
    await state.update_data(category=cat, ad_type=action)
    await state.set_state(AdForm.photo)
    await call.message.edit_text("📸 **Отправь фото/скриншот:**", parse_mode="Markdown")
    await call.answer()

@router.message(AdForm.photo, F.photo)
async def ad_photo(message: Message, state: FSMContext):
    await state.update_data(photo=message.photo[-1].file_id)
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
    await message.answer("🆔 **Твой игровой ID:**", parse_mode="Markdown")

@router.message(AdForm.game_id, F.text)
async def ad_id(message: Message, state: FSMContext):
    await state.update_data(game_id=message.text)
    await state.set_state(AdForm.contact)
    await message.answer("📞 **Контакт для связи (@username):**", parse_mode="Markdown")

@router.message(AdForm.contact, F.text)
async def ad_contact(message: Message, state: FSMContext, bot: Bot):
    await state.update_data(contact=message.text)
    data = await state.get_data()
    username = f"@{message.from_user.username}" if message.from_user.username else message.from_user.first_name
    
    ad_id = add_ad_to_db(
        message.from_user.id, username, data['category'], data['ad_type'], 
        data['title'], data['description'], data['price'], data['game_id'], data['contact'], data['photo']
    )
    
    # Отправляем на модерацию админам
    from bot import ADMIN_IDS
    from keyboards import admin_approve_kb
    mod_text = (
        f"🚨 **НОВОЕ ОБЪЯВЛЕНИЕ #{ad_id}** 🚨\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"👤 **Автор:** {username}\n"
        f"📦 **Тип:** {data['ad_type']}\n"
        f"📝 **Заголовок:** {data['title']}\n"
        f"💰 **Цена:** {data['price']}\n"
    )
    for admin_id in ADMIN_IDS:
        try:
            await bot.send_photo(admin_id, photo=data['photo'], caption=mod_text, reply_markup=admin_approve_kb(ad_id), parse_mode="Markdown")
        except Exception: pass

    await state.clear()
    await message.answer(f"✅ **Объявление #{ad_id} отправлено на модерацию!**", reply_markup=main_menu(False), parse_mode="Markdown")

# --- КАТАЛОГИ ПОКУПКИ ---
@router.callback_query(F.data.in_({"buy_car_catalog", "buy_acc_catalog"}))
async def show_catalog(call: CallbackQuery):
    cat = "car" if call.data == "buy_car_catalog" else "acc"
    ads = get_approved_ads(cat, "sale")
    
    if not ads:
        await call.message.edit_text("🛒 **Каталог пуст.** Админ еще не одобрил ни одного объявления.", reply_markup=main_menu(False))
        await call.answer()
        return
    
    # Показываем первое объявление (упрощенно)
    ad = ads[0]
    text = f"🚗 **{ad[5]}**\n\n{ad[6]}\n\n💰 **Цена:** {ad[7]}\n👤 **Продавец:** {ad[2]}\n📞 **Контакт:** {ad[9]}"
    kb = InlineKeyboardBuilder()
    kb.button(text="💬 Написать продавцу", url=f"https://t.me/{ad[9].replace('@', '')}")
    kb.button(text="⬅️ Назад", callback_data="back_main")
    kb.adjust(1, 1)
    await call.message.answer_photo(photo=ad[10], caption=text, reply_markup=kb.as_markup(), parse_mode="Markdown")
    await call.answer()

# --- ГОНКИ ---
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
    await state.set_state(RaceForm.game_nick)
    await call.message.edit_text(f"🏎️ **{r_type}**\n\nВведи свой **игровой ник**:")
    await call.answer()

@router.message(RaceForm.game_nick, F.text)
async def race_nick(message: Message, state: FSMContext):
    await state.update_data(game_nick=message.text)
    await state.set_state(RaceForm.game_id)
    await message.answer("🆔 **Твой игровой ID:**")

@router.message(RaceForm.game_id, F.text)
async def race_id(message: Message, state: FSMContext):
    await state.update_data(game_id=message.text)
    await state.set_state(RaceForm.car)
    await message.answer("🚗 **На какой машине едешь?**")

@router.message(RaceForm.car, F.text)
async def race_car(message: Message, state: FSMContext, bot: Bot):
    data = await state.get_data()
    from bot import ADMIN_IDS
    username = f"@{message.from_user.username}" if message.from_user.username else message.from_user.first_name
    admin_text = f"🚨 **ЗАЯВКА НА ГОНКУ!** 🚨\n━━━━━━━━━━━━━━━━━━━━━━\n👤 **ТГ:** {username}\n🎮 **Ник:** {data['game_nick']}\n🏁 **Тип:** {data['race_type']}\n🆔 **ID:** `{data['game_id']}`\n🚗 **Машина:** {message.text}\n━━━━━━━━━━━━━━━━━━━━━━\n👉 *Добавь его в друзья!*"
    for admin_id in ADMIN_IDS:
        try: await bot.send_message(admin_id, admin_text, parse_mode="Markdown")
        except Exception: pass
    await state.clear()
    await message.answer("✅ **Заявка принята!** Ожидай.", reply_markup=main_menu(False))
