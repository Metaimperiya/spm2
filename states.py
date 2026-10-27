from aiogram.fsm.state import StatesGroup, State

class AdForm(StatesGroup):
    category = State()
    ad_type = State()
    title = State()
    description = State()
    price = State()
    game_id = State()
    contact = State()
    photo = State()
    confirm = State()

class RaceForm(StatesGroup):
    game_nick = State()
    game_id = State()
    car_class = State()
    photo = State()
    confirm = State()

class AdminAdForm(StatesGroup):
    category = State()
    ad_type = State()
    title = State()
    description = State()
    price = State()
    photo = State()
    confirm = State()
