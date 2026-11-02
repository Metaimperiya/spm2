import asyncio
import os
from aiogram import Bot, Dispatcher
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiohttp import web

from handlers import user_handlers, admin_handlers, member_handlers
from database import init_db
from firebase_bridge import (
    initialize,
    pending_telegram_listings,
    mark_listing_posted,
    get_newsletter_subscribers,
)
from bot_config import (
    ADMIN_IDS,
    MAIN_CLAN_CHANNEL,
    SALE_CHANNEL,
    TRADE_CHANNEL,
    SELL_ACC_CHANNEL,
    PODSLUSHKA_CHANNEL,
    is_admin,
)
from html import escape

BOT_TOKEN = os.environ.get("BOT_TOKEN")
if not BOT_TOKEN:
    raise RuntimeError("Не задан BOT_TOKEN в переменных окружения.")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

dp.include_router(user_handlers.router)
dp.include_router(admin_handlers.router)
dp.include_router(member_handlers.router)


async def start_health_server():
    """Keep Render Web Service healthy while the bot uses Telegram long polling."""
    app = web.Application()
    app.router.add_get("/health", lambda request: web.Response(text="ok"))
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", int(os.environ.get("PORT", "10000")))
    await site.start()
    return runner

async def main():
    init_db()
    # render.yaml запускает background worker: для него используем long polling,
    # которому не нужен публичный WEBHOOK_URL.
    await bot.delete_webhook(drop_pending_updates=False)
    bridge_ready = await asyncio.to_thread(initialize)
    if bridge_ready:
        sync_task = asyncio.create_task(sync_approved_cpm2_listings())
    else:
        sync_task = None
    health_runner = await start_health_server()
    try:
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    finally:
        await health_runner.cleanup()
        if sync_task:
            sync_task.cancel()
            try:
                await sync_task
            except asyncio.CancelledError:
                pass
        await bot.session.close()


async def sync_approved_cpm2_listings():
    """Publish newly approved site listings once to their corresponding channel."""
    while True:
        try:
            listings = await asyncio.to_thread(pending_telegram_listings, 100)
            for listing_id, item in listings:
                channel = TRADE_CHANNEL if item.get("dealMode") == "trade" else SALE_CHANNEL
                price = item.get("price", "")
                title = escape(str(item.get("title") or "Автомобиль")[:35])
                description = escape(str(item.get("description") or "")[:35])
                game_id = escape(str(item.get("gameId") or "")[:15])
                city_country = escape(", ".join(part for part in [item.get("city"), item.get("country")] if part)[:20])
                deal = "TRADE · Обмен" if item.get("dealMode") == "trade" else f"SELL · {escape(str(price))} CPM2"
                body = f"🚘 <b>{deal}</b>\n<b>{title}</b>\n\n{description}"
                if game_id:
                    body += f"\n\n🆔 ID игрока: <code>{game_id}</code>"
                contact = escape(str(item.get("telegramContact") or "")[:15])
                if contact:
                    body += f"\n💬 Связь: {contact}"
                if city_country:
                    body += f"\n📍 {city_country}"
                keyboard = InlineKeyboardMarkup(inline_keyboard=[[
                    InlineKeyboardButton(text="Открыть CPM2 на сайте", url="https://www.metaimperiya.com/?page=marketplace")
                ]])
                try:
                    image_url = item.get("imageUrl")
                    if image_url:
                        sent = await bot.send_photo(channel, photo=image_url, caption=body, parse_mode="HTML", reply_markup=keyboard)
                    else:
                        sent = await bot.send_message(channel, body, parse_mode="HTML", reply_markup=keyboard)
                    await asyncio.to_thread(mark_listing_posted, listing_id, channel, sent.message_id)
                    subscribers = await asyncio.to_thread(get_newsletter_subscribers)
                    for subscriber_id in subscribers:
                        try:
                            if image_url:
                                await bot.send_photo(
                                    subscriber_id,
                                    photo=image_url,
                                    caption=body,
                                    parse_mode="HTML",
                                    reply_markup=keyboard,
                                )
                            else:
                                await bot.send_message(
                                    subscriber_id,
                                    body,
                                    parse_mode="HTML",
                                    reply_markup=keyboard,
                                )
                        except Exception as error:
                            print(f"Newsletter delivery failed for {subscriber_id}: {error}")
                        await asyncio.sleep(0.05)
                    await asyncio.sleep(0.4)
                except Exception as error:
                    print(f"Telegram sync failed for {listing_id} ({channel}): {error}")
        except asyncio.CancelledError:
            raise
        except Exception as error:
            print(f"Firebase listing sync error: {error}")
        await asyncio.sleep(30)

if __name__ == "__main__":
    asyncio.run(main())
