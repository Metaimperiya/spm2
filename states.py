from aiogram.fsm.state import State, StatesGroup


class AdForm(StatesGroup):
    category = State()
    ad_type = State()
    media = State()
    title = State()
    description = State()
    price = State()
    game_id = State()
    contact = State()
    country = State()
    country_code = State()
    city = State()


class RaceForm(StatesGroup):
    race_type = State()
    game_id = State()
    car = State()


class AdminAdForm(StatesGroup):
    media = State()
    text = State()
    buttons = State()


class AdminBroadcast(StatesGroup):
    message = State()


class AdminButtonsOnly(StatesGroup):
    count = State()
    buttons = State()
