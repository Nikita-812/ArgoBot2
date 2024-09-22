import os

from langchain.text_splitter import CharacterTextSplitter
from langchain_community.document_loaders import TextLoader
from langchain_community.vectorstores import Chroma
from langchain_core.documents import Document
from langchain_openai import OpenAIEmbeddings
from dotenv import load_dotenv
import pandas as pd

load_dotenv()
print(os.getenv("OPENAI_API_KEY"))

# Define the directory containing the text file and the persistent directory

current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
file_path = os.path.join(current_dir, "data", "products.csv")
persistent_directory = os.path.join(current_dir, "gptapi", "db", "chroma_db")

# Check if the Chroma vector store already exists
if not os.path.exists(persistent_directory):
    print("Persistent directory does not exist. Initializing vector store...")

    # Ensure the text file exists
    if not os.path.exists(file_path):
        raise FileNotFoundError(
            f"The file {file_path} does not exist. Please check the path."
        )

    df = pd.read_csv(file_path, sep=';', encoding='')

    text_columns = [
        'GOODS_NAME', "GOODS_URL", 'GOODS_CONDITION', 'GOODS_ANTY_CONDITION',
        'GOODS_RECOMMENDATION', 'GOODS_PROPERTY'
    ]

    df['combined_text'] = df[text_columns].apply(lambda row: ' '.join(row.dropna()), axis=1)
    documents = df['combined_text']
    documents = [Document(page_content=text) for text in df['combined_text'].tolist()]

    # Split the document into chunks
    text_splitter = CharacterTextSplitter(chunk_size=1000, chunk_overlap=200, separator='\t')
    docs = text_splitter.split_documents(documents)

    # Create embeddings
    print("\n--- Creating embeddings ---")
    embeddings = OpenAIEmbeddings(
        model="text-embedding-3-small"
    )  # Update to a valid embedding model if needed
    print("\n--- Finished creating embeddings ---")

    # Create the vector store and persist it automatically
    print("\n--- Creating vector store ---")
    db = Chroma.from_documents(
        docs, embeddings, persist_directory=persistent_directory)
    print("\n--- Finished creating vector store ---")
    print("\n--- Document Chunks Information ---")
    print(f"Number of document chunks: {len(docs)}")
    # print(f"Sample chunk:\n{docs[0].page_content}\n")

else:
    print("Vector store already exists. No need to initialize.")
