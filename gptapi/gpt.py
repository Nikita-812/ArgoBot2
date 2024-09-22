import os

from dotenv import load_dotenv
from langchain_community.vectorstores import Chroma
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI, OpenAIEmbeddings

load_dotenv()


def get_gpt_rag_answer(query):
    current_dir = os.path.dirname(os.path.abspath(__file__))
    persistent_directory = os.path.join(current_dir, "db", "chroma_db")

    # Define the embedding model
    embeddings = OpenAIEmbeddings(model="text-embedding-3-small")

    # Load the existing vector store with the embedding function
    db = Chroma(persist_directory=persistent_directory,
                embedding_function=embeddings)

    retriever = db.as_retriever(
        search_type="mmr",
        search_kwargs={"k": 1, "lambda_mult": 0.5},
    )
    relevant_docs = retriever.invoke(query)

    # Display the relevant results with metadata
    print("\n--- Relevant Documents ---")
    for i, doc in enumerate(relevant_docs, 1):
        print(f"Document {i}:\n{doc.page_content}\n")

    # Combine the query and the relevant document contents
    combined_input = (
            "Вот некоторые документы, которые могут помочь ответить на этот вопрос: "
            + query
            + "\n\nСоответствующие документы:\n"
            + "\n\n".join([doc.page_content for doc in relevant_docs])
            + "\n\nПросим дать ответ только на основании предоставленных документов, если в документе есть ссылка на продукт вставь ее в ответ с фразой 'более полную информацию вы можете получить здесь: '. Если тебя просят что-нибудь посоветовать, в конце ответа обязательно порекомендуй обратиться к врачу. Если документа нет, ответьте у меня нет информации об этом."
    )

    # Create a ChatOpenAI model
    model = ChatOpenAI(model="gpt-4o-mini", )

    # Define the messages for the model
    messages = [
        SystemMessage(
            content="Ты консультант по продукции компании Арго, отвечаешь только на вопросы связанные с Арго, в противном случае отвечаешь, что ты не запрограммирован отвечать на вопрос."),
        HumanMessage(content=combined_input),
    ]

    # Invoke the model with the combined input
    result = model.invoke(messages)

    # Display the full result and content only
    print("\n--- Generated Response ---")
    # print("Full result:")
    # print(result)
    print("Content only:")
    print(result.content)

    return result.content


if __name__ == '__main__':
    get_gpt_rag_answer('посоветуй какой-нибудь крем для кожи?')
