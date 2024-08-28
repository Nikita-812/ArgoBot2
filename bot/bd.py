import aiosqlite
import asyncio


async def bd_reg_participant(user_data):
    async with aiosqlite.connect('sql_bd.db') as connection:
        await connection.execute('''INSERT INTO users (id, api_id, name, birth_date, email, phone_number)
                                    VALUES (?, ?, ?, ?, ?, ?)''',
                                 (user_data['id'], user_data['api_id'], user_data['name'], user_data['birthDate'],
                                  user_data['email'], user_data['mobilePhone']))
        await connection.commit()  # Commit the transaction to save the changes
        print("User registered successfully")


async def bd_get_user_by_phone(phone_number: str):
    async with aiosqlite.connect('sql_bd.db') as db:
        cursor = await db.execute('''SELECT id, name, birth_date, email, phone_number 
                                     FROM users WHERE phone_number = ?''', (phone_number,))
        user = await cursor.fetchone()

        if user:
            # Map the result to a dictionary
            user_data = {
                'id': user[0],
                'name': user[1],
                'birth_date': user[2],
                'email': user[3],
                'phone_number': user[4]
            }
            return user_data
        else:
            return None  # Return None if no user was found with the given phone number


async def bd_get_user_by_id(id: int):
    async with aiosqlite.connect('sql_bd.db') as db:
        cursor = await db.execute('''SELECT api_id, name, birth_date, email, phone_number 
                                     FROM users WHERE api_id = ?''', (id,))
        user = await cursor.fetchone()
        if user:
            # Map the result to a dictionary
            user_data = {
                'api_id': user[0],
                'name': user[1],
                'birth_date': user[2],
                'email': user[3],
                'phone_number': user[4]
            }
            return user_data
        else:
            return None  # Return None if no user was found with the given phone number


async def on_startup():
    async with aiosqlite.connect('sql_bd.db') as db:
        await db.execute('''CREATE TABLE IF NOT EXISTS users (
                              id INTEGER PRIMARY KEY AUTOINCREMENT,
                              api_id INTEGER UNIQUE NOT NULL,
                              name TEXT NOT NULL,
                              birth_date TEXT NOT NULL,
                              email TEXT NOT NULL,
                              phone_number TEXT NOT NULL
                            )''')
        await db.commit()  # Commit the transaction to create the table
        print("Database initialized")


async def bd_get_user_by_tg_id(tg_id: int):
    async with aiosqlite.connect('sql_bd.db') as db:
        cursor = await db.execute('''SELECT id, api_id, name, birth_date, email, phone_number 
                                     FROM users WHERE api_id = ?''', (tg_id,))
        user = await cursor.fetchone()
        if user:
            user_data = {
                'id': user[0],
                'tg_id': user[1],
                'name': user[2],
                'birth_date': user[3],
                'email': user[4],
                'phone_number': user[5]
            }
            return user_data['id']
        else:
            return None


async def main():
    await on_startup()
    await bd_reg_participant(user_data={
        'id': 3678,
        'api_id': 13,
        'name': 'nik',
        'birthDate': '2022-02-21',
        'mobilePhone': '+1555555555',
        'email': 'nikitsoasphynin#gmai.com'
    })
    data = await bd_get_user_by_id(3678)
    print(data)


if __name__ == '__main__':
    asyncio.run(main())  # This runs the main() coroutine, which handles startup and registration
