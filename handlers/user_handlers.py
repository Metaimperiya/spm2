import os
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder

from states import AdForm, RaceForm
from keyboards import main_menu, bottom_menu, cars_menu, accs_menu, money_menu, community_menu, confirm_menu
from database import get_channels, add_ad

router = Router()

@router.message(F.text == "/start")
async def start(message: Message, state: FSMContext):
    await state.clear()
    text = (
        "🏁 **METAIMPERIYA | CPM 2 HUB** 🏁\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"Здарова, **{message.from_user.first_name}**!\n\n"
        "Добро пожаловать на главную торговую площадку CPM 2.\n"
        "👇 *Выбирай нужный раздел:*"
    )
    await message.answer(text, reply_markup=bottom_menu(), parse_mode="Markdown")
    await message.answer("🚀 **Главное меню:**", reply_markup=main_menu(), parse_mode="Markdown")

@router.message(F.text == "🏠 В главное меню")
async def open_bottom_menu(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("🚀 **Главное меню:**", reply_markup=main_menu(), parse_mode="Markdown")

@router.callback_query(F.data == "back_main")
async def back_main(call: CallbackQuery, state: FSMContext):
    await state.clear()
    await call.message.edit_text("🚀 **Главное меню:**", reply_markup=main_menu(), parse_mode="Markdown")
    await call.answer()

# --- ПОДАЧА ОБЪЯВЛЕНИЯ (ГЛАВНАЯ КНОПКА) ---
@router.callback_query(F.data == "create_ad")
async def start_create_ad(call: CallbackQuery, state: FSMContext):
    kb = InlineKeyboardBuilder()
    kb.button(text="🚗 Продать машину", callback_data="car_sell")
    kb.button(text="👤 Продать аккаунт", callback_data="acc_sell")
    kb.button(text="⬅️ Назад", callback_data="back_main")
    kb.adjust(1, 1, 1)
    
    await call.message.edit_text(
        "📢 **Подача объявления**\n\nВыбери, что ты хочешь выставить:",
        reply_markup=kb.as_markup(),
        parse_mode="Markdown"
    )
    await call.answer()

# --- АВТОМОБИЛИ ---
@router.callback_query(F.data == "menu_cars")
async def show_cars(call: CallbackQuery):
    await call.message.edit_text("🚗 **Автомобили**", reply_markup=cars_menu())
    await call.answer()

@router.callback_query(F.data == "car_sell")
async def start_car_sell(call: CallbackQuery, state: FSMContext):
    await state.set_state(AdForm.photo)
    await state.update_data(category="car", ad_type="sale")
    await call.message.edit_text("📸 **Отправь фото машины:**", parse_mode="Markdown")
    await call.answer()

# --- АККАУНТЫ ---
@router.callback_query(F.data == "menu_accs")
async def show_accs(call: CallbackQuery):
    await call.message.edit_text("👤 **Аккаунты**", reply_markup=accs_menu())
    await call.answer()

@router.callback_query(F.data == "acc_sell")
async def start_acc_sell(call: CallbackQuery, state: FSMContext):
    await state.set_state(AdForm.photo)
    await state.update_data(category="acc", ad_type="sale")
    await call.message.edit_text("📸 **Отправь скриншот аккаунта:**", parse_mode="Markdown")
    await call.answer()

# --- МОНЕТЫ ---
@router.callback_query(F.data == "menu_money")
async def show_money(call: CallbackQuery):
    await call.message.edit_text("💵 **Монеты**", reply_markup=money_menu())
    await call.answer()

# --- ГОНКИ ---
@router.callback_query(F.data == "menu_races")
async def show_races(call: CallbackQuery, state: FSMContext):
    await state.set_state(RaceForm.game_nick)
    await call.message.edit_text("🏁 **Регистрация на гонку**\n\nВведи свой **игровой ник**:", parse_mode="Markdown")
    await call.answer()

# --- СООБЩЕСТВО ---
@router.callback_query(F.data == "menu_community")
async def show_community(call: CallbackQuery):
    channels = get_channels()
    await call.message.edit_text("💬 **Наше сообщество:**", reply_markup=community_menu(channels))
    await call.answer()

# --- СБОР ДАННЫХ ДЛЯ ОБЪЯВЛЕНИЯ ---
@router.message(AdForm.photo, F.photo)
async def process_photo(message: Message, state: FSMContext):
    await state.update_data(photo=message.photo[-1].file_id)
    await state.set_state(AdForm.title)
    await message.answer("📝 **Напиши заголовок объявления:**", parse_mode="Markdown")

@router.message(AdForm.title, F.text)
async def process_title(message: Message, state: FSMContext):
    await state.update_data(title=message.text)
    await state.set_state(AdForm.description)
    await message.answer("📝 **Напиши описание** (характеристики, цена):", parse_mode="Markdown")

@router.message(AdForm.description, F.text)
async def process_description(message: Message, state: FSMContext):
    await state.update_data(description=message.text)
    await state.set_state(AdForm.price)
    await message.answer("💰 **Укажи цену:**", parse_mode="Markdown")

@router.message(AdForm.price, F.text)
async def process_price(message: Message, state: FSMContext):
    await state.update_data(price=message.text)
    await state.set_state(AdForm.game_id)
    await message.answer("🆔 **Введи свой игровой ID:**", parse_mode="Markdown")

@router.message(AdForm.game_id, F.text)
async def process_game_id(message: Message, state: FSMContext):
    await state.update_data(game_id=message.text)
    await state.set_state(AdForm.contact)
    await message.answer("📞 **Контакт для связи (@username):**", parse_mode="Markdown")

@router.message(AdForm.contact, F.text)
async def process_contact(message: Message, state: FSMContext):
    await state.update_data(contact=message.text)
    data = await state.get_data()
    
    # Сохраняем в БД со статусом "На модерации"
    ad_id = add_ad(
        user_id=message.from_user.id,
        category=data['category'],
        ad_type=data['ad_type'],
        title=data['title'],
        description=data['description'],
        price=data['price'],
        game_id=data['game_id'],
        contact=data['contact'],
        photo_id=data['photo']
    )
    
    await state.clear()
    await message.answer(
        f"✅ **Объявление #{ad_id} отправлено на модерацию!**\n\n"
        "Администратор проверит его, и после одобрения оно появится в каналах.",
        reply_markup=main_menu(),
        parse_mode="Markdown"
    )
