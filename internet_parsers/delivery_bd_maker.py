import csv

from delivery_parse import get_sale_points, towns

# Открываем файл для записи
with open('sale_points.csv', 'a', newline='', encoding='utf-8') as f:
    # Создаем объект writer с разделителем ','
    writer = csv.writer(f, delimiter=',')

    # Проходим по списку городов
    for town in towns:
        sale_points = get_sale_points(town)

        # Если торговых точек нет, пропускаем город
        if isinstance(sale_points, str) and "не зарегистрировано" in sale_points:
            continue

        # Записываем каждую точку продажи в файл
        for point in sale_points:
            print(point)
            writer.writerow([town, point['address'], point['payment_methods'], point['phone'], point['email']])
