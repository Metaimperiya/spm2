from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder
import asyncio

from states import AdminAdForm, AdminBroadcast, AdminButtonsOnly
from keyboards import main_menu, admin_panel_kb, custom_post_kb, AUTO_BUTTONS
from database import approve_ad, get_ad_by_id, get_user_language
from locales import get_text, SUPPORTED_LANGUAGES
from firebase_bridge import get_newsletter_subscribers
from bot_config import (
    ADMIN_IDS,
    MAIN_CLAN_CHANNEL,
    SALE_CHANNEL,
    TRADE_CHANNEL,
    SELL_ACC_CHANNEL,
    PODSLUSHKA_CHANNEL,
    is_admin,
)

router = Router()

def is_admin_check(user):
    return is_admin(user)

def admin_lang(user_id):
    lang = get_user_language(user_id)
    return lang if lang in SUPPORTED_LANGUAGES else "ru"

def admin_text(user_id, key, **kwargs):
    return get_text(key, admin_lang(user_id), **kwargs)

def ad_caption(ad, lang):
    return get_text(
        "new_ad", lang, title=ad[5] or "", description=ad[6] or "",
        price=ad[7] or "—", id=ad[8] or "—", seller=ad[2] or "—",
        contact=ad[9] or "—",
    )

def ad_post_keyboard(lang):
    kb = InlineKeyboardBuilder()
    kb.button(text=get_text("site", lang), url="https://www.metaimperiya.com/")
    kb.button(text=get_text("contact_admin", lang), url="https://t.me/metaimperiya")
    kb.adjust(1, 1)
    return kb.as_markup()

# --- ОДОБРЕНИЕ / ОТКЛОНЕНИЕ ---
@router.callback_query(F.data.startswith("approve_"))
async def approve_ad_callback(call: CallbackQuery, bot: Bot):
    if call.from_user.id not in ADMIN_IDS:
        return

    ad_id = int(call.data.split("_")[1])
    approve_ad(ad_id)
    ad = get_ad_by_id(ad_id)
    if not ad:
        return

    listing_lang = get_user_language(ad[1])
    post_text = ad_caption(ad, listing_lang)
    kb = ad_post_keyboard(listing_lang)

    channels = [MAIN_CLAN_CHANNEL, PODSLUSHKA_CHANNEL]
    if ad[4] == "car_trade":
        channels.append(TRADE_CHANNEL)
    elif ad[3] == "acc":
        channels.append(SELL_ACC_CHANNEL)
    else:
        channels.append(SALE_CHANNEL)

    for chat in set(channels):
        try:
            if len(ad) > 11 and ad[11] == "video":
                await bot.send_video(chat, video=ad[10], caption=post_text,
                                     reply_markup=kb, parse_mode="Markdown")
            else:
                await bot.send_photo(chat, photo=ad[10], caption=post_text,
                                     reply_markup=kb, parse_mode="Markdown")
        except Exception as e:
            print(f"Ошибка approve в {chat}: {e}")

    # User-submitted listings go to the configured Telegram groups only.
    # Newsletter delivery remains available for explicit admin broadcasts.
    await call.message.edit_caption(caption=admin_text(call.from_user.id, "approved"))
    await call.answer(admin_text(call.from_user.id, "approved"))

@router.callback_query(F.data.startswith("reject_"))
async def reject_ad_callback(call: CallbackQuery):
    if call.from_user.id not in ADMIN_IDS:
        return
    ad_id = int(call.data.split("_")[1])
    await call.message.edit_caption(caption=admin_text(call.from_user.id, "rejected_caption", id=ad_id))
    await call.answer(admin_text(call.from_user.id, "rejected"))

# --- АДМИН-ПАНЕЛЬ ---
@router.callback_query(F.data == "admin_panel")
async def admin_panel(call: CallbackQuery):
    if not is_admin_check(call.from_user):
        await call.answer(admin_text(call.from_user.id, "no_rights"), show_alert=True)
        return
    lang = admin_lang(call.from_user.id)
    await call.message.edit_text(admin_text(call.from_user.id, "panel"), reply_markup=admin_panel_kb(lang))
    await call.answer()

# --- РАССЫЛКА ---
@router.callback_query(F.data == "admin_broadcast")
async def admin_broadcast_start(call: CallbackQuery, state: FSMContext):
    if not is_admin_check(call.from_user):
        return
    await state.set_state(AdminBroadcast.message)
    await call.message.edit_text(
        admin_text(call.from_user.id, "broadcast_prompt", count=len(await asyncio.to_thread(get_newsletter_subscribers))),
        parse_mode="Markdown",
    )
    await call.answer()

