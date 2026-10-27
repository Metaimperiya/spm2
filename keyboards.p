from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

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
    kb.button(text="🚗 Автомобили", callback_data="menu_cars")
    kb.button(text="👤 Аккаунты", callback_data="menu_accs")
    kb.button(text="💵 Монеты", callback_data="menu_money")
    kb.button(text="🏁 Гонки", callback_data="menu_races")
    kb.button(text="💼 Услуги и другое", callback_data="menu_services")
    kb.button(text="💬 Сообщество", callback_data="menu_community")
    
    if is_admin:
        kb.button(text="👑 Админ-панель", callback_data="admin_panel")
        kb.adjust(2, 2, 1, 1)
    else:
        kb.adjust(2, 2, 1, 1)
    return kb.as_markup()

# --- МЕНЮ АВТОМОБИЛЕЙ ---
def cars_menu():
    kb = InlineKeyboardBuilder()
    kb.button(text="💰 Продать машину", callback_data="car_sell")
    kb.button(text="🛒 Купить машину", callback_data="car_buy")
    kb.button(text="🔄 Обменять машину", callback_data="car_trade")
    kb.button(text="📁 Мои объявления", callback_data="my_ads")
    kb.button(text="⬅️ Назад", callback_data="back_main")
    kb.adjust(1, 1, 1, 1, 1)
    return kb.as_markup()

# --- МЕНЮ АККАУНТОВ ---
def accs_menu():
    kb = InlineKeyboardBuilder()
    kb.button(text="💰 Продать аккаунт", callback_data="acc_sell")
    kb.button(text="🛒 Купить аккаунт", callback_data="acc_buy")
    kb.button(text="📁 Мои объявления", callback_data="my_ads")
    kb.button(text="⬅️ Назад", callback_data="back_main")
    kb.adjust(1, 1, 1, 1)
    return kb.as_markup()

# --- МЕНЮ МОНЕТ ---
def money_menu():
    kb = InlineKeyboardBuilder()
    kb.button(text="💰 Продать монеты", callback_data="money_sell")
    kb.button(text="🛒 Купить монеты", callback_data="money_buy")
    kb.button(text="📜 Условия и помощь", callback_data="money_help")
    kb.button(text="⬅️ Назад", callback_data="back_main")
    kb.adjust(1, 1, 1, 1)
    return kb.as_markup()

# --- МЕНЮ СООБЩЕСТВА ---
def community_menu(channels: dict):
    kb = InlineKeyboardBuilder()
    if channels.get("main"):
        kb.button(text="🛡️ Главный канал", url=f"https://t.me/{channels['main'].replace('@', '')}")
    if channels.get("trade"):
        kb.button(text="🔄 Канал обмена", url=f"https://t.me/{channels['trade'].replace('@', '')}")
    if channels.get("sell_acc"):
        kb.button(text="👤 Продажа аккаунтов", url=f"https://t.me/{channels['sell_acc'].replace('@', '')}")
    if channels.get("buy_acc"):
        kb.button(text="🤝 Покупка аккаунтов", url=f"https://t.me/{channels['buy_acc'].replace('@', '')}")
    if channels.get("sale"):
        kb.button(text="🚗 Продажа авто", url=f"https://t.me/{channels['sale'].replace('@', '')}")
        
    kb.button(text="🌐 Наш сайт", url="https://www.metaimperiya.com/")
    kb.button(text="⬅️ Назад", callback_data="back_main")
    kb.adjust(2, 2, 2, 1)
    return kb.as_markup()

# --- ПОДТВЕРЖДЕНИЕ ---
def confirm_menu():
    kb = InlineKeyboardBuilder()
    kb.button(text="✅ Опубликовать", callback_data="confirm_publish")
    kb.button(text="✏️ Изменить", callback_data="confirm_edit")
    kb.button(text="❌ Отмена", callback_data="back_main")
    kb.adjust(1, 1, 1)
    return kb.as_markup()
