from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder

from states import AdForm, RaceForm
from keyboards import main_menu, bottom_menu, cars_menu, accs_menu, money_menu, community_menu, newsletter_settings_kb, newsletter_done_kb, language_menu
from database import add_ad_to_db, get_approved_ads, add_user_to_db, get_user_language, set_user_language
from locales import get_text, SUPPORTED_LANGUAGES, TEXTS
from firebase_bridge import (
    consume_link_code,
    create_garage_submission,
    get_linked_uid,
    initialize,
    unlink_telegram_account,
    is_newsletter_subscriber,
    set_newsletter_subscription,
)
from bot_config import ADMIN_IDS, is_admin
import asyncio
import re

router = Router()

def user_lang(user_id):
    lang = get_user_language(user_id)
    return lang if lang in SUPPORTED_LANGUAGES else "ru"

def translated(user_id, key, **kwargs):
    return get_text(key, user_lang(user_id), **kwargs)

def localized_button_values(key):
    return {get_text(key, code) for code in SUPPORTED_LANGUAGES}

@router.message(F.text.regexp(r"^/link(?:@\w+)?\s+([A-Za-z0-9_-]{6,32})$"))
async def link_website_account(message: Message):
    code = message.text.split(maxsplit=1)[1].strip()
    try:
        if not await asyncio.to_thread(initialize):
            await message.answer(translated(message.from_user.id, "link_unconfigured"))
            return
        uid = await asyncio.to_thread(consume_link_code, code, message.from_user.id,
                                     message.from_user.username, message.from_user.first_name)
        if not uid:
            await message.answer(translated(message.from_user.id, "link_code_invalid"))
            return
        await message.answer(translated(message.from_user.id, "link_success"))
    except Exception as error:
        print(f"Firebase link error: {error}")
        await message.answer(translated(message.from_user.id, "link_failed"))

@router.message(F.text == "/link")
async def link_help(message: Message):
    await message.answer(translated(message.from_user.id, "link_help"))

@router.message(F.text == "/unlink")
async def unlink_website_account(message: Message):
    try:
        removed = await asyncio.to_thread(unlink_telegram_account, message.from_user.id)
        await message.answer(translated(message.from_user.id, "link_removed" if removed else "link_none"))
    except Exception as error:
        print(f"Firebase unlink error: {error}")
        await message.answer(translated(message.from_user.id, "unlink_failed"))

def is_admin_check(user):
    return is_admin(user)


def newsletter_status_text(enabled, lang="ru"):
    return get_text("newsletter_on" if enabled else "newsletter_off", lang)


@router.callback_query(F.data.in_({"newsletter_subscribe", "newsletter_unsubscribe"}))
async def change_newsletter_subscription(call: CallbackQuery):
    enabled = call.data == "newsletter_subscribe"
    add_user_to_db(
        call.from_user.id,
        f"@{call.from_user.username}" if call.from_user.username else "скрыт",
        call.from_user.first_name,
    )
    try:
        await asyncio.to_thread(
            set_newsletter_subscription,
            call.from_user.id,
            call.from_user.username,
            call.from_user.first_name,
            enabled,
        )
    except Exception as error:
        print(f"Telegram newsletter preference error: {error}")
        lang = user_lang(call.from_user.id)
        await call.answer(get_text("newsletter_error", lang), show_alert=True)
        return
    lang = user_lang(call.from_user.id)
    await call.message.edit_text(
        newsletter_status_text(enabled, lang),
        reply_markup=newsletter_done_kb(lang),
    )
    await call.answer(get_text("lang_saved", lang))


@router.callback_query(F.data == "newsletter_settings")
async def open_newsletter_settings(call: CallbackQuery):
    lang = user_lang(call.from_user.id)
    try:
        enabled = await asyncio.to_thread(is_newsletter_subscriber, call.from_user.id)
    except Exception as error:
        print(f"Telegram newsletter status error: {error}")
        await call.answer(get_text("newsletter_error", lang), show_alert=True)
        return
    await call.message.edit_text(
        newsletter_status_text(enabled, lang),
        reply_markup=newsletter_settings_kb(enabled, lang),
    )
    await call.answer()


