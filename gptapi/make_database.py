import os
import re
import json
import asyncio
import aiohttp
import aiofiles
import pandas as pd
from io import StringIO
from dotenv import load_dotenv
from typing import List, Tuple
import nltk
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
import openai
import chromadb
import logging

# Загрузка переменных окружения и API ключа OpenAI
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")
if not openai.api_key:
    raise ValueError("API ключ OpenAI не найден. Пожалуйста, установите переменную окружения OPENAI_API_KEY.")

# Настройка логирования
logging.basicConfig(level=logging.INFO)

# Загрузка необходимых ресурсов NLTK
nltk.download('stopwords')
nltk.download('punkt_tab')
nltk.download('wordnet')

# Инициализация стоп-слов и лемматизатора
stop_words = set(stopwords.words('russian'))
lemmatizer = WordNetLemmatizer()

# Список текстовых колонок для извлечения из CSV файлов
text_columns = [
    'GOODS_NAME', 'GOODS_DESCRIPTION'  # Предполагая, что 'GOODS_DESCRIPTION' содержит описание товара
]

# Папка с данными
data_folder = './rag_data/'  # Замените на путь к вашей папке с данными

def clean_text(text: str) -> str:
    """
    Очищает и нормализует текст: удаляет HTML теги, специальные символы,
    приводит к нижнему регистру, удаляет стоп-слова и выполняет лемматизацию.
    """
    if not isinstance(text, str):
        return ''
    # Удаление HTML тегов
    text = re.sub(r'<[^>]+>', '', text)
    # Приведение к нижнему регистру
    text = text.lower()
    # Удаление специальных символов и цифр
    text = re.sub(r'[^\w\s]', '', text)
    # Токенизация
    tokens = nltk.word_tokenize(text)
    # Удаление стоп-слов и лемматизация
    tokens = [lemmatizer.lemmatize(word) for word in tokens if word not in stop_words]
    return ' '.join(tokens).strip()

def chunk_text(text: str, max_tokens: int = 500) -> List[str]:
    """
    Разбивает текст на чанки, не превышающие max_tokens по количеству слов.
    """
    sentences = re.split(r'(?<=[.!?]) +', text)
    chunks = []
    current_chunk = ''
    for sentence in sentences:
        if len((current_chunk + ' ' + sentence).split()) <= max_tokens:
            current_chunk += ' ' + sentence
        else:
            chunks.append(current_chunk.strip())
            current_chunk = sentence
    if current_chunk:
        chunks.append(current_chunk.strip())
    return chunks

async def load_and_preprocess_csv(csv_file: str) -> Tuple[List[str], List[dict]]:
    """
    Асинхронная загрузка и предобработка данных из CSV файла.
    """
    async with aiofiles.open(csv_file, mode='r', encoding='utf-8') as f:
        content = await f.read()
    
    # Чтение CSV файла
    df = pd.read_csv(StringIO(content), sep='\t')

    # Проверка наличия необходимых колонок
    for col in text_columns:
        if col not in df.columns:
            df[col] = ''

    # Очистка текстовых колонок
    for col in text_columns:
        df[col] = df[col].apply(clean_text)

    # Объединение текстовых колонок
    df['combined_text'] = df[text_columns].fillna('').agg(' '.join, axis=1)

    texts = []
    metadatas = []

    # Определение необходимых метаданных
    metadata_columns = ['GOODS_NAME', 'CATEGORY', 'GOODS_URL']

    for _, row in df.iterrows():
        text_chunks = chunk_text(row['combined_text'])
        for idx, chunk in enumerate(text_chunks):
            texts.append(chunk)
            metadatas.append({
                'goods_name': row.get('GOODS_NAME', ''),
                'category': row.get('CATEGORY', ''),
                'goods_url': row.get('GOODS_URL', ''),
                'chunk_index': idx
            })

    return texts, metadatas