@router.message(AdminBroadcast.message, F.text == "/cancel")
async def admin_broadcast_cancel(message: Message, state: FSMContext):
    await state.clear()
    lang = admin_lang(message.from_user.id)
    await message.answer(admin_text(message.from_user.id, "cancelled"), reply_markup=main_menu(True, lang))

@router.message(AdminBroadcast.message)
async def admin_broadcast_send(message: Message, state: FSMContext):
    users = await asyncio.to_thread(get_newsletter_subscribers)
    await state.clear()
    if not users:
        lang = admin_lang(message.from_user.id)
        await message.answer(
            admin_text(message.from_user.id, "no_subscribers"),
            reply_markup=main_menu(True, lang),
        )
        return
    await message.answer(admin_text(message.from_user.id, "broadcast_start", count=len(users)))
    success, fail = 0, 0
    for user_id in users:
        try:
            await message.send_copy(chat_id=user_id)
            success += 1
        except Exception:
            fail += 1
    lang = admin_lang(message.from_user.id)
    await message.answer(admin_text(message.from_user.id, "broadcast_done", success=success, fail=fail),
                         reply_markup=main_menu(True, lang))

# --- СОЗДАНИЕ ПОСТА ---
@router.callback_query(F.data == "admin_post_simple")
async def admin_simple_post_start(call: CallbackQuery, state: FSMContext):
    if not is_admin_check(call.from_user):
        return
    await state.set_state(AdminAdForm.media)
    await call.message.edit_text(admin_text(call.from_user.id, "post_media"))
    await call.answer()

@router.message(AdminAdForm.media, F.photo | F.video)
async def admin_simple_media(message: Message, state: FSMContext):
    if message.photo:
        await state.update_data(media=message.photo[-1].file_id, media_type="photo")
    else:
        await state.update_data(media=message.video.file_id, media_type="video")
    await state.set_state(AdminAdForm.text)
    await message.answer(admin_text(message.from_user.id, "post_text"))

@router.message(AdminAdForm.media, F.text == "/skip")
async def admin_simple_skip_media(message: Message, state: FSMContext):
    await state.update_data(media=None, media_type=None)
    await state.set_state(AdminAdForm.text)
    await message.answer(admin_text(message.from_user.id, "post_text"))

@router.message(AdminAdForm.text, F.text)
async def admin_simple_get_text(message: Message, state: FSMContext):
    await state.update_data(text=message.text, buttons=[])
    await state.set_state(AdminAdForm.buttons)

    kb = InlineKeyboardBuilder()
    kb.button(text=admin_text(message.from_user.id, "buttons_auto"), callback_data="auto_buttons")
    kb.adjust(1)

    await message.answer(
        admin_text(message.from_user.id, "buttons_prompt"),
        reply_markup=kb.as_markup(),
        parse_mode="Markdown",
    )

@router.callback_query(F.data == "auto_buttons")
async def admin_auto_buttons(call: CallbackQuery, state: FSMContext):
    buttons = [f"{name} | {url}" for name, url in AUTO_BUTTONS]
    await state.update_data(buttons=buttons)
    await call.message.edit_text(admin_text(call.from_user.id, "buttons_added"), parse_mode="Markdown")
    await call.answer()

@router.message(AdminAdForm.buttons, F.text == "/done")
async def admin_simple_finish(message: Message, state: FSMContext, bot: Bot):
    data = await state.get_data()
    buttons = data.get("buttons", [])
    if not buttons:
        buttons = [
            f"{admin_text(message.from_user.id, 'site')} | https://www.metaimperiya.com/",
            f"{admin_text(message.from_user.id, 'contact_admin')} | https://t.me/metaimperiya",
        ]
    kb = custom_post_kb(buttons)
    channels = [MAIN_CLAN_CHANNEL, SALE_CHANNEL, TRADE_CHANNEL, SELL_ACC_CHANNEL, PODSLUSHKA_CHANNEL]
    success, errors = 0, []
    for chat in channels:
        try:
            if data.get("media_type") == "photo":
                await bot.send_photo(chat, photo=data["media"], caption=data["text"], reply_markup=kb, parse_mode="Markdown")
            elif data.get("media_type") == "video":
                await bot.send_video(chat, video=data["media"], caption=data["text"], reply_markup=kb, parse_mode="Markdown")
            else:
                await bot.send_message(chat, text=data["text"], reply_markup=kb, parse_mode="Markdown")
            success += 1
        except Exception as e:
            print(f"Ошибка post в {chat}: {e}")
            errors.append(f"{chat}: {e}")
    await state.clear()
    text = admin_text(message.from_user.id, "post_sent", count=success)
    if errors:
        text += "\n\n" + admin_text(message.from_user.id, "broadcast_caption", errors="\n".join(errors))
    lang = admin_lang(message.from_user.id)
    await message.answer(text, reply_markup=main_menu(True, lang))

