import json

# Чтение JSON-файла
with open("C:\\Users\\nikita\\Downloads\\response_1724152483806.json", 'r', encoding='utf-8') as file:
    data = json.load(file)

# Извлечение всех имен
names = set()  # Используем set для уникальности имен

for key, value in data.items():
    if 'participantName' in value:
        names.add(value['participantName'])
    if 'participant' in value and 'name' in value['participant']:
        names.add(value['participant']['name'])
