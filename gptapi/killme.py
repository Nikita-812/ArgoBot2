import json

# Открываем и читаем файл
with open('./rag_data/learning.json', 'r', encoding='utf-8') as file:
    lines = file.readlines()

qa_pairs = []

# Пробегаем по строкам файла
for line in lines:
    # Убираем лишние пробелы и проверяем, что строка не пуста
    line = line.strip()
    if line:
        try:
            # Преобразуем строку в JSON
            data = json.loads(line)
            # Извлекаем последний элемент 'request', который содержит вопрос
            question = data['request'][-1]['text']
            # Извлекаем ответ
            answer = data.get('response')
            if question and answer:
                # Добавляем пару (вопрос, ответ) в список
                qa_pairs.append((question, answer))
        except json.JSONDecodeError:
            # Если строка не является корректным JSON, пропускаем ее
            continue

# Печатаем пары вопрос-ответ
for question, answer in qa_pairs:
    print(f"Вопрос: {question}\nОтвет: {answer}\n")

