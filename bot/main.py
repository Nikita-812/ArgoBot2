import asyncio
import logging
import sys

import requests
from dateutil import parser
from email_validation import email_validation_filter
from bot.States import RegStates
from utils.is_aproximate_word import is_word_approx_in_string, is_town_approx_in_string
from gpt.request_maker import request_maker
from gpt.yandexgpt import gpt
from aiogram import Bot, Dispatcher, html
from aiogram import F
from aiogram.types import Message, KeyboardButton, ReplyKeyboardMarkup
from aiogram.fsm.context import FSMContext
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart
from os import getenv, environ
from internet_parsers.parse_working_hours import get_working_hours
from internet_parsers.delivery_parse import get_sale_point_from_csv
from requests_to_lk.work_with_api import create_participant_data, post_new_participant
from aiogram.utils import markdown
from internet_parsers.towns import towns

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
    reg = "Зарегистрироваться"


def parse_birthdate(date_str: str) -> str:
    try:
        # Используем dateutil.parser для распознавания даты
        parsed_date = parser.parse(date_str, dayfirst=True)
        return parsed_date.strftime("%Y-%m-%d")
    except (ValueError, TypeError):
        # Возвращаем сообщение об ошибке, если строку невозможно распознать как дату
        return False


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
    btn5 = KeyboardButton(text=ButtonText.reg)
    markup = ReplyKeyboardMarkup(
        keyboard=[
            [btn1, btn2],  # Первая строка с двумя кнопками
            [btn3, btn4],  # Вторая строка с двумя кнопками
            [btn5]  # Третья строка с одной кнопкой
        ],
        resize_keyboard=True  # Клавиатура адаптируется под размер экрана
    )
    return markup


@dp.message(F.text == ButtonText.reg)
async def get_on_reg_message(message: Message, state: FSMContext):
    await state.set_state(RegStates.full_name)
    await message.answer(text="Как вас зовут?")


@dp.message(RegStates.full_name, F.text)
async def get_full_name(message: Message, state: FSMContext):
    await state.update_data(full_name=message.text)
    await message.answer(f"{markdown.hbold(message.text)}, введите ваш адрес электронной почты")
    await state.set_state(RegStates.email)


@dp.message(RegStates.email, email_validation_filter)
async def get_email_address(message: Message, state: FSMContext, email: str):
    # Обновляем данные состояния, сохраняя email
    await state.update_data(email=email)
    await state.set_state(RegStates.phone_number)
    contact_button = KeyboardButton(text="Поделиться номером телефона", request_contact=True)
    contact_keyboard = ReplyKeyboardMarkup(keyboard=[[contact_button]], resize_keyboard=True, one_time_keyboard=True)

    await message.answer("Введите свой номер телефона", reply_markup=contact_keyboard)


@dp.message(RegStates.phone_number)
async def process_contact(message: Message, state: FSMContext):
    if message.contact:
        contact = message.contact
        phone_number = contact.phone_number
        await state.update_data(phone_number=phone_number)
        await message.answer(f"Спасибо! Мы получили ваш номер: {phone_number}. Введите дату рождения.")
        await state.set_state(RegStates.birthday)
    else:
        await message.answer("Пожалуйста, используйте кнопку, чтобы поделиться номером телефона.")


@dp.message(RegStates.birthday)
async def get_birthday(message: Message, state: FSMContext):
    birthday = parse_birthdate(message.text)
    if birthday:
        data = await state.update_data(birthday=birthday)
        try:
            status_code, json_response = post_new_participant(
                create_participant_data(name=data["full_name"], email=data['email'],
                                        mobile_phone=data['phone_number'], birth_date=data['birthday']))
            if status_code != 200:
                print(json_response)
                await message.answer('Что-то пошло не так!', reply_markup=get_on_start_kb())
            else:
                await message.answer('Вы успешно зарегестрированы!', reply_markup=get_on_start_kb())
        except requests.exceptions.ConnectTimeout:
            await message.answer('Что-то пошло не так!', reply_markup=get_on_start_kb())
        finally:
            await state.clear()
    else:
        await message.answer('Неверный формат даты')


@dp.message(RegStates.email)
async def invalid_email_address(message: Message):
    await message.answer("Неверный email")


@dp.message(RegStates.full_name, F.text)
async def get_full_name_invalid_content(message: Message):
    await message.answer("Отправьте ваше имя текстом")


@dp.message(F.text == ButtonText.times)
async def get_on_contact_message(message: Message):
    await message.answer(text=get_working_hours())


@dp.message(F.text == ButtonText.where)
async def get_on_contact_message(message: Message, state: FSMContext):
    await message.answer(text="В каком городе?")
    await state.set_state(RegStates.town)


@dp.message(RegStates.town, F.text)
async def reply_sail_points(message: Message, state: FSMContext):
    city_name = is_town_approx_in_string(message.text.lower().strip())
    if city_name:
        sale_points = get_sale_point_from_csv(city_name)
        await state.clear()
    else:
        await message.answer('Неверное название города')

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
    await dp.start_polling(bot)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())
