import os
import asyncio
from telegram import Bot

TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

async def main():
    bot = Bot(token=TOKEN)
    await bot.send_message(chat_id=CHAT_ID, text="Привет! Это сообщение от Cron Job на Render.")
    # Важно: скрипт должен завершиться сам, без bot.polling()

if __name__ == "__main__":
    asyncio.run(main())
