from aiogram.fsm.state import StatesGroup, State

class AdForm(StatesGroup):
    category = State()      # Авто / Аккаунт
    ad_type = State()       # Продажа / Обмен
    media = State()         # Фото или видео
    title = State()
    description = State()
    price = State()
    game_id = State()
    contact = State()
    buttons = State()       # Для доп. кнопок (если захочет)
    
class RaceForm(StatesGroup):
    race_type = State()
    game_id = State()
    car = State()

class AdminAdForm(StatesGroup):
    media = State()
    text = State()
    buttons = State()
