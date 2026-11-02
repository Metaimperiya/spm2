from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder

from states import AdForm, RaceForm
from keyboards import (
    main_menu,
    bottom_menu,
    cars_menu,
    accs_menu,
    money_menu,
    community_menu,
    admin_approve_kb,
)
from database import add_ad_to_db, get_approved_ads, add_user_to_db
from firebase_bridge import (
    consume_link_code,
    create_garage_submission,
    get_linked_uid,
    initialize,
    unlink_telegram_account,
)

import asyncio
import re

router = Router()

# Здесь проверяем администраторов локально.
# Не импортируй bot.py из обработчика: это повторно подключает роутеры.
ADMIN_IDS = [806159173, 5493746865]


def is_admin(user_or_id):
    user_id = getattr(user_or_id, "id", user_or_id)
    return user_id in ADMIN_IDS


def is_admin_check(user):
    return is_admin(user)


@router.message(F.text.regexp(r"^/link(?:@\w+)?\s+([A-Za-z0-9_-]{6,32})$"))
async def link_website_account(message: Message):
    code = message.text.split(maxsplit=1)[1].strip()

    try:
        if not await asyncio.to_thread(initialize):
            await message.answer(
                "Связь с сайтом пока не настроена. Администратору нужно "
                "добавить Firebase service account в переменные окружения бота."
            )
            return

        uid = await asyncio.to_thread(
            consume_link_code,
            code,
            message.from_user.id,
            message.from_user.username,
            message.from_user.first_name,
        )

        if not uid:
            await message.answer(
                "Код не найден или срок его действия истёк. "
                "Создай новый код в разделе CPM2 на сайте."
            )
            return

        await message.answer(
            "✅ Аккаунт сайта привязан. Теперь заявки на CPM2-машины "
            "из бота попадут в общую очередь модерации сайта."
        )

    except Exception as error:
        print(f"Firebase link error: {error}")
        await message.answer(
            "Не удалось привязать аккаунт. Проверь код и попробуй ещё раз."
        )


@router.message(F.text == "/link")
async def link_help(message: Message):
    await message.answer(
        "Открой CPM2 на сайте, создай код привязки и отправь его так: /link КОД"
    )


@router.message(F.text == "/unlink")
async def unlink_website_account(message: Message):
    try:
        removed = await asyncio.to_thread(
            unlink_telegram_account,
            message.from_user.id,
        )

        if removed:
            await message.answer("Привязка Telegram к сайту удалена.")
        else:
            await message.answer(
                "Этот Telegram пока не привязан к аккаунту сайта."
            )

    except Exception as error:
        print(f"Firebase unlink error: {error}")
        await message.answer(
            "Не получилось удалить привязку. Попробуй ещё раз позже."
        )


@router.message(F.text == "/start")
async def start(message: Message, state: FSMContext):
    await state.clear()

    username = (
        f"@{message.from_user.username}"
        if message.from_user.username
        else "скрыт"
    )

    add_user_to_db(
        message.from_user.id,
        username,
        message.from_user.first_name,
    )

    admin_status = is_admin_check(message.from_user)

    text = (
        f"🏁 **METAIMPERIYA | CPM 2 HUB** 🏁\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"Здарова, **{message.from_user.first_name}**!\n\n"
        f"👇 *Жми кнопку внизу:*"
    )

    await message.answer(
        text,
        reply_markup=bottom_menu(),
        parse_mode="Markdown",
    )
    await message.answer(
        "🚀 **Главное меню:**",
        reply_markup=main_menu(admin_status),
        parse_mode="Markdown",
    )


@router.message(F.text == "🏠 В главное меню")
async def bottom_back(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "🚀 **Главное меню:**",
        reply_markup=main_menu(is_admin_check(message.from_user)),
        parse_mode="Markdown",
    )


@router.callback_query(F.data == "back_main")
async def back_main(call: CallbackQuery, state: FSMContext):
    await state.clear()
    await call.message.edit_text(
        "🚀 **Главное меню:**",
        reply_markup=main_menu(is_admin_check(call.from_user)),
        parse_mode="Markdown",
    )
    await call.answer()


@router.callback_query(F.data == "menu_cars")
async def show_cars(call: CallbackQuery):
    await call.message.edit_text(
        "🚗 **Автомобили**",
        reply_markup=cars_menu(),
    )
    await call.answer()


@router.callback_query(F.data == "menu_accs")
async def show_accs(call: CallbackQuery):
    await call.message.edit_text(
        "👤 **Аккаунты**",
        reply_markup=accs_menu(),
    )
    await call.answer()


@router.callback_query(F.data == "menu_money")
async def show_money(call: CallbackQuery):
    await call.message.edit_text(
        "💵 **Монеты и Услуги**",
        reply_markup=money_menu(),
    )
    await call.answer()