@router.callback_query(F.data == "newsletter_back")
async def close_newsletter_settings(call: CallbackQuery):
    lang = user_lang(call.from_user.id)
    await call.message.edit_text(
        get_text("main_title", lang),
        reply_markup=main_menu(is_admin_check(call.from_user), lang),
        parse_mode="Markdown",
    )
    await call.answer()


@router.message(F.text == "/subscribe")
async def newsletter_subscribe_command(message: Message):
    add_user_to_db(
        message.from_user.id,
        f"@{message.from_user.username}" if message.from_user.username else "скрыт",
        message.from_user.first_name,
    )
    try:
        await asyncio.to_thread(
            set_newsletter_subscription,
            message.from_user.id,
            message.from_user.username,
            message.from_user.first_name,
            True,
        )
    except Exception as error:
        print(f"Telegram newsletter preference error: {error}")
        await message.answer(translated(message.from_user.id, "newsletter_error"))
        return
    await message.answer(
        newsletter_status_text(True, user_lang(message.from_user.id)),
        reply_markup=newsletter_done_kb(user_lang(message.from_user.id)),
    )


@router.message(F.text == "/unsubscribe")
async def newsletter_unsubscribe_command(message: Message):
    add_user_to_db(
        message.from_user.id,
        f"@{message.from_user.username}" if message.from_user.username else "скрыт",
        message.from_user.first_name,
    )
    try:
        await asyncio.to_thread(
            set_newsletter_subscription,
            message.from_user.id,
            message.from_user.username,
            message.from_user.first_name,
            False,
        )
    except Exception as error:
        print(f"Telegram newsletter preference error: {error}")
        await message.answer(translated(message.from_user.id, "newsletter_error"))
        return
    await message.answer(
        get_text("newsletter_off", user_lang(message.from_user.id)),
        reply_markup=newsletter_done_kb(user_lang(message.from_user.id)),
    )

@router.message(F.text.regexp(r"^/start(?:@\w+)?(?:\s.*)?$"))
async def start(message: Message, state: FSMContext):
    await state.clear()
    username = f"@{message.from_user.username}" if message.from_user.username else "скрыт"
    add_user_to_db(message.from_user.id, username, message.from_user.first_name)
    display_name = message.from_user.full_name or "Без имени"
    profile = f"@{message.from_user.username}" if message.from_user.username else "username скрыт"
    notification = (
        "▶️ Запуск бота (/start)\n"
        f"Имя: {display_name}\n"
        f"Профиль: {profile}\n"
        f"Telegram ID: {message.from_user.id}"
    )
    for admin_id in ADMIN_IDS:
        try:
            await message.bot.send_message(admin_id, notification)
        except Exception as error:
            print(f"Start notification failed for admin {admin_id}: {error}")
    await message.answer(translated(message.from_user.id, "choose_lang"), reply_markup=language_menu(), parse_mode="Markdown")

@router.message(F.text == "/language")
async def language_command(message: Message):
    add_user_to_db(message.from_user.id, f"@{message.from_user.username}" if message.from_user.username else "скрыт", message.from_user.first_name)
    await message.answer(translated(message.from_user.id, "choose_lang"), reply_markup=language_menu(), parse_mode="Markdown")

@router.callback_query(F.data == "choose_language")
async def choose_language(call: CallbackQuery):
    add_user_to_db(call.from_user.id, f"@{call.from_user.username}" if call.from_user.username else "скрыт", call.from_user.first_name)
    await call.message.edit_text(translated(call.from_user.id, "choose_lang"), reply_markup=language_menu(), parse_mode="Markdown")
    await call.answer()

