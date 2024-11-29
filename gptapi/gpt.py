from openai import AsyncOpenAI
import os
import asyncio
from get_product_context import query_database

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
            + "\n\nОтвечай только на основании предоставленных документов. Если в документе указана ссылка на продукт, вставь её в ответ с фразой: Более полную информацию вы можете получить здесь: [ссылка].Если запрашивается рекомендация, в конце ответа обязательно добавляй: Для более точной информации рекомендуется обратиться к врачу.Если документа по вопросу нет, отвечай: У меня нет информации об этом. Если находится несколько подходящих продуктов, выбери наиболее подходящие и выведи их списком с указанием ссылок."
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
