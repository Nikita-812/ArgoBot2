# file path: argo_parser.py

import requests
from bs4 import BeautifulSoup


def fetch_html(url):
    response = requests.get(url)
    response.raise_for_status()  # Ensure we notice bad responses
    return response.text


def parse_working_hours(html):
    soup = BeautifulSoup(html, 'html.parser')

    # Create a dictionary to store working hours of Moscow and St. Petersburg centers
    working_hours = {
        "Москва": None,
        "Новосибирск": None
    }

    # Find the sections for Moscow and St. Petersburg
    moscow_section = soup.find('a', href=lambda href: href and 'contacts/stores/2000859' in href)
    petersburg_section = soup.find('a', href=lambda href: href and 'contacts/stores/2000860' in href)

    # Extract working hours for Moscow
    if moscow_section:
        moscow_table = moscow_section.find_next('table')
        if moscow_table:
            moscow_hours = moscow_table.get_text(separator=" ").strip()
            working_hours["Москва"] = moscow_hours

    # Extract working hours for St. Petersburg
    if petersburg_section:
        petersburg_table = petersburg_section.find_next('table')
        if petersburg_table:
            petersburg_hours = petersburg_table.get_text(separator=" ").strip()
            working_hours["Новосибирск"] = petersburg_hours

    return working_hours


def get_working_hours():
    url = "https://argo.company/contacts/"
    html = fetch_html(url)
    working_hours = parse_working_hours(html)
    res = ''
    for city, hours in working_hours.items():
        res += (f"{city}: {hours}")
        res+='\n'
    return res


if __name__ == "__main__":
    print(get_working_hours())
