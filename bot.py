import os
from typing import Any

import asyncpg
import asyncio
from aiogram import Bot, Dispatcher
from aiogram.filters import Command, CommandStart
from aiogram.types import Message, FSInputFile
from dotenv import load_dotenv
import datetime
from apscheduler.schedulers.asyncio import AsyncIOScheduler

import filters
import messages

load_dotenv()

DB_USER = os.environ["DB_USER"]
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_NAME = os.getenv("DB_NAME")
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
API_TOKEN = os.getenv("API_TOKEN")

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
        is_birthday = False
        for student in students:
            if student['birthday']:
                if datetime.date.today().day == student['birthday'].day and datetime.date.today().month == student[
                    'birthday'].month:
                    is_birthday = True
                    await send_bd_message(message, student)
        if not is_birthday:
            await bot.send_message(message.chat.id, "No students with birthday today")


async def send_bd_message(message: Message, student: dict[str: Any]):
    message_text = await messages.birthday_message(student['first_name'])
    bd_image = FSInputFile('imgs/bd_image.jpg')
    await bot.send_photo(message.chat.id, bd_image, caption=message_text)
    await bot.send_message(message.chat.id,
                           f"{student['first_name']} {student['last_name']}\n@{student['handle']}")


async def get_user_id(username: str) -> int:
    user = await bot.get_chat(username)
    return user.id


async def send_bd_message_auto(student: dict[str: Any], user_id: int):
    message_text = await messages.birthday_message(student['first_name'])
    bd_image = FSInputFile('imgs/bd_image.jpg')
    await bot.send_photo(user_id, bd_image, caption=message_text)
    await bot.send_message(user_id,
                           f"{student['first_name']} {student['last_name']}\n@{student['handle']}")


async def scheduled_birthday_check():
    user_id = await get_user_id(os.getenv('TG_HANDLE'))
    async with db_con_pool.acquire() as connection:
        students = await connection.fetch("SELECT * FROM students")
        is_birthday = False
        for student in students:
            if student['birthday']:
                if datetime.date.today().day == student['birthday'].day and datetime.date.today().month == student[
                    'birthday'].month:
                    is_birthday = True
                    await send_bd_message_auto(student, user_id)
        if not is_birthday:
            await bot.send_message(user_id, "No students with birthday today")


async def main():
    await init_db()
    scheduler = AsyncIOScheduler()
    scheduler.add_job(scheduled_birthday_check, 'cron', hour=9, minute=0)  # Schedule job daily at 09:00 AM
    scheduler.start()
    await dp.start_polling(bot)


if __name__ == '__main__':
    asyncio.run(main())
