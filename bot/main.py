import asyncio
import logging
import sys
from request_maker import request_maker
from gpt.yandexgpt import gpt
from aiogram import Bot, Dispatcher, html
from aiogram import F
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart
from aiogram.types import Message
from os import getenv, environ
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, KeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove
from parse_working_hours import get_working_hours
TOKEN = getenv("BOT_TOKEN")
dp = Dispatcher()

class ButtonText:
    info = 'Справочная информация'
    consalt = "Чат с консультантом"
    times = "Время работы"
    contact = "Контакты"
    delivery = "Доставка"
    delivery_ans = """Бесплатно осуществляется доставка Почтой России и службой доставки СДЭК при выполнении следующих условий:
Бесплатная доставка по г. Москва и г. Новосибирск при сумме заказа от 1 500 рублей.
Бесплатная доставка в пределах Московской и Новосибирской области при сумме заказа от 2 000 рублей.
Бесплатная доставка по территории РФ при сумме заказа от 3 000 рублей"""
    get_contact = """При обращении к оператору интернет-магазина будьте готовы сообщить номер заказа
8-800-700-5643 доб.: 
(1) - оператор интернет-магазина (Москва) пн. - пт. с 9:00 до 17 по Мск.,
(2) - оператор интернет-магазина (Новосибирск) пн. – пт. с 10:00 до 17:00, сб. с 10:00 до 15:00 по Нск.,
(3) - проблемы с оплатами пн. – пт. с 5:00 до 14:00 по Мск.,
(8) - техподдержка и прочие вопросы пн. – пт. с 8:00 до 21:00 по Мск.
+7 (965) 824 56 76  - Московский центр
+7 (965) 820 24 86  - Новосибирский центр"""
def ans_gpt():
    api_key = environ['API_KEY']
    headers = {
        'Authorization': 'Api-Key {}'.format(api_key),
    }
    res = gpt(headers).json()
    res = res['result']
    res = res['alternatives']
    res = res[0]
    return res['message']["text"]

@dp.message(F.text == ButtonText.info)
async def set_info_keyboard(message: Message):
    await message.answer(text = "тест",reply_markup=get_on_cons_info())

@dp.message(F.text == ButtonText.delivery)
async def get_delivary_message(message: Message):
    await message.answer(text = ButtonText.delivery_ans)

@dp.message(F.text == ButtonText.contact)
async def get_on_contact_message(message: Message):
    await message.answer(text = ButtonText.get_contact)


@dp.message(F.text == ButtonText.times)
async def get_on_contact_message(message: Message):#TODO сделать парсер на время работы с сайта, спросить у Марка где лучше брать
    await message.answer(text = get_working_hours())

def get_on_cons_info():
    btn1 = KeyboardButton(text=ButtonText.delivery)
    btn2 = KeyboardButton(text=ButtonText.times)
    btn3 = KeyboardButton(text=ButtonText.contact)
    markup = ReplyKeyboardMarkup(resize_keyboard=True, keyboard=[[btn1], [btn2], [btn3]])
    return markup

def get_on_start_kb():
    btn1 = KeyboardButton(text=ButtonText.info)
    btn2 = KeyboardButton(text=ButtonText.consalt)
    btns_first_row = [btn1]
    btns_second_row = [btn2]
    markup = ReplyKeyboardMarkup(keyboard=[btns_first_row, btns_second_row], resize_keyboard=True)
    return markup


@dp.message(CommandStart())
async def command_start_handler(message: Message) -> None:
    """
    This handler receives messages with `/start` command
    """
    await message.answer(f"Здравствуйте, {html.bold(message.from_user.full_name)}!", reply_markup=get_on_start_kb())


@dp.message()
async def ans_handler(message: Message) -> None:
    """
    Handler will forward receive a message back to the sender

    By default, message handler will handle all message types (like a text, photo, sticker etc.)
    """
    message_text = message.text
    request_maker(message_text)
    try:
        await message.reply(ans_gpt())
    except TypeError:
        # But not all the types is supported to be copied so need to handle it
        await message.answer("Что-то пошло не так")


async def main() -> None:
    logging.basicConfig(level=logging.INFO)
    # Initialize Bot instance with default bot properties which will be passed to all API calls
    bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))

    # And the run events dispatching
    await dp.start_polling(bot)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())