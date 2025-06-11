import sqlite3
from typing import List, Dict, Any, Tuple, Optional
import os
import json
from datetime import datetime

from bot.config import DATABASE_FILE, TESTNET, SUPPORTED_CURRENCIES

def get_db_path() -> str:
    """Возвращает путь к файлу базы данных"""
    return DATABASE_FILE

def init_db() -> None:
    """Инициализирует базу данных с необходимыми таблицами"""
    conn = sqlite3.connect(get_db_path())
    cursor = conn.cursor()
    
    # Таблица товаров с ценой в рублях
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            description TEXT,
            price_rub REAL NOT NULL,
            image_url TEXT,
            available_currencies TEXT
        )
    ''')
    
    # Таблица заказов
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY,
            user_id INTEGER NOT NULL,
            product_id INTEGER NOT NULL,
            invoice_id INTEGER,
            currency TEXT NOT NULL,
            amount REAL NOT NULL,
            status TEXT DEFAULT 'pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (product_id) REFERENCES products (id)
        )
    ''')
    
    # Добавляем тестовые товары, если таблица пуста
    cursor.execute('SELECT COUNT(*) FROM products')
    if cursor.fetchone()[0] == 0:
        # Используем валюты из конфигурации для тестовых товаров
        test_products = [
            ("То, без чего не сдать программирование", "Супер секретно", 100.0, "https://example.com/course.jpg", json.dumps(SUPPORTED_CURRENCIES)),
            ("Секретная nft", "Невероятно секретно",100.0, "https://example.com/book.jpg", json.dumps(SUPPORTED_CURRENCIES)),
        ]
        cursor.executemany(
            'INSERT INTO products (name, description, price_rub, image_url, available_currencies) VALUES (?, ?, ?, ?, ?)',
            test_products
        )
    else:
        # Обновляем существующие товары, чтобы они поддерживали все валюты
        cursor.execute('UPDATE products SET available_currencies = ?', (json.dumps(SUPPORTED_CURRENCIES),))
    
    conn.commit()
    conn.close()

def get_products() -> List[Tuple]:
    """Получает все товары из базы данных"""
    conn = sqlite3.connect(get_db_path())
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM products')
    products = cursor.fetchall()
    conn.close()
    return products

def get_product_by_id(product_id: int) -> Optional[Tuple]:
    """Получает товар по его ID"""
    conn = sqlite3.connect(get_db_path())
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM products WHERE id = ?', (product_id,))
    product = cursor.fetchone()
    conn.close()
    return product

def create_order(user_id: int, product_id: int, currency: str, amount: float) -> int:
    """Создает новый заказ и возвращает его ID"""
    conn = sqlite3.connect(get_db_path())
    cursor = conn.cursor()
    cursor.execute(
        'INSERT INTO orders (user_id, product_id, currency, amount) VALUES (?, ?, ?, ?)',
        (user_id, product_id, currency, amount)
    )
    order_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return order_id

def update_order_invoice(order_id: int, invoice_id: int) -> None:
    """Обновляет заказ, добавляя ID счета"""
    conn = sqlite3.connect(get_db_path())
    cursor = conn.cursor()
    cursor.execute(
        'UPDATE orders SET invoice_id = ? WHERE id = ?',
        (invoice_id, order_id)
    )
    conn.commit()
    conn.close()

def update_order_status(invoice_id: int, status: str) -> None:
    """Обновляет статус заказа по ID счета"""
    conn = sqlite3.connect(get_db_path())
    cursor = conn.cursor()
    cursor.execute(
        'UPDATE orders SET status = ? WHERE invoice_id = ?',
        (status, invoice_id)
    )
    conn.commit()
    conn.close()

def get_order_by_invoice_id(invoice_id: int) -> Optional[Tuple]:
    """Получает заказ по ID счета"""
    conn = sqlite3.connect(get_db_path())
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM orders WHERE invoice_id = ?', (invoice_id,))
    order = cursor.fetchone()
    conn.close()
    return order

def add_product(name: str, description: str, price_rub: float, image_url: str, 
                available_currencies: List[str]) -> int:
    """Добавляет новый товар в базу данных и возвращает его ID"""
    conn = sqlite3.connect(get_db_path())
    cursor = conn.cursor()
    cursor.execute(
        'INSERT INTO products (name, description, price_rub, image_url, available_currencies) VALUES (?, ?, ?, ?, ?)',
        (name, description, price_rub, image_url, json.dumps(available_currencies))
    )
    product_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return product_id

def update_product(product_id: int, name: str, description: str, price_rub: float, 
                  image_url: str, available_currencies: List[str]) -> bool:
    """Обновляет существующий товар"""
    conn = sqlite3.connect(get_db_path())
    cursor = conn.cursor()
    cursor.execute(
        '''UPDATE products SET 
           name = ?, description = ?, price_rub = ?, image_url = ?, available_currencies = ?
           WHERE id = ?''',
        (name, description, price_rub, image_url, json.dumps(available_currencies), product_id)
    )
    success = cursor.rowcount > 0
    conn.commit()
    conn.close()
    return success

def delete_product(product_id: int) -> bool:
    """Удаляет товар по его ID"""
    conn = sqlite3.connect(get_db_path())
    cursor = conn.cursor()
    cursor.execute('DELETE FROM products WHERE id = ?', (product_id,))
    success = cursor.rowcount > 0
    conn.commit()
    conn.close()
    return success 