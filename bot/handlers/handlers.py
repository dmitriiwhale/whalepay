import logging
import json
from aiogram import Router, F, Bot
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

from bot.database import db
from bot.services import crypto_service
from bot.keyboards import keyboards
from bot.utils.product_manager import deliver_digital_product
from bot.config import TESTNET, SUPPORTED_CURRENCIES, SUPPORT_ENABLED, SUPPORT_WELCOME_MESSAGE

# Инициализируем роутер
router = Router()

@router.message(Command("start"))
async def cmd_start(message: Message):
    """Обработка команды /start"""
    # Определяем текст с учетом текущей сети
    network_text = "тестовой" if TESTNET else "основной"
    currencies_text = ", ".join(SUPPORTED_CURRENCIES)
    
    await message.answer(
        f"🤖 Добро пожаловать в whalepay!\n\n"
        f"Здесь вы можете приобрести цифровые товары за криптовалюту.\n"
        f"Бот работает в {network_text} сети.\n"
        f"Поддерживаемые валюты: {currencies_text}",
        reply_markup=keyboards.main_menu_keyboard()
    )

@router.message(Command("update_rates"))
async def cmd_update_rates(message: Message):
    """Обработка команды /update_rates для обновления курсов валют"""
    # Проверяем, является ли пользователь администратором (можно добавить проверку ID)
    try:
        await message.answer("🔄 Обновление курсов валют...")
        await crypto_service.initialize_exchange_rates()
        
        # Получаем текущие курсы для отображения
        usd_rate = crypto_service._usd_rate_cache
        crypto_rates = crypto_service._crypto_prices_cache
        
        rates_info = f"✅ Курсы валют обновлены:\n\n"
        rates_info += f"💵 USD/RUB: {1/usd_rate:.2f} ₽\n\n"
        
        for currency, price in crypto_rates.items():
            rates_info += f"💰 {currency}/USD: ${price:.2f}\n"
        
        await message.answer(rates_info)
    except Exception as e:
        logging.error(f"Error updating rates: {e}")
        await message.answer("❌ Ошибка при обновлении курсов валют")

@router.message(Command("test_invoice"))
async def cmd_test_invoice(message: Message, bot: Bot):
    """Тестовая команда для создания счета напрямую"""
    try:
        # Выбираем первую доступную валюту
        currency = SUPPORTED_CURRENCIES[0]
        amount = str(crypto_service.MIN_AMOUNTS.get(currency, 1.0))
        
        # Получаем имя бота для отладки
        bot_info = await bot.get_me()
        bot_username = bot_info.username
        callback_url = f"https://t.me/{bot_username}"
        
        await message.answer(
            f"Создаю тестовый счет:\n"
            f"- Валюта: {currency}\n"
            f"- Сумма: {amount}\n"
            f"- Callback URL: {callback_url}\n"
            f"- Тестовая сеть: {TESTNET}"
        )
        
        # Создаем счет напрямую через API
        invoice_data = crypto_service.create_invoice(
            currency,
            amount,
            "Тестовый счет",
            "test_payload"
        )
        
        if invoice_data.get('ok'):
            invoice = invoice_data['result']
            invoice_id = invoice['invoice_id']
            pay_url = invoice['pay_url']
            
            await message.answer(
                f"✅ Тестовый счет создан!\n\n"
                f"Валюта: {currency}\n"
                f"Сумма: {amount}\n"
                f"ID: {invoice_id}\n\n"
                f"URL для оплаты: {pay_url}"
            )
        else:
            error = invoice_data.get('error', 'Неизвестная ошибка')
            error_code = invoice_data.get('code', 'Нет кода')
            error_name = invoice_data.get('name', 'Нет имени')
            
            await message.answer(
                f"❌ Ошибка создания счета:\n"
                f"- Код: {error_code}\n"
                f"- Имя: {error_name}\n"
                f"- Описание: {error}\n\n"
                f"Полный ответ API: {invoice_data}"
            )
    except Exception as e:
        logging.error(f"Error in test_invoice: {e}", exc_info=True)
        await message.answer(f"❌ Ошибка: {str(e)}")

