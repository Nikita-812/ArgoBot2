import pandas as pd
from io import StringIO
import asyncio
import aiohttp
import aiofiles
import re
import openai
from chromadb.config import Settings
import chromadb
from typing import List, Tuple
import unicodedata
from nltk.tokenize import sent_tokenize, word_tokenize
import os
from dotenv import load_dotenv
import json
import unicodedata
import spacy
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from nltk.stem import WordNetLemmatizer
import nltk

# Загрузка переменных окружения
load_dotenv()
# Установка API ключа OpenAI
openai.api_key = os.getenv("OPENAI_API_KEY")

# Список текстовых колонок для извлечения из CSV файлов
text_columns = [
    'GOODS_NAME', 'GOODS_URL', 'GOODS_PV', 'GOODS_CONDITION', 'GOODS_ANTY_CONDITION', 'GOODS_RECOMMENDATION',
    'GOODS_PROPERTY', 'GOODS_COMPOSITION', 'GOODS_PACKING', 'GOODS_WEIGHT', 'CATALOG_NAME', 'CATALOG_FULL_NAME',
    'CATEGORY'
]

# Папка с данными
data_folder = './rag_data/'  # Замените на путь к вашей папке с данными

nltk.download('punkt')
nltk.download('wordnet')
nltk.download('stopwords')

# Загрузка модели Spacy
nlp = spacy.load("ru_core_news_md") 

def clean_text(text: str) -> str:
    """
    Полностью подготавливает текст для использования в RAG системе.
    Включает очистку от HTML-тегов, нормализацию, удаление стоп-слов, извлечение сущностей, лемматизацию и другие преобразования.
    """
    if not isinstance(text, str):
        return ''

    # Удаление HTML-тегов
    text = re.sub(r'<[^>]+>', '', text)

    # Декодирование HTML сущностей
    try:
        import html
        text = html.unescape(text)
    except ImportError:
        pass

    # Приведение текста к Unicode NFC для стандартизации
    text = unicodedata.normalize('NFC', text)

    # Удаление избыточных пробелов
    text = re.sub(r'\s+', ' ', text)

    # Приведение к нижнему регистру
    text = text.lower().strip()

    # Удаление всех символов, кроме букв, цифр и базовой пунктуации
    text = re.sub(r'[^\w\s.,!?\'"]+', '', text)

    # Токенизация
    tokens = word_tokenize(text)

    # Удаление стоп-слов
    stop_words = set(stopwords.words('russian'))
    tokens = [word for word in tokens if word not in stop_words]

    # Лемматизация с использованием NLTK
    lemmatizer = WordNetLemmatizer()
    tokens = [lemmatizer.lemmatize(word) for word in tokens]

    # Сборка текста обратно
    text = ' '.join(tokens)

    # Обработка текста с помощью Spacy
    doc = nlp(text)

    # Извлечение важных сущностей (например, DRUG, ORG, MONEY)
    important_entities = {ent.text: ent.label_ for ent in doc.ents if ent.label_ in {"DRUG", "ORG", "MONEY"}}

    # Дополнение текста извлеченными сущностями
    entity_text = ' '.join(important_entities.keys())
    text = f"{text} {entity_text}"

    return text

def create_chunks_nltk(text: str, max_tokens: int = 200, overlap: int = 0) -> List[str]:
    """
    Разбивает текст на чанки заданного размера с использованием NLTK.

    Args:
        text (str): Исходный текст для разбиения.
        max_tokens (int): Максимальное количество токенов в одном чанке.
        overlap (int): Количество перекрывающихся токенов между чанками.

    Returns:
        List[str]: Список чанков текста.
    """
    # Токенизация текста на предложения
    sentences = sent_tokenize(text)

    # Формируем чанки
    chunks = []
    current_chunk = []
    current_token_count = 0

    for sentence in sentences:
        # Токенизация предложения на слова
        sentence_tokens = word_tokenize(sentence)
        token_count = len(sentence_tokens)

        # Проверяем, поместится ли предложение в текущий чанк
        if current_token_count + token_count <= max_tokens:
            current_chunk.append(sentence)
            current_token_count += token_count
        else:
            # Завершаем текущий чанк и создаём новый
            chunks.append(" ".join(current_chunk))
            
            # Добавляем предложение в новый чанк, учитывая overlap
            if overlap > 0:
                overlap_tokens = current_chunk[-overlap:] if current_chunk else []
                current_chunk = overlap_tokens + [sentence]
            else:
                current_chunk = [sentence]
            
            current_token_count = token_count

    # Добавляем последний чанк
    if current_chunk:
        chunks.append(" ".join(current_chunk))

    return chunks

