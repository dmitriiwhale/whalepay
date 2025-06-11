import argparse
import json
import sys
import os
import logging
from typing import List

# Добавляем текущую директорию в sys.path для импорта модулей bot
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from bot.database import db
from bot.config import SUPPORTED_CURRENCIES

def setup_logging():
    """Настройка конфигурации логирования"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    )

def validate_currencies(currencies: List[str]) -> List[str]:
    """Проверка поддерживаемых валют"""
    valid_currencies = []
    for currency in currencies:
        if currency in SUPPORTED_CURRENCIES:
            valid_currencies.append(currency)
        else:
            logging.warning(f"Currency {currency} is not supported. Skipping.")
    return valid_currencies

def interactive_add_product():
    """Интерактивное добавление товара"""
    print("=== Добавление нового товара ===")
    
    # Получаем детали товара
    name = input("Введите название товара: ")
    description = input("Введите описание товара: ")
    
    # Получаем цену с проверкой
    while True:
        try:
            price_rub = float(input("Введите цену в рублях: "))
            if price_rub <= 0:
                print("Цена должна быть положительным числом.")
                continue
            break
        except ValueError:
            print("Пожалуйста, введите корректное число.")
    
    image_url = input("Введите URL изображения товара (или оставьте пустым): ")
    
    # Получаем валюты с проверкой
    print(f"Доступные валюты: {', '.join(SUPPORTED_CURRENCIES)}")
    currencies_input = input("Введите валюты через запятую (например, TON,BTC,USDT): ")
    currencies = [c.strip() for c in currencies_input.split(',') if c.strip()]
    valid_currencies = validate_currencies(currencies)
    
    if not valid_currencies:
        print("Не указаны валидные валюты. Используем все поддерживаемые валюты.")
        valid_currencies = SUPPORTED_CURRENCIES.copy()
    
    # Подтверждаем детали
    print("\n=== Информация о товаре ===")
    print(f"Название: {name}")
    print(f"Описание: {description}")
    print(f"Цена: {price_rub} ₽")
    print(f"URL изображения: {image_url or 'Не указан'}")
    print(f"Валюты: {', '.join(valid_currencies)}")
    
    confirm = input("\nДобавить товар? (y/n): ").lower()
    if confirm != 'y':
        print("Операция отменена.")
        return
    
    # Добавляем товар в базу данных
    try:
        product_id = db.add_product(name, description, price_rub, image_url, valid_currencies)
        print(f"Товар успешно добавлен с ID: {product_id}")
    except Exception as e:
        print(f"Ошибка при добавлении товара: {e}")

def add_product_from_args(args):
    """Добавление товара из аргументов командной строки"""
    # Парсим валюты
    currencies = args.currencies.split(',') if args.currencies else []
    valid_currencies = validate_currencies(currencies)
    
    if not valid_currencies:
        logging.warning("No valid currencies specified. Using all supported currencies.")
        valid_currencies = SUPPORTED_CURRENCIES.copy()
    
    try:
        product_id = db.add_product(
            args.name,
            args.description,
            args.price,
            args.image_url,
            valid_currencies
        )
        logging.info(f"Product added successfully with ID: {product_id}")
    except Exception as e:
        logging.error(f"Error adding product: {e}")
        sys.exit(1)

def main():
    """Основная функция"""
    setup_logging()
    
    # Инициализируем базу данных
    db.init_db()
    
    parser = argparse.ArgumentParser(description='Add a product to the Crypto Store')
    parser.add_argument('--interactive', '-i', action='store_true', help='Run in interactive mode')
    parser.add_argument('--name', '-n', help='Product name')
    parser.add_argument('--description', '-d', help='Product description')
    parser.add_argument('--price', '-p', type=float, help='Product price in RUB')
    parser.add_argument('--image-url', '-img', help='Product image URL')
    parser.add_argument('--currencies', '-c', help='Comma-separated list of supported currencies')
    
    args = parser.parse_args()
    
    if args.interactive:
        interactive_add_product()
    elif all([args.name, args.description, args.price]):
        add_product_from_args(args)
    else:
        if not any([args.name, args.description, args.price, args.image_url, args.currencies]):
            interactive_add_product()
        else:
            parser.error("If not using interactive mode, --name, --description, and --price are required")

if __name__ == "__main__":
    main() 