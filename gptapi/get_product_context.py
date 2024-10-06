import asyncio
import aiohttp
import openai
import chromadb
from typing import List
import os
from dotenv import load_dotenv

load_dotenv()


# Колонки, которые нужно извлечь из метаданных продукта
text_columns = [
    'GOODS_NAME', 'GOODS_URL', 'GOODS_PV', 'GOODS_CONDITION', 'GOODS_ANTY_CONDITION', 'GOODS_RECOMMENDATION',
    'GOODS_PROPERTY', 'GOODS_COMPOSITION', 'GOODS_PACKING', 'GOODS_WEIGHT', 'CATALOG_NAME', 'CATALOG_FULL_NAME',
    "CATEGORY"
]

async def generate_query_embedding(query_text: str) -> List[float]:
    """
    Генерирует эмбеддинг для текста запроса пользователя с помощью OpenAI API.
    """
    url = 'https://api.openai.com/v1/embeddings'
    headers = {
        'Authorization': f'Bearer {os.getenv("OPENAI_API_KEY")}',
        'Content-Type': 'application/json'
    }
    data = {
        'input': query_text,
        'model': 'text-embedding-ada-002'
    }
    async with aiohttp.ClientSession() as session:
        async with session.post(url, headers=headers, json=data) as resp:
            response = await resp.json()
            query_embedding = response['data'][0]['embedding']
    return query_embedding

async def query_database(query_text: str) -> str:
    """
    Выполняет запрос к векторной базе данных с использованием эмбеддинга запроса
    и возвращает наиболее релевантную информацию о продукте.
    """
    # Генерация эмбеддинга для запроса
    query_embedding = await generate_query_embedding(query_text)
    persist_directory = "/home/nik/PycharmProjects/ArgoBot21/gptapi/chroma"
    client = chromadb.PersistentClient(persist_directory)
    try:
        collection = client.get_collection(name='products')
    except chromadb.errors.InvalidCollectionException:
        print("Коллекция 'products' не найдена. Убедитесь, что база данных была создана и сохранена правильно.")
        return ''
    # Выполнение запроса для поиска наиболее похожего продукта
    def blocking_query():
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=1
        )
        return results
    # Выполнение блокирующего запроса в отдельном потоке
    results = await asyncio.to_thread(blocking_query)
    # Обработка и отображение результата
    if results['documents']:
        # Извлечение информации о продукте
        product_info = results['documents'][0][0]
        product_metadata = results['metadatas'][0][0]
        # Форматирование информации о продукте в строку
        product_data = ''
        for col in text_columns:
            value = product_metadata.get(col, '')
            if value:
                product_data += f"{col}: {value}\n"
        # Вывод информации (можно вернуть или отправить пользователю в боте)
        return product_data
    else:
        return 'Товар не найден.'

async def main():
    # Пример запроса пользователя
    query_text = 'посоветуй что-нибудь от гипертонии?'
    print(await query_database(query_text))

if __name__ == "__main__":
    asyncio.run(main())