@router.callback_query(F.data == "menu_community")
async def show_community(call: CallbackQuery):
    await call.message.edit_text(
        "💬 **Наши каналы и группы:**",
        reply_markup=community_menu(),
    )
    await call.answer()


@router.message(F.text == "📢 Подать объявление")
async def bottom_create_ad(message: Message, state: FSMContext):
    await state.clear()
    admin_status = is_admin_check(message.from_user)

    kb = InlineKeyboardBuilder()

    if admin_status:
        kb.button(
            text="🚗 Продать машину (Админ)",
            callback_data="admin_post_car",
        )
        kb.button(
            text="🔄 Обменять машину (Админ)",
            callback_data="admin_post_trade",
        )
        kb.button(
            text="👤 Продать аккаунт (Админ)",
            callback_data="admin_post_acc",
        )
        kb.button(
            text="📝 ПРОСТО ОБЪЯВЛЕНИЕ (С кнопками)",
            callback_data="admin_post_simple",
        )
        kb.button(text="⬅️ Назад", callback_data="back_main")
        kb.adjust(1, 1, 1, 1, 1)

        await message.answer(
            "👑 **Админ-меню подачи:**",
            reply_markup=kb.as_markup(),
        )
    else:
        kb.button(text="🚗 Продать машину", callback_data="car_sell")
        kb.button(text="🔄 Обменять машину", callback_data="car_trade")
        kb.button(text="👤 Продать аккаунт", callback_data="acc_sell")
        kb.button(text="⬅️ Назад", callback_data="back_main")
        kb.adjust(1, 1, 1, 1)

        await message.answer(
            "📢 **Что выставляем?**",
            reply_markup=kb.as_markup(),
        )


@router.callback_query(F.data.in_({"car_sell", "car_trade", "acc_sell"}))
async def process_ad_type(call: CallbackQuery, state: FSMContext):
    category = "acc" if call.data == "acc_sell" else "car"

    if category == "car":
        try:
            linked = await asyncio.to_thread(
                get_linked_uid,
                call.from_user.id,
            )
        except Exception:
            linked = None

        if not linked:
            await call.answer(
                "Сначала привяжи аккаунт сайта: CPM2 → Telegram → код → /link КОД",
                show_alert=True,
            )
            return

    await state.update_data(category=category, ad_type=call.data)
    await state.set_state(AdForm.media)
    await call.message.edit_text("📸 **Отправь фото или видео:**")
    await call.answer()


@router.message(AdForm.media, F.photo | F.video)
async def ad_media(message: Message, state: FSMContext):
    if message.photo:
        await state.update_data(
            media=message.photo[-1].file_id,
            media_type="photo",
        )
    else:
        data = await state.get_data()

        if data.get("category") == "car":
            await message.answer(
                "Для объявления в CPM2 на сайте нужно фото автомобиля. "
                "Пришли фотографию, не видео."
            )
            return

        await state.update_data(
            media=message.video.file_id,
            media_type="video",
        )

    await state.set_state(AdForm.title)
    await message.answer("📝 **Напиши заголовок:**")


@router.message(AdForm.title, F.text)
async def ad_title(message: Message, state: FSMContext):
    await state.update_data(title=message.text)
    await state.set_state(AdForm.description)
    await message.answer("📝 **Напиши описание:**")


@router.message(AdForm.description, F.text)
async def ad_desc(message: Message, state: FSMContext):
    await state.update_data(description=message.text)
    await state.set_state(AdForm.price)
    await message.answer("💰 **Укажи цену:**")


@router.message(AdForm.price, F.text)
async def ad_price(message: Message, state: FSMContext):
    data = await state.get_data()
    price = message.text.strip().replace(" ", "").replace(",", "")

    if data.get("category") == "car":
        if not price.isdigit() or not 1 <= int(price) <= 1_000_000_000_000:
            await message.answer(
                "Укажи целую цену CPM2 от 1 до 1 000 000 000 000."
            )
            return

    await state.update_data(price=price)
    await state.set_state(AdForm.game_id)
    await message.answer(
        "🆔 **Введи игровой ID, например PX847653:**"
    )


@router.message(AdForm.game_id, F.text)
async def ad_game_id(message: Message, state: FSMContext):
    game_id = message.text.strip()

    if (
        not game_id.isascii()
        or not game_id.replace("-", "").replace("_", "").isalnum()
        or not 3 <= len(game_id) <= 40
    ):
        await message.answer(
            "⚠️ **Проверь ID:** введи от 3 до 40 латинских букв, "
            "цифр, дефисов или подчёркиваний."
        )
        return

    await state.update_data(game_id=game_id)
    await state.set_state(AdForm.contact)
    await message.answer("📞 **Контакт для связи (@username):**")


