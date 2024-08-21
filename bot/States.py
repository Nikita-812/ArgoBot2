from aiogram.fsm.state import StatesGroup, State


class RegStates(StatesGroup):
    phone_number = State()
    full_name = State()
    email = State()
    birthday = State()
    town = State()
