import pandas as pd
import asyncio
import aiohttp
import aiofiles
import re
import openai
import chromadb
from typing import List
import os
from dotenv import load_dotenv

# Загрузка переменных окружения
load_dotenv()
# Установка API-ключа OpenAI

# Колонки с текстом из CSV файла
text_columns = [
    'GOODS_NAME', 'GOODS_URL', 'GOODS_PV', 'GOODS_CONDITION', 'GOODS_ANTY_CONDITION', 'GOODS_RECOMMENDATION',
    'GOODS_PROPERTY', 'GOODS_COMPOSITION', 'GOODS_PACKING', 'GOODS_WEIGHT', 'CATALOG_NAME', 'CATALOG_FULL_NAME',
    "CATEGORY"
]


def clean_text(text: str) -> str:
    """
    Очищает текст от HTML-тегов и лишних символов, при этом оставляя URL-адреса.
    """
    if not isinstance(text, str):
        return ''
    # Удаление HTML-тегов
    text = re.sub(r'<[^>]+>', '', text)
    # Удаление ненужных символов, кроме тех, которые используются в URL
    text = re.sub(r'[^\w\s:/.-]', '', text)
    return text.strip()


async def load_and_preprocess_data(csv_file: str) -> pd.DataFrame:
    """
    Асинхронно загружает и обрабатывает данные из CSV файла.
    Очищает текстовые колонки и объединяет их в одно текстовое поле.
    """
    async with aiofiles.open(csv_file, mode='r', encoding='utf-8') as f:
        content = await f.read()
    from io import StringIO
    df = pd.read_csv(StringIO(content))
    # Очистка текстовых колонок
    for col in text_columns:
        if col in df.columns:
            df[col] = df[col].apply(clean_text)
        else:
            df[col] = ''
    # Объединение всех текстовых колонок в одно текстовое поле
    df['combined_text'] = df[text_columns].fillna('').agg(' '.join, axis=1)
    return df


async def generate_embeddings(texts: List[str]) -> List[List[float]]:
    """
    Генерирует эмбеддинги для списка текстов через OpenAI API.
    Работает пакетами для ускорения обработки.
    """
    embeddings = []
    batch_size = 16  # Размер пакета для API-запросов
    url = 'https://api.openai.com/v1/embeddings'
    headers = {
        'Authorization': f'Bearer {openai.api_key}',
        'Content-Type': 'application/json'
    }

    async with aiohttp.ClientSession() as session:
        tasks = []
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            data = {
                'input': batch,
                'model': 'text-embedding-ada-002'
            }
            tasks.append(fetch_embedding(session, url, headers, data))
        # Выполнение всех запросов асинхронно
        results = await asyncio.gather(*tasks)
        # Извлечение эмбеддингов из ответов
        for result in results:
            for item in result['data']:
                embeddings.append(item['embedding'])
    return embeddings


async def fetch_embedding(session, url, headers, data):
    """
    Асинхронная функция для выполнения запроса на получение эмбеддингов.
    """
    async with session.post(url, headers=headers, json=data) as resp:
        response = await resp.json()
        return response


async def main():
    # Путь к CSV файлу с данными
    csv_file = '/home/nik/PycharmProjects/ArgoBot21/data/cleaned_products.csv'
    # Загрузка и предварительная обработка данных
    df = await load_and_preprocess_data(csv_file)
    # Генерация эмбеддингов для всех продуктов
    texts = df['combined_text'].tolist()
    embeddings = await generate_embeddings(texts)

    # Инициализация ChromaDB клиента с указанием директории для сохранения данных
    client =chromadb.PersistentClient()

    # Создание или получение коллекции 'products'
    try:
        collection = client.create_collection(name='products')
    except chromadb.errors.CollectionAlreadyExistsError:
        collection = client.get_collection(name='products')



    # Добавление эмбеддингов и метаданных в коллекцию
    def blocking_add():
        collection.add(
            embeddings=embeddings,
            documents=texts,
            metadatas=df.to_dict('records'),
            ids=[str(i) for i in df.index]
        )

    # Асинхронный вызов для добавления данных
    await asyncio.to_thread(blocking_add)

    print("Векторная база данных успешно создана и сохранена.")


if __name__ == "__main__":
    asyncio.run(main())

