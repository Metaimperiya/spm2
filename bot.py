import os
import uvicorn
from fastapi import FastAPI
from aiogram import Bot, Dispatcher
from aiogram.types import Update
from contextlib import asynccontextmanager

from handlers import user_handlers, admin_handlers, member_handlers
from database import init_db

BOT_TOKEN = os.environ.get("BOT_TOKEN")
WEBHOOK_URL = os.environ.get("WEBHOOK_URL")

# --- ГЛАВНЫЕ НАСТРОЙКИ ---
ADMIN_USERNAME = "metaimperiya"
# ТВОИ РЕАЛЬНЫЕ ID (оба аккаунта):
ADMIN_IDS = [806159173, 5493746865]
ADMIN_USERNAMES = ["metaimperiya", "cpm2trader"]

# КАНАЛЫ
MAIN_CLAN_CHANNEL = "@cpm_2_clan"
SALE_CHANNEL = "@cpm_2_sale"
TRADE_CHANNEL = "@cpm_2_trade"
SELL_ACC_CHANNEL = "@Sell_CPM_2_accounts"
PODSLUSHKA_CHANNEL = "@podslushkacpm2"

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

dp.include_router(user_handlers.router)
dp.include_router(admin_handlers.router)
dp.include_router(member_handlers.router)

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    if WEBHOOK_URL:
        await bot.delete_webhook(drop_pending_updates=True)
        webhook_path = f"{WEBHOOK_URL}/webhook"
        await bot.set_webhook(webhook_path, allowed_updates=["message", "callback_query", "chat_member"])
        print("Webhook установлен")
    yield
    await bot.session.close()

app = FastAPI(lifespan=lifespan)

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
