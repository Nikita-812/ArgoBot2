import os
import aiohttp
import time
import asyncio
import aiofiles
import ssl
import logging
from openpyxl import Workbook
from pathlib import Path

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

HEADERS = {
    'accept': 'application/json',
    'Content-Type': 'application/json',
}

def api_create_participant_data(parent_id=2147483647, name='', status='new',
                                bitrix_id=2147483647, email='',
                                mobile_phone='', birth_date='',
                                registrator_id=0,
                                country_id=0, region_id=0, city_id=0):
    current_time = time.localtime()
    formatted_date = time.strftime('%Y-%m-%d', current_time)
    json_data = {
        'parentId': parent_id,
        'name': name,
        'status': status,
        'bitrixId': bitrix_id,
        'email': email,
        'mobilePhone': mobile_phone,
        'birthDate': birth_date,
        'registratorId': registrator_id,
        'countryId': country_id,
        'regionId': region_id,
        'cityId': city_id,
        'registrationDate': formatted_date,
    }
    return json_data

async def api_post_new_participant(data):
    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE
    async with aiohttp.ClientSession() as session:
        async with session.post("https://192.168.0.15/DailyNews/Participant", headers=HEADERS, json=data,
                                ssl=ssl_context) as response:
            logger.info("Status: %s", response.status)
            html = await response.text()
            return response.status, html

async def api_get_user_by_id(user_id: int):
    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE
    async with aiohttp.ClientSession() as session:
        async with session.get(f"https://192.168.0.15/DailyNews/Participant/{user_id}", headers=HEADERS,
                               ssl=ssl_context) as response:
            logger.info("Status: %s", response.status)
            html = await response.json()
            return response.status, html

async def api_get_user_score(user_id: int):
    headers = {
        'accept': 'application/json',
        'X-authUserNumber-Header': str(user_id),
    }
    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE
    async with aiohttp.ClientSession() as session:
        async with session.get(f"https://192.168.0.15/DailyNews/BonusBalance/{user_id}", headers=headers,
                               ssl=ssl_context) as response:
            logger.info("Status: %s", response.status)
            html = await response.json()
            return response.status, html

async def create_excel_file(file_path, name, personalpv):
    def sync_create_excel_file():
        workbook = Workbook()
        sheet = workbook.active

        # Define column headers
        sheet['A1'] = 'Name'
        sheet['B1'] = 'PersonalPV'
        sheet['A2'] = name
        sheet['B2'] = personalpv
        workbook.save(file_path)
        return file_path

    result = await asyncio.to_thread(sync_create_excel_file)
    logger.info(f"Excel file created at {result}")
    return result

async def api_get_user_tree_score(user_id: int) -> str:
    headers = {
        'accept': '*/*',
        'X-authUserNumber-Header': str(user_id),
    }
    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE

    # Проверка и создание директории Struct
    struct_dir = Path(__file__).parent.parent / 'Struct'
    if not struct_dir.exists():
        struct_dir.mkdir(parents=True, exist_ok=True)

    async with aiohttp.ClientSession() as session:
        async with session.get(f"https://192.168.0.15/DailyNews/Report/stat/{user_id}", headers=headers,
                               ssl=ssl_context) as response:
            file_path = struct_dir / f"{user_id}.xlsx"
            if response.status == 200:
                file_content = await response.read()
                async with aiofiles.open(file_path, 'wb') as file:
                    await file.write(file_content)
                    await file.flush()
                logger.info(f"File successfully saved at {file_path}")
                return file_path
            else:
                user_status, user = await api_get_user_by_id(user_id)
                score_status, score = await api_get_user_score(user_id)

                if user_status == 200 and score_status == 200:
                    result = await create_excel_file(file_path, user['name'], score['personalPv'])
                    return result
                else:
                    error_msg = f"Error fetching user data for ID {user_id}."
                    logger.error(error_msg)
                    raise Exception(error_msg)

async def send_file_to_telegram(file_path):
    # Implement your Telegram sending logic here
    # Ensure you wait for the file to exist and be fully written
    if not file_path.exists():
        logger.error(f"File {file_path} does not exist.")
        return

    # Example: Using aiogram or another Telegram bot library
    # await bot.send_document(chat_id, open(file_path, 'rb'))
    logger.info(f"File {file_path} sent to Telegram.")

async def main():
    user_id = 13
    try:
        file_path = await api_get_user_tree_score(user_id)
        logger.info(f"Proceeding to send the file {file_path} to Telegram.")
        await send_file_to_telegram(file_path)
    except Exception as e:
        logger.error(f"An error occurred: {e}")

if __name__ == '__main__':
    asyncio.run(main())

