import asyncio
import aiohttp
import openai
import chromadb
from typing import List
import os
from dotenv import load_dotenv

load_dotenv()

openai.api_key = os.getenv("OPENAI_API_KEY")

# Columns to extract from product metadata
product_columns = [
    'GOODS_NAME', 'GOODS_URL', 'GOODS_PV', 'GOODS_CONDITION', 'GOODS_ANTY_CONDITION', 'GOODS_RECOMMENDATION',
    'GOODS_PROPERTY', 'GOODS_COMPOSITION', 'GOODS_PACKING', 'GOODS_WEIGHT', 'CATALOG_NAME', 'CATALOG_FULL_NAME',
    'CATEGORY'
]

# Columns to extract from FAQ metadata
faq_columns = [
    'question', 'answer'
]


async def generate_query_embedding(query_text: str) -> List[float]:
    """
    Generates an embedding for the user's query text using the OpenAI API.
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


async def query_database(query_text: str) -> str:
    """
    Queries the vector database using the query embedding
    and returns the most relevant information.
    """
    # Generate embedding for the query
    query_embedding = await generate_query_embedding(query_text)
    persist_directory = '/home/nik/PycharmProjects/ArgoBot2/gptapi/chroma_db'
    client = chromadb.PersistentClient(path=persist_directory)
    try:
        collection = client.get_collection(name='argo_collection')
    except chromadb.errors.InvalidCollectionException:
        print("Collection 'argo_collection' not found. Ensure the database was created correctly.")
        return ''
    # Perform the query to find the most similar entries
    def blocking_query():
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=3
        )
        return results
    # Execute the blocking query in a separate thread
    results = await asyncio.to_thread(blocking_query)
    # Process and display the result
    if results['documents']:
        # Extract the most relevant document and its metadata
        document = results['documents'][0][0]
        metadata = results['metadatas'][0][0]
        # Determine if the metadata is from a product or FAQ entry
        if 'question' in metadata and 'answer' in metadata:
            # It's an FAQ entry
            response = f"Вопрос: {metadata['question']}\nОтвет: {metadata['answer']}"
        else:
            # It's a product entry
            response = ''
            for col in product_columns:
                value = metadata.get(col, '')
                if value:
                    response += f"{col}: {value}\n"
            if not response:
                response = document  # Fallback to the document text
        return response
    else:
        return 'Извините, ответ не найден.'


async def main():
    # User query
    query_text = input("Введите ваш вопрос: ")
    response = await query_database(query_text)
    print("\nОтвет:")
    print(response)


if __name__ == "__main__":
    asyncio.run(main())
