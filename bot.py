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

# --- КАНАЛЫ И ГРУППЫ СЕТИ ---
MAIN_CLAN_CHANNEL = "@cpm_2_clan"
SALE_CHANNEL = "@cpm_2_sale"
TRADE_CHANNEL = "@cpm_2_trade"
MONEY_CHANNEL = "@cpm_2_money"
SITE_URL = "https://www.metaimperiya.com/"

# --- АДМИНЫ (СЮДА ПРИЛЕТАЮТ ЗАЯВКИ) ---
# ВАЖНО: Замени эти цифры на свои реальные Telegram ID!
# Узнать свой ID можно у бота @userinfobot
ADMIN_IDS = [123456789, 987654321] # Замени на ID @citymain и @metaimperiya

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
app = FastAPI()

# --- СОСТОЯНИЯ ---
class AdForm(StatesGroup):
    category = State()
    photo = State()
    description = State()

class AdminAdForm(StatesGroup):
    photo = State()
    description = State()

class RaceForm(StatesGroup):
    race_type = State()
    game_id = State()
    car = State()

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
    kb.button(text="🏁 Записаться на гонку", callback_data="join_race")
    kb.button(text="🛒 Барахолка (Купить/Продать)", callback_data="create_ad")
    kb.button(text="🏎️ Класс A (Спорткары)", callback_data="class_a")
    kb.button(text="🚙 Класс B (Внедорожники)", callback_data="class_b")
    kb.button(text="🚗 Класс C (Городские)", callback_data="class_c")
    kb.button(text="🌐 Наш Сайт", url=SITE_URL)
    kb.button(text="💬 Сеть каналов CPM 2", callback_data="groups_menu")
    
    if is_admin:
        kb.button(text="👑 Создать рекламный пост", callback_data="admin_create_ad")
        kb.adjust(1, 1, 3, 1, 1, 1)
    else:
        kb.adjust(1, 1, 3, 1, 1)
        
    return kb.as_markup()

def categories_menu():
    kb = InlineKeyboardBuilder()
    kb.button(text="💰 Продать машину", callback_data="cat_sale")
    kb.button(text="🔄 Обменять машину", callback_data="cat_trade")
    kb.button(text="💵 Услуги / Деньги", callback_data="cat_money")
    kb.button(text="⬅️ Назад", callback_data="back_main")
    kb.adjust(1, 1, 1, 1)
    return kb.as_markup()

def groups_menu():
    kb = InlineKeyboardBuilder()
    kb.button(text="🛡️ Наш Клан", url="https://t.me/cpm_2_clan")
    kb.button(text="🚗 Тачки (Мемы)", url="https://t.me/tachki_cpm_2")
    kb.button(text="📈 Трейд (Обмен)", url="https://t.me/cpm_2_trade")
    kb.button(text="💰 Продажа", url="https://t.me/cpm_2_sale")
    kb.button(text="💵 Заработок", url="https://t.me/cpm_2_money")
    kb.button(text="⬅️ Назад", callback_data="back_main")
    kb.adjust(2, 2, 1, 1)
    return kb.as_markup()

def universal_post_keyboard():
    kb = InlineKeyboardBuilder()
    kb.button(text="🌐 Наш сайт", url=SITE_URL)
    kb.button(text="🛡️ Клан", url="https://t.me/cpm_2_clan")
    kb.button(text="🚗 Тачки", url="https://t.me/tachki_cpm_2")
    kb.button(text="📈 Трейд", url="https://t.me/cpm_2_trade")
    kb.button(text="💰 Продажа", url="https://t.me/cpm_2_sale")
    kb.button(text="💵 Заработок", url="https://t.me/cpm_2_money")
    kb.adjust(2, 2, 2)
    return kb.as_markup()

def check_is_admin(user) -> bool:
    if not user.username:
        return False
    return user.username.lower() in ADMINS

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
        "Добро пожаловать в главный хаб сети Car Parking Multiplayer 2.\n"
        "👇 *Выбирай нужный раздел в меню ниже:*"
    )
    
    await message.answer(text, reply_markup=bottom_menu(), parse_mode="Markdown")
    await message.answer("🚀 **Главное меню:**", reply_markup=main_menu(is_admin), parse_mode="Markdown")

