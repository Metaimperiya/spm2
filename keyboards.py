from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

ADMIN_USERNAME = "metaimperiya"
SITE_URL = "https://www.metaimperiya.com/"

# НИЖНЯЯ КЛАВИАТУРА (КНОПКА ВОЗВРАЩЕНА)
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
    kb.button(text="🛡️ Клан", url="https://t.me/cpm_2_clan")
    kb.button(text="🚗 Тачки", url="https://t.me/tachki_cpm_2")
    kb.button(text="📈 Трейд", url="https://t.me/cpm_2_trade")
    kb.button(text="💰 Продажа авто", url="https://t.me/cpm_2_sale")
    kb.button(text="👤 Продажа акков", url="https://t.me/Sell_CPM_2_accounts")
    kb.button(text="🤝 Покупка акков", url="https://t.me/BuyCPM2accounts")
    kb.button(text="🌐 Наш сайт", url=SITE_URL)
    kb.button(text="⬅️ Назад", callback_data="back_main")
    kb.adjust(2, 2, 2, 1, 1)
    return kb.as_markup()

# Кнопки для поста (когда юзер или админ их добавляет)
def custom_post_kb(buttons_list):
    kb = InlineKeyboardBuilder()
    for btn in buttons_list:
        try:
            name, url = btn.split("|")
            kb.button(text=name.strip(), url=url.strip())
        except:
            pass
    kb.adjust(1)
    return kb.as_markup()

def admin_approve_kb(ad_id):
    kb = InlineKeyboardBuilder()
    kb.button(text="✅ Одобрить", callback_data=f"approve_{ad_id}")
    kb.button(text="❌ Отклонить", callback_data=f"reject_{ad_id}")
    kb.adjust(2)
    return kb.as_markup()
