import asyncio
import os
from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart, StateFilter, Command
from aiogram.types import Message, CallbackQuery, Update
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
from fastapi import FastAPI
import uvicorn

BOT_TOKEN = os.environ.get("BOT_TOKEN")
WEBHOOK_URL = os.environ.get("WEBHOOK_URL")

# --- КАНАЛЫ И ГРУППЫ ---
MAIN_CLAN_CHANNEL = "@cpm_2_clan"
SALE_CHANNEL = "@cpm_2_sale"
TRADE_CHANNEL = "@cpm_2_trade"
MONEY_CHANNEL = "@cpm_2_money"

# --- АДМИНЫ БОТА (Юзернеймы без @ или с @) ---
ADMINS = {"citymain", "metaimperiya"}  # Можешь дописать сюда еще кого-то в нижнем регистре

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
app = FastAPI()

# --- СОСТОЯНИЯ ДЛЯ ПОДАЧИ ОБЪЯВЛЕНИЯ ---
class AdForm(StatesGroup):
    category = State()
    photo = State()
    description = State()

# --- ГЛАВНОЕ МЕНЮ ---
def main_menu(is_admin=False):
    kb = InlineKeyboardBuilder()
    kb.button(text="📢 Подать объявление", callback_data="create_ad")
    kb.button(text="🏎️ Класс A", callback_data="class_a")
    kb.button(text="🚙 Класс B", callback_data="class_b")
    kb.button(text="🚗 Класс C", callback_data="class_c")
    kb.button(text="🌐 Наш сайт (METAIMPERIYA)", url="https://www.metaimperiya.com/")
    kb.button(text="💬 Все наши группы", callback_data="groups_menu")
    
    if is_admin:
        kb.button(text="⚙️ Панель Администратора", callback_data="admin_panel")
        kb.adjust(1, 3, 1, 1, 1)
    else:
        kb.adjust(1, 3, 1, 1)
        
    return kb.as_markup()

# --- МЕНЮ КАТЕГОРИЙ ОБЪЯВЛЕНИЙ ---
def categories_menu():
    kb = InlineKeyboardBuilder()
    kb.button(text="💰 Продажа (Sale)", callback_data="cat_sale")
    kb.button(text="🔄 Обмен (Trade)", callback_data="cat_trade")
    kb.button(text="💵 Услуги/Деньги (Money)", callback_data="cat_money")
    kb.button(text="⬅️ Отмена", callback_data="back_main")
    kb.adjust(1, 1, 1, 1)
    return kb.as_markup()

# --- МЕНЮ ГРУПП С КНОПКАМИ ---
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

# Функция проверки на админа
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
        f"Здарова, **{message.from_user.first_name}**! Добро пожаловать в официальный бот."
        f"{admin_badge}\n\n"
        "⚡ Здесь ты можешь выставить объявление, заценить тачки и залететь в наши группы.\n"
        "Выбирай нужный раздел ниже:"
    )
    await message.answer(text, reply_markup=main_menu(is_admin), parse_mode="Markdown")

@dp.callback_query(F.data == "admin_panel")
async def admin_panel(call: CallbackQuery):
    if not check_is_admin(call.from_user):
        await call.answer("⛔ У тебя нет прав администратора!", show_alert=True)
        return
    
    kb = InlineKeyboardBuilder()
    kb.button(text="⬅️ Назад в меню", callback_data="back_main")
    kb.adjust(1)
    
    await call.message.edit_text(
        "⚙️ **Панель управления администратора**\n\n"
        "Приветствую, босс! Здесь в будущем будут инструменты управления ботом и рассылками.",
        reply_markup=kb.as_markup(),
        parse_mode="Markdown"
    )
    await call.answer()

@dp.callback_query(F.data == "groups_menu")
async def show_groups(call: CallbackQuery):
    text = "💬 **Наши официальные ресурсы и группы CPM 2:**"
    await call.message.edit_text(text, reply_markup=groups_menu(), parse_mode="Markdown")
    await call.answer()

@dp.callback_query(F.data == "back_main")
async def back_main(call: CallbackQuery, state: FSMContext):
    await state.clear()
    is_admin = check_is_admin(call.from_user)
    text = "🔥 **METAIMPERIYA | CPM 2 HUB & CLAN** 🔥\n\nГлавное меню:"
    await call.message.edit_text(text, reply_markup=main_menu(is_admin), parse_mode="Markdown")
    await call.answer()

# --- ПОДАЧА ОБЪЯВЛЕНИЯ ---

@dp.callback_query(F.data == "create_ad")
async def start_ad(call: CallbackQuery, state: FSMContext):
    await state.set_state(AdForm.category)
    await call.message.edit_text(
        "📢 **Подача объявления в сеть METAIMPERIYA**\n\n"
        "Выбери категорию сделки:\n"
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
        "📸 **Отправь фото / скриншот тачки.**\n\n"
        "Загрузи одно изображение прямо сюда в чат.",
        parse_mode="Markdown"
    )
    await call.answer()

@dp.message(StateFilter(AdForm.photo), F.photo)
async def process_photo(message: Message, state: FSMContext):
    photo_id = message.photo[-1].file_id
    await state.update_data(photo=photo_id)
    await state.set_state(AdForm.description)
    
    await message.answer(
        "📝 **Напиши текст объявления.**\n\n"
        "Укажи название машины, тюнинг, цену или условия, а также твой контакт/ID.",
        parse_mode="Markdown"
    )

@dp.message(StateFilter(AdForm.photo))
async def process_photo_invalid(message: Message):
    await message.answer("⚠️ Пожалуйста, отправь именно **картинку/фото** машины!")

@dp.message(StateFilter(AdForm.description), F.text)
async def process_description(message: Message, state: FSMContext):
    user_data = await state.get_data()
    category = user_data["category"]
    photo_id = user_data["photo"]
    description_text = message.text
    
    username = f"@{message.from_user.username}" if message.from_user.username else message.from_user.first_name

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
        f"👤 **Автор:** {username}\n"
        f"🛡️ **Клановый хаб:** {MAIN_CLAN_CHANNEL}"
    )

    # Неудалимые постоянные кнопки для репостов и каналов
    post_kb = InlineKeyboardBuilder()
    post_kb.button(text="🌐 Наш сайт", url="https://www.metaimperiya.com/")
    post_kb.button(text="💬 Наш Клан", url="https://t.me/cpm_2_clan")
    post_kb.adjust(2)
    markup = post_kb.as_markup()

    # Публикация в основной клановый канал
    try:
        await bot.send_photo(chat_id=MAIN_CLAN_CHANNEL, photo=photo_id, caption=post_text, reply_markup=markup, parse_mode="Markdown")
    except Exception as e:
        print(f"Ошибка публикации в главный клан: {e}")

    # Публикация в профильный канал
    try:
        await bot.send_photo(chat_id=target_channel, photo=photo_id, caption=post_text, reply_markup=markup, parse_mode="Markdown")
    except Exception as e:
        print(f"Ошибка публикации в {target_channel}: {e}")

    await state.clear()
    is_admin = check_is_admin(message.from_user)
    await message.answer(
        "✅ **Объявление успешно опубликовано!**\n\n"
        f"Пост улетел в каналы с несгораемыми кнопками.",
        reply_markup=main_menu(is_admin),
        parse_mode="Markdown"
    )

@dp.callback_query(F.data.in_({"class_a", "class_b", "class_c"}))
async def classes_info(call: CallbackQuery):
    class_name = call.data.upper().replace("_", " ")
    await call.answer(f"Раздел '{class_name}' заправляется топливом, скоро откроем!", show_alert=True)

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
