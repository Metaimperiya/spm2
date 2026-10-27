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

# --- КАНАЛЫ И ГРУППЫ СЕТИ ---
MAIN_CLAN_CHANNEL = "@cpm_2_clan"
SALE_CHANNEL = "@cpm_2_sale"
TRADE_CHANNEL = "@cpm_2_trade"
MONEY_CHANNEL = "@cpm_2_money"

# --- АДМИНЫ БОТА ---
ADMINS = {"citymain", "metaimperiya"}

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
app = FastAPI()

# --- СОСТОЯНИЯ (FSM) ---
class AdForm(StatesGroup):
    category = State()
    photo = State()
    description = State()

class AdminAdForm(StatesGroup):
    photo = State()
    description = State()

# --- КЛАВИАТУРЫ ---
def main_menu(is_admin=False):
    kb = InlineKeyboardBuilder()
    kb.button(text="📢 Подать объявление", callback_data="create_ad")
    kb.button(text="🏎️ Класс A", callback_data="class_a")
    kb.button(text="🚙 Класс B", callback_data="class_b")
    kb.button(text="🚗 Класс C", callback_data="class_c")
    kb.button(text="🌐 Наш сайт (METAIMPERIYA)", url="https://www.metaimperiya.com/")
    kb.button(text="💬 Все наши группы", callback_data="groups_menu")
    
    if is_admin:
        kb.button(text="👑 Админ: Создать рекламу", callback_data="admin_create_ad")
        kb.adjust(1, 3, 1, 1, 1)
    else:
        kb.adjust(1, 3, 1, 1)
        
    return kb.as_markup()

def categories_menu():
    kb = InlineKeyboardBuilder()
    kb.button(text="💰 Продажа (Sale)", callback_data="cat_sale")
    kb.button(text="🔄 Обмен (Trade)", callback_data="cat_trade")
    kb.button(text="💵 Услуги/Деньги (Money)", callback_data="cat_money")
    kb.button(text="⬅️ Отмена", callback_data="back_main")
    kb.adjust(1, 1, 1, 1)
    return kb.as_markup()

def groups_menu():
    kb = InlineKeyboardBuilder()
    kb.button(text="🛡️ Клан CPM 2", url="https://t.me/cpm_2_clan")
    kb.button(text="🚗 Тачки CPM 2", url="https://t.me/tachki_cpm_2")
    kb.button(text="📈 CPM 2 Trade", url="https://t.me/cpm_2_trade")
    kb.button(text="💰 CPM 2 Sale", url="https://t.me/cpm_2_sale")
    kb.button(text="💵 CPM 2 Money", url="https://t.me/cpm_2_money")
    kb.button(text="⬅️ Назад в меню", callback_data="back_main")
    kb.adjust(2, 2, 1, 1)
    return kb.as_markup()

# Полный набор вечных кнопок для постов и рекламы
def universal_post_keyboard():
    kb = InlineKeyboardBuilder()
    kb.button(text="🌐 Наш сайт", url="https://www.metaimperiya.com/")
    kb.button(text="🛡️ Наш Клан", url="https://t.me/cpm_2_clan")
    kb.button(text="🚗 Тачки", url="https://t.me/tachki_cpm_2")
    kb.button(text="📈 Трейд", url="https://t.me/cpm_2_trade")
    kb.button(text="💰 Продажа", url="https://t.me/cpm_2_sale")
    kb.button(text="💵 Деньги", url="https://t.me/cpm_2_money")
    kb.adjust(2, 2, 2)
    return kb.as_markup()

def check_is_admin(user) -> bool:
    if not user.username:
        return False
    return user.username.lower() in ADMINS

@dp.message(CommandStart())
async def start(message: Message, state: FSMContext):
    await state.clear()
    is_admin = check_is_admin(message.from_user)
    admin_badge = "\n👑 **Статус:** Администратор сети" if is_admin else ""
    
    text = (
        "🔥 **METAIMPERIYA | CPM 2 HUB & CLAN** 🔥\n\n"
        f"Здарова, **{message.from_user.first_name}**!"
        f"{admin_badge}\n\n"
        "⚡ Выбирай нужный раздел в меню ниже:"
    )
    await message.answer(text, reply_markup=main_menu(is_admin), parse_mode="Markdown")

@dp.callback_query(F.data == "groups_menu")
async def show_groups(call: CallbackQuery):
    await call.message.edit_text("💬 **Наши официальные ресурсы и группы CPM 2:**", reply_markup=groups_menu(), parse_mode="Markdown")
    await call.answer()

@dp.callback_query(F.data == "back_main")
async def back_main(call: CallbackQuery, state: FSMContext):
    await state.clear()
    is_admin = check_is_admin(call.from_user)
    await call.message.edit_text("🔥 **METAIMPERIYA | CPM 2 HUB & CLAN** 🔥\n\nГлавное меню:", reply_markup=main_menu(is_admin), parse_mode="Markdown")
    await call.answer()

# --- ПОДАЧА ОБЫЧНОГО ОБЪЯВЛЕНИЯ ПОЛЬЗОВАТЕЛЯМИ ---
@dp.callback_query(F.data == "create_ad")
async def start_ad(call: CallbackQuery, state: FSMContext):
    await state.set_state(AdForm.category)
    await call.message.edit_text(
        "📢 **Подача объявления**\n\nВыбери категорию сделки:",
        reply_markup=categories_menu(),
        parse_mode="Markdown"
    )
    await call.answer()

