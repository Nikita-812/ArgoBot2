import csv

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup


def get_sale_points(city_name):
    options = Options()
    options.add_argument('--headless')  # Запуск браузера в фоновом режиме
    options.add_argument('--disable-gpu')

    # Укажите путь к драйверу ChromeDriver
    chromedriver_path = "C:\\Users\\nikita\\PycharmProjects\\ArgoBot\\chromedrive\\chromedriver.exe"
    service = Service(chromedriver_path)

    # Инициализация WebDriver
    driver = webdriver.Chrome(service=service, options=options)

    try:
        # Открытие целевой страницы
        driver.get('https://argo.company/company/sale-points/')

        # Найти поле ввода города
        search_box = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, 'city_list'))
        )

        # Ввести название города
        search_box.send_keys(city_name)

        # Ожидание появления подсказки и клик на неё
        suggestion = WebDriverWait(driver, 4).until(
            EC.element_to_be_clickable((By.ID, 'ui-id-1'))
        )
        suggestion.click()

        try:
            # Ожидание загрузки таблицы
            table = WebDriverWait(driver, 4).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 'table.ordinary'))
            )
        except Exception as e:
            return f"В выбранном городе на текущий момент не зарегистрировано официальных торговых партнеров компании АРГО."

        # Получение HTML-кода страницы с результатами
        html = driver.page_source

    finally:
        # Закрытие браузера
        driver.quit()

    # Разбор HTML с использованием BeautifulSoup
    soup = BeautifulSoup(html, 'html.parser')

    # Поиск таблицы с торговыми точками
    table = soup.find('table', class_='ordinary')

    if not table:
        return f"Не удалось найти таблицу с торговыми точками для города."

    # Парсинг строк таблицы
    sale_points = []
    rows = table.find_all('tr')[1:]  # Пропускаем заголовок таблицы
    for row in rows:
        cells = row.find_all('td')
        if len(cells) >= 5:
            address = cells[1].get_text(strip=True)
            payment_methods = cells[2].get_text(strip=True)
            phone = cells[3].get_text(strip=True)
            email = cells[4].get_text(strip=True)
            sale_points.append({
                'town': city_name,
                'address': address,
                'payment_methods': payment_methods,
                'phone': phone,
                'email': email
            })

    return sale_points


def get_sale_point_from_csv(city_name):
    with open("C:\\Users\\nikita\\PycharmProjects\\ArgoBot\\internet_parsers\\sale_points.csv", encoding='utf-8') as f:
        data = csv.DictReader(f)
        sale_points = []
        for row in data:
            if row['City'] == city_name:
                sale_points.append(row)
    return sale_points


if __name__ == "__main__":
    city = "Москва"
    get_sale_point_from_csv(city)