from aiogram.fsm.state import StatesGroup, State

class AdForm(StatesGroup):
    category = State(); ad_type = State(); media = State(); title = State()
    description = State(); price = State(); game_id = State(); contact = State()

class RaceForm(StatesGroup):
    race_type = State(); game_id = State(); car = State()

class AdminAdForm(StatesGroup):
    media = State(); text = State(); buttons = State()

class AdminBroadcast(StatesGroup):
    message = State()

# НОВОЕ СОСТОЯНИЕ ДЛЯ КНОПОК БЕЗ ТЕКСТА
class AdminButtonsOnly(StatesGroup):
    count = State()
    buttons = State()
