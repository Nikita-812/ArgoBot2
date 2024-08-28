import aiohttp
import time
import asyncio
import aiofiles
import ssl
from openpyxl import Workbook

headers = {
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
        async with session.post("https://192.168.0.15/DailyNews/Participant", headers=headers, json=data,
                                ssl=ssl_context) as response:
            print("Status:", response.status)
            html = await response.text()
            return response.status, html


async def api_get_user_by_id(id: int):
    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE
    async with aiohttp.ClientSession() as session:
        async with session.get(f"https://192.168.0.15/DailyNews/Participant/{id}", headers=headers,
                               ssl=ssl_context) as response:
            print("Status:", response.status)
            html = await response.json()
            return response.status, html


async def api_get_user_score(id: int):
    headers = {
        'accept': 'application/json',
        'X-authUserNumber-Header': str(id),
    }
    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE
    async with aiohttp.ClientSession() as session:
        async with session.get(f"https://192.168.0.15/DailyNews/BonusBalance/{id}", headers=headers,
                               ssl=ssl_context) as response:
            print("status:", response.status)
            html = await response.json()
            return response.status, html


def create_excel_file(file_path, name, personalpv):
    # Create a workbook and select the active worksheet
    workbook = Workbook()
    sheet = workbook.active

    # Define column headers
    sheet['A1'] = 'Name'
    sheet['A2'] = name
    sheet['B2'] = personalpv
    sheet['B1'] = 'PersonalPV'

    # Save the workbook to the specified file path
    workbook.save(file_path)


async def api_get_user_tree_score(id: int) -> str:
    headers = {
        'accept': '*/*',
        'X-authUserNumber-Header': str(id),
    }
    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE

    async with aiohttp.ClientSession() as session:
        async with session.get(f"https://192.168.0.15/DailyNews/Report/stat/{id}", headers=headers,
                               ssl=ssl_context) as response:
            file_path = f"../Struct/{id}.xlsx"
            if response.status == 200:
                file_content = await response.read()
                async with aiofiles.open(file_path, 'wb') as file:
                    await file.write(file_content)
            else:
                file_path = f"../Struct/{id}.xlsx"
                user = await api_get_user_by_id(id)
                score = await api_get_user_score(id)
                create_excel_file(file_path, user[1]['name'], score[1]['personalPv'])
    return file_path


async def main():
    # status, txt = await post_new_participant(create_participant_data(
    #     parent_id=1,
    #     name='Никита',
    #     status='New',
    #     bitrix_id=1,
    #     email='nikitospashynin@gmail.com',
    #     mobile_phone='89231416154',
    #     birth_date='2005-08-19',
    #     registrator_id=0,
    #     country_id=0,
    #     region_id=0,
    #     city_id=0
    # ))
    await api_get_user_tree_score(1)


if __name__ == '__main__':
    asyncio.run(main())
