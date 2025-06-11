import asyncio
import logging
import sys
import os

# Добавляем текущую директорию в sys.path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Импортируем из пакета bot
from bot.main import main

# Настраиваем логирование
logging.basicConfig(level=logging.INFO)

if __name__ == "__main__":
    asyncio.run(main())