import psycopg
from psycopg.rows import dict_row
import asyncio

host = '127.0.0.1'
user = 'postgres'
password = ''
port = 5432

# Асинхронное подключение к базе данных PostgreSQL
async def connect_db():
    try:
        conn = await psycopg.AsyncConnection.connect(

            user=user,
            password=password,
            host=host,
            port="5432"
        )
        return conn
    except Exception as e:
        print(f"Ошибка подключения к базе данных: {e}")
        return None

# Создание таблицы users с уникальным ограничением на поле api_id
async def create_users_table():
    conn = await connect_db()
    if conn:
        try:
            async with conn.cursor() as cur:
                await cur.execute('''
                    CREATE TABLE IF NOT EXISTS users (
                        id INTEGER UNIQUE NOT NULL,
                        api_id INTEGER UNIQUE NOT NULL,
                        name TEXT NOT NULL,
                        birth_date TEXT NOT NULL,
                        email TEXT NOT NULL,
                        phone_number TEXT NOT NULL
                    )
                ''')
                await conn.commit()
                print("Таблица users создана или уже существует.")
        except Exception as e:
            print(f"Ошибка при создании таблицы: {e}")
        finally:
            await conn.close()

# Регистрация пользователя
async def bd_reg_participant(user_data):
    conn = await connect_db()
    if conn:
        try:
            async with conn.cursor() as cur:
                query = '''
                    INSERT INTO users (id, api_id, name, birth_date, email, phone_number)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    ON CONFLICT (api_id) DO NOTHING
                '''
                await cur.execute(query, (user_data['id'], user_data['api_id'], user_data['name'], user_data['birthDate'],
                                  user_data['email'], user_data['mobilePhone']))
                await conn.commit()
                print("Пользователь зарегистрирован.")
        except Exception as e:
            print(f"Ошибка при регистрации пользователя: {e}")
        finally:
            await conn.close()

# Получение пользователя по номеру телефона
async def bd_get_user_by_phone(phone_number):
    conn = await connect_db()
    if conn:
        try:
            async with conn.cursor(row_factory=dict_row) as cur:
                query = 'SELECT * FROM users WHERE phone_number = %s'
                await cur.execute(query, (phone_number,))
                user = await cur.fetchone()
                return user
        except Exception as e:
            print(f"Ошибка при получении пользователя по номеру телефона: {e}")
        finally:
            await conn.close()

# Получение пользователя по идентификатору
async def bd_get_user_by_id(user_id):
    conn = await connect_db()
    if conn:
        try:
            async with conn.cursor(row_factory=dict_row) as cur:
                query = "SELECT * FROM users WHERE id = %s"
                await cur.execute(query, (user_id,))
                user = await cur.fetchone()
                return user
        except Exception as e:
            print(f"Ошибка при получении пользователя по ID: {e}")
        finally:
            await conn.close()


# Получение пользователя по Telegram ID (api_id)
async def bd_get_user_by_tg_id(api_id):
    conn = await connect_db()
    if conn:
        try:
            async with conn.cursor(row_factory=dict_row) as cur:
                query = 'SELECT * FROM users WHERE api_id = %s'
                await cur.execute(query, (api_id,))
                user = await cur.fetchone()
                return user
        except Exception as e:
            print(f"Ошибка при получении пользователя по API ID: {e}")
        finally:
            await conn.close()

# Пример вызова функций
async def main():
    await create_users_table()
    #await bd_reg_participant({'id': 13, 'api_id': 1005930271, 'name': "Nikita", "birthDate": "2005-08-19", "email": "nikitospashynin@gmail.com", "mobilePhone": "89231416154"})
    z = await bd_get_user_by_id(13)
    print(z)

if __name__ == '__main__':
    asyncio.run(main())