@router.callback_query(F.data == "catalog")
async def show_catalog(callback_query: CallbackQuery):
    """Показать каталог товаров"""
    products = db.get_products()
    
    if not products:
        await callback_query.message.edit_text("Каталог пуст")
        return
    
    await callback_query.message.edit_text(
        "🛍 **Каталог товаров:**\n\nВыберите товар для покупки:",
        reply_markup=keyboards.catalog_keyboard(products),
        parse_mode="Markdown"
    )

@router.callback_query(F.data.startswith("product_"))
async def show_product(callback_query: CallbackQuery):
    """Показать детали товара"""
    product_id = int(callback_query.data.split("_")[1])
    product = db.get_product_by_id(product_id)
    
    if not product:
        await callback_query.answer("Товар не найден")
        return
    
    # Получаем цены в USD и криптовалюте для отображения
    usd_rate = crypto_service._usd_rate_cache
    price_usd = product[3] * usd_rate  # price_rub * usd_rate
    
    # Парсим доступные валюты
    available_currencies_raw = json.loads(product[5]) if product[5] else []
    
    # Фильтруем валюты, чтобы показывать только те, которые поддерживаются в текущей сети
    available_currencies = [c for c in available_currencies_raw if c in SUPPORTED_CURRENCIES]
    
    if not available_currencies:
        # Если нет доступных валют, используем все поддерживаемые
        available_currencies = SUPPORTED_CURRENCIES
    
    # Создаем текст с ценами
    price_text = f"💰 Цена: {product[3]} ₽ ({price_usd:.2f} USD)\n\n"
    for currency in available_currencies:
        crypto_amount = await crypto_service.calculate_crypto_amount(product[3], currency)
        price_text += f"• {crypto_amount} {currency}\n"
    
    product_text = (
        f"📦 **{product[1]}**\n\n"
        f"📝 {product[2]}\n\n"
        f"{price_text}"
    )
    
    await callback_query.message.edit_text(
        product_text,
        reply_markup=keyboards.product_keyboard(product_id),
        parse_mode="Markdown"
    )

@router.callback_query(F.data.startswith("buy_"))
async def select_currency(callback_query: CallbackQuery):
    """Показать выбор валюты для покупки"""
    product_id = int(callback_query.data.split("_")[1])
    product = db.get_product_by_id(product_id)
    
    if not product:
        await callback_query.answer("Товар не найден")
        return
    
    # Парсим доступные валюты
    available_currencies_raw = json.loads(product[5]) if product[5] else []
    
    # Фильтруем валюты, чтобы показывать только те, которые поддерживаются в текущей сети
    available_currencies = [c for c in available_currencies_raw if c in SUPPORTED_CURRENCIES]
    
    if not available_currencies:
        # Если нет доступных валют, используем все поддерживаемые
        available_currencies = SUPPORTED_CURRENCIES
    
    if not available_currencies:
        await callback_query.answer("Нет доступных валют для оплаты")
        return
    
    await callback_query.message.edit_text(
        f"🔄 Выберите криптовалюту для оплаты товара **{product[1]}**:",
        reply_markup=keyboards.currency_selection_keyboard(product_id, available_currencies),
        parse_mode="Markdown"
    )

