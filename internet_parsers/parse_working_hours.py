import asyncio

from bs4 import BeautifulSoup
import aiofiles
import aiohttp
import pathlib

async def fetch_html(url):
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            return await response.text()


async def parse_working_hours(html):
    soup = BeautifulSoup(html, 'html.parser')

    working_hours = {
        "Москва": None,
        "Новосибирск": None
    }

    moscow_section = soup.find('a', href=lambda href: href and 'contacts/stores/2000859' in href)
    petersburg_section = soup.find('a', href=lambda href: href and 'contacts/stores/2000860' in href)

    if moscow_section:
        moscow_table = moscow_section.find_next('table')
        if moscow_table:
            moscow_hours = moscow_table.get_text(separator=" ").strip()
            working_hours["Москва"] = moscow_hours

    if petersburg_section:
        petersburg_table = petersburg_section.find_next('table')
        if petersburg_table:
            petersburg_hours = petersburg_table.get_text(separator=" ").strip()
            working_hours["Новосибирск"] = petersburg_hours

    # Asynchronously write the working hours to a file
    async with aiofiles.open('working_hours.txt', 'w') as file:
        for city, hours in working_hours.items():
            await file.write(f"{city}: {hours}\n")

    return working_hours


async def write_working_hours(output_file='working_hours.txt'):
    url = "https://argo.company/contacts/"
    html = await fetch_html(url)  # Asynchronously fetch HTML
    working_hours = await parse_working_hours(html)  # Parse working hours asynchronously

    # Asynchronously write the working hours to a file
    async with aiofiles.open(output_file, 'w', encoding='utf-8') as file:
        for city, hours in working_hours.items():
            await file.write(f"{city}: {hours}\n")


async def get_working_hours_from_file(filename=pathlib.Path(__file__).resolve().parent / 'working_hours.txt'):
    content = ""
    print(filename)
    async with aiofiles.open(filename, 'r', encoding='utf-8') as file:
        content = await file.read()
    return content


async def main():
    #await write_working_hours()
    await get_working_hours_from_file()


if __name__ == "__main__":
    asyncio.run(main())
    #print("Working hours have been written to 'working_hours.txt'")
