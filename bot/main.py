import asyncio
import logging
import sys
from os import getenv

from aiogram import Bot, Dispatcher, F, html
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ChatAction, ParseMode
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import FSInputFile, Message

from ButtonText import ButtonText
from bot.States import FilesStates, RegStates, TownsStates
from bot.constructor_kb import (create_background_info_keyboard,
                                create_familiar_user_keyboard,
                                create_start_keyboard)
from db.db import bd_get_user_by_id, bd_get_user_by_tg_id, bd_reg_participant
from gptapi.gpt import generate_response
from internet_parsers.delivery_parse import get_sale_point_from_csv
from internet_parsers.parse_delivery_conditions import get_delivery_conditions_from_txt
from internet_parsers.parse_operators_contact import get_operators_contacts_from_txt
from internet_parsers.parse_working_hours import get_working_hours_from_file
from requests_to_lk.work_with_api import (api_get_user_by_id,
                                          api_get_user_score,
                                          api_get_user_tree_score)
from utils.is_aproximate_word import is_town_approx_in_string
from utils.sending_email_messages import generate_password, send_email_password
from utils.validation import id_validation_filter

# Initialize logging
logging.basicConfig(level=logging.INFO, stream=sys.stdout)
logger = logging.getLogger(__name__)

# Initialize bot and dispatcher
TOKEN = getenv("BOT_TOKEN")
if not TOKEN:
    logger.error("Bot token is not provided. Please set BOT_TOKEN environment variable.")
    sys.exit(1)

bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()

# Handlers

@dp.message(F.text == ButtonText.where)
async def handle_where_to_buy(message: Message, state: FSMContext) -> None:
    """
    Handler for 'Where to Buy' button. Asks the user to specify the city.
    """
    await bot.send_chat_action(chat_id=message.chat.id, action=ChatAction.TYPING)
    await message.answer("Пожалуйста, укажите город.")
    await state.set_state(TownsStates.town)


@dp.message(TownsStates.town, F.text)
async def handle_town_selection(message: Message, state: FSMContext) -> None:
    """
    Handles the user's input for the city name and provides sale points in that city.
    """
    city_name = is_town_approx_in_string(message.text.lower().strip())
    if city_name:
        sale_points = get_sale_point_from_csv(city_name)
        await state.clear()
        if isinstance(sale_points, list):
            result_message = f"Торговые точки в городе {city_name}:\n"
            for point in sale_points:
                result_message += (
                    f"Адрес: {point['Address']}\n"
                    f"Оплата: {point['Payment_method']}\n"
                    f"Телефон: {point['Phone']}\n"
                    f"E-Mail: {point['Email']}\n\n"
                )
        else:
            result_message = sale_points

        user = await bd_get_user_by_tg_id(message.from_user.id)
        if user:
            logger.info(f"User {message.from_user.id} is recognized.")
            await message.answer(
                text=result_message,
                reply_markup=create_familiar_user_keyboard()
            )
        else:
            await message.answer(
                text=result_message,
                reply_markup=create_start_keyboard()
            )
    else:
        await message.answer(
            'Извините, но название города не распознано. Пожалуйста, попробуйте снова.'
        )


@dp.message(TownsStates.town)
async def failure_town_selection(message: Message) -> None:
    """
    Handles incorrect city name input.
    """
    await message.answer('Пожалуйста, введите название города текстом.')


@dp.message(F.text == ButtonText.delivery)
async def handle_delivery_request(message: Message) -> None:
    """
    Provides delivery conditions to the user.
    """
    content = await get_delivery_conditions_from_txt()
    await message.answer(text=content)


@dp.message(F.text == ButtonText.contact)
async def handle_contact_request(message: Message) -> None:
    """
    Provides contact information to the user.
    """
    content = await get_operators_contacts_from_txt()
    await message.answer(text=content)


@dp.message(F.text == ButtonText.times)
async def handle_working_hours_request(message: Message) -> None:
    """
    Provides working hours information to the user.
    """
    try:
        content = await get_working_hours_from_file()
        await message.answer(text=content)
    except Exception as e:
        logger.error(f"Error getting working hours: {e}")
        await message.answer(f"Произошла ошибка при получении рабочего времени: {str(e)}")


@dp.message(F.text == ButtonText.reg)
async def handle_registration_start(message: Message, state: FSMContext) -> None:
    """
    Initiates the registration process.
    """
    await state.set_state(RegStates.name)
    await message.answer(text="Как вас зовут?")


@dp.message(F.text == ButtonText.enter_account)
async def handle_enter_account(message: Message, state: FSMContext) -> None:
    """
    Initiates the login process by asking for user ID.
    """
    await state.set_state(RegStates.id)
    await message.answer('Пожалуйста, введите ваш ID.')


