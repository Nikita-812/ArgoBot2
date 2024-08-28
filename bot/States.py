from aiogram.fsm.state import StatesGroup, State


class RegStates(StatesGroup):
    phone_number = State()
    name = State()
    email = State()
    birth_date = State()
    id = State()
    password = State()


class TownsStates(StatesGroup):
    town = State()


class FilesStates(StatesGroup):
    files = State()
