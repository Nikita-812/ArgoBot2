from aiogram.types import KeyboardButton, ReplyKeyboardMarkup
from ButtonText import ButtonText


def create_start_keyboard():
    buttons = [
        [KeyboardButton(text=ButtonText.delivery), KeyboardButton(text=ButtonText.times)],
        [KeyboardButton(text=ButtonText.contact), KeyboardButton(text=ButtonText.where)],
        [KeyboardButton(text=ButtonText.enter_account)]
    ]
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)


def create_background_info_keyboard():
    buttons = [
        [KeyboardButton(text=ButtonText.delivery), KeyboardButton(text=ButtonText.times)],
        [KeyboardButton(text=ButtonText.contact), KeyboardButton(text=ButtonText.where)],
        [KeyboardButton(text=ButtonText.get_start)]
    ]
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)


def create_familiar_user_keyboard():
    buttons = [
        [KeyboardButton(text=ButtonText.get_bonus_score_of_tree)],
        [KeyboardButton(text=ButtonText.get_bonus_score)],
        [KeyboardButton(text=ButtonText.background_info)],
    ]
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)