@dp.message(F.text == "🏠 В главное меню")
async def open_bottom_menu(message: Message, state: FSMContext):
    await state.clear()
    is_admin = check_is_admin(message.from_user)
    await message.answer("🚀 **Главное меню:**", reply_markup=main_menu(is_admin), parse_mode="Markdown")

# --- ЛОГИКА ГОНОК ---
@dp.callback_query(F.data == "join_race")
async def start_race(call: CallbackQuery, state: FSMContext):
    kb = InlineKeyboardBuilder()
    kb.button(text="🏎️ Дрэг-рейсинг (1/2 мили)", callback_data="race_drag")
    kb.button(text="🌪️ Дрифт", callback_data="race_drift")
    kb.button(text="⬅️ Назад", callback_data="back_main")
    kb.adjust(1, 1, 1)
    
    await state.set_state(RaceForm.race_type)
    await call.message.edit_text(
        "🏁 **Регистрация на гонку**\n\n"
        "Выбери тип гонки, в которой хочешь участвовать:",
        reply_markup=kb.as_markup(),
        parse_mode="Markdown"
    )
    await call.answer()

@dp.callback_query(StateFilter(RaceForm.race_type), F.data.startswith("race_"))
async def process_race_type(call: CallbackQuery, state: FSMContext):
    race_type = "Дрэг-рейсинг" if call.data == "race_drag" else "Дрифт"
    await state.update_data(race_type=race_type)
    await state.set_state(RaceForm.game_id)
    
    await call.message.edit_text(
        f"🏎️ **{race_type}**\n\n"
        "Введи свой **ID в игре** (только цифры, например: 12345678):",
        parse_mode="Markdown"
    )
    await call.answer()

@dp.message(StateFilter(RaceForm.game_id), F.text)
async def process_game_id(message: Message, state: FSMContext):
    await state.update_data(game_id=message.text)
    await state.set_state(RaceForm.car)
    await message.answer("🚗 **На какой машине будешь участвовать?**\n\nНапиши модель (например: Nissan GTR R35):", parse_mode="Markdown")

@dp.message(StateFilter(RaceForm.car), F.text)
async def process_race_car(message: Message, state: FSMContext):
    data = await state.get_data()
    race_type = data["race_type"]
    game_id = data["game_id"]
    car = message.text
    username = f"@{message.from_user.username}" if message.from_user.username else message.from_user.first_name
    
    # Текст заявки для админов
    admin_text = (
        "🚨 **НОВАЯ ЗАЯВКА НА ГОНКУ!** 🚨\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        f"👤 **Игрок:** {username}\n"
        f"🏁 **Тип гонки:** {race_type}\n"
        f"🆔 **ID в игре:** `{game_id}`\n"
        f"🚗 **Машина:** {car}\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "👉 *Срочно добавь его в друзья в игре!*"
    )
    
    # Отправляем заявку всем админам
    for admin_id in ADMIN_IDS:
        try:
            await bot.send_message(chat_id=admin_id, text=admin_text, parse_mode="Markdown")
        except Exception as e:
            print(f"Не удалось отправить админу {admin_id}: {e}")

    await state.clear()
    await message.answer(
        "✅ **Заявка принята!**\n\n"
        "Ожидай, админ скоро добавит тебя в друзья в игре для проведения гонки.",
        reply_markup=main_menu(check_is_admin(message.from_user)),
        parse_mode="Markdown"
    )

