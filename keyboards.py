from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

ADMIN_USERNAME = "metaimperiya"
SITE_URL = "https://www.metaimperiya.com/"

# СПИСОК ТВОИХ ГРУПП ДЛЯ АВТО-КНОПОК
AUTO_BUTTONS = [
    ("💰 Продажа", "https://t.me/cpm_2_sale"),
    ("🔄 Обмен", "https://t.me/cpm_2_trade"),
    ("👤 Аккаунты", "https://t.me/Sell_CPM_2_accounts"),
    ("🛡️ Клан", "https://t.me/cpm_2_clan"),
    ("🇷🇺 Россия", "https://t.me/cpm_2_russia"),
    ("🇬🇧 English", "https://t.me/CPM_2_English"),
    ("🇺🇸 USA", "https://t.me/CPM2USA"),
    ("📱 Mobile", "https://t.me/CPM2_Mobile"),
    ("🇹🇷 Turkey", "https://t.me/CPM2Turkey"),
    ("🇺🇦 Ukraine", "https://t.me/CPM2Ukraine"),
    ("📈 Trading", "https://t.me/CPM2Trading"),
    ("🌐 Наш сайт", SITE_URL)
]

def bottom_menu():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📢 Подать объявление")],
            [KeyboardButton(text="🏠 В главное меню")]
        ],
        resize_keyboard=True, is_persistent=True
    )

def main_menu(is_admin=False):
    kb = InlineKeyboardBuilder()
    kb.button(text="🚗 Автомобили", callback_data="menu_cars")
    kb.button(text="👤 Аккаунты", callback_data="menu_accs")
    kb.button(text="💵 Монеты / Услуги", callback_data="menu_money")
    kb.button(text="🏁 Гонки", callback_data="join_race")
    kb.button(text="💬 Сообщество", callback_data="menu_community")
    if is_admin:
        kb.button(text="👑 Админ-панель", callback_data="admin_panel")
        kb.adjust(2, 2, 1, 1)
    else:
        kb.adjust(2, 2, 1)
    return kb.as_markup()

def cars_menu():
    kb = InlineKeyboardBuilder()
    kb.button(text="💰 Продать машину", callback_data="car_sell")
    kb.button(text="🔄 Обменять машину", callback_data="car_trade")
    kb.button(text="🛒 Купить машину", callback_data="buy_car_catalog")
    kb.button(text="⬅️ Назад", callback_data="back_main")
    kb.adjust(1, 1, 1, 1)
    return kb.as_markup()

def accs_menu():
    kb = InlineKeyboardBuilder()
    kb.button(text="💰 Продать аккаунт", callback_data="acc_sell")
    kb.button(text="🛒 Купить аккаунт", callback_data="buy_acc_catalog")
    kb.button(text="⬅️ Назад", callback_data="back_main")
    kb.adjust(1, 1, 1)
    return kb.as_markup()

def money_menu():
    kb = InlineKeyboardBuilder()
    kb.button(text="💰 Продать монеты", url=f"https://t.me/{ADMIN_USERNAME}")
    kb.button(text="🛒 Купить монеты", url=f"https://t.me/{ADMIN_USERNAME}")
    kb.button(text="💼 Услуги", url=f"https://t.me/{ADMIN_USERNAME}")
    kb.button(text="⬅️ Назад", callback_data="back_main")
    kb.adjust(1, 1, 1, 1)
    return kb.as_markup()

def community_menu():
    kb = InlineKeyboardBuilder()
    for name, url in AUTO_BUTTONS:
        kb.button(text=name, url=url)
    kb.button(text="⬅️ Назад", callback_data="back_main")
    kb.adjust(2, 2, 2, 2, 2, 2, 1) # Сетка по 2 кнопки в ряд
    return kb.as_markup()

def custom_post_kb(buttons_list):
    kb = InlineKeyboardBuilder()
    for btn in buttons_list:
        try:
            name, url = btn.split("|")
            kb.button(text=name.strip(), url=url.strip())
        except:
            pass
    kb.adjust(2) # Сетка по 2 в ряд для постов
    return kb.as_markup()

def admin_approve_kb(ad_id):
    kb = InlineKeyboardBuilder()
    kb.button(text="✅ Одобрить", callback_data=f"approve_{ad_id}")
    kb.button(text="❌ Отклонить", callback_data=f"reject_{ad_id}")
    kb.adjust(2)
    return kb.as_markup()

def admin_panel_kb():
    kb = InlineKeyboardBuilder()
    kb.button(text="📢 Создать рекламный пост", callback_data="admin_post_simple")
    kb.button(text="⬅️ Назад", callback_data="back_main")
    kb.adjust(1, 1)
    return kb.as_markup()
