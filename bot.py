import asyncio
import os
import uvicorn
from fastapi import FastAPI
from aiogram import Bot, Dispatcher, types
from aiogram.types import Update
from contextlib import asynccontextmanager

# Импортируем базу данных
from database import init_db
# Импортируем все роутеры (обработчики)
from handlers import user_handlers, admin_handlers, member_handlers

BOT_TOKEN = os.environ.get("BOT_TOKEN")
WEBHOOK_URL = os.environ.get("WEBHOOK_URL")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Подключаем роутеры (все обработчики)
dp.include_router(user_handlers.router)
dp.include_router(admin_handlers.router)
dp.include_router(member_handlers.router)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Инициализация базы данных при старте
    init_db()
    
    if WEBHOOK_URL:
        await bot.delete_webhook(drop_pending_updates=True)
        webhook_path = f"{WEBHOOK_URL}/webhook"
        # ВАЖНО: allowed_updates добавляет отслеживание входа в группы (chat_member)
        await bot.set_webhook(webhook_path, allowed_updates=["message", "callback_query", "chat_member"])
        print(f"Webhook установлен на {webhook_path}")
    yield
    await bot.session.close()

app = FastAPI(lifespan=lifespan)

@app.post("/webhook")
async def webhook(update: dict):
    telegram_update = Update(**update)
    await dp.feed_update(bot, telegram_update)
    return {"ok": True}

@app.get("/")
async def index():
    return {"status": "bot is running"}

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    uvicorn.run("bot:app", host="0.0.0.0", port=port)