@dp.callback_query(StateFilter(AdForm.category), F.data.startswith("cat_"))
async def process_category(call: CallbackQuery, state: FSMContext):
    category = call.data.split("_")[1]
    await state.update_data(category=category)
    await state.set_state(AdForm.photo)
    await call.message.edit_text("📸 **Отправь фото / скриншот машины.**", parse_mode="Markdown")
    await call.answer()

@dp.message(StateFilter(AdForm.photo), F.photo)
async def process_photo(message: Message, state: FSMContext):
    await state.update_data(photo=message.photo[-1].file_id)
    await state.set_state(AdForm.description)
    await message.answer("📝 **Напиши текст объявления** (характеристики, цена, контакт).", parse_mode="Markdown")

@dp.message(StateFilter(AdForm.photo))
async def process_photo_invalid(message: Message):
    await message.answer("⚠️ Отправь именно **картинку/фото**!")

@dp.message(StateFilter(AdForm.description), F.text)
async def process_description(message: Message, state: FSMContext):
    data = await state.get_data()
    category = data["category"]
    photo_id = data["photo"]
    
    username = f"@{message.from_user.username}" if message.from_user.username else message.from_user.first_name
    cat_tag = "#ПРОДАЖА" if category == "sale" else ("#ОБМЕН" if category == "trade" else "#УСЛУГИ_ДЕНЬГИ")
    target_channel = SALE_CHANNEL if category == "sale" else (TRADE_CHANNEL if category == "trade" else MONEY_CHANNEL)

    post_text = (
        f"🔥 **ОБЪЯВЛЕНИЕ CPM 2** ({cat_tag})\n\n"
        f"{message.text}\n\n"
        f"👤 **Автор:** {username}\n"
        f"🛡️ **Клановый хаб:** {MAIN_CLAN_CHANNEL}"
    )

    markup = universal_post_keyboard()

    for chat in {MAIN_CLAN_CHANNEL, target_channel}:
        try:
            await bot.send_photo(chat_id=chat, photo=photo_id, caption=post_text, reply_markup=markup, parse_mode="Markdown")
        except Exception as e:
            print(f"Ошибка отправки в {chat}: {e}")

    await state.clear()
    await message.answer("✅ **Объявление успешно опубликовано в каналах!**", reply_markup=main_menu(check_is_admin(message.from_user)), parse_mode="Markdown")

# --- АДМИНСКИЙ КАСТОМНЫЙ ПОСТ (РЕКЛАМА) ---
@dp.callback_query(F.data == "admin_create_ad")
async def admin_start_ad(call: CallbackQuery, state: FSMContext):
    if not check_is_admin(call.from_user):
        await call.answer("⛔ Недостаточно прав!", show_alert=True)
        return
    
    await state.set_state(AdminAdForm.photo)
    await call.message.edit_text(
        "👑 **Админ-режим: Создание рекламы**\n\n"
        "Отправь картинку/баннер для рекламного поста:",
        parse_mode="Markdown"
    )
    await call.answer()

@dp.message(StateFilter(AdminAdForm.photo), F.photo)
async def admin_process_photo(message: Message, state: FSMContext):
    await state.update_data(photo=message.photo[-1].file_id)
    await state.set_state(AdminAdForm.description)
    await message.answer("📝 **Напиши текст рекламного поста:**", parse_mode="Markdown")

@dp.message(StateFilter(AdminAdForm.description), F.text)
async def admin_process_description(message: Message, state: FSMContext):
    data = await state.get_data()
    photo_id = data["photo"]
    
    ad_text = (
        "🔥 **ОФИЦИАЛЬНОЕ СООБЩЕНИЕ METAIMPERIYA** 🔥\n\n"
        f"{message.text}"
    )

    markup = universal_post_keyboard()

    # Публикуем во все ключевые каналы сразу
    channels = [MAIN_CLAN_CHANNEL, SALE_CHANNEL, TRADE_CHANNEL, MONEY_CHANNEL]
    for chat in channels:
        try:
            await bot.send_photo(chat_id=chat, photo=photo_id, caption=ad_text, reply_markup=markup, parse_mode="Markdown")
        except Exception as e:
            print(f"Ошибка админ-рассылки в {chat}: {e}")

    await state.clear()
    await message.answer(
        "✅ **Рекламный пост успешно разлетелcя по всем группам и каналам с полным набором кнопок!**",
        reply_markup=main_menu(True),
        parse_mode="Markdown"
    )

@dp.callback_query(F.data.in_({"class_a", "class_b", "class_c"}))
async def classes_info(call: CallbackQuery):
    class_name = call.data.upper().replace("_", " ")
    await call.answer(f"Раздел '{class_name}' заправляется, скоро откроем!", show_alert=True)

# --- СЕРВЕР И ВЕБХУКИ ---
@app.on_event("startup")
async def on_startup():
    if WEBHOOK_URL:
        await bot.delete_webhook(drop_pending_updates=True)
        webhook_path = f"{WEBHOOK_URL}/webhook"
        await bot.set_webhook(webhook_path)
        print(f"Webhook установлен на {webhook_path}")

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
