import asyncio
import os
from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart
from aiogram.types import Message, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder

BOT_TOKEN = os.environ.get("BOT_TOKEN")
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

def main_menu():
    kb = InlineKeyboardBuilder()
    kb.button(text="🚗 Класс A", callback_data="class_a")
    kb.button(text="🚙 Класс B", callback_data="class_b")
    kb.button(text="🏎️ Класс C", callback_data="class_c")
    kb.button(text="🌐 Наш сайт", url="https://www.metaimperiya.com/")
    kb.button(text="💬 Наши группы", callback_data="groups")
    kb.adjust(3, 1, 1)
    return kb.as_markup()

@dp.message(CommandStart())
async def start(message: Message):
    await message.answer(f"Привет, {message.from_user.first_name}!\n\nВыбирай раздел:", reply_markup=main_menu())

@dp.callback_query(F.data == "groups")
async def groups(call: CallbackQuery):
    kb = InlineKeyboardBuilder()
    kb.button(text="🚗 Тачки CPM 2", url="https://t.me/tachki_cpm_2")
    kb.button(text="📈 CPM 2 Trade", url="https://t.me/cpm_2_trade")
    kb.button(text="💰 CPM 2 Sale", url="https://t.me/cpm_2_sale")
    kb.button(text="💵 CPM 2 Money", url="https://t.me/cpm_2_money")
    kb.button(text="⬅️ Назад", callback_data="back_main")
    kb.adjust(2, 2, 1)
    await call.message.edit_text("Наши группы:", reply_markup=kb.as_markup())
    await call.answer()

@dp.callback_query(F.data == "back_main")
async def back_main(call: CallbackQuery):
    await call.message.edit_text("Главное меню:", reply_markup=main_menu())
    await call.answer()

# Заглушки для классов, чтобы не было ошибок
@dp.callback_query(F.data.in_({"class_a", "class_b", "class_c"}))
async def classes(call: CallbackQuery):
    await call.answer("Скоро тут будет инфа", show_alert=True)

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