@router.message(AdForm.contact, F.text)
async def ad_contact(message: Message, state: FSMContext):
    await state.update_data(contact=message.text)
    data = await state.get_data()

    if data.get("category") == "car":
        await state.set_state(AdForm.country)
        await message.answer("🌍 Напиши страну, например Украина:")
        return

    await finish_legacy_ad(message, state, data)


async def finish_legacy_ad(message: Message, state: FSMContext, data):
    ad_id = add_ad_to_db(
        message.from_user.id,
        (
            f"@{message.from_user.username}"
            if message.from_user.username
            else message.from_user.first_name
        ),
        data["category"],
        data["ad_type"],
        data["title"],
        data["description"],
        data["price"],
        data["game_id"],
        data["contact"],
        data["media"],
        data.get("media_type", "photo"),
    )

    author_name = (
        f"@{message.from_user.username}"
        if message.from_user.username
        else message.from_user.first_name
    )

    mod_text = (
        f"🚨 **НОВОЕ ОБЪЯВЛЕНИЕ #{ad_id}** 🚨\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"👤 **Автор:** {author_name}\n"
        f"📦 **Тип:** {data['ad_type']}\n"
        f"📝 **Заголовок:** {data['title']}\n"
        f"💰 **Цена:** {data['price']}\n"
        f"🆔 **Игровой ID:** `{data['game_id']}`"
    )

    for admin_id in ADMIN_IDS:
        try:
            if data.get("media_type") == "photo":
                await message.bot.send_photo(
                    admin_id,
                    photo=data["media"],
                    caption=mod_text,
                    reply_markup=admin_approve_kb(ad_id),
                    parse_mode="Markdown",
                )
            else:
                await message.bot.send_video(
                    admin_id,
                    video=data["media"],
                    caption=mod_text,
                    reply_markup=admin_approve_kb(ad_id),
                    parse_mode="Markdown",
                )
        except Exception:
            pass

    await state.clear()
    await message.answer(
        f"✅ **Объявление #{ad_id} отправлено на модерацию!**",
        reply_markup=main_menu(False),
    )


@router.message(AdForm.country, F.text)
async def ad_country(message: Message, state: FSMContext):
    country = message.text.strip()

    if not 2 <= len(country) <= 80:
        await message.answer("Напиши название страны (2–80 символов).")
        return

    await state.update_data(country=country)
    await state.set_state(AdForm.country_code)
    await message.answer(
        "Введи двухбуквенный код страны ISO, например UA, PL или DE:"
    )


@router.message(AdForm.country_code, F.text)
async def ad_country_code(message: Message, state: FSMContext):
    country_code = message.text.strip().upper()

    if not re.fullmatch(r"[A-Z]{2}", country_code):
        await message.answer(
            "Нужен код из двух латинских букв, например UA."
        )
        return

    await state.update_data(country_code=country_code)
    await state.set_state(AdForm.city)
    await message.answer("🏙 Напиши город:")


@router.message(AdForm.city, F.text)
async def ad_city(message: Message, state: FSMContext):
    city = message.text.strip()

    if not 1 <= len(city) <= 80:
        await message.answer(
            "Название города должно быть от 1 до 80 символов."
        )
        return

    data = await state.get_data()

    try:
        file = await message.bot.get_file(data["media"])
        from io import BytesIO

        photo = BytesIO()
        await message.bot.download_file(
            file.file_path,
            destination=photo,
        )

        trade_mode = data["ad_type"] == "car_trade"

        uid, submission_id = await asyncio.to_thread(
            create_garage_submission,
            message.from_user.id,
            data["title"],
            data["description"],
            int(data["price"]),
            data["game_id"],
            data["contact"],
            photo.getvalue(),
            data["country"],
            data["country_code"],
            city,
            "trade" if trade_mode else "sell",
            data["description"] if trade_mode else "",
            message.from_user.full_name,
        )

    except (ValueError, KeyError):
        await message.answer(
            "Проверь цену: укажи целое положительное число CPM2."
        )
        return

    except Exception as error:
        print(f"Firebase garage submission error: {error}")
        await message.answer(
            "Не удалось отправить заявку в сайт. "
            "Проверь привязку аккаунта и попробуй позже."
        )
        return

    for admin_id in ADMIN_IDS:
        try:
            await message.bot.send_message(
                admin_id,
                f"Новая заявка CPM2 из Telegram\n"
                f"{data['title']} · "
                f"{'TRADE' if trade_mode else 'SELL'}\n"
                f"ID игрока: {data['game_id']}\n"
                f"UID сайта: {uid}\n"
                f"Заявка: {submission_id}\n"
                "Открой CPM2 → комиссионный гараж на сайте для модерации.",
            )
        except Exception:
            pass

    await state.clear()
    await message.answer(
        "✅ Заявка добавлена в общую очередь CPM2 на сайте. "
        "После одобрения она появится в Sell/Trade и будет опубликована "
        "в соответствующем Telegram-канале.",
        reply_markup=main_menu(False),
    )


