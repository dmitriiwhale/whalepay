from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import json
from typing import List, Dict, Any

def main_menu_keyboard() -> InlineKeyboardMarkup:
    """Generate the main menu keyboard"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🛍 Каталог товаров", callback_data="catalog")],
        [InlineKeyboardButton(text="🆘 Поддержка", callback_data="support")]
    ])
    return keyboard

def catalog_keyboard(products: List[tuple]) -> InlineKeyboardMarkup:
    """Generate the catalog keyboard with products"""
    buttons = [
        [InlineKeyboardButton(
            text=f"{product[1]} - {product[3]} ₽", 
            callback_data=f"product_{product[0]}"
        )] for product in products
    ]
    buttons.append([InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_main")])
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def product_keyboard(product_id: int) -> InlineKeyboardMarkup:
    """Generate the product details keyboard"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💳 Купить", callback_data=f"buy_{product_id}")],
        [InlineKeyboardButton(text="🔙 К каталогу", callback_data="catalog")]
    ])
    return keyboard

def currency_selection_keyboard(product_id: int, available_currencies: List[str]) -> InlineKeyboardMarkup:
    """Generate keyboard for selecting cryptocurrency"""
    buttons = [
        [InlineKeyboardButton(
            text=f"{currency}", 
            callback_data=f"currency_{product_id}_{currency}"
        )] for currency in available_currencies
    ]
    buttons.append([InlineKeyboardButton(text="🔙 Назад", callback_data=f"product_{product_id}")])
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def payment_keyboard(pay_url: str, invoice_id: str) -> InlineKeyboardMarkup:
    """Generate keyboard for payment"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💳 Оплатить", url=pay_url)],
        [InlineKeyboardButton(text="🔄 Проверить оплату", callback_data=f"check_{invoice_id}")],
        [InlineKeyboardButton(text="🔙 К каталогу", callback_data="catalog")]
    ])
    return keyboard

def back_to_catalog_keyboard() -> InlineKeyboardMarkup:
    """Generate keyboard to go back to catalog"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🛍 К каталогу", callback_data="catalog")]
    ])
    return keyboard

def support_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура для поддержки"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_support")],
    ])
    return keyboard

def admin_support_keyboard(user_id: int) -> InlineKeyboardMarkup:
    """Клавиатура для администраторов поддержки"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✏️ Ответить", callback_data=f"reply_to_{user_id}")],
        [InlineKeyboardButton(text="✅ Закрыть обращение", callback_data=f"close_ticket_{user_id}")],
    ])
    return keyboard 