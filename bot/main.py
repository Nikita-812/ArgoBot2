import asyncio
import logging
import os
import sys
from os import getenv

from aiogram import Bot, Dispatcher, F, html
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode, ChatAction
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, FSInputFile

from ButtonText import ButtonText
from bot.constructor_kb import create_start_keyboard, create_familiar_user_keyboard, create_background_info_keyboard
from utils.is_aproximate_word import is_town_approx_in_string
from db.db import bd_reg_participant, bd_get_user_by_id, bd_get_user_by_tg_id
from bot.States import RegStates, TownsStates, FilesStates
from internet_parsers.delivery_parse import get_sale_point_from_csv
from internet_parsers.parse_working_hours import get_working_hours_from_file
from requests_to_lk.work_with_api import (
    api_get_user_by_id, api_get_user_score, api_get_user_tree_score
)
from utils.sending_email_messages import generate_password, send_email_password
from utils.validation import id_validation_filter

TOKEN = getenv("BOT_TOKEN")
dp = Dispatcher()
bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))


@dp.message(F.text == ButtonText.where)
async def handle_where_to_buy(message: Message, state: FSMContext):
    await bot.send_chat_action(chat_id=message.chat.id, action=ChatAction.TYPING)
    await message.answer("Пожалуйста, укажите город.")
    await state.set_state(TownsStates.town)


@dp.message(TownsStates.town, F.text)
async def handle_town_selection(message: Message, state: FSMContext):
    city_name = is_town_approx_in_string(message.text.lower().strip())
    if city_name:
        sale_points = get_sale_point_from_csv(city_name)
        await state.clear()
        if isinstance(sale_points, list):
            result_message = f"Торговые точки в городе {city_name}:\n"
            for point in sale_points:
                result_message += (
                    f"Город: {point['City']}\n"
                    f"Адрес: {point['Address']}\n"
                    f"Оплата: {point['Payment Methods']}\n"
                    f"Телефон: {point['Phone']}\n"
                    f"E-Mail: {point['Email']}\n\n"
                )
        else:
            result_message = sale_points
        await message.answer(text=result_message, reply_markup=create_familiar_user_keyboard())
    else:
        await message.answer('Извините, но название города не распознано. Пожалуйста, попробуйте снова.')


@dp.message(TownsStates.town)
async def failure_town_selection(message: Message):
    await message.answer('Пожалуйста, введите название города текстом')


@dp.message(F.text == ButtonText.delivery)
async def handle_delivery_request(message: Message):
    await message.answer(text=ButtonText.delivery_ans)


@dp.message(F.text == ButtonText.contact)
async def handle_contact_request(message: Message):
    await message.answer(text=ButtonText.get_contact)


@dp.message(F.text == ButtonText.times)
async def handle_working_hours_request(message: Message):
    try:
        content = await get_working_hours_from_file()
        await message.answer(text=content)
    except Exception as e:
        await message.answer(f"Произошла ошибка при получении рабочего времени: {str(e)}")


@dp.message(F.text == ButtonText.reg)
async def handle_registration_start(message: Message, state: FSMContext):
    await state.set_state(RegStates.name)
    await message.answer(text="Как вас зовут?")


@dp.message(F.text == ButtonText.enter_account)
async def handle_enter_account(message: Message, state: FSMContext):
    await state.set_state(RegStates.id)
    await message.answer('Пожалуйста, введите ваш ID')


@dp.message(RegStates.id, F.text)
async def handle_user_search(message: Message, state: FSMContext):
    user_id = id_validation_filter(message.text)
    status, user = await api_get_user_by_id(user_id)
    if status:
        password = generate_password()
        send_email_password(user['email'], password)
        await message.answer("Пароль отправлен на вашу почту. Пожалуйста, введите его.")
        await state.update_data(id=user)
        await state.set_state(RegStates.password)
        await state.update_data(password=password)
    else:
        await message.answer('Не удалось подключиться к серверу, попробуйте позже.')


@dp.message(RegStates.id)
async def failure_get_user_id(message: Message):
    await message.answer('Пожалуйста, введите ваш id текстом')


@dp.message(RegStates.password, F.text)
async def handle_password_check(message: Message, state: FSMContext):
    try:
        password = message.text
        user_data = await state.get_data()
        if password == user_data['password']:
            user_data['id']['api_id'] = message.from_user.id
            await bd_reg_participant(user_data['id'])
            await message.answer("Пароль верен. Вы успешно вошли в аккаунт.",
                                 reply_markup=create_familiar_user_keyboard())
            await state.clear()
        else:
            await message.answer("Неверный пароль. Попробуйте еще раз.")
    except Exception as e:
        logging.error(f"Ошибка при проверке пароля: {e}")
        await message.answer('Произошла ошибка. Попробуйте войти позже.')


@dp.message(RegStates.password)
async def failure_password_check(message: Message):
    await message.answer('Введите ваш пароль текстом')


@dp.message(F.text == ButtonText.get_bonus_score)
async def handle_bonus_score_request(message: Message):
    api_id = await bd_get_user_by_tg_id(message.from_user.id)
    status, user_info = await api_get_user_score(api_id)
    if status == 200:
        personal_pv = user_info['personalPv']
        await message.answer(f'Ваш персональный PV: {personal_pv}')
    else:
        await message.answer('Не удалось получить информацию о бонусах. Попробуйте позже.')


def get_latest_file(directory: str) -> str:
    files = [os.path.join(directory, f) for f in os.listdir(directory) if os.path.isfile(os.path.join(directory, f))]
    if not files:
        raise FileNotFoundError(f"Файлы в директории {directory} отсутствуют.")

    latest_file = max(files, key=os.path.getmtime)
    return latest_file


@dp.message(F.text == ButtonText.get_bonus_score_of_tree)
async def handle_bonus_score_of_tree_request(
        message: Message,
        state: FSMContext):
    await message.answer('Формируется файл, пожалуйста подождите...')
    await bot.send_chat_action(chat_id=message.chat.id, action=ChatAction.TYPING)
    await state.set_state(FilesStates.files)
    try:
        user_id = await bd_get_user_by_tg_id(message.from_user.id)
        file_path = await api_get_user_tree_score(user_id)
        document = FSInputFile(file_path)
        await bot.send_document(chat_id=message.chat.id, document=document, caption="Баллы вашей структуры.")
    except FileNotFoundError as e:
        await message.answer(f"Ошибка: {str(e)}")
    except Exception as e:
        logging.error(f"Ошибка при отправке файла: {e}")
        await message.answer("Произошла ошибка при работе с сайтом.")
    finally:
        await state.clear()


@dp.message(FilesStates.files)
async def waiting_file_message(message: Message):
    await message.answer('Пожалуйста, подождите загрузки файла')


@dp.message(F.text == ButtonText.get_start)
async def handle_start_request(message: Message):
    await message.answer("Вы находитесь в начальном меню.", reply_markup=create_familiar_user_keyboard())


@dp.message(F.text == ButtonText.background_info)
async def handle_background_info_request(message: Message):
    await message.answer('Предоставляется справочная информация:', reply_markup=create_background_info_keyboard())


@dp.message(CommandStart())
async def handle_start_command(message: Message):
    user = await bd_get_user_by_id(message.from_user.id)
    if user is None:
        await message.answer(f"Здравствуйте, {html.bold(message.from_user.full_name)}!",
                             reply_markup=create_start_keyboard())
    else:
        await message.answer(f"Добро пожаловать, {html.bold(user['name'])}!",
                             reply_markup=create_familiar_user_keyboard())


async def main():
    logging.basicConfig(level=logging.INFO)
    await dp.start_polling(bot)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())
