import asyncio
import os
from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

BOT_TOKEN = os.environ.get("BOT_TOKEN")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# --- ГЛАВНОЕ МЕНЮ ---
def main_menu():
    kb = InlineKeyboardBuilder()
    kb.button(text="🚗 Класс A", callback_data="class_a")
    kb.button(text="🚙 Класс B", callback_data="class_b")
    kb.button(text="🏎️ Класс C", callback_data="class_c")
    kb.button(text="🌐 Наш сайт", url="https://www.metaimperiya.com/")
    kb.button(text="💬 Наши группы", callback_data="groups")
    kb.adjust(3, 1, 1)  # 3 кнопки в ряд, потом по одной
    return kb.as_markup()

@dp.message(CommandStart())
async def start(message: Message):
    await message.answer(
        f"Привет, {message.from_user.first_name}!\n\n"
        "Это бот по CPM 2. Выбирай раздел:",
        reply_markup=main_menu()
    )

# --- ОБРАБОТКА КЛАССОВ ---
@dp.callback_query(F.data == "class_a")
async def class_a(call: CallbackQuery):
    await call.message.edit_text(
        "🚗 **Класс A**\n\n"
        "Здесь будет инфа по классу A (машины, гайды, обсуждения).\n"
        "Пока пусто — наполни сам через код.",
        reply_markup=back_menu()
    )
    await call.answer()

@dp.callback_query(F.data == "class_b")
async def class_b(call: CallbackQuery):
    await call.message.edit_text(
        "🚙 **Класс B**\n\n"
        "Здесь будет инфа по классу B.",
        reply_markup=back_menu()
    )
    await call.answer()

@dp.callback_query(F.data == "class_c")
async def class_c(call: CallbackQuery):
    await call.message.edit_text(
        "🏎️ **Класс C**\n\n"
        "Здесь будет инфа по классу C.",
        reply_markup=back_menu()
    )
    await call.answer()

# --- ГРУППЫ ---
@dp.callback_query(F.data == "groups")
async def groups(call: CallbackQuery):
    kb = InlineKeyboardBuilder()
    kb.button(text="🚗 Тачки CPM 2", url="https://t.me/tachki_cpm_2")
    kb.button(text="📈 CPM 2 Trade", url="https://t.me/cpm_2_trade")
    kb.button(text="💰 CPM 2 Sale", url="https://t.me/cpm_2_sale")
    kb.button(text="💵 CPM 2 Money", url="https://t.me/cpm_2_money")
    kb.button(text="⬅️ Назад", callback_data="back_main")
    kb.adjust(2, 2, 1)  # по 2 в ряд, потом 1
    await call.message.edit_text(
        "💬 **Наши группы и каналы:**",
        reply_markup=kb.as_markup()
    )
    await call.answer()

# --- КНОПКА НАЗАД ---
def back_menu():
    kb = InlineKeyboardBuilder()
    kb.button(text="⬅️ В главное меню", callback_data="back_main")
    return kb.as_markup()

@dp.callback_query(F.data == "back_main")
async def back_main(call: CallbackQuery):
    await call.message.edit_text(
        "Главное меню:",
        reply_markup=main_menu()
    )
    await call.answer()

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