# ================== ГОНКИ ==================

@router.callback_query(F.data == "join_race")
async def start_race(call: CallbackQuery, state: FSMContext):
    kb = InlineKeyboardBuilder()
    kb.button(text="🏎️ Дрэг", callback_data="race_drag")
    kb.button(text="🌪️ Дрифт", callback_data="race_drift")
    kb.button(text="⬅️ Назад", callback_data="back_main")
    kb.adjust(1, 1, 1)

    await state.set_state(RaceForm.race_type)
    await call.message.edit_text(
        "🏁 **Выбери тип гонки:**",
        reply_markup=kb.as_markup(),
    )
    await call.answer()


@router.callback_query(RaceForm.race_type, F.data.startswith("race_"))
async def race_type(call: CallbackQuery, state: FSMContext):
    race_name = "Дрэг" if call.data == "race_drag" else "Дрифт"

    await state.update_data(race_type=race_name)
    await state.set_state(RaceForm.game_id)
    await call.message.edit_text(
        f"🏎️ **{race_name}**\n\n🆔 **Введи свой игровой ID:**"
    )
    await call.answer()


@router.message(RaceForm.game_id, F.text)
async def race_id(message: Message, state: FSMContext):
    game_id = message.text.strip()

    if (
        not game_id.isascii()
        or not game_id.replace("-", "").replace("_", "").isalnum()
        or not 3 <= len(game_id) <= 40
    ):
        await message.answer(
            "⚠️ **Проверь ID:** введи от 3 до 40 латинских букв, "
            "цифр, дефисов или подчёркиваний."
        )
        return

    await state.update_data(game_id=game_id)
    await state.set_state(RaceForm.car)
    await message.answer("🚗 **На какой машине едешь?**")


@router.message(RaceForm.car, F.text)
async def race_car(message: Message, state: FSMContext):
    data = await state.get_data()

    username = (
        f"@{message.from_user.username}"
        if message.from_user.username
        else message.from_user.first_name
    )

    admin_text = (
        f"🚨 **ЗАЯВКА НА ГОНКУ!** 🚨\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"👤 **ТГ:** {username}\n"
        f"🏁 **Тип:** {data['race_type']}\n"
        f"🆔 **ID:** `{data['game_id']}`\n"
        f"🚗 **Машина:** {message.text}"
    )

    for admin_id in ADMIN_IDS:
        try:
            await message.bot.send_message(
                admin_id,
                admin_text,
                parse_mode="Markdown",
            )
        except Exception:
            pass

    await state.clear()
    await message.answer(
        "✅ **Заявка принята!** Ожидай.",
        reply_markup=main_menu(False),
    )


# ================== КАТАЛОГ ==================

@router.callback_query(F.data.in_({"buy_car_catalog", "buy_acc_catalog"}))
async def show_catalog(call: CallbackQuery):
    category = "car" if call.data == "buy_car_catalog" else "acc"
    ad_type = "car_sell" if category == "car" else "acc_sell"

    ads = get_approved_ads(category, ad_type)

    if not ads:
        await call.message.edit_text(
            "🛒 **Каталог пуст.**",
            reply_markup=main_menu(False),
        )
        await call.answer()
        return

    for ad in ads[:5]:
        text = (
            f"🚗 **{ad[5]}**\n\n"
            f"{ad[6]}\n\n"
            f"💰 **Цена:** {ad[7]}\n"
            f"🆔 **Игровой ID:** `{ad[8]}`\n"
            f"📞 **Контакт:** {ad[9]}"
        )

        kb = InlineKeyboardBuilder()
        contact = ad[9].replace("@", "") if ad[9] else ""

        if contact:
            kb.button(
                text="💬 Написать продавцу",
                url=f"https://t.me/{contact}",
            )

        kb.button(text="⬅️ Назад", callback_data="back_main")
        kb.adjust(1, 1)

        try:
            if len(ad) > 11 and ad[11] == "video":
                await call.message.answer_video(
                    video=ad[10],
                    caption=text,
                    reply_markup=kb.as_markup(),
                    parse_mode="Markdown",
                )
            else:
                await call.message.answer_photo(
                    photo=ad[10],
                    caption=text,
                    reply_markup=kb.as_markup(),
                    parse_mode="Markdown",
                )
        except Exception:
            await call.message.answer(
                text,
                reply_markup=kb.as_markup(),
                parse_mode="Markdown",
            )

    await call.answer()