@router.callback_query(F.data.startswith("lang_"))
async def set_language_callback(call: CallbackQuery):
    language = call.data[5:]
    if language not in SUPPORTED_LANGUAGES:
        await call.answer("Language unavailable", show_alert=True)
        return
    add_user_to_db(call.from_user.id, f"@{call.from_user.username}" if call.from_user.username else "скрыт", call.from_user.first_name)
    set_user_language(call.from_user.id, language)
    lang = language
    await call.message.edit_text(get_text("main_title", lang), reply_markup=main_menu(is_admin_check(call.from_user), lang), parse_mode="Markdown")
    await call.message.answer(get_text("lang_saved", lang), reply_markup=bottom_menu(lang))
    await call.answer(get_text("lang_saved", lang))

@router.message(F.text.in_(localized_button_values("btn_main")))
async def bottom_back(message: Message, state: FSMContext):
    await state.clear()
    lang = user_lang(message.from_user.id)
    await message.answer(get_text("main_title", lang), reply_markup=main_menu(is_admin_check(message.from_user), lang), parse_mode="Markdown")

@router.callback_query(F.data == "back_main")
async def back_main(call: CallbackQuery, state: FSMContext):
    await state.clear()
    lang = user_lang(call.from_user.id)
    await call.message.edit_text(get_text("main_title", lang), reply_markup=main_menu(is_admin_check(call.from_user), lang), parse_mode="Markdown")
    await call.answer()

@router.callback_query(F.data == "menu_cars")
async def show_cars(call: CallbackQuery):
    lang = user_lang(call.from_user.id)
    await call.message.edit_text(get_text("cars_title", lang), reply_markup=cars_menu(lang))
    await call.answer()

@router.callback_query(F.data == "menu_accs")
async def show_accs(call: CallbackQuery):
    lang = user_lang(call.from_user.id)
    await call.message.edit_text(get_text("accs_title", lang), reply_markup=accs_menu(lang))
    await call.answer()

@router.callback_query(F.data == "menu_money")
async def show_money(call: CallbackQuery):
    lang = user_lang(call.from_user.id)
    await call.message.edit_text(get_text("money_title", lang), reply_markup=money_menu(lang))
    await call.answer()

@router.callback_query(F.data == "menu_community")
async def show_community(call: CallbackQuery):
    lang = user_lang(call.from_user.id)
    await call.message.edit_text(get_text("community_title", lang), reply_markup=community_menu(lang))
    await call.answer()

@router.message(F.text.in_(localized_button_values("btn_post")))
async def bottom_create_ad(message: Message, state: FSMContext):
    await state.clear()
    is_admin = is_admin_check(message.from_user)
    kb = InlineKeyboardBuilder()
    if is_admin:
        lang = user_lang(message.from_user.id)
        kb.button(text=get_text("btn_sell_car_admin", lang), callback_data="admin_post_car")
        kb.button(text=get_text("btn_trade_car_admin", lang), callback_data="admin_post_trade")
        kb.button(text=get_text("btn_sell_acc_admin", lang), callback_data="admin_post_acc")
        kb.button(text=get_text("btn_simple_post", lang), callback_data="admin_post_simple")
        kb.button(text=get_text("btn_back", lang), callback_data="back_main")
        kb.adjust(1, 1, 1, 1, 1)
        await message.answer(translated(message.from_user.id, "choose_action"), reply_markup=kb.as_markup(), parse_mode="Markdown")
    else:
        lang = user_lang(message.from_user.id)
        kb.button(text=get_text("btn_sell_car_user", lang), callback_data="car_sell")
        kb.button(text=get_text("btn_trade_car_user", lang), callback_data="car_trade")
        kb.button(text=get_text("btn_sell_acc_user", lang), callback_data="acc_sell")
        kb.button(text=get_text("btn_back", lang), callback_data="back_main")
        kb.adjust(1, 1, 1, 1)
        await message.answer(translated(message.from_user.id, "choose_action"), reply_markup=kb.as_markup(), parse_mode="Markdown")