@router.callback_query(F.data.startswith("currency_"))
async def process_purchase(callback_query: CallbackQuery, bot: Bot):
    """Обработка покупки с выбранной валютой"""
    parts = callback_query.data.split("_")
    product_id = int(parts[1])
    selected_currency = parts[2]
    
    # Проверяем, поддерживается ли выбранная валюта в текущей сети
    if selected_currency not in SUPPORTED_CURRENCIES:
        await callback_query.answer(f"Валюта {selected_currency} не поддерживается в текущей сети")
        return
    
    product = db.get_product_by_id(product_id)
    user_id = callback_query.from_user.id
    
    if not product:
        await callback_query.answer("Товар не найден")
        return
    
    try:
        # Calculate crypto amount
        crypto_amount = await crypto_service.calculate_crypto_amount(product[3], selected_currency)
        logging.info(f"Calculated amount: {crypto_amount} {selected_currency} for {product[3]} RUB")
        
        # Проверяем минимальную сумму
        min_amount = crypto_service.MIN_AMOUNTS.get(selected_currency, 0)
        if crypto_amount < min_amount:
            crypto_amount = min_amount
            logging.info(f"Adjusted to minimum amount: {crypto_amount} {selected_currency}")
        
        # Create order in DB
        order_id = db.create_order(user_id, product_id, selected_currency, crypto_amount)
        logging.info(f"Created order ID: {order_id}")
        
        # Получаем имя пользователя бота для callback URL
        bot_info = await bot.get_me()
        bot_username = bot_info.username
        await crypto_service.set_bot_username(bot_username)
        
        # Формируем payload
        payload = f"order_{order_id}"
        
        # Create invoice in Crypto Pay
        invoice_data = crypto_service.create_invoice(
            selected_currency,
            str(crypto_amount),
            f"Покупка: {product[1]}",
            payload
        )
        
        if invoice_data.get('ok'):
            invoice = invoice_data['result']
            invoice_id = invoice['invoice_id']
            pay_url = invoice['pay_url']
            
            # Update order with invoice ID
            db.update_order_invoice(order_id, invoice_id)
            
            # Show payment info
            usd_rate = crypto_service._usd_rate_cache
            price_usd = product[3] * usd_rate
            
            await callback_query.message.edit_text(
                f"💳 **Счет создан!**\n\n"
                f"📦 Товар: {product[1]}\n"
                f"💰 К оплате: {crypto_amount} {selected_currency}\n"
                f"💵 Эквивалент: {product[3]} ₽ / {price_usd:.2f} USD\n"
                f"🆔 Счет: `{invoice_id}`\n\n"
                f"Нажмите кнопку \"Оплатить\" для перехода к оплате.\n"
                f"После оплаты используйте \"Проверить оплату\".",
                reply_markup=keyboards.payment_keyboard(pay_url, str(invoice_id)),
                parse_mode="Markdown"
            )
        else:
            error_msg = invoice_data.get('error', 'Неизвестная ошибка')
            error_code = invoice_data.get('code', 'Нет кода')
            error_name = invoice_data.get('name', 'Нет имени')
            logging.error(f"Failed to create invoice: {error_code} {error_name} - {error_msg}")
            
            # Проверяем конкретные ошибки
            if "asset" in str(error_msg).lower() or "currency" in str(error_msg).lower():
                await callback_query.message.edit_text(
                    f"❌ Ошибка: Валюта {selected_currency} временно недоступна.\n"
                    f"Пожалуйста, выберите другую валюту или попробуйте позже."
                )
            elif "amount" in str(error_msg).lower():
                await callback_query.message.edit_text(
                    f"❌ Ошибка: Некорректная сумма ({crypto_amount} {selected_currency}).\n"
                    f"Пожалуйста, выберите другую валюту или попробуйте позже."
                )
            elif "paid_btn_url" in str(error_name).lower():
                await callback_query.message.edit_text(
                    f"❌ Ошибка: Не удалось создать URL для возврата.\n"
                    f"Пожалуйста, попробуйте позже."
                )
            else:
                await callback_query.message.edit_text(
                    f"❌ Ошибка создания счета: {error_name} ({error_code})\n"
                    f"Пожалуйста, попробуйте позже."
                )
            
    except Exception as e:
        logging.error(f"Error in process_purchase: {e}", exc_info=True)
        await callback_query.message.edit_text(
            "❌ Произошла ошибка при обработке запроса.\n"
            "Пожалуйста, попробуйте позже или выберите другую валюту."
        )