async def load_and_preprocess_csv(csv_file: str) -> Tuple[List[str], List[dict]]:
    """
    Асинхронная загрузка и предобработка данных из CSV файла.
    Очищает текстовые колонки и объединяет их в одно текстовое поле.
    
    Parameters:
    - csv_file: путь к CSV файлу
    - text_columns: список колонок с текстом для очистки и объединения
    
    Returns:
    - texts: список строк с объединенным текстом из указанных колонок
    - metadatas: список словарей, содержащий записи из DataFrame
    """
    async with aiofiles.open(csv_file, mode='r', encoding='utf-8') as f:
        content = await f.read()
    
    # Чтение CSV файла
    df = pd.read_csv(StringIO(content), sep = '\t')

    # Очистка и объединение текстовых колонок
    for col in text_columns:
        if col in df.columns:
            df[col] = df[col].apply(clean_text)
        else:
            # Если колонки нет, добавляем пустую колонку
            df[col] = ''
    
    # Объединение всех текстовых колонок в одно поле
    df['combined_text'] = df[text_columns].fillna('').agg(' '.join, axis=1)

    # Преобразуем в нужные форматы
    texts = df['combined_text'].tolist()
    metadatas = df.to_dict('records')

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
        texts.append(combined_text)
        metadatas.append({
            'question': question,
            'answer': answer
        })
    return texts, metadatas


async def load_and_preprocess_txt(txt_file: str, max_tokens: int = 50, overlap: int = 20) -> Tuple[List[str], List[dict]]:
    """
    Асинхронная загрузка текста из файла, разбиение на чанки и создание метаданных.

    Args:
        txt_file (str): Путь к текстовому файлу.
        max_tokens (int): Максимальное количество токенов в одном чанке.
        overlap (int): Количество перекрывающихся предложений между чанками.

    Returns:
        Tuple[List[str], List[dict]]: Список чанков текста и метаданные.
    """
    # Асинхронное чтение текста из файла
    async with aiofiles.open(txt_file, mode='r', encoding='utf-8') as f:
        content = await f.read()
    
    print("txt file open")
    # Разделение текста на чанки
    chunks = create_chunks_nltk(content, max_tokens=max_tokens, overlap=overlap)
    print('chunks cretaed')
    # Создание метаданных
    metadatas = [
        {
            'chunk_index': idx,
            'chunk_text': chunk,
            'start_token': sum(len(word_tokenize(chunks[i])) for i in range(idx)),
            'end_token': sum(len(word_tokenize(chunks[i])) for i in range(idx + 1))
        }
        for idx, chunk in enumerate(chunks)
    ]
    print('meatadatas created')
    return chunks, metadatas

async def generate_embeddings(texts: List[str]) -> List[List[float]]:
    """
    Генерация эмбеддингов для списка текстов с использованием OpenAI API.
    Работает пакетами для ускорения обработки.
    """
    embeddings = []
    batch_size = 16  # Размер пакета для API запросов
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
    Асинхронная функция для выполнения API запроса эмбеддинга.
    """
    async with session.post(url, headers=headers, json=data) as resp:
        response = await resp.json()
        return response

async def process_files_in_folder(folder: str) -> Tuple[List[str], List[dict]]:
    """
    Асинхронная обработка всех файлов в указанной папке, возвращает тексты и метаданные.
    """
    texts = []
    metadatas = []

    for root, _, files in os.walk(folder):
        for file in files:
            file_path = os.path.join(root, file)
            if file.endswith('.csv'):
                # Обработка CSV файла
                csv_texts, csv_metadatas = await load_and_preprocess_csv(file_path)
                texts.extend(csv_texts)
                metadatas.extend(csv_metadatas)
            elif file.endswith('.json'):
                # Обработка JSON файла
                json_texts, json_metadatas = await load_and_preprocess_json(file_path)
                texts.extend(json_texts)
                metadatas.extend(json_metadatas)
            elif file.endswith(".txt"):
                text_texts, text_metadatas = await  load_and_preprocess_txt(file_path)
                texts.extend(text_texts)
                metadatas.extend(text_metadatas)

    return texts, metadatas

async def main():
    # Загрузка и предобработка всех данных из папки
    texts, metadatas = await process_files_in_folder(data_folder)
    print("все файлы обработаны")
    # Генерация эмбеддингов для всех текстов
    embeddings = await generate_embeddings(texts)
    print("запрос к openAI прошел")
    # Подключение к асинхронному клиенту ChromaDB
    client = await chromadb.AsyncHttpClient(host='localhost', port = 8000)

    try:
        # Попытка получить коллекцию 'chroma'
        collection = await client.get_collection(name='chroma')
        print("Коллекция 'chroma' успешно найдена.")
    except chromadb.errors.InvalidCollectionException:
        # Если коллекция не найдена, создаём её
        print("Коллекция 'chroma' не найдена. Создаём новую коллекцию.")
        collection = await client.create_collection(name='chroma')
        print("Коллекция 'chroma' успешно создана.")

    # Добавление эмбеддингов и метаданных в коллекцию
    await collection.add(
        embeddings=embeddings,
        documents=texts,
        metadatas=metadatas,
        ids=[str(i) for i in range(len(texts))]
    )

    print("Векторная база данных успешно создана и сохранена.")

if __name__ == "__main__":
    asyncio.run(main())
