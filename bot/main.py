import asyncio
import logging
import sys

from utils.is_aproximate_word import is_word_approx_in_string
from gpt.request_maker import request_maker
from gpt.yandexgpt import gpt
from aiogram import Bot, Dispatcher, html
from aiogram import F
from aiogram.types import Message, KeyboardButton, ReplyKeyboardMarkup

from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart
from os import getenv, environ
from internet_parsers.parse_working_hours import get_working_hours
from internet_parsers.delivery_parse import get_sale_point_from_csv
from internet_parsers.delivery_parse import towns

TOKEN = getenv("BOT_TOKEN")
dp = Dispatcher()


class ButtonText:
    info = 'Справочная информация'
    where = 'Где купить?'
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


@dp.message(F.text == ButtonText.delivery)
async def get_delivary_message(message: Message):
    await message.answer(text=ButtonText.delivery_ans)


@dp.message(F.text == ButtonText.contact)
async def get_on_contact_message(message: Message):
    await message.answer(text=ButtonText.get_contact)


def get_on_cons_info():
    btn1 = KeyboardButton(text=ButtonText.delivery)
    btn2 = KeyboardButton(text=ButtonText.times)
    btn3 = KeyboardButton(text=ButtonText.contact)
    markup = ReplyKeyboardMarkup(resize_keyboard=True, keyboard=[[btn1], [btn2], [btn3]])
    return markup


def get_on_start_kb():
    btn1 = KeyboardButton(text=ButtonText.delivery)
    btn2 = KeyboardButton(text=ButtonText.times)
    btn3 = KeyboardButton(text=ButtonText.contact)
    btn4 = KeyboardButton(text=ButtonText.where)
    markup = ReplyKeyboardMarkup(keyboard=[[btn1], [btn2], [btn3], [btn4]], resize_keyboard=True)
    return markup


@dp.message(F.text == ButtonText.times)
async def get_on_contact_message(message: Message):
    await message.answer(text=get_working_hours())


@dp.message(F.text == ButtonText.where)
async def get_on_contact_message(message: Message):
    await message.answer(text="В каком городе?")


@dp.message(lambda message: message.text in [town for town in towns])
async def reply_sail_points(message: Message):
    city_name = message.text.strip()
    sale_points = get_sale_point_from_csv(city_name)

    # Преобразование списка точек продаж в строку
    if isinstance(sale_points, list):
        result_message = f"Торговые точки в городе {city_name}:\n"
        for point in sale_points:
            result_message += f"Город: {point['City']}\n"
            result_message += f"Адрес: {point['Address']}\n"
            result_message += f"Оплата: {point['Payment Methods']}\n"
            result_message += f"Телефон: {point['Phone']}\n"
            result_message += f"E-Mail: {point['Email']}\n"
            result_message += "\n"
    else:
        result_message = sale_points

    await message.answer(text=result_message)


@dp.message(CommandStart())
async def command_start_handler(message: Message) -> None:
    await message.answer(f"Здравствуйте, {html.bold(message.from_user.full_name)}!", reply_markup=get_on_start_kb())


@dp.message()
async def ans_handler(message: Message) -> None:
    message_text = message.text

    request_maker(message_text)
    try:
        await message.reply(ans_gpt())
    except TypeError:
        await message.answer("Что-то пошло не так")
    is_approx = is_word_approx_in_string(message_text)
    if (is_approx != ''):
        await message.answer(is_approx)


async def main():
    logging.basicConfig(level=logging.INFO)
    bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))

    # And the run events dispatching
    await dp.start_polling(bot)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())
