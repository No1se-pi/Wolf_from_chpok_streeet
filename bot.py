import asyncio #Подключение библиотеки для бота
import logging #Подключение библиотеки для логирования

from aiogram import Bot, Dispatcher 
from aiogram.filters import CommandStart
from aiogram.types import Message

from config import TOKEN #Подключение конфига для безопасного хранения токена

bot = Bot(token=TOKEN) #Указание токена
dp = Dispatcher() #


@dp.message(CommandStart())
async def cmd_start(messege: Message):
    await messege.answer('Привет!')

async def main ():
    await dp.start_polling(bot)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    try:
        print('Bot is running')
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Exit")
