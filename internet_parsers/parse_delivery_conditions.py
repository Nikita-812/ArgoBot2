import aiohttp
from bs4 import BeautifulSoup
import pathlib
import aiofiles
import re

async def get_delivery_conditions():
    url = "https://argo.company/delivery/"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            response.raise_for_status()
            html = await response.text()

    soup = BeautifulSoup(html, 'html.parser')

    # Locate the heading for "Условия бесплатной доставки"
    section_heading = soup.find(string="Условия бесплатной доставки")
    if section_heading:
        # Find the parent element of the heading
        parent_element = section_heading.find_parent()

        # Initialize an empty list to store formatted content
        content = [f"## {section_heading.strip()}"]

        # Collect all elements (paragraphs, lists, etc.) that follow the heading
        next_element = parent_element.find_next_sibling()
        while next_element and (next_element.name in ['p', 'ul', 'ol'] or next_element.find('li')):
            if next_element.name == 'p':
                # Убираем лишние пробелы из текста абзаца
                paragraph_text = re.sub(r'\s+', ' ', next_element.get_text(strip=True))
                content.append(paragraph_text)
            elif next_element.name == 'ul':
                for li in next_element.find_all('li'):
                    list_item = re.sub(r'\s+', ' ', li.get_text(strip=True))
                    content.append(f"- {list_item}")
            elif next_element.name == 'ol':
                for i, li in enumerate(next_element.find_all('li'), start=1):
                    list_item = re.sub(r'\s+', ' ', li.get_text(strip=True))
                    content.append(f"{i}. {list_item}")
            next_element = next_element.find_next_sibling()

        # Join the content into a Markdown-formatted string
        delivery_conditions = "\n\n".join(content)

        # Убираем из текста излишние переносы строк
        full_text = re.sub(r'\n{3,}', '\n\n', delivery_conditions)
        return full_text
    else:
        return "Could not find delivery conditions on the page."
async def get_delivery_conditions_from_txt():
    current_dir = pathlib.Path(__file__).parent
    txt_file_path = current_dir / 'delivery_conditions.txt'

    try:
        async with aiofiles.open(txt_file_path, 'r', encoding='utf-8') as file:
            content = await file.read()
        return content
    except FileNotFoundError:
        return "Error: delivery_conditions.txt not found."
    except Exception as e:
        return f"An error occurred: {e}"


async def write_delivery_conditions_to_txt(content):
    async with aiofiles.open("delivery_conditions.txt", "w", encoding="utf-8") as f:
        await f.write(content)


async def main():
    url = "https://argo.company/delivery/"
    delivery_conditions = await get_delivery_conditions()

    await write_delivery_conditions_to_txt(delivery_conditions)

    print(delivery_conditions)


if __name__ == '__main__':
    import asyncio
    asyncio.run(main())

