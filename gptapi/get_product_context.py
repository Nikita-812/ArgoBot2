import asyncio
import aiohttp
import openai
import chromadb
from chromadb.config import Settings
from typing import List
import os
from dotenv import load_dotenv
from make_database import clean_text

load_dotenv()

openai.api_key = os.getenv("OPENAI_API_KEY")

# Колонки для извлечения из метаданных продуктов
product_columns = [
    'GOODS_NAME', 'GOODS_URL', 'GOODS_PV', 'GOODS_CONDITION', 'GOODS_ANTY_CONDITION', 'GOODS_RECOMMENDATION',
    'GOODS_PROPERTY', 'GOODS_COMPOSITION', 'GOODS_PACKING', 'GOODS_WEIGHT', 'CATALOG_NAME', 'CATALOG_FULL_NAME',
    'CATEGORY'
]

# Колонки для извлечения из метаданных FAQ
faq_columns = [
    'question', 'answer'
]

async def generate_query_embedding(query_text: str) -> List[float]:
    """
    Генерация эмбеддинга для запроса пользователя с использованием OpenAI API.
    """
    url = 'https://api.openai.com/v1/embeddings'
    headers = {
        'Authorization': f'Bearer {openai.api_key}',
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

async def query_database(query_text: str) -> List[str]:
    """
    Поиск в векторной базе данных по эмбеддингу запроса и возвращение релевантной информации.
    """
    # Генерация эмбеддинга для запроса
    query_embedding = await generate_query_embedding(query_text)
    
    # Подключение к асинхронному клиенту ChromaDB
    client = await chromadb.AsyncHttpClient(host='localhost', port = 8000)
    
    try:
        # Получение коллекции 'chroma'
        collection = await client.get_collection(name='chroma')
    except chromadb.errors.InvalidCollectionException:
        print("Коллекция 'chroma' не найдена. Убедитесь, что база данных создана правильно.")
        return []
    
    # Выполнение запроса для нахождения наиболее похожих записей
    results = await collection.query(
        query_embeddings=[query_embedding],
        n_results=3
    )
    
    # Обработка и возврат результатов
    responses = []
    if results['documents']:
        for docs, metadatas in zip(results['documents'], results['metadatas']):
            for doc, metadata in zip(docs, metadatas):
                # Определение, является ли запись продуктом или FAQ
                if 'question' in metadata and 'answer' in metadata:
                    # Это запись из FAQ
                    response = f"Вопрос: {metadata['question']}\nОтвет: {metadata['answer']}"
                else:
                    # Это запись продукта
                    response = ''
                    for col in product_columns:
                        value = metadata.get(col, '')
                        if value:
                            response += f"{col}: {value}\n"
                    if not response:
                        response = doc  # Используем текст документа по умолчанию
                responses.append(response)
    else:
        responses.append('Извините, ответ не найден.')
    
    return responses

async def main():
    # Ввод запроса пользователя
    query_text =str(clean_text(input("Введите ваш вопрос: ")))
    responses = await query_database(query_text)
    print("\nОтветы:")
    for response in responses:
        print(response)
        print("-" * 50)

if __name__ == "__main__":
    asyncio.run(main())