@dp.message(RegStates.id, F.text)
async def handle_user_search(message: Message, state: FSMContext) -> None:
    """
    Handles user ID input and sends a password to the user's email.
    """
    user_id = id_validation_filter(message.text)
    if not user_id:
        await message.answer('Некорректный ID. Пожалуйста, введите числовой ID.')
        return

    status, user = await api_get_user_by_id(user_id)
    if status == 200 and user:
        password = generate_password()
        send_email_password(user['email'], password)
        await message.answer("Пароль отправлен на вашу почту. Пожалуйста, введите его.")
        await state.update_data(id=user)
        await state.set_state(RegStates.password)
        await state.update_data(password=password)
    else:
        await message.answer('Не удалось найти пользователя с указанным ID. Попробуйте снова.')


@dp.message(RegStates.id)
async def failure_get_user_id(message: Message) -> None:
    """
    Handles incorrect user ID input.
    """
    await message.answer('Пожалуйста, введите ваш ID числом.')


@dp.message(RegStates.password, F.text)
async def handle_password_check(message: Message, state: FSMContext) -> None:
    """
    Checks the password entered by the user.
    """
    try:
        password = message.text
        user_data = await state.get_data()
        if password == user_data.get('password'):
            user_data['id']['api_id'] = message.from_user.id
            await bd_reg_participant(user_data['id'])
            await message.answer(
                "Пароль верен. Вы успешно вошли в аккаунт.",
                reply_markup=create_familiar_user_keyboard()
            )
            await state.clear()
        else:
            await message.answer("Неверный пароль. Попробуйте еще раз.")
    except Exception as e:
        logger.error(f"Error during password check: {e}")
        await message.answer('Произошла ошибка. Попробуйте войти позже.')


@dp.message(RegStates.password)
async def failure_password_check(message: Message) -> None:
    """
    Handles incorrect password input.
    """
    await message.answer('Введите ваш пароль текстом.')


@dp.message(F.text == ButtonText.get_bonus_score)
async def handle_bonus_score_request(message: Message) -> None:
    """
    Provides the user's personal PV (bonus score).
    """
    user = await bd_get_user_by_tg_id(message.from_user.id)
    if not user:
        await message.answer('Вы не зарегистрированы. Пожалуйста, войдите в аккаунт.')
        return

    status, user_info = await api_get_user_score(user['id'])
    if status == 200 and user_info:
        personal_pv = user_info.get('personalPv', 'Нет данных')
        await message.answer(f'Ваш персональный PV: {personal_pv}')
    else:
        await message.answer('Не удалось получить информацию о бонусах. Попробуйте позже.')


@dp.message(F.text == ButtonText.get_bonus_score_of_tree)
async def handle_bonus_score_of_tree_request(message: Message, state: FSMContext) -> None:
    """
    Sends a file with the user's bonus score tree.
    """
    await message.answer('Формируется файл, пожалуйста подождите...')
    await bot.send_chat_action(chat_id=message.chat.id, action=ChatAction.UPLOAD_DOCUMENT)
    await state.set_state(FilesStates.files)
    try:
        user = await bd_get_user_by_tg_id(message.from_user.id)
        if not user:
            await message.answer('Вы не зарегистрированы. Пожалуйста, войдите в аккаунт.')
            await state.clear()
            return

        file_path = await api_get_user_tree_score(user['id'])
        document = FSInputFile(file_path)
        await bot.send_document(
            chat_id=message.chat.id,
            document=document,
            caption="Баллы вашей структуры."
        )
    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        await message.answer(f"Ошибка: {str(e)}")
    except Exception as e:
        logger.error(f"Error sending file: {e}")
        await message.answer("Произошла ошибка при работе с сайтом.")
    finally:
        await state.clear()


@dp.message(FilesStates.files)
async def waiting_file_message(message: Message) -> None:
    """
    Informs the user to wait while the file is being prepared.
    """
    await message.answer('Пожалуйста, подождите загрузки файла.')


@dp.message(F.text == ButtonText.get_start)
async def handle_start_request(message: Message) -> None:
    """
    Handles 'Start' button and provides the main menu.
    """
    await message.answer(
        "Вы находитесь в начальном меню.",
        reply_markup=create_familiar_user_keyboard()
    )


@dp.message(F.text == ButtonText.background_info)
async def handle_background_info_request(message: Message) -> None:
    """
    Provides background information to the user.
    """
    await message.answer(
        'Предоставляется справочная информация:',
        reply_markup=create_background_info_keyboard()
    )


@dp.message(CommandStart())
async def handle_start_command(message: Message) -> None:
    """
    Handles the '/start' command and greets the user.
    """
    user = await bd_get_user_by_tg_id(message.from_user.id)
    if user is None:
        await message.answer(
            f"Здравствуйте, {html.bold(message.from_user.full_name)}!",
            reply_markup=create_start_keyboard()
        )
    else:
        await message.answer(
            f"Добро пожаловать, {html.bold(user['name'])}!",
            reply_markup=create_familiar_user_keyboard()
        )


@dp.message(F.text)
async def gpt_ans(message: Message) -> None:
    """
    Handles all other text messages and generates a response using GPT.
    """
    prompt = message.text
    response = await generate_response(prompt)
    await message.answer(response)


# Main function

async def main():
    logging.basicConfig(level=logging.INFO)
    await dp.start_polling(bot)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())
