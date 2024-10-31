from openai import AsyncOpenAI
import os
import asyncio
from .get_product_context import query_database
aclient = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))



async def generate_response(user_query: str) -> str:
    """
    Функция для генерации ответа ChatGPT на основе запроса пользователя.
    """
    combined_input = (
            "Вот некоторые документы, которые могут помочь ответить на этот вопрос: "
            + user_query
            + "\n\nСоответствующие документы:\n"
            + "\n\n" + ''.join(await query_database(user_query))
            + "\n\nПросим дать ответ только на основании предоставленных документов, если в документе есть ссылка на продукт вставь ее в ответ с фразой 'более полную информацию вы можете получить здесь: '. Если тебя просят что-нибудь посоветовать, продуктов, в конце ответа обязательно порекомендуй обратиться к врачу. Если документа нет, ответьте у меня нет информации об этом. Если ты получаешь несколько подходящих продуктов, выбери из них наиболее подходящие и выведи списком с ссылками. Если нужно дать ссылку на основной сайт компании то вот она: https://argo.company."
    )

    try:
        response = await aclient.chat.completions.create(model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "Ты консультант по продукции компании Арго, отвечаешь только по теме продукции компании."},
            {"role": "user", "content": combined_input}
        ])
        # Получаем контент сообщения
        gpt_response = response.choices[0].message.content.strip()
        return gpt_response
    except Exception as e:
        return f"Произошла ошибка при обращении к модели: {e}"


async def main():
    user_query = input("user's query: ")
    assistant_response = await generate_response(user_query)
    print(assistant_response)


if __name__ == "__main__":
    asyncio.run(main())
