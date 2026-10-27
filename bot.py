import os
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart
from aiogram.types import Message, CallbackQuery, Update
from aiogram.utils.keyboard import InlineKeyboardBuilder

# --- НАСТРОЙКИ ---
BOT_TOKEN = os.environ.get("BOT_TOKEN")
WEBHOOK_URL = os.environ.get("WEBHOOK_URL")  # Без слэша на конце!

logging.basicConfig(level=logging.INFO)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# --- КЛАВИАТУРЫ ---
def main_menu():
    kb = InlineKeyboardBuilder()
    kb.button(text="🚗 Класс A", callback_data="class_a")
    kb.button(text="🚙 Класс B", callback_data="class_b")
    kb.button(text="🏎️ Класс C", callback_data="class_c")
    kb.button(text="🌐 Наш сайт", url="https://www.metaimperiya.com/")
    kb.button(text="💬 Наши группы", callback_data="groups")
    kb.adjust(3, 1, 1)
    return kb.as_markup()

def back_menu():
    kb = InlineKeyboardBuilder()
    kb.button(text="⬅️ В главное меню", callback_data="back_main")
    return kb.as_markup()

# --- ХЭНДЛЕРЫ ---
@dp.message(CommandStart())
async def start(message: Message):
    await message.answer(
        f"Привет, {message.from_user.first_name}!\n\nЭто бот по CPM 2. Выбирай раздел:",
        reply_markup=main_menu()
    )

@dp.callback_query(F.data == "class_a")
async def class_a(call: CallbackQuery):
    await call.message.edit_text("🚗 **Класс A**\n\nЗдесь будет инфа по классу A.", reply_markup=back_menu())
    await call.answer()

@dp.callback_query(F.data == "class_b")
async def class_b(call: CallbackQuery):
    await call.message.edit_text("🚙 **Класс B**\n\nЗдесь будет инфа по классу B.", reply_markup=back_menu())
    await call.answer()

@dp.callback_query(F.data == "class_c")
async def class_c(call: CallbackQuery):
    await call.message.edit_text("🏎️ **Класс C**\n\nЗдесь будет инфа по классу C.", reply_markup=back_menu())
    await call.answer()

@dp.callback_query(F.data == "groups")
async def groups(call: CallbackQuery):
    kb = InlineKeyboardBuilder()
    kb.button(text="🚗 Тачки CPM 2", url="https://t.me/tachki_cpm_2")
    kb.button(text="📈 CPM 2 Trade", url="https://t.me/cpm_2_trade")
    kb.button(text="💰 CPM 2 Sale", url="https://t.me/cpm_2_sale")
    kb.button(text="💵 CPM 2 Money", url="https://t.me/cpm_2_money")
    kb.button(text="⬅️ Назад", callback_data="back_main")
    kb.adjust(2, 2, 1)
    await call.message.edit_text("💬 **Наши группы и каналы:**", reply_markup=kb.as_markup())
    await call.answer()

@dp.callback_query(F.data == "back_main")
async def back_main(call: CallbackQuery):
    await call.message.edit_text("Главное меню:", reply_markup=main_menu())
    await call.answer()

# --- FASTAPI И ВЕБХУК ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Устанавливаем вебхук при старте
    webhook_endpoint = f"{WEBHOOK_URL}/webhook"
    await bot.set_webhook(url=webhook_endpoint)
    logging.info(f"Webhook установлен на {webhook_endpoint}")
    yield
    # Удаляем при остановке
    await bot.delete_webhook()
    await bot.session.close()

app = FastAPI(lifespan=lifespan)

@app.post("/webhook")
async def telegram_webhook(request: Request):
    # Принимаем сообщения от Telegram
    update_data = await request.json()
    update = Update.model_validate(update_data, context={"bot": bot})
    await dp.feed_update(bot, update)
    return {"ok": True}

@app.get("/")
async def health_check():
    # Эндпоинт для пинга от cron-job.org
    return {"status": "alive"}
