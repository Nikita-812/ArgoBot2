
import requests
from bs4 import BeautifulSoup
import aiofiles
import asyncio
import pathlib
import re

def get_page(url):
    response = requests.get(url)
    response.raise_for_status()  # Ensure request was successful

    soup = BeautifulSoup(response.text, 'html.parser')
    
    # Удаляем иконки WhatsApp
    for icon in soup.find_all("i", class_="fab fa-whatsapp"):
        icon.decompose()

    # Извлекаем текст из всех параграфов
    contacts = soup.find_all('p')
    res = []
    for contact in contacts:
        text = contact.get_text(separator=" ")
        res.append(text)

    # Объединяем параграфы с переносом строки для удобства
    full_text = '\n'.join(res)

   
    # Обрезаем текст от "Телефон", если эта фраза присутствует
    index = full_text.find("Телефон")
    if index != -1:
        full_text = full_text[index:]

    # Удаляем фразу о cookies
    full_text = re.sub(
        r"Мы используем файлы cookies и метрики для улучшения работы сайта\. "
        r"Продолжая использование сайта, вы соглашаетесь с этим\.", 
        '', 
        full_text
    ).strip()

    # Удаляем лишние пробелы (множество пробелов заменяем одним)
    full_text = re.sub(r'[ ]{2,}', ' ', full_text)
    # 2. Заменяем более двух последовательных переносов строк на двойной перенос строки
    full_text = re.sub(r'\n{3,}', '\n\n', full_text) 

    return full_text

async def get_operators_contacts_from_txt():
    # Get the path to the current file's directory
    current_dir = pathlib.Path(__file__).parent

    # Define the path to the operators.txt file
    txt_file_path = current_dir / 'operators.txt'

    try:
        # Open the file asynchronously and read the content
        async with aiofiles.open(txt_file_path, 'r', encoding='utf-8') as file:
            content = await file.read()  # Read the whole file content as a string
            content = re.sub(r'^\s+', '', content)
            content = content.replace('\u00A0', '').strip()
        return content
    except FileNotFoundError:
        return "Error: operators.txt not found."
    except Exception as e:
        return f"An error occurred: {e}"

async def write_contacts_to_txt(content):
    # Asynchronously write the formatted content to 'operators.txt'
    async with aiofiles.open("operators.txt", "w", encoding="utf-8") as f:
        await f.write(content)

async def main():
    # Retrieve and format contact details from the page
    url = "https://argo.company/contacts/"
    result = get_page(url)

    # Asynchronously write the formatted result to 'operators.txt'
    await write_contacts_to_txt(result)
    print(result)

if __name__ == '__main__':
    asyncio.run(main())

