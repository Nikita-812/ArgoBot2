import re

# Путь к файлу
file_path = "unsatisfactory_reports.txt"

# Словарь для хранения вопросов и ответов
qa_dict = {}

# Чтение данных из файла
with open(file_path, "r", encoding="utf-8") as file:
    text = file.read()

# Разделение на блоки по "User:" и "Assistant:"
entries = re.split(r"(User:.*?\nAssistant:.*?)\n\n", text, flags=re.DOTALL)
entries = [entry.strip() for entry in entries if entry.strip()]

# Обработка блоков и создание словаря
for entry in entries:
    match = re.match(r"User:(.*?)\nAssistant:(.*)", entry, re.DOTALL)
    if match:
        question = match.group(1).strip()
        answer = match.group(2).strip()
        qa_dict[question] = answer

# Вывод только вопросов
print("Вопросы:")
for question in qa_dict.keys():
    print(question)
