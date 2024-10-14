import pandas as pd
import asyncio
import aiohttp
import aiofiles
import re
import openai
import chromadb
from typing import List, Tuple
import os
from dotenv import load_dotenv
import json

# Load environment variables
load_dotenv()
# Set OpenAI API key
openai.api_key = os.getenv("OPENAI_API_KEY")

# Text columns to extract from CSV files
text_columns = [
    'GOODS_NAME', 'GOODS_URL', 'GOODS_PV', 'GOODS_CONDITION', 'GOODS_ANTY_CONDITION', 'GOODS_RECOMMENDATION',
    'GOODS_PROPERTY', 'GOODS_COMPOSITION', 'GOODS_PACKING', 'GOODS_WEIGHT', 'CATALOG_NAME', 'CATALOG_FULL_NAME',
    'CATEGORY'
]

# Folder containing data files
data_folder = '/home/nik/PycharmProjects/ArgoBot2/gptapi/rag_data'


def clean_text(text: str) -> str:
    """
    Cleans text by removing HTML tags and unnecessary characters while preserving URLs.
    """
    if not isinstance(text, str):
        return ''
    # Remove HTML tags
    text = re.sub(r'<[^>]+>', '', text)
    # Remove unwanted characters except those used in URLs
    text = re.sub(r'[^\w\s:/\.-]', '', text)
    return text.strip()


async def load_and_preprocess_csv(csv_file: str) -> Tuple[List[str], List[dict]]:
    """
    Asynchronously loads and preprocesses data from a CSV file.
    Cleans text columns and combines them into a single text field.
    """
    async with aiofiles.open(csv_file, mode='r', encoding='utf-8') as f:
        content = await f.read()
    from io import StringIO
    df = pd.read_csv(StringIO(content))
    # Clean text columns
    for col in text_columns:
        if col in df.columns:
            df[col] = df[col].apply(clean_text)
        else:
            df[col] = ''
    # Combine all text columns into a single text field
    df['combined_text'] = df[text_columns].fillna('').agg(' '.join, axis=1)
    texts = df['combined_text'].tolist()
    metadatas = df.to_dict('records')
    return texts, metadatas


async def load_and_preprocess_json(json_file: str) -> Tuple[List[str], List[dict]]:
    """
    Asynchronously loads data from a JSON file and returns texts and metadata.
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

async def generate_embeddings(texts: List[str]) -> List[List[float]]:
    """
    Generates embeddings for a list of texts using the OpenAI API.
    Works in batches for faster processing.
    """
    embeddings = []
    batch_size = 16  # Batch size for API requests
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
        # Execute all requests asynchronously
        results = await asyncio.gather(*tasks)
        # Extract embeddings from responses
        for result in results:
            for item in result['data']:
                embeddings.append(item['embedding'])
    return embeddings


async def fetch_embedding(session, url, headers, data):
    """
    Asynchronous function to perform the embedding API request.
    """
    async with session.post(url, headers=headers, json=data) as resp:
        response = await resp.json()
        return response


async def process_files_in_folder(folder: str) -> Tuple[List[str], List[dict]]:
    """
    Asynchronously processes all files in the specified folder and returns texts and metadata.
    """
    texts = []
    metadatas = []

    for root, _, files in os.walk(folder):
        for file in files:
            file_path = os.path.join(root, file)
            if file.endswith('.csv'):
                # Process CSV file
                csv_texts, csv_metadatas = await load_and_preprocess_csv(file_path)
                texts.extend(csv_texts)
                metadatas.extend(csv_metadatas)
            elif file.endswith('.json'):
                # Process JSON file
                json_texts, json_metadatas = await load_and_preprocess_json(file_path)
                texts.extend(json_texts)
                metadatas.extend(json_metadatas)

    return texts, metadatas


async def main():
    # Load and preprocess all data from the folder
    texts, metadatas = await process_files_in_folder(data_folder)

    # Generate embeddings for all texts
    embeddings = await generate_embeddings(texts)

    # Initialize ChromaDB client with a directory to persist data
    persist_directory = '/home/nik/PycharmProjects/ArgoBot2/gptapi/chroma_db'
    client = chromadb.PersistentClient(path=persist_directory)

    # Create or get the 'products' collection
    collection = client.get_or_create_collection(name='argo_collection')

    # Add embeddings and metadata to the collection
    def blocking_add():
        collection.add(
            embeddings=embeddings,
            documents=texts,
            metadatas=metadatas,
            ids=[str(i) for i in range(len(texts))]
        )

    # Asynchronous call to add data
    await asyncio.to_thread(blocking_add)

    print("Vector database successfully created and saved.")


if __name__ == "__main__":
    asyncio.run(main())
