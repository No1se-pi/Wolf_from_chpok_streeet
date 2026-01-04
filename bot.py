import asyncio #Подключение библиотеки для бота
import logging #Подключение библиотеки для логирования

from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart, Command
from aiogram.types import Message

from config import TOKEN #Подключение конфига для безопасного хранения токена

bot = Bot(token=TOKEN) #Указание токена
dp = Dispatcher() #


@dp.message(CommandStart())
async def cmd_start(messege: Message):
    await messege.answer('Привет!')

@dp.message(Command("help"))
async def get_help(messege: Message):
    await messege.answer("Это комманда /help")

@dp.message(F.text == "Как дела?")
async def how_are_you(messege: Message):
    await messege.answer("Kaif!")

@dp.message(F.photo)
async def photo(message: Message):
    await message.answer(f"ID фото: {message.photo[-1].file_id}")


@dp.message(Command('photo'))
async def get_photo(message: Message):
    await message.answer_photo(photo="ID photo",
                               caption='Это фото')
    


async def main ():
    await dp.start_polling(bot)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    try:
        print('Bot is running')
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Exit")
