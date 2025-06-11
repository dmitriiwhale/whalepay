import aiohttp
import logging
import time
from typing import Dict, Any, Optional, List, Tuple
from crypto_pay_api_sdk import cryptopay

from bot.config import CRYPTO_PAY_TOKEN, TESTNET, EXCHANGE_RATE_API_URL, CRYPTO_PRICE_API_URL, CRYPTO_ID_MAPPING, TELEGRAM_BOT_TOKEN

# Инициализируем клиент Crypto Pay
crypto = cryptopay.Crypto(CRYPTO_PAY_TOKEN, testnet=TESTNET)

# Переменная для хранения имени бота
_bot_username = None

# Минимальные суммы для разных валют (в соответствии с требованиями Crypto Pay API)
MIN_AMOUNTS = {
    'TON': 0.01,    # Минимальная сумма для TON
    'TONCOIN': 0.01, # Минимальная сумма для TONCOIN (тестовая сеть)
    'BTC': 0.00001, # Минимальная сумма для BTC
    'USDT': 1.0,    # Минимальная сумма для USDT
    'USDC': 1.0,    # Минимальная сумма для USDC
    'BUSD': 1.0,    # Минимальная сумма для BUSD
    'ETH': 0.001,    # Минимальная сумма для ETH
}

# Глобальные переменные для кэширования курсов валют
_usd_rate_cache = 0.01  # Курс USD/RUB (по умолчанию 0.01)
_crypto_prices_cache = {}  # Кэш для курсов криптовалют
_cache_initialized = False  # Флаг инициализации кэша

async def set_bot_username(username: str) -> None:
    """Установить имя бота для использования в URL"""
    global _bot_username
    _bot_username = username
    logging.info(f"Bot username set to: {_bot_username}")

def get_callback_url() -> str:
    """Получить URL для возврата после оплаты"""
    if _bot_username:
        return f"https://t.me/{_bot_username}"
    return "https://t.me/"  # Резервный URL

async def initialize_exchange_rates():
    """Инициализация курсов валют при запуске бота"""
    global _usd_rate_cache, _crypto_prices_cache, _cache_initialized
    
    try:
        # Получаем курс RUB/USD
        _usd_rate_cache = await get_exchange_rate_rub_to_usd(use_cache=False)
        
        # Получаем курсы криптовалют
        currencies = list(CRYPTO_ID_MAPPING.keys())
        _crypto_prices_cache = await get_crypto_prices(currencies, use_cache=False)
        
        _cache_initialized = True
        logging.info(f"Exchange rates initialized: USD={_usd_rate_cache}, Crypto={_crypto_prices_cache}")
    except Exception as e:
        logging.error(f"Failed to initialize exchange rates: {e}")
        # Устанавливаем резервные значения
        _usd_rate_cache = 0.01  # ~100 рублей за доллар
        _crypto_prices_cache = {
            'TON': 5.0,
            'TONCOIN': 5.0,
            'BTC': 60000.0,
            'ETH': 3000.0,  # Примерная цена ETH
            'USDT': 1.0,
            'USDC': 1.0,
            'BUSD': 1.0
        }

async def get_exchange_rate_rub_to_usd(use_cache=True) -> float:
    """Получить текущий обменный курс RUB к USD"""
    global _usd_rate_cache
    
    # Возвращаем кэшированное значение, если оно доступно и запрошено
    if use_cache and _cache_initialized:
        return _usd_rate_cache
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(EXCHANGE_RATE_API_URL) as response:
                if response.status == 200:
                    data = await response.json()
                    rate = data['rates']['USD']
                    # Обновляем кэш
                    _usd_rate_cache = rate
                    return rate
                else:
                    logging.error(f"Failed to get exchange rate: {response.status}")
                    return _usd_rate_cache  # Возвращаем кэшированное значение в случае ошибки
    except Exception as e:
        logging.error(f"Error getting exchange rate: {e}")
        return _usd_rate_cache  # Возвращаем кэшированное значение в случае ошибки

