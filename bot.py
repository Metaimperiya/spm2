import asyncio
import os
from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart
from aiogram.types import Message, CallbackQuery, Update
from aiogram.utils.keyboard import InlineKeyboardBuilder
from fastapi import FastAPI
import uvicorn

BOT_TOKEN = os.environ.get("BOT_TOKEN")
WEBHOOK_URL = os.environ.get("WEBHOOK_URL")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
app = FastAPI()

# --- КРАСИВОЕ ГЕЙМЕРСКОЕ ГЛАВНОЕ МЕНЮ ---
def main_menu():
    kb = InlineKeyboardBuilder()
    # Заголовок / брендинг вшиваем прямо в логику или текст, а тут кнопки по классам
    kb.button(text="🏎️ Класс A (Топ тачки)", callback_data="class_a")
    kb.button(text="🚙 Класс B (Спорт)", callback_data="class_b")
    kb.button(text="🚗 Класс C (База)", callback_data="class_c")
    kb.button(text="🌐 Наш сайт (METAIMPERIYA)", url="https://www.metaimperiya.com/")
    kb.button(text="💬 Комьюнити и Группы", callback_data="groups_menu")
    kb.adjust(1, 2, 1, 1)
    return kb.as_markup()

# --- МЕНЮ ГРУПП ---
def groups_menu():
    kb = InlineKeyboardBuilder()
    kb.button(text="🚗 Тачки CPM 2", url="https://t.me/tachki_cpm_2")
    kb.button(text="📈 CPM 2 Trade", url="https://t.me/cpm_2_trade")
    kb.button(text="💰 CPM 2 Sale", url="https://t.me/cpm_2_sale")
    kb.button(text="💵 CPM 2 Money", url="https://t.me/cpm_2_money")
    kb.button(text="⬅️ Назад в меню", callback_data="back_main")
    kb.adjust(2, 2, 1)
    return kb.as_markup()

@dp.message(CommandStart())
async def start(message: Message):
    text = (
        "🔥 **METAIMPERIYA | CPM 2 HUB** 🔥\n\n"
        f"Здарова, **{message.from_user.first_name}**! Добро пожаловать в официальный бот по **Car Parking Multiplayer 2**.\n\n"
        "⚡ Здесь ты найдешь лучшие тачки, актуальные курсы обмена, торговлю и мощное комьюнити.\n"
        "Выбирай нужный раздел в меню ниже:"
    )
    await message.answer(text, reply_markup=main_menu(), parse_mode="Markdown")

@dp.callback_query(F.data == "groups_menu")
async def show_groups(call: CallbackQuery):
    text = "💬 **Наши официальные ресурсы и группы CPM 2:**\nВыбирай, куда хочешь залететь:"
    await call.message.edit_text(text, reply_markup=groups_menu(), parse_mode="Markdown")
    await call.answer()

@dp.callback_query(F.data == "back_main")
async def back_main(call: CallbackQuery):
    text = (
        "🔥 **METAIMPERIYA | CPM 2 HUB** 🔥\n\n"
        "Главное меню:"
    )
    await call.message.edit_text(text, reply_markup=main_menu(), parse_mode="Markdown")
    await call.answer()

@dp.callback_query(F.data.in_({"class_a", "class_b", "class_c"}))
async def classes_info(call: CallbackQuery):
    class_name = call.data.upper().replace("_", " ")
    await call.answer(f"Раздел '{class_name}' заправляется и скоро взлетит! Ожидай обновление.", show_alert=True)

# --- ВЕБХУКИ И СЕРВЕР ---
@app.on_event("startup")
async def on_startup():
    if WEBHOOK_URL:
        await bot.delete_webhook(drop_pending_updates=True)
        webhook_path = f"{WEBHOOK_URL}/webhook"
        await bot.set_webhook(webhook_path)
        print(f"Webhook успешно установлен на {webhook_path}")

@app.post("/webhook")
async def webhook(update: dict):
    telegram_update = Update(**update)
    await dp.feed_update(bot, telegram_update)
    return {"ok": True}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.get("/")
async def index():
    return {"status": "bot is running"}

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    uvicorn.run("bot:app", host="0.0.0.0", port=port)
