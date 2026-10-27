import asyncio
import os
from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart, StateFilter
from aiogram.types import Message, CallbackQuery, Update
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
from fastapi import FastAPI
import uvicorn

BOT_TOKEN = os.environ.get("BOT_TOKEN")
WEBHOOK_URL = os.environ.get("WEBHOOK_URL")

# --- АДРЕСА ТВОИХ КАНАЛОВ И ГРУПП ---
MAIN_CLAN_CHANNEL = "@cpm_2_clan"
SALE_CHANNEL = "@cpm_2_sale"
TRADE_CHANNEL = "@cpm_2_trade"
MONEY_CHANNEL = "@cpm_2_money"

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
app = FastAPI()

# --- СОСТОЯНИЯ ДЛЯ ПОДАЧИ ОБЪЯВЛЕНИЯ ---
class AdForm(StatesGroup):
    category = State()    # Выбор: Продажа / Обмен / Деньги
    photo = State()       # Загрузка фото
    description = State() # Текст объявления и цена
    confirm = State()     # Подтверждение отправки

# --- МЕНЮ СТАРА ---
def main_menu():
    kb = InlineKeyboardBuilder()
    kb.button(text="📢 Подать объявление", callback_data="create_ad")
    kb.button(text="🏎️ Класс A", callback_data="class_a")
    kb.button(text="🚙 Класс B", callback_data="class_b")
    kb.button(text="🚗 Класс C", callback_data="class_c")
    kb.button(text="🌐 Наш сайт (METAIMPERIYA)", url="https://www.metaimperiya.com/")
    kb.button(text="💬 Все наши группы", callback_data="groups_menu")
    kb.adjust(1, 3, 1, 1)
    return kb.as_markup()

# --- МЕНЮ ВЫБОРА КАТЕГОРИИ ОБЪЯВЛЕНИЯ ---
def categories_menu():
    kb = InlineKeyboardBuilder()
    kb.button(text="💰 Продажа (Sale)", callback_data="cat_sale")
    kb.button(text="🔄 Обмен (Trade)", callback_data="cat_trade")
    kb.button(text="💵 Услуги/Деньги (Money)", callback_data="cat_money")
    kb.button(text="❌ Отмена", callback_data="back_main")
    kb.adjust(1, 1, 1, 1)
    return kb.as_markup()

# --- МЕНЮ ГРУПП ---
def groups_menu():
    kb = InlineKeyboardBuilder()
    kb.button(text="🛡️ Наш Клан CPM 2", url="https://t.me/cpm_2_clan")
    kb.button(text="🚗 Тачки CPM 2", url="https://t.me/tachki_cpm_2")
    kb.button(text="📈 CPM 2 Trade", url="https://t.me/cpm_2_trade")
    kb.button(text="💰 CPM 2 Sale", url="https://t.me/cpm_2_sale")
    kb.button(text="💵 CPM 2 Money", url="https://t.me/cpm_2_money")
    kb.button(text="⬅️ Назад в меню", callback_data="back_main")
    kb.adjust(2, 2, 1, 1)
    return kb.as_markup()

@dp.message(CommandStart())
async def start(message: Message, state: FSMContext):
    await state.clear()
    text = (
        "🔥 **METAIMPERIYA | CPM 2 HUB & CLAN** 🔥\n\n"
        f"Здарова, **{message.from_user.first_name}**!\n"
        "Здесь ты можешь выложить объявление о продаже, обмене тачек или услугах в CPM 2.\n\n"
        "Выбирай нужное действие ниже:"
    )
    await message.answer(text, reply_markup=main_menu(), parse_mode="Markdown")

@dp.callback_query(F.data == "groups_menu")
async def show_groups(call: CallbackQuery):
    text = "💬 **Наши официальные ресурсы и группы CPM 2:**"
    await call.message.edit_text(text, reply_markup=groups_menu(), parse_mode="Markdown")
    await call.answer()

@dp.callback_query(F.data == "back_main")
async def back_main(call: CallbackQuery, state: FSMContext):
    await state.clear()
    text = "🔥 **METAIMPERIYA | CPM 2 HUB & CLAN** 🔥\n\nГлавное меню:"
    await call.message.edit_text(text, reply_markup=main_menu(), parse_mode="Markdown")
    await call.answer()

