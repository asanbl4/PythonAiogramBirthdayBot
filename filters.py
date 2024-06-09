import re
from aiogram.filters import BaseFilter
from aiogram.types import Message


class StartsWithAtFilter(BaseFilter):
    async def __call__(self, message: Message) -> bool:
        return message.text.startswith('@')


class EmailFilter(BaseFilter):
    async def __call__(self, message: Message) -> bool:
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        if re.search(email_pattern, message.text):
            return True
        return False