# --- ОСТАЛЬНОЙ КОД (БАРАХОЛКА И Т.Д.) ---
@dp.callback_query(F.data.in_({"class_a", "class_b", "class_c"}))
async def classes_info(call: CallbackQuery):
    if call.data == "class_a":
        text = "🏎️ **Класс A | Спорткары**\n\nСамые быстрые тачки. Lamborghini, Ferrari и другие."
    elif call.data == "class_b":
        text = "🚙 **Класс B | Внедорожники**\n\nНадежные тачки для бездорожья. УАЗ, Нива."
    else:
        text = "🚗 **Класс C | Городские**\n\nКлассика для города."
    
    kb = InlineKeyboardBuilder()
    kb.button(text="⬅️ Назад в меню", callback_data="back_main")
    await call.message.edit_text(text, reply_markup=kb.as_markup(), parse_mode="Markdown")
    await call.answer()

@dp.callback_query(F.data == "groups_menu")
async def show_groups(call: CallbackQuery):
    await call.message.edit_text("💬 **Официальная сеть CPM 2:**", reply_markup=groups_menu(), parse_mode="Markdown")
    await call.answer()

@dp.callback_query(F.data == "back_main")
async def back_main(call: CallbackQuery, state: FSMContext):
    await state.clear()
    is_admin = check_is_admin(call.from_user)
    await call.message.edit_text("🚀 **Главное меню:**", reply_markup=main_menu(is_admin), parse_mode="Markdown")
    await call.answer()

@dp.callback_query(F.data == "create_ad")
async def start_ad(call: CallbackQuery, state: FSMContext):
    await state.set_state(AdForm.category)
    await call.message.edit_text("🛒 **Барахолка**\n\nЧто ты хочешь сделать?", reply_markup=categories_menu(), parse_mode="Markdown")
    await call.answer()

@dp.callback_query(StateFilter(AdForm.category), F.data.startswith("cat_"))
async def process_category(call: CallbackQuery, state: FSMContext):
    category = call.data.split("_")[1]
    await state.update_data(category=category)
    await state.set_state(AdForm.photo)
    cat_name = "Продажа" if category == "sale" else ("Обмен" if category == "trade" else "Услуги")
    await call.message.edit_text(f"📸 **{cat_name}**\n\nОтправь фото тачки:", parse_mode="Markdown")
    await call.answer()

@dp.message(StateFilter(AdForm.photo), F.photo)
async def process_photo(message: Message, state: FSMContext):
    await state.update_data(photo=message.photo[-1].file_id)
    await state.set_state(AdForm.description)
    await message.answer("📝 **Напиши описание** (цена, контакт):", parse_mode="Markdown")

@dp.message(StateFilter(AdForm.description), F.text)
async def process_description(message: Message, state: FSMContext):
    data = await state.get_data()
    category = data["category"]
    photo_id = data["photo"]
    username = f"@{message.from_user.username}" if message.from_user.username else message.from_user.first_name
    cat_tag = "#ПРОДАЖА" if category == "sale" else ("#ОБМЕН" if category == "trade" else "#УСЛУГИ")
    target_channel = SALE_CHANNEL if category == "sale" else (TRADE_CHANNEL if category == "trade" else MONEY_CHANNEL)
    post_text = f"🔥 **ОБЪЯВЛЕНИЕ CPM 2** ({cat_tag})\n\n{message.text}\n\n👤 **Автор:** {username}"
    markup = universal_post_keyboard()
    for chat in {MAIN_CLAN_CHANNEL, target_channel}:
        try:
            await bot.send_photo(chat_id=chat, photo=photo_id, caption=post_text, reply_markup=markup, parse_mode="Markdown")
        except Exception as e:
            print(f"Ошибка: {e}")
    await state.clear()
    await message.answer("✅ **Объявление опубликовано!**", reply_markup=main_menu(check_is_admin(message.from_user)), parse_mode="Markdown")

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
    for chat in [MAIN_CLAN_CHANNEL, SALE_CHANNEL, TRADE_CHANNEL, MONEY_CHANNEL]:
        try:
            await bot.send_photo(chat_id=chat, photo=photo_id, caption=ad_text, reply_markup=markup, parse_mode="Markdown")
        except Exception as e:
            print(f"Ошибка: {e}")
    await state.clear()
    await message.answer("✅ **Реклама отправлена!**", reply_markup=main_menu(True), parse_mode="Markdown")

# --- ВЕБХУКИ ---
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
