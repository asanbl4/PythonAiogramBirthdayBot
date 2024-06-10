from aiogram import Bot, Dispatcher
from aiogram.filters import Command, CommandStart
from aiogram.types import Message, FSInputFile
import asyncpg
import asyncio

import filters
import secret
import messages
import datetime

DB_USER = secret.DB_USER
DB_PASSWORD = secret.DB_PASSWORD
DB_NAME = secret.DB_NAME
DB_HOST = secret.DB_HOST
DB_PORT = secret.DB_PORT
API_TOKEN = secret.API_TOKEN

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

db_con_pool = None


async def init_db():
    global db_con_pool
    db_con_pool = await asyncpg.create_pool(
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME,
        host=DB_HOST,
        port=DB_PORT,
    )


@dp.message(CommandStart())
async def send_welcome(message: Message):
    await message.answer(f"Hi, {message.from_user.first_name}! This is the welcome message from aiogram!")


@dp.message(Command('username'))
async def send_username(message: Message):
    await message.answer(f'@{message.from_user.username}')


# example@gmail.com
@dp.message(filters.EmailFilter())
async def show_student_info(message: Message):
    async with db_con_pool.acquire() as connection:
        email = message.text
        student = await connection.fetchrow("SELECT * FROM students WHERE email=$1", email)
        if student:
            await send_bd_message(message, student)
        else:
            await message.answer(f'No students with handle: {email} found in database')


@dp.message(Command('today'))
async def show_today_birthday(message: Message):
    async with db_con_pool.acquire() as connection:
        students = await connection.fetch("SELECT * FROM students")
        for student in students:
            if student['birthday']:
                if datetime.date.today().day == student['birthday'].day and datetime.date.today().month == student[
                    'birthday'].month:
                    await send_bd_message(message, student)
        await bot.send_message(message.chat.id, "Request done")


async def send_bd_message(message, student):
    message_text = await messages.birthday_message(student['first_name'])
    bd_image = FSInputFile('imgs/bd_image.jpg')
    await bot.send_photo(message.chat.id, bd_image, caption=message_text)
    await bot.send_message(message.chat.id,
                           f"{student['first_name']} {student['last_name']}\n@{student['handle']}")


async def main():
    await init_db()
    await dp.start_polling(bot)


if __name__ == '__main__':
    asyncio.run(main())