@router.callback_query(F.data.startswith("check_"))
async def check_payment(callback_query: CallbackQuery, bot: Bot):
    """Проверка статуса платежа"""
    invoice_id = callback_query.data.split("_")[1]
    logging.info(f"Checking payment for invoice_id: {invoice_id}")
    
    try:
        # Проверяем статус счета
        invoice_data = crypto_service.check_invoice(invoice_id)
        logging.info(f"Invoice data: {invoice_data}")
        
        if invoice_data.get('ok') and invoice_data['result']['items']:
            invoice = invoice_data['result']['items'][0]
            logging.info(f"Invoice status: {invoice['status']}, payload: {invoice['payload']}")
            
            if invoice['status'] == 'paid':
                # Обновляем статус заказа
                db.update_order_status(int(invoice_id), "paid")
                logging.info(f"Updated order status to paid for invoice_id: {invoice_id}")
                
                await callback_query.message.edit_text(
                    "✅ **Оплата успешно получена!**\n\n"
                    "📦 Ваш товар будет доставлен в ближайшее время.\n"
                    "Спасибо за покупку! 🎉",
                    reply_markup=keyboards.back_to_catalog_keyboard(),
                    parse_mode="Markdown"
                )
                
                # Доставляем цифровой товар
                await deliver_digital_product(bot, callback_query.from_user.id, invoice['payload'])
                
            else:
                await callback_query.answer("⏳ Платеж еще не поступил")
        else:
            logging.error(f"Failed to check invoice: {invoice_data}")
            await callback_query.answer("❌ Не удалось проверить статус платежа")
            
    except Exception as e:
        logging.error(f"Error checking payment: {e}", exc_info=True)
        await callback_query.answer("❌ Ошибка проверки платежа")

@router.callback_query(F.data == "balance")
async def show_balance(callback_query: CallbackQuery):
    """Показать баланс аккаунта Crypto Pay"""
    try:
        balance_data = crypto_service.get_balance()
        
        if balance_data.get('ok'):
            balances = balance_data['result']
            
            balance_text = "💰 **Баланс приложения:**\n\n"
            for balance in balances:
                balance_text += f"{balance['currency_code']}: {balance['available']} ({balance['onhold']} в холде)\n"
            
            await callback_query.message.edit_text(
                balance_text,
                reply_markup=keyboards.main_menu_keyboard(),
                parse_mode="Markdown"
            )
        else:
            await callback_query.message.edit_text("❌ Не удалось получить баланс")
            
    except Exception as e:
        logging.error(f"Error getting balance: {e}")
        await callback_query.message.edit_text("❌ Ошибка получения баланса")

@router.callback_query(F.data == "back_to_main")
async def back_to_main(callback_query: CallbackQuery):
    """Вернуться в главное меню"""
    # Определяем текст с учетом текущей сети
    network_text = "тестовой" if TESTNET else "основной"
    currencies_text = ", ".join(SUPPORTED_CURRENCIES)
    
    await callback_query.message.edit_text(
        f"🤖 Добро пожаловать в Crypto Store!\n\n"
        f"Здесь вы можете приобрести цифровые товары за криптовалюту.\n"
        f"Бот работает в {network_text} сети.\n"
        f"Поддерживаемые валюты: {currencies_text}",
        reply_markup=keyboards.main_menu_keyboard()
    )

@router.callback_query(F.data == "support")
async def support_button(callback_query: CallbackQuery, state: FSMContext):
    """Обработка нажатия на кнопку поддержки в главном меню"""
    from bot.handlers.support_handlers import SupportStates
    
    if not SUPPORT_ENABLED:
        await callback_query.answer("❌ Поддержка временно недоступна.")
        return
    
    # Отправляем приветственное сообщение и переводим в состояние ожидания сообщения
    await callback_query.message.edit_text(
        SUPPORT_WELCOME_MESSAGE,
        reply_markup=keyboards.support_keyboard()
    )
    await state.set_state(SupportStates.waiting_for_message)
    await callback_query.answer() 