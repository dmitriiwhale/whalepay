import logging
import os
from aiogram import Bot
from aiogram.types import FSInputFile
from typing import Optional

from bot.database import db
from bot.config.products import get_product_file_info

async def deliver_digital_product(bot: Bot, user_id: int, payload: str) -> None:
    """
    Доставка цифрового товара пользователю
    
    Эта функция обрабатывает доставку цифровых товаров после успешной оплаты.
    Может быть расширена для обработки различных типов цифровых товаров.
    
    Аргументы:
        bot: Экземпляр бота
        user_id: ID пользователя Telegram
        payload: Полезная нагрузка из счета, обычно в формате "order_{order_id}"
    """
    try:
        # Извлекаем order_id из payload
        order_id = None
        if payload and payload.startswith("order_"):
            order_id = int(payload.split("_")[1])
            logging.info(f"Extracted order_id from payload: {order_id}")
        else:
            logging.error(f"Invalid payload format: {payload}")
            await bot.send_message(
                user_id,
                "❌ Произошла ошибка при доставке товара. Пожалуйста, свяжитесь с поддержкой."
            )
            return
        
        # Получаем информацию о заказе напрямую по order_id
        conn = db.sqlite3.connect(db.get_db_path())
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM orders WHERE id = ?', (order_id,))
        order = cursor.fetchone()
        conn.close()
        
        if not order:
            logging.error(f"Order not found by order_id: {order_id}")
            await bot.send_message(
                user_id,
                "❌ Заказ не найден. Пожалуйста, свяжитесь с поддержкой."
            )
            return
        
        # Получаем ID товара из заказа
        product_id = order[2]  # Индекс 2 - это product_id в кортеже заказа
        logging.info(f"Found product_id: {product_id} for order_id: {order_id}")
        
        # Получаем информацию о товаре
        product = db.get_product_by_id(product_id)
        if not product:
            logging.error(f"Product not found: {product_id}")
            await bot.send_message(
                user_id,
                "❌ Товар не найден. Пожалуйста, свяжитесь с поддержкой."
            )
            return
        
        # Получаем информацию о файле товара
        product_file_info = get_product_file_info(product_id)
        logging.info(f"Product file info: {product_file_info}")
        
        if not product_file_info:
            # Если информация о файле не найдена, отправляем стандартное сообщение
            await bot.send_message(
                user_id,
                "🎁 **Ваш заказ готов!**\n\n"
                f"Товар: **{product[1]}**\n"
                "Спасибо за покупку!\n\n"
                f"Номер заказа: `{order_id}`",
                parse_mode="Markdown"
            )
            return
        
        # Обрабатываем товар в зависимости от его типа
        if product_file_info["type"] == "file":
            # Проверяем, существует ли файл
            if not product_file_info["file_path"] or not os.path.exists(product_file_info["file_path"]):
                logging.error(f"File not found: {product_file_info['file_path']}")
                await bot.send_message(
                    user_id,
                    "❌ Файл товара не найден. Пожалуйста, свяжитесь с поддержкой."
                )
                return
            
            # Отправляем сообщение о доставке товара
            await bot.send_message(
                user_id,
                f"🎁 **Ваш заказ готов!**\n\n"
                f"Товар: **{product[1]}**\n"
                f"Описание: {product_file_info['description']}\n\n"
                f"Номер заказа: `{order_id}`",
                parse_mode="Markdown"
            )
            
            # Отправляем файл
            file = FSInputFile(product_file_info["file_path"], filename=product_file_info["file_name"])
            await bot.send_document(
                user_id,
                document=file,
                caption=f"📁 {product_file_info['file_name']}\n\n"
                        f"Спасибо за покупку! Если у вас возникнут вопросы, свяжитесь с поддержкой."
            )
            
        elif product_file_info["type"] == "text":
            # Форматируем текстовый контент, подставляя order_id если нужно
            content = product_file_info["content"].format(order_id=order_id)
            
            # Отправляем текстовое сообщение с информацией
            await bot.send_message(
                user_id,
                f"🎁 **Ваш заказ готов!**\n\n"
                f"Товар: **{product[1]}**\n"
                f"Описание: {product_file_info['description']}\n\n"
                f"{content}",
                parse_mode="Markdown"
            )
        
        else:
            # Неизвестный тип товара
            logging.error(f"Unknown product type: {product_file_info['type']}")
            await bot.send_message(
                user_id,
                "❌ Неизвестный тип товара. Пожалуйста, свяжитесь с поддержкой."
            )
        
    except Exception as e:
        logging.error(f"Error delivering product: {e}", exc_info=True)
        # Уведомляем пользователя о проблеме с доставкой
        await bot.send_message(
            user_id,
            "❌ Произошла ошибка при доставке товара. Пожалуйста, свяжитесь с поддержкой."
        ) 