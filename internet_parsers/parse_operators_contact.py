import requests
from bs4 import BeautifulSoup

# URL to parse
url = 'https://argo.company/delivery/'

# Fetch the page content
response = requests.get(url)
if response.status_code != 200:
    print("Error fetching the page")
    exit()

# Parse the page with BeautifulSoup
soup = BeautifulSoup(response.text, 'html.parser')


def extract_info_between_h3(soup, start_text, end_text):
    extracted_text = []

    # Find the <h3> tags by their text content
    start_tag = soup.find('h3', text=start_text)
    end_tag = soup.find(text=end_text)

    if not start_tag or not end_tag:
        print("Could not find the specified <h3> headers.")
        return None

    # Iterate through elements between the two <h3> tags
    for element in start_tag.find_all_next():
        # Stop when we reach the end tag
        if element == end_tag:
            break
        extracted_text.append(element)

    # Join and return the extracted text
    return ''.join([el.text if hasattr(el, 'text') else str(el) for el in extracted_text])


# Extract data between two <h3> headers
start_h3 = "Условия бесплатной доставки"
end_h3 = "Уважаемые аргонавты,"
parsed_info = extract_info_between_h3(soup, start_h3, end_h3)

# Output the extracted information
if parsed_info:
    print(parsed_info)