async def get_crypto_prices(currencies: List[str], use_cache=True) -> Dict[str, float]:
    """Получить текущие цены криптовалют в USD"""
    global _crypto_prices_cache
    
    # Возвращаем кэшированные значения, если они доступны и запрошены
    if use_cache and _cache_initialized:
        return {currency: _crypto_prices_cache.get(currency, 1.0) for currency in currencies}
    
    crypto_ids = [CRYPTO_ID_MAPPING.get(currency, currency.lower()) for currency in currencies]
    crypto_ids_str = ','.join(crypto_ids)
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{CRYPTO_PRICE_API_URL}?ids={crypto_ids_str}&vs_currencies=usd") as response:
                if response.status == 200:
                    data = await response.json()
                    result = {}
                    for currency in currencies:
                        crypto_id = CRYPTO_ID_MAPPING.get(currency, currency.lower())
                        if crypto_id in data and 'usd' in data[crypto_id]:
                            result[currency] = data[crypto_id]['usd']
                        else:
                            # Используем кэшированное или резервное значение
                            result[currency] = _crypto_prices_cache.get(currency, 1.0)
                    
                    # Обновляем кэш
                    _crypto_prices_cache.update(result)
                    return result
                else:
                    logging.error(f"Failed to get crypto prices: {response.status}")
                    return {currency: _crypto_prices_cache.get(currency, 1.0) for currency in currencies}
    except Exception as e:
        logging.error(f"Error getting crypto prices: {e}")
        return {currency: _crypto_prices_cache.get(currency, 1.0) for currency in currencies}

async def calculate_crypto_amount(price_rub: float, currency: str) -> float:
    """Рассчитать сумму в криптовалюте на основе цены в рублях"""
    # Используем кэшированные значения курсов
    usd_rate = _usd_rate_cache
    price_usd = price_rub * usd_rate
    
    # Получаем курс криптовалюты из кэша
    crypto_price_usd = _crypto_prices_cache.get(currency, 1.0)
    
    # Рассчитываем сумму в криптовалюте
    crypto_amount = price_usd / crypto_price_usd
    
    # Проверяем, что сумма не меньше минимальной
    min_amount = MIN_AMOUNTS.get(currency, 0)
    if crypto_amount < min_amount:
        logging.warning(f"Calculated amount {crypto_amount} {currency} is less than minimum {min_amount}. Using minimum amount.")
        crypto_amount = min_amount
    
    # Форматируем с нужной точностью
    if currency in ['BTC']:
        return round(crypto_amount, 8)  # BTC обычно использует 8 десятичных знаков
    elif currency in ['TON', 'TONCOIN', 'ETH']:
        return round(crypto_amount, 6)  # TON и ETH обычно используют 6 десятичных знаков
    else:
        return round(crypto_amount, 2)  # Стейблкоины обычно используют 2 десятичных знака

def create_invoice(currency: str, amount: str, description: str, payload: str) -> Dict[str, Any]:
    """Создать счет на оплату с использованием Crypto Pay API"""
    try:
        # Логируем параметры запроса
        logging.info(f"Creating invoice: currency={currency}, amount={amount}, description={description}, payload={payload}")
        
        # Проверяем формат суммы и конвертируем при необходимости
        try:
            # Убедимся, что amount - это строка с правильным форматом
            float_amount = float(amount)
            # Округляем до нужного количества знаков в зависимости от валюты
            if currency == 'BTC':
                float_amount = round(float_amount, 8)
            elif currency in ['TON', 'TONCOIN', 'ETH']:
                float_amount = round(float_amount, 6)
            else:
                float_amount = round(float_amount, 2)
            
            # Преобразуем обратно в строку
            amount_str = str(float_amount)
        except ValueError:
            logging.error(f"Invalid amount format: {amount}")
            return {"ok": False, "error": "Invalid amount format"}
        
        # Получаем URL для возврата после оплаты
        callback_url = get_callback_url()
        
        # Создаем счет
        invoice_data = crypto.createInvoice(
            currency,
            amount_str,
            params={
                "description": description,
                "payload": payload,
                "paid_btn_name": "callback",
                "paid_btn_url": callback_url,  # URL для возврата после оплаты
                "expires_in": 1800  # 30 минут
            }
        )
        
        # Логируем ответ API
        if invoice_data.get('ok'):
            logging.info(f"Invoice created successfully: {invoice_data['result']['invoice_id']}")
        else:
            logging.error(f"API error: {invoice_data}")
        
        return invoice_data
    except Exception as e:
        logging.error(f"Error creating invoice: {e}")
        return {"ok": False, "error": str(e)}

def check_invoice(invoice_id: str) -> Dict[str, Any]:
    """Проверить статус счета по его ID"""
    try:
        return crypto.getInvoices(params={"invoice_ids": [invoice_id]})
    except Exception as e:
        logging.error(f"Error checking invoice: {e}")
        return {"ok": False, "error": str(e)}

def get_balance() -> Dict[str, Any]:
    """Получить баланс аккаунта Crypto Pay"""
    try:
        return crypto.getBalance()
    except Exception as e:
        logging.error(f"Error getting balance: {e}")
        return {"ok": False, "error": str(e)} 