# --- СЦЕНАРИЙ ПОДАЧИ ОБЪЯВЛЕНИЯ ---

@dp.callback_query(F.data == "create_ad")
async def start_ad(call: CallbackQuery, state: FSMContext):
    await state.set_state(AdForm.category)
    await call.message.edit_text(
        "Выбери тип твоего объявления:\n\n"
        "• **Продажа** — улетит в Клан и в CPM 2 Sale\n"
        "• **Обмен** — улетит в Клан и в CPM 2 Trade\n"
        "• **Деньги** — улетит в Клан и в CPM 2 Money",
        reply_markup=categories_menu(),
        parse_mode="Markdown"
    )
    await call.answer()

@dp.callback_query(StateFilter(AdForm.category), F.data.startswith("cat_"))
async def process_category(call: CallbackQuery, state: FSMContext):
    category = call.data.split("_")[1]
    await state.update_data(category=category)
    await state.set_state(AdForm.photo)
    
    await call.message.edit_text(
        "📸 **Отправь фото машины или скриншот.**\n\n"
        "Загрузи одно фото прямо сюда в чат.",
        parse_mode="Markdown"
    )
    await call.answer()

@dp.message(StateFilter(AdForm.photo), F.photo)
async def process_photo(message: Message, state: FSMContext):
    photo_id = message.photo[-1].file_id
    await state.update_data(photo=photo_id)
    await state.set_state(AdForm.description)
    
    await message.answer(
        "📝 **Теперь напиши описание объявления.**\n\n"
        "Укажи название тачки, характеристики, цену/условия обмена и свой игровой ID.",
        parse_mode="Markdown"
    )

@dp.message(StateFilter(AdForm.photo))
async def process_photo_invalid(message: Message):
    await message.answer("Пожалуйста, отправь именно **картинку/фотография**!")

@dp.message(StateFilter(AdForm.description), F.text)
async def process_description(message: Message, state: FSMContext):
    user_data = await state.get_data()
    category = user_data["category"]
    photo_id = user_data["photo"]
    description_text = message.text
    
    username = f"@{message.from_user.username}" if message.from_user.username else message.from_user.first_name

    # Опредяем категорию и куда шлем
    if category == "sale":
        cat_tag = "#ПРОДАЖА"
        target_channel = SALE_CHANNEL
    elif category == "trade":
        cat_tag = "#ОБМЕН"
        target_channel = TRADE_CHANNEL
    else:
        cat_tag = "#УСЛУГИ_ДЕНЬГИ"
        target_channel = MONEY_CHANNEL

    post_text = (
        f"🔥 **ОБЪЯВЛЕНИЕ CPM 2** ({cat_tag})\n\n"
        f"{description_text}\n\n"
        f"👤 **Продавец/Автор:** {username}\n"
        f"🛡️ **Сообщество:** {MAIN_CLAN_CHANNEL}"
    )

    # Публикуем в Основной клановый канал
    try:
        await bot.send_photo(chat_id=MAIN_CLAN_CHANNEL, photo=photo_id, caption=post_text, parse_mode="Markdown")
    except Exception as e:
        print(f"Ошибка публикации в главный клан: {e}")

    # Публикуем в профильный канал (Sale / Trade / Money)
    try:
        await bot.send_photo(chat_id=target_channel, photo=photo_id, caption=post_text, parse_mode="Markdown")
    except Exception as e:
        print(f"Ошибка публикации в {target_channel}: {e}")

    await state.clear()
    await message.answer(
        "✅ **Ваше объявление успешно опубликовано!**\n\n"
        f"Оно улетело в главный канал {MAIN_CLAN_CHANNEL} и в целевой {target_channel}.",
        reply_markup=main_menu(),
        parse_mode="Markdown"
    )

@dp.callback_query(F.data.in_({"class_a", "class_b", "class_c"}))
async def classes_info(call: CallbackQuery):
    class_name = call.data.upper().replace("_", " ")
    await call.answer(f"Раздел '{class_name}' заправляется и скоро взлетит!", show_alert=True)

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
