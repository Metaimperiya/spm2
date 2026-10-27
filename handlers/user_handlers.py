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

# --- АВТОМОБИЛИ ---
@router.callback_query(F.data == "menu_cars")
async def show_cars(call: CallbackQuery):
    await call.message.edit_text("🚗 **Автомобили**", reply_markup=cars_menu())
    await call.answer()

@router.callback_query(F.data == "car_sell")
async def start_car_sell(call: CallbackQuery, state: FSMContext):
    await state.set_state(AdForm.category)
    await state.update_data(category="car", ad_type="sale")
    await call.message.edit_text("📸 **Отправь фото машины:**", parse_mode="Markdown")
    await state.set_state(AdForm.photo)
    await call.answer()

# --- АККАУНТЫ ---
@router.callback_query(F.data == "menu_accs")
async def show_accs(call: CallbackQuery):
    await call.message.edit_text("👤 **Аккаунты**", reply_markup=accs_menu())
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

@router.callback_query(F.data == "back_main")
async def back_main(call: CallbackQuery, state: FSMContext):
    await state.clear()
    await call.message.edit_text("🚀 **Главное меню:**", reply_markup=main_menu(), parse_mode="Markdown")
    await call.answer()

# --- СБОР ФОТО (ЗАГЛУШКА ДЛЯ ПРИМЕРА) ---
@router.message(AdForm.photo, F.photo)
async def process_photo(message: Message, state: FSMContext):
    await state.update_data(photo=message.photo[-1].file_id)
    await state.set_state(AdForm.title)
    await message.answer("📝 **Напиши заголовок объявления:**", parse_mode="Markdown")
