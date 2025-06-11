"""
Конфигурация товаров и их файлов
"""

# Словарь соответствия ID товаров и их файлов
PRODUCT_FILES = {
    1: {
        "file_path": "bot/files/snake_game.py",
        "file_name": "snake_game.py",
        "description": "Секрет",
        "type": "file"  # Тип товара: file - файл, text - текстовая информация
    },
    2: {
        "file_path": "bot/files/nft.jpg",
        "file_name": "nft.jpg",
        "description": "Секрет",
        "type": "file"
    }
}

# Функция для получения информации о файле товара
def get_product_file_info(product_id):
    """
    Получить информацию о файле товара по его ID
    
    Args:
        product_id: ID товара
        
    Returns:
        dict: Информация о файле товара или None, если товар не найден
    """
    return PRODUCT_FILES.get(product_id) 