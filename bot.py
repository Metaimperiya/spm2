import asyncio
import os
from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart, StateFilter
from aiogram.types import Message, CallbackQuery, Update, ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
from fastapi import FastAPI
import uvicorn

BOT_TOKEN = os.environ.get("BOT_TOKEN")
WEBHOOK_URL = os.environ.get("WEBHOOK_URL")

# --- КАНАЛЫ СЕТИ ---
MAIN_CLAN_CHANNEL = "@cpm_2_clan"
SALE_CHANNEL = "@cpm_2_sale"
TRADE_CHANNEL = "@cpm_2_trade"
SELL_ACC_CHANNEL = "@Sell_CPM_2_accounts"  # Твой канал
BUY_ACC_CHANNEL = "@BuyCPM2accounts"       # Твой канал
SITE_URL = "https://www.metaimperiya.com/"

# --- ТВОЙ ЛИЧНЫЙ ЮЗЕРНЕЙМ (Для кнопки "Написать админу") ---
ADMIN_USERNAME = "metaimperiya" # Замени на свой, если нужно

# --- ВАЖНО: ЦИФРОВЫЕ ID АДМИНОВ ---
ADMIN_IDS = [123456789, 987654321] 

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
app = FastAPI()

# --- СОСТОЯНИЯ ---
class AdForm(StatesGroup):
    category = State() # Что продаем (машина, аккаунт)
    action = State()   # Продажа или Покупка
    photo = State()
    description = State()

class AdminAdForm(StatesGroup):
    photo = State()
    description = State()

class RaceForm(StatesGroup):
    race_type = State()
    game_id = State()
    car = State()

def check_is_admin(user) -> bool:
    return user.id in ADMIN_IDS

# --- НИЖНЯЯ КЛАВИАТУРА ---
def bottom_menu():
    kb = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="🏠 В главное меню")]],
        resize_keyboard=True,
        is_persistent=True
    )
    return kb

# --- ГЛАВНОЕ МЕНЮ ---
def main_menu(is_admin=False):
    kb = InlineKeyboardBuilder()
    kb.button(text="🏁 Гонки (Заявка)", callback_data="join_race")
    kb.button(text="🛒 Барахолка (Тачки)", callback_data="market_cars")
    kb.button(text="👤 Аккаунты (Купить/Продать)", callback_data="market_accs")
    kb.button(text="💵 Монеты / Услуги", callback_data="market_money")
    kb.button(text="💬 Сеть каналов CPM 2", callback_data="groups_menu")
    kb.button(text="🌐 Наш Сайт", url=SITE_URL)
    
    if is_admin:
        kb.button(text="👑 Создать рекламный пост", callback_data="admin_create_ad")
        kb.adjust(1, 1, 1, 1, 1, 1, 1)
    else:
        kb.adjust(1, 1, 1, 1, 1, 1)
        
    return kb.as_markup()

# --- МЕНЮ БАРАХОЛКИ ---
def market_cars_menu():
    kb = InlineKeyboardBuilder()
    kb.button(text="💰 Продать машину", callback_data="car_sell")
    kb.button(text="🛒 Купить машину", callback_data="car_buy")
    kb.button(text="🔄 Обменять машину", callback_data="car_trade")
    kb.button(text="⬅️ Назад", callback_data="back_main")
    kb.adjust(1, 1, 1, 1)
    return kb.as_markup()

def market_accs_menu():
    kb = InlineKeyboardBuilder()
    kb.button(text="💰 Продать аккаунт", callback_data="acc_sell")
    kb.button(text="🛒 Купить аккаунт", callback_data="acc_buy")
    kb.button(text="⬅️ Назад", callback_data="back_main")
    kb.adjust(1, 1, 1)
    return kb.as_markup()

def market_money_menu():
    kb = InlineKeyboardBuilder()
    kb.button(text="💰 Продать монеты", url=f"https://t.me/{ADMIN_USERNAME}")
    kb.button(text="🛒 Купить монеты", url=f"https://t.me/{ADMIN_USERNAME}")
    kb.button(text="💼 Услуги / Другое", url=f"https://t.me/{ADMIN_USERNAME}")
    kb.button(text="⬅️ Назад", callback_data="back_main")
    kb.adjust(1, 1, 1, 1)
    return kb.as_markup()