@router.message(AdminAdForm.buttons, F.text)
async def admin_simple_add_button(message: Message, state: FSMContext):
    data = await state.get_data()
    buttons = data.get("buttons", [])
    if "|" not in message.text:
        await message.answer(admin_text(message.from_user.id, "button_format"), parse_mode="Markdown")
        return
    buttons.append(message.text)
    await state.update_data(buttons=buttons)
    await message.answer(admin_text(message.from_user.id, "button_added"))

@router.callback_query(F.data.in_({"admin_post_car", "admin_post_trade", "admin_post_acc"}))
async def admin_sell_start(call: CallbackQuery, state: FSMContext):
    if not is_admin_check(call.from_user):
        return
    await state.set_state(AdminAdForm.media)
    await call.message.edit_text(admin_text(call.from_user.id, "admin_sale"))
    await call.answer()

# --- ТОЛЬКО КНОПКИ ---
@router.callback_query(F.data == "admin_buttons_only")
async def admin_buttons_only_start(call: CallbackQuery, state: FSMContext):
    if not is_admin_check(call.from_user):
        return
    await state.set_state(AdminButtonsOnly.count)
    await call.message.edit_text(
        admin_text(call.from_user.id, "buttons_count"),
    )
    await call.answer()

@router.message(AdminButtonsOnly.count, F.text == "/cancel")
async def admin_buttons_cancel(message: Message, state: FSMContext):
    await state.clear()
    lang = admin_lang(message.from_user.id)
    await message.answer(admin_text(message.from_user.id, "cancelled"), reply_markup=main_menu(True, lang))

@router.message(AdminButtonsOnly.count, F.text)
async def admin_buttons_get_count(message: Message, state: FSMContext):
    if not message.text.isdigit():
        await message.answer(admin_text(message.from_user.id, "digit"))
        return
    count = int(message.text)
    if count < 1 or count > 10:
        await message.answer(admin_text(message.from_user.id, "range"))
        return
    await state.update_data(count=count, current=0, buttons=[])
    await state.set_state(AdminButtonsOnly.buttons)
    await message.answer(admin_text(message.from_user.id, "button_n", number=1), parse_mode="Markdown")

@router.message(AdminButtonsOnly.buttons, F.text)
async def admin_buttons_collect(message: Message, state: FSMContext, bot: Bot):
    data = await state.get_data()
    buttons = data.get("buttons", [])
    current = data.get("current", 0)
    count = data.get("count", 1)

    if "|" not in message.text:
        await message.answer(admin_text(message.from_user.id, "button_format"), parse_mode="Markdown")
        return

    buttons.append(message.text)
    current += 1

    if current < count:
        await state.update_data(buttons=buttons, current=current)
        await message.answer(admin_text(message.from_user.id, "button_n", number=current + 1), parse_mode="Markdown")
        return

    kb = InlineKeyboardBuilder()
    for btn in buttons:
        try:
            name, url = btn.split("|")
            kb.button(text=name.strip(), url=url.strip())
        except Exception:
            pass
    kb.adjust(1)

    channels = [MAIN_CLAN_CHANNEL, SALE_CHANNEL, TRADE_CHANNEL, SELL_ACC_CHANNEL, PODSLUSHKA_CHANNEL]
    success, errors = 0, []
    for chat in channels:
        try:
            await bot.send_message(chat, text=".", reply_markup=kb.as_markup())
            success += 1
        except Exception as e:
            print(f"Ошибка buttons в {chat}: {e}")
            errors.append(f"{chat}: {e}")

    await state.clear()
    text = admin_text(message.from_user.id, "buttons_sent", count=success)
    if errors:
        text += "\n\n" + admin_text(message.from_user.id, "broadcast_caption", errors="\n".join(errors))
    lang = admin_lang(message.from_user.id)
    await message.answer(text, reply_markup=main_menu(True, lang))