@router.callback_query(F.data.in_({"car_sell", "car_trade", "acc_sell"}))
async def process_ad_type(call: CallbackQuery, state: FSMContext):
    cat = "acc" if call.data == "acc_sell" else "car"
    if cat == "car":
        try:
            linked = await asyncio.to_thread(get_linked_uid, call.from_user.id)
        except Exception:
            linked = None
        if not linked:
            await call.answer(translated(call.from_user.id, "need_site_link"), show_alert=True)
            return
    await state.update_data(category=cat, ad_type=call.data)
    await state.set_state(AdForm.media)
    await call.message.edit_text(translated(call.from_user.id, "send_media"), parse_mode="Markdown")
    await call.answer()

@router.message(AdForm.media, F.photo | F.video)
async def ad_media(message: Message, state: FSMContext):
    if message.photo:
        await state.update_data(media=message.photo[-1].file_id, media_type="photo")
    else:
        data = await state.get_data()
        if data.get("category") == "car":
            await message.answer(translated(message.from_user.id, "car_photo_required"))
            return
        await state.update_data(media=message.video.file_id, media_type="video")
    await state.set_state(AdForm.title)
    await message.answer(translated(message.from_user.id, "send_title"), parse_mode="Markdown")

@router.message(AdForm.title, F.text)
async def ad_title(message: Message, state: FSMContext):
    await state.update_data(title=message.text)
    await state.set_state(AdForm.description)
    await message.answer(translated(message.from_user.id, "send_desc"), parse_mode="Markdown")

@router.message(AdForm.description, F.text)
async def ad_desc(message: Message, state: FSMContext):
    await state.update_data(description=message.text)
    await state.set_state(AdForm.price)
    await message.answer(translated(message.from_user.id, "send_price"), parse_mode="Markdown")

@router.message(AdForm.price, F.text)
async def ad_price(message: Message, state: FSMContext):
    data = await state.get_data()
    price = message.text.strip().replace(" ", "").replace(",", "")
    if data.get("category") == "car" and (not price.isdigit() or not 1 <= int(price) <= 1000000000000):
        await message.answer(translated(message.from_user.id, "price_invalid"))
        return
    await state.update_data(price=price)
    await state.set_state(AdForm.game_id)
    await message.answer(translated(message.from_user.id, "game_id_prompt"), parse_mode="Markdown")

@router.message(AdForm.game_id, F.text)
async def ad_game_id(message: Message, state: FSMContext):
    game_id = message.text.strip()
    if not game_id.isascii() or not game_id.replace("-", "").replace("_", "").isalnum() or not 3 <= len(game_id) <= 40:
        await message.answer(translated(message.from_user.id, "game_id_invalid"), parse_mode="Markdown")
        return
    await state.update_data(game_id=game_id)
    await state.set_state(AdForm.contact)
    await message.answer(translated(message.from_user.id, "send_contact"), parse_mode="Markdown")

@router.message(AdForm.contact, F.text)
async def ad_contact(message: Message, state: FSMContext):
    await state.update_data(contact=message.text)
    data = await state.get_data()
    if data.get("category") == "car":
        await state.set_state(AdForm.country)
        await message.answer(translated(message.from_user.id, "country_prompt"))
        return
    await finish_legacy_ad(message, state, data)

async def finish_legacy_ad(message: Message, state: FSMContext, data):
    ad_id = add_ad_to_db(
        message.from_user.id, f"@{message.from_user.username}" if message.from_user.username else message.from_user.first_name, data['category'], data['ad_type'],
        data['title'], data['description'], data['price'], data['game_id'], data['contact'], data['media'], data.get('media_type', 'photo'),
    )
    author_name = f"@{message.from_user.username}" if message.from_user.username else message.from_user.first_name
    mod_text = (
        f"🚨 **НОВОЕ ОБЪЯВЛЕНИЕ #{ad_id}** 🚨\n━━━━━━━━━━━━━━━━━━━━━━\n"
        f"👤 **Автор:** {author_name}\n"
        f"📦 **Тип:** {data['ad_type']}\n"
        f"📝 **Заголовок:** {data['title']}\n"
        f"💰 **Цена:** {data['price']}\n"
        f"🆔 **Игровой ID:** `{data['game_id']}`"
    )
    from keyboards import admin_approve_kb
    for admin_id in ADMIN_IDS:
        try:
            if data.get('media_type') == "photo":
                await message.bot.send_photo(admin_id, photo=data['media'], caption=mod_text, reply_markup=admin_approve_kb(ad_id), parse_mode="Markdown")
            else:
                await message.bot.send_video(admin_id, video=data['media'], caption=mod_text, reply_markup=admin_approve_kb(ad_id), parse_mode="Markdown")
        except Exception:
            pass
    await state.clear()
    lang = user_lang(message.from_user.id)
    await message.answer(get_text("ad_submitted", lang, id=ad_id), reply_markup=main_menu(False, lang), parse_mode="Markdown")

