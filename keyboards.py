from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from locales import get_text, SUPPORTED_LANGUAGES

ADMIN_USERNAME = "metaimperiya"
SITE_URL = "https://www.metaimperiya.com/"

# Список остальных каналов (БЕЗ ПОДСЛУШКИ)
AUTO_BUTTONS = [
    ("💰 Продажа", "https://t.me/cpm_2_sale"),
    ("🔄 Обмен", "https://t.me/cpm_2_trade"),
    ("👤 Аккаунты", "https://t.me/Sell_CPM_2_accounts"),
    ("🛡️ Клан", "https://t.me/cpm_2_clan"),
    ("🇷🇺 Россия", "https://t.me/cpm_2_russia"),
    ("🇬🇧 English", "https://t.me/CPM_2_English"),
    ("📱 Mobile", "https://t.me/CPM2_Mobile"),
    ("🇹🇷 Turkey", "https://t.me/CPM2Turkey"),
    ("🇺🇦 Ukraine", "https://t.me/CPM2Ukraine"),
    ("📈 Trading", "https://t.me/CPM2Trader"),
    ("🌐 Наш сайт", SITE_URL)
]

def bottom_menu(lang="ru"):
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=get_text("btn_post", lang))],
            [KeyboardButton(text=get_text("btn_main", lang))]
        ],
        resize_keyboard=True, is_persistent=True
    )

def main_menu(is_admin=False, lang="ru"):
    kb = InlineKeyboardBuilder()
    kb.button(text=get_text("btn_ads", lang), callback_data="menu_cars")
    kb.button(text=get_text("btn_accs", lang), callback_data="menu_accs")
    kb.button(text=get_text("btn_money", lang), callback_data="menu_money")
    kb.button(text=get_text("btn_races", lang), callback_data="join_race")
    kb.button(text=get_text("btn_community", lang), callback_data="menu_community")
    kb.button(text=get_text("btn_listening", lang), url="https://t.me/podslushkacpm2")
    if is_admin:
        kb.button(text=get_text("btn_admin", lang), callback_data="admin_panel")
        kb.adjust(2, 2, 1, 1, 1)
    else:
        kb.adjust(2, 2, 1, 1)
    kb.button(text=get_text("btn_lang", lang), callback_data="choose_language")
    kb.adjust(2, 2, 1, 1, 1)
    return kb.as_markup()

def language_menu():
    kb = InlineKeyboardBuilder()
    for code, label in SUPPORTED_LANGUAGES.items():
        kb.button(text=label, callback_data=f"lang_{code}")
    kb.adjust(2, 2, 2, 2, 2, 2, 2, 1)
    return kb.as_markup()

def cars_menu(lang="ru"):
    kb = InlineKeyboardBuilder()
    kb.button(text=get_text("btn_sell_car", lang), callback_data="car_sell")
    kb.button(text=get_text("btn_trade_car", lang), callback_data="car_trade")
    kb.button(text=get_text("btn_buy_car", lang), callback_data="buy_car_catalog")
    kb.button(text=get_text("btn_back", lang), callback_data="back_main")
    kb.adjust(1, 1, 1, 1)
    return kb.as_markup()

def accs_menu(lang="ru"):
    kb = InlineKeyboardBuilder()
    kb.button(text=get_text("btn_sell_acc", lang), callback_data="acc_sell")
    kb.button(text=get_text("btn_buy_acc", lang), callback_data="buy_acc_catalog")
    kb.button(text=get_text("btn_back", lang), callback_data="back_main")
    kb.adjust(1, 1, 1)
    return kb.as_markup()

def money_menu(lang="ru"):
    kb = InlineKeyboardBuilder()
    kb.button(text=get_text("btn_sell_coin", lang), url=f"https://t.me/{ADMIN_USERNAME}")
    kb.button(text=get_text("btn_buy_coin", lang), url=f"https://t.me/{ADMIN_USERNAME}")
    kb.button(text=get_text("btn_services", lang), url=f"https://t.me/{ADMIN_USERNAME}")
    kb.button(text=get_text("btn_back", lang), callback_data="back_main")
    kb.adjust(1, 1, 1, 1)
    return kb.as_markup()

def community_menu(lang="ru"):
    kb = InlineKeyboardBuilder()
    kb.button(text=get_text("btn_listening", lang), url="https://t.me/podslushkacpm2")
    for name, url in AUTO_BUTTONS:
        kb.button(text=name, url=url)
    kb.button(text=get_text("btn_back", lang), callback_data="back_main")
    kb.adjust(1, 2, 2, 2, 2, 2, 2, 1)
    return kb.as_markup()

def custom_post_kb(buttons_list):
    kb = InlineKeyboardBuilder()
    kb.button(text="👂 ПОДСЛУШКА CPM 2", url="https://t.me/podslushkacpm2")
    for btn in buttons_list:
        try:
            name, url = btn.split("|")
            kb.button(text=name.strip(), url=url.strip())
        except:
            pass
    kb.adjust(1, 2)
    return kb.as_markup()

def admin_approve_kb(ad_id):
    kb = InlineKeyboardBuilder()
    kb.button(text="✅ Одобрить", callback_data=f"approve_{ad_id}")
    kb.button(text="❌ Отклонить", callback_data=f"reject_{ad_id}")
    kb.adjust(2)
    return kb.as_markup()

def admin_panel_kb(lang="ru"):
    kb = InlineKeyboardBuilder()
    kb.button(text=get_text("create_post", lang), callback_data="admin_post_simple")
    kb.button(text=get_text("buttons_only", lang), callback_data="admin_buttons_only")
    kb.button(text=get_text("broadcast", lang), callback_data="admin_broadcast")
    kb.button(text=get_text("back", lang), callback_data="back_main")
    kb.adjust(1, 1, 1, 1)
    return kb.as_markup()


def newsletter_settings_kb(enabled=False, lang="ru"):
    if enabled:
        button = InlineKeyboardButton(
            text=get_text("btn_unsubscribe", lang),
            callback_data="newsletter_unsubscribe",
        )
    else:
        button = InlineKeyboardButton(
            text=get_text("btn_subscribe", lang),
            callback_data="newsletter_subscribe",
        )
    return InlineKeyboardMarkup(inline_keyboard=[[button]])