def groups_menu():
    kb = InlineKeyboardBuilder()
    kb.button(text="🛡️ Наш Клан", url="https://t.me/cpm_2_clan")
    kb.button(text="🚗 Тачки (Мемы)", url="https://t.me/tachki_cpm_2")
    kb.button(text="📈 Трейд (Обмен)", url="https://t.me/cpm_2_trade")
    kb.button(text="💰 Продажа тачек", url="https://t.me/cpm_2_sale")
    kb.button(text="👤 Продажа аккаунтов", url="https://t.me/Sell_CPM_2_accounts")
    kb.button(text="🤝 Покупка аккаунтов", url="https://t.me/BuyCPM2accounts")
    kb.button(text="⬅️ Назад", callback_data="back_main")
    kb.adjust(2, 2, 2, 1)
    return kb.as_markup()

def universal_post_keyboard():
    kb = InlineKeyboardBuilder()
    kb.button(text="🌐 Наш сайт", url=SITE_URL)
    kb.button(text="💬 Написать админу", url=f"https://t.me/{ADMIN_USERNAME}")
    kb.button(text="🛡️ Клан", url="https://t.me/cpm_2_clan")
    kb.adjust(1, 2)
    return kb.as_markup()

# --- СТАРТ ---
@dp.message(CommandStart())
async def start(message: Message, state: FSMContext):
    await state.clear()
    is_admin = check_is_admin(message.from_user)
    admin_badge = "\n👑 *Статус:* Администратор" if is_admin else ""
    
    text = (
        "🏁 **METAIMPERIYA | CPM 2 HUB** 🏁\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"Здарова, **{message.from_user.first_name}**!{admin_badge}\n\n"
        "Добро пожаловать на главную торговую площадку CPM 2.\n"
        "Здесь ты можешь купить/продать тачку, аккаунт или монеты.\n\n"
        "👇 *Выбирай нужный раздел:*"
    )
    await message.answer(text, reply_markup=bottom_menu(), parse_mode="Markdown")
    await message.answer("🚀 **Главное меню:**", reply_markup=main_menu(is_admin), parse_mode="Markdown")

@dp.message(F.text == "🏠 В главное меню")
async def open_bottom_menu(message: Message, state: FSMContext):
    await state.clear()
    is_admin = check_is_admin(message.from_user)
    await message.answer("🚀 **Главное меню:**", reply_markup=main_menu(is_admin), parse_mode="Markdown")

@dp.callback_query(F.data == "back_main")
async def back_main(call: CallbackQuery, state: FSMContext):
    await state.clear()
    is_admin = check_is_admin(call.from_user)
    await call.message.edit_text("🚀 **Главное меню:**", reply_markup=main_menu(is_admin), parse_mode="Markdown")
    await call.answer()

# --- ТОРГОВЫЕ РАЗДЕЛЫ ---
@dp.callback_query(F.data == "market_cars")
async def show_market_cars(call: CallbackQuery):
    await call.message.edit_text("🛒 **Барахолка: Тачки**\n\nВыбери действие:", reply_markup=market_cars_menu(), parse_mode="Markdown")
    await call.answer()

@dp.callback_query(F.data == "market_accs")
async def show_market_accs(call: CallbackQuery):
    await call.message.edit_text("👤 **Барахолка: Аккаунты**\n\nВыбери действие:", reply_markup=market_accs_menu(), parse_mode="Markdown")
    await call.answer()

@dp.callback_query(F.data == "market_money")
async def show_market_money(call: CallbackQuery):
    await call.message.edit_text("💵 **Монеты / Услуги**\n\nВсе сделки проходят через администратора:", reply_markup=market_money_menu(), parse_mode="Markdown")
    await call.answer()

@dp.callback_query(F.data == "groups_menu")
async def show_groups(call: CallbackQuery):
    await call.message.edit_text("💬 **Официальная сеть CPM 2:**", reply_markup=groups_menu(), parse_mode="Markdown")
    await call.answer()

