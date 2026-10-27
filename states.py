from aiogram.fsm.state import StatesGroup, State

class AdForm(StatesGroup):
    category = State(); ad_type = State(); photo = State(); title = State()
    description = State(); price = State(); game_id = State(); contact = State()

class RaceForm(StatesGroup):
    race_type = State(); game_nick = State(); game_id = State(); car = State()

class AdminAdForm(StatesGroup):
    photo = State(); description = State()