async def load_and_preprocess_json(json_file: str) -> Tuple[List[str], List[dict]]:
    """
    Асинхронная загрузка данных из JSON файла и возвращение текстов и метаданных.
    """
    async with aiofiles.open(json_file, mode='r', encoding='utf-8') as f:
        content = await f.read()
    data = json.loads(content)
    texts = []
    metadatas = []
    for entry in data:
        question = clean_text(entry.get('text', ''))
        answer = clean_text(entry.get('response', ''))
        combined_text = f"Вопрос: {question}\nОтвет: {answer}"
        text_chunks = chunk_text(combined_text)
        for idx, chunk in enumerate(text_chunks):
            texts.append(chunk)
            metadatas.append({
                'question': question,
                'answer': answer,
                'chunk_index': idx
            })
    return texts, metadatas

async def fetch_embedding(session, url, headers, data, max_retries=5):
    """
    Асинхронная функция для выполнения API запроса эмбеддинга с обработкой ошибок и повторными попытками.
    """
    for attempt in range(max_retries):
        try:
            async with session.post(url, headers=headers, json=data) as resp:
                response = await resp.json()
                if resp.status == 200:
                    return response
                else:
                    logging.error(f"Ошибка {resp.status}: {response}")
        except Exception as e:
            logging.error(f"Исключение при попытке {attempt+1}: {e}")
        wait_time = 2 ** attempt
        await asyncio.sleep(wait_time)
    raise Exception("Превышено количество попыток для fetch_embedding")

async def generate_embeddings(texts: List[str]) -> List[List[float]]:
    """
    Генерация эмбеддингов для списка текстов с использованием OpenAI API.
    Работает пакетами для ускорения обработки и включает обработку ошибок.
    """
    embeddings = []
    batch_size = 64  # Оптимальный размер пакета (можно настроить)
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

async def process_file(file_path: str) -> Tuple[List[str], List[dict]]:
    """
    Асинхронная обработка отдельного файла.
    """
    if file_path.endswith('.csv'):
        return await load_and_preprocess_csv(file_path)
    elif file_path.endswith('.json'):
        return await load_and_preprocess_json(file_path)
    else:
        return [], []

async def process_files_in_folder(folder: str) -> Tuple[List[str], List[dict]]:
    """
    Асинхронная обработка всех файлов в указанной папке, возвращает тексты и метаданные.
    """
    tasks = []
    for root, _, files in os.walk(folder):
        for file in files:
            file_path = os.path.join(root, file)
            tasks.append(process_file(file_path))
    results = await asyncio.gather(*tasks)
    texts, metadatas = [], []
    for res_texts, res_metadatas in results:
        texts.extend(res_texts)
        metadatas.extend(res_metadatas)
    return texts, metadatas

async def main():
    # Загрузка и предобработка всех данных из папки
    texts, metadatas = await process_files_in_folder(data_folder)

    # Проверка соответствия количества текстов и метаданных
    assert len(texts) == len(metadatas), "Количество текстов и метаданных не совпадает."

    # Генерация эмбеддингов для всех текстов
    embeddings = await generate_embeddings(texts)

    # Проверка соответствия количества текстов и эмбеддингов
    assert len(texts) == len(embeddings), "Количество текстов и эмбеддингов не совпадает."

    # Подключение к клиенту ChromaDB
    client = chromadb.Client()  # Используем синхронный клиент для простоты

    collection_name = 'chroma'

    # Проверка наличия коллекции и создание при необходимости
    if collection_name in [col.name for col in client.list_collections()]:
        collection = client.get_collection(name=collection_name)
        logging.info(f"Коллекция '{collection_name}' успешно найдена.")
    else:
        logging.info(f"Коллекция '{collection_name}' не найдена. Создаём новую коллекцию.")
        collection = client.create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"}
        )
        logging.info(f"Коллекция '{collection_name}' успешно создана.")

    # Добавление эмбеддингов и метаданных в коллекцию
    collection.add(
        embeddings=embeddings,
        documents=texts,
        metadatas=metadatas,
        ids=[str(i) for i in range(len(texts))]
    )

    logging.info("Векторная база данных успешно создана и сохранена.")

if __name__ == "__main__":
    asyncio.run(main())

