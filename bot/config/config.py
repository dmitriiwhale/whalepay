import os
from typing import List

# Токен бота
TELEGRAM_BOT_TOKEN = ""

# Токен Crypto Pay API
CRYPTO_PAY_TOKEN = ''
TESTNET = True  # Установите False для основной сети

# Важно: при TESTNET=True доступны только тестовые валюты
# При работе в тестовой сети доступны: TONCOIN, BTC, ETH, USDT, USDC, BUSD
# При работе в основной сети доступны: TON, BTC, USDT, USDC, BUSD

# Настройки базы данных
DATABASE_FILE = "crypto_store.db"

# Поддерживаемые криптовалюты
# Важно: убедитесь, что эти валюты доступны в выбранной сети (тестовой или основной)
if TESTNET:
    SUPPORTED_CURRENCIES = ["TON", "BTC", "ETH", "USDT", "USDC", "BUSD"]
else:
    SUPPORTED_CURRENCIES = ["TON", "BTC", "USDT", "USDC", "BUSD"]

# URL API обменного курса (для конвертации RUB в USD)
EXCHANGE_RATE_API_URL = "https://api.exchangerate-api.com/v4/latest/RUB"

# URL API цен на криптовалюты (для конвертации USD в крипту)
CRYPTO_PRICE_API_URL = "https://api.coingecko.com/api/v3/simple/price"

# Соответствие тикеров криптовалют идентификаторам CoinGecko
CRYPTO_ID_MAPPING = {
    "TON": "the-open-network",
    "TONCOIN": "the-open-network",  # Добавляем маппинг для тестовой сети
    "BTC": "bitcoin",
    "ETH": "ethereum",
    "USDT": "tether",
    "USDC": "usd-coin",
    "BUSD": "binance-usd"
}

# Настройки поддержки
SUPPORT_ENABLED = True  # Включить/выключить функционал поддержки
SUPPORT_CHAT_ID = None  # ID чата поддержки (заполните своим ID)
SUPPORT_ADMIN_IDS = []  # Список ID администраторов поддержки
SUPPORT_WELCOME_MESSAGE = "👋 Добро пожаловать в поддержку! Опишите вашу проблему, и мы постараемся помочь в ближайшее время.\n\nСоздатель бота: @dmitriiwhale"
SUPPORT_REPLY_TEMPLATE = "✉️ *Ответ от поддержки*:\n\n{message}"
SUPPORT_TICKET_TEMPLATE = "🎫 *Новое обращение*\n\nОт: {user_name} (ID: {user_id})\n\n{message}" 