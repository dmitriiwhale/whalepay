import asyncio
import logging
from aiogram import Bot, Dispatcher

from bot.config import TELEGRAM_BOT_TOKEN
from bot.database import db
from bot.handlers.handlers import router
from bot.handlers.support_handlers import support_router
from bot.services import crypto_service

# Настраиваем логирование
logging.basicConfig(level=logging.INFO)

# Инициализируем бота и диспетчер
bot = Bot(token=TELEGRAM_BOT_TOKEN)
dp = Dispatcher()

# Регистрируем роутеры
dp.include_router(router)
dp.include_router(support_router)

async def main():
    # Инициализируем базу данных
    db.init_db()
    
    # Получаем и устанавливаем имя бота
    try:
        bot_info = await bot.get_me()
        bot_username = bot_info.username
        logging.info(f"Bot username: {bot_username}")
        await crypto_service.set_bot_username(bot_username)
    except Exception as e:
        logging.error(f"Failed to get bot username: {e}")
    
    # Инициализируем обменные курсы
    logging.info("Initializing exchange rates...")
    await crypto_service.initialize_exchange_rates()
    
    # Запускаем поллинг
    logging.info("Starting bot...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main()) 