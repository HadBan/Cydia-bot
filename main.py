import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

from config import BOT_TOKEN
from handlers import start, court, messages

logging.basicConfig(level=logging.INFO)


async def main():
    bot = Bot(token=BOT_TOKEN)
    
    # Получаем данные бота и сохраняем username
    me = await bot.me()
    bot.my_username = me.username
    logging.info(f"Бот запущен: @{me.username}")
    
    dp = Dispatcher(storage=MemoryStorage())

    dp.include_router(start.router)
    dp.include_router(court.router)
    dp.include_router(messages.router)

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