# --- ЛОГИКА ПОДАЧИ ОБЪЯВЛЕНИЙ ---
@dp.callback_query(F.data.in_({"car_sell", "car_trade", "acc_sell"}))
async def start_sell(call: CallbackQuery, state: FSMContext):
    action = call.data
    await state.update_data(action=action)
    await state.set_state(AdForm.photo)
    
    if action == "acc_sell":
        text = "📸 **Продажа аккаунта**\n\nОтправь скриншот гаража или профиля аккаунта:"
    elif action == "car_trade":
        text = "📸 **Обмен машины**\n\nОтправь фото тачки, которую хочешь обменять:"
    else:
        text = "📸 **Продажа машины**\n\nОтправь фото тачки:"
        
    await call.message.edit_text(text, parse_mode="Markdown")
    await call.answer()

# Кнопка "Купить" ведет на связь с тобой
@dp.callback_query(F.data.in_({"car_buy", "acc_buy"}))
async def start_buy(call: CallbackQuery):
    await call.answer("Перенаправляем...", show_alert=False)
    kb = InlineKeyboardBuilder()
    kb.button(text="💬 Написать админу", url=f"https://t.me/{ADMIN_USERNAME}")
    kb.button(text="⬅️ Назад", callback_data="back_main")
    kb.adjust(1, 1)
    
    text = (
        "🛒 **Покупка**\n\n"
        "Чтобы купить эту позицию или посмотреть, что есть в наличии, напиши нашему администратору. Он подберет лучший вариант!"
    )
    await call.message.edit_text(text, reply_markup=kb.as_markup(), parse_mode="Markdown")

@dp.message(StateFilter(AdForm.photo), F.photo)
async def process_photo(message: Message, state: FSMContext):
    await state.update_data(photo=message.photo[-1].file_id)
    await state.set_state(AdForm.description)
    
    data = await state.get_data()
    action = data["action"]
    
    if action == "acc_sell":
        text = (
            "📝 **Напиши описание аккаунта**\n\n"
            "Обязательно укажи:\n"
            "1. Уровень аккаунта\n"
            "2. Сколько денег на счету\n"
            "3. Какие есть редкие тачки (ТОП)\n"
            "4. Цена и твой контакт для связи (@username)"
        )
    else:
        text = "📝 **Напиши описание** (характеристики, цена, твой @username):"
        
    await message.answer(text, parse_mode="Markdown")

@dp.message(StateFilter(AdForm.description), F.text)
async def process_description(message: Message, state: FSMContext):
    data = await state.get_data()
    action = data["action"]
    photo_id = data["photo"]
    
    username = f"@{message.from_user.username}" if message.from_user.username else message.from_user.first_name
    
    # Определяем, куда и с каким тегом отправлять
    if action == "car_sell":
        cat_tag = "#ПРОДАЖА_ТАЧКИ"
        target_channel = SALE_CHANNEL
    elif action == "car_trade":
        cat_tag = "#ОБМЕН_ТАЧКИ"
        target_channel = TRADE_CHANNEL
    else:
        cat_tag = "#ПРОДАЖА_АККАУНТА"
        target_channel = SELL_ACC_CHANNEL

    post_text = (
        f"🔥 **ОБЪЯВЛЕНИЕ CPM 2** ({cat_tag})\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        f"{message.text}\n\n"
        f"👤 **Продавец:** {username}"
    )
    
    markup = universal_post_keyboard()
    
    # Отправляем в главный канал и в нужный канал
    for chat in {MAIN_CLAN_CHANNEL, target_channel}:
        try:
            await bot.send_photo(chat_id=chat, photo=photo_id, caption=post_text, reply_markup=markup, parse_mode="Markdown")
        except Exception as e:
            print(f"Ошибка отправки в {chat}: {e}")

    await state.clear()
    await message.answer("✅ **Объявление успешно опубликовано в каналах!**", reply_markup=main_menu(check_is_admin(message.from_user)), parse_mode="Markdown")

# --- ЛОГИКА ГОНОК (ОСТАЛАСЬ) ---
@dp.callback_query(F.data == "join_race")
async def start_race(call: CallbackQuery, state: FSMContext):
    kb = InlineKeyboardBuilder()
    kb.button(text="🏎️ Дрэг-рейсинг (1/2 мили)", callback_data="race_drag")
    kb.button(text="🌪️ Дрифт", callback_data="race_drift")
    kb.button(text="⬅️ Назад", callback_data="back_main")
    kb.adjust(1, 1, 1)
    
    await state.set_state(RaceForm.race_type)
    await call.message.edit_text("🏁 **Регистрация на гонку**\n\nВыбери тип гонки:", reply_markup=kb.as_markup(), parse_mode="Markdown")
    await call.answer()

