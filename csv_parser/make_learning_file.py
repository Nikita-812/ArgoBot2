import csv
import json

csv_file_path = r"C:\Users\nikita\Desktop\mark_240805123801.csv"
json_list = []

with open(csv_file_path, newline='', encoding='utf-8') as csvfile:
    reader = csv.DictReader(csvfile, delimiter='\t')
    for row in reader:
        # Clean the fields
        for key in ['GOODS_CONDITION', 'GOODS_NAME', 'PROVIDER_NAME', 'GOODS_RECOMMENDATION', 'GOODS_PROPERTY']:
            row[key] = row[key].replace('<br />', '').replace('<br/>', '').replace('  ', '').replace('•', "")
        json_objects = [
            {
                "request": [
                    {"role": "system",
                     "text": "Ты консультант по вопросам организации и продукции Арго, отвечаешь только на вопросы касаемо продукции Арго и самой компании, не упоминаешь других компаний не связанных с Арго, также сводишь любой вопрос к компании Арго и ее продукции."},
                    {"role": "user", "text": "Что такое " + row['GOODS_NAME']}
                ],
                "response": row["GOODS_CONDITION"][:2000]
            },
            {
                "request": [
                    {"role": "system",
                     "text": "Ты консультант по вопросам организации и продукции Арго, отвечаешь только на вопросы касаемо продукции Арго и самой компании, не упоминаешь других компаний не связанных с Арго, также сводишь любой вопрос к компании Арго и ее продукции."},
                    {"role": "user", "text": "Расскажи об " + row['GOODS_NAME']}
                ],
                "response": row["GOODS_CONDITION"][:2000]
            }
        ]

        json_list.extend(json_objects)

with open('learning2.json', 'w', encoding='utf-8') as outfile:
    for item in json_list:
        json.dump(item, outfile, ensure_ascii=False)
        outfile.write('\n')