@router.message(AdForm.country, F.text)
async def ad_country(message: Message, state: FSMContext):
    country = message.text.strip()
    if not 2 <= len(country) <= 80:
        await message.answer(translated(message.from_user.id, "country_invalid"))
        return
    await state.update_data(country=country)
    await state.set_state(AdForm.country_code)
    await message.answer(translated(message.from_user.id, "country_code_prompt"))

@router.message(AdForm.country_code, F.text)
async def ad_country_code(message: Message, state: FSMContext):
    country_code = message.text.strip().upper()
    if not re.fullmatch(r"[A-Z]{2}", country_code):
        await message.answer(translated(message.from_user.id, "country_code_invalid"))
        return
    await state.update_data(country_code=country_code)
    await state.set_state(AdForm.city)
    await message.answer(translated(message.from_user.id, "city_prompt"))

@router.message(AdForm.city, F.text)
async def ad_city(message: Message, state: FSMContext):
    city = message.text.strip()
    if not 1 <= len(city) <= 80:
        await message.answer(translated(message.from_user.id, "city_invalid"))
        return
    data = await state.get_data()
    try:
        file = await message.bot.get_file(data["media"])
        from io import BytesIO
        photo = BytesIO()
        await message.bot.download_file(file.file_path, destination=photo)
        trade_mode = data["ad_type"] == "car_trade"
        uid, submission_id = await asyncio.to_thread(
            create_garage_submission, message.from_user.id, data["title"], data["description"],
            int(data["price"]), data["game_id"], data["contact"], photo.getvalue(),
            data["country"], data["country_code"], city, "trade" if trade_mode else "sell",
            data["description"] if trade_mode else "", message.from_user.full_name,
        )
    except (ValueError, KeyError):
        await message.answer(translated(message.from_user.id, "price_invalid"))
        return
    except Exception as error:
        print(f"Firebase garage submission error: {error}")
        await message.answer(translated(message.from_user.id, "site_submit_failed"))
        return
    for admin_id in ADMIN_IDS:
        try:
            await message.bot.send_message(admin_id,
                f"Новая заявка CPM2 из Telegram\n{data['title']} · {'TRADE' if trade_mode else 'SELL'}\n"
                f"ID игрока: {data['game_id']}\nUID сайта: {uid}\nЗаявка: {submission_id}\n"
                "Открой CPM2 → комиссионный гараж на сайте для модерации.")
        except Exception:
            pass
    await state.clear()
    lang = user_lang(message.from_user.id)
    await message.answer(get_text("site_submission_ok", lang), reply_markup=main_menu(False, lang))

# ================== ГОНКИ ==================
@router.callback_query(F.data == "join_race")
async def start_race(call: CallbackQuery, state: FSMContext):
    kb = InlineKeyboardBuilder()
    lang = user_lang(call.from_user.id)
    kb.button(text=get_text("race_drag", lang), callback_data="race_drag")
    kb.button(text=get_text("race_drift", lang), callback_data="race_drift")
    kb.button(text=get_text("btn_back", lang), callback_data="back_main")
    kb.adjust(1, 1, 1)
    await state.set_state(RaceForm.race_type)
    lang = user_lang(call.from_user.id)
    await call.message.edit_text(get_text("race_type", lang), reply_markup=kb.as_markup(), parse_mode="Markdown")
    await call.answer()