@dp.callback_query(StateFilter(RaceForm.race_type), F.data.startswith("race_"))
async def process_race_type(call: CallbackQuery, state: FSMContext):
    race_type = "Дрэг-рейсинг" if call.data == "race_drag" else "Дрифт"
    await state.update_data(race_type=race_type)
    await state.set_state(RaceForm.game_id)
    await call.message.edit_text(f"🏎️ **{race_type}**\n\nВведи свой **ID в игре** (только цифры):", parse_mode="Markdown")
    await call.answer()

@dp.message(StateFilter(RaceForm.game_id), F.text)
async def process_game_id(message: Message, state: FSMContext):
    await state.update_data(game_id=message.text)
    await state.set_state(RaceForm.car)
    await message.answer("🚗 **На какой машине будешь участвовать?**\n\nНапиши модель:", parse_mode="Markdown")

@dp.message(StateFilter(RaceForm.car), F.text)
async def process_race_car(message: Message, state: FSMContext):
    data = await state.get_data()
    race_type = data["race_type"]
    game_id = data["game_id"]
    car = message.text
    username = f"@{message.from_user.username}" if message.from_user.username else message.from_user.first_name
    
    admin_text = (
        "🚨 **НОВАЯ ЗАЯВКА НА ГОНКУ!** 🚨\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        f"👤 **Игрок:** {username}\n"
        f"🏁 **Тип:** {race_type}\n"
        f"🆔 **ID:** `{game_id}`\n"
        f"🚗 **Машина:** {car}"
    )
    
    for admin_id in ADMIN_IDS:
        try:
            await bot.send_message(chat_id=admin_id, text=admin_text, parse_mode="Markdown")
        except Exception as e:
            print(f"Не удалось отправить админу {admin_id}: {e}")

    await state.clear()
    await message.answer("✅ **Заявка принята!** Ожидай, админ добавит тебя в друзья.", reply_markup=main_menu(check_is_admin(message.from_user)), parse_mode="Markdown")

# --- АДМИН РЕКЛАМА ---
@dp.callback_query(F.data == "admin_create_ad")
async def admin_start_ad(call: CallbackQuery, state: FSMContext):
    if not check_is_admin(call.from_user):
        await call.answer("⛔ Нет прав!", show_alert=True)
        return
    await state.set_state(AdminAdForm.photo)
    await call.message.edit_text("👑 **Админ: Реклама**\n\nОтправь фото:", parse_mode="Markdown")
    await call.answer()

@dp.message(StateFilter(AdminAdForm.photo), F.photo)
async def admin_process_photo(message: Message, state: FSMContext):
    await state.update_data(photo=message.photo[-1].file_id)
    await state.set_state(AdminAdForm.description)
    await message.answer("📝 **Текст рекламы:**", parse_mode="Markdown")

@dp.message(StateFilter(AdminAdForm.description), F.text)
async def admin_process_description(message: Message, state: FSMContext):
    data = await state.get_data()
    photo_id = data["photo"]
    ad_text = "🔥 **ОФИЦИАЛЬНОЕ СООБЩЕНИЕ METAIMPERIYA** 🔥\n\n" + message.text
    markup = universal_post_keyboard()
    for chat in [MAIN_CLAN_CHANNEL, SALE_CHANNEL, TRADE_CHANNEL, SELL_ACC_CHANNEL]:
        try:
            await bot.send_photo(chat_id=chat, photo=photo_id, caption=ad_text, reply_markup=markup, parse_mode="Markdown")
        except Exception as e:
            print(f"Ошибка: {e}")
    await state.clear()
    await message.answer("✅ **Реклама отправлена!**", reply_markup=main_menu(True), parse_mode="Markdown")

# --- СЕРВЕР ---
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

@app.get("/")
async def index():
    return {"status": "bot is running"}

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    uvicorn.run("bot:app", host="0.0.0.0", port=port)