@router.callback_query(RaceForm.race_type, F.data.startswith("race_"))
async def race_type(call: CallbackQuery, state: FSMContext):
    lang = user_lang(call.from_user.id)
    r_type = get_text("race_drag" if call.data == "race_drag" else "race_drift", lang)
    await state.update_data(race_type=r_type)
    await state.set_state(RaceForm.game_id)
    await call.message.edit_text(f"🏎️ **{r_type}**\n\n{get_text('race_id', lang)}", parse_mode="Markdown")
    await call.answer()

@router.message(RaceForm.game_id, F.text)
async def race_id(message: Message, state: FSMContext):
    game_id = message.text.strip()
    if not game_id.isascii() or not game_id.replace("-", "").replace("_", "").isalnum() or not 3 <= len(game_id) <= 40:
        await message.answer(translated(message.from_user.id, "game_id_invalid"), parse_mode="Markdown")
        return
    await state.update_data(game_id=game_id)
    await state.set_state(RaceForm.car)
    await message.answer(translated(message.from_user.id, "race_car"), parse_mode="Markdown")

@router.message(RaceForm.car, F.text)
async def race_car(message: Message, state: FSMContext):
    data = await state.get_data()
    username = f"@{message.from_user.username}" if message.from_user.username else message.from_user.first_name
    admin_text = (
        f"🚨 **ЗАЯВКА НА ГОНКУ!** 🚨\n━━━━━━━━━━━━━━━━━━━━━━\n"
        f"👤 **ТГ:** {username}\n"
        f"🏁 **Тип:** {data['race_type']}\n"
        f"🆔 **ID:** `{data['game_id']}`\n"
        f"🚗 **Машина:** {message.text}"
    )
    for admin_id in ADMIN_IDS:
        try:
            await message.bot.send_message(admin_id, admin_text, parse_mode="Markdown")
        except Exception:
            pass
    await state.clear()
    lang = user_lang(message.from_user.id)
    await message.answer(get_text("race_accepted", lang), reply_markup=main_menu(False, lang), parse_mode="Markdown")

# ================== КАТАЛОГ ==================
@router.callback_query(F.data.in_({"buy_car_catalog", "buy_acc_catalog"}))
async def show_catalog(call: CallbackQuery):
    cat = "car" if call.data == "buy_car_catalog" else "acc"
    ads = get_approved_ads(cat, "car_sell" if cat == "car" else "acc_sell")
    if not ads:
        lang = user_lang(call.from_user.id)
        await call.message.edit_text(get_text("catalog_empty", lang), reply_markup=main_menu(False, lang), parse_mode="Markdown")
        await call.answer()
        return
    for ad in ads[:5]:
        lang = user_lang(call.from_user.id)
        text = (
            f"🚗 **{ad[5]}**\n\n{ad[6]}\n\n"
            f"💰 **{get_text('catalog_price', lang)}:** {ad[7]}\n"
            f"🆔 **{get_text('catalog_game_id', lang)}:** `{ad[8]}`\n"
            f"📞 **{get_text('catalog_contact', lang)}:** {ad[9]}"
        )
        kb = InlineKeyboardBuilder()
        contact = ad[9].replace('@', '') if ad[9] else ""
        if contact:
            kb.button(text=get_text("btn_contact_seller", lang), url=f"https://t.me/{contact}")
        kb.button(text=get_text("btn_back", lang), callback_data="back_main")
        kb.adjust(1, 1)
        try:
            if len(ad) > 11 and ad[11] == "video":
                await call.message.answer_video(video=ad[10], caption=text, reply_markup=kb.as_markup(), parse_mode="Markdown")
            else:
                await call.message.answer_photo(photo=ad[10], caption=text, reply_markup=kb.as_markup(), parse_mode="Markdown")
        except Exception:
            await call.message.answer(text, reply_markup=kb.as_markup(), parse_mode="Markdown")
    await call.answer()
