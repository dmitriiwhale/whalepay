import logging
from aiogram import Router, F, Bot
from aiogram.filters import Command, StateFilter
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from bot.config import (
    SUPPORT_ENABLED, SUPPORT_CHAT_ID, SUPPORT_ADMIN_IDS,
    SUPPORT_WELCOME_MESSAGE, SUPPORT_REPLY_TEMPLATE, SUPPORT_TICKET_TEMPLATE
)
from bot.keyboards import keyboards

# Инициализируем роутер
support_router = Router()

# Определяем состояния для FSM (Finite State Machine)
class SupportStates(StatesGroup):
    waiting_for_message = State()  # Ожидание сообщения от пользователя
    waiting_for_reply = State()    # Ожидание ответа от администратора

# Команда для начала диалога с поддержкой
@support_router.message(Command("support"))
async def cmd_support(message: Message, state: FSMContext):
    """Обработка команды /support"""
    if not SUPPORT_ENABLED:
        await message.answer("❌ Поддержка временно недоступна.")
        return
    
    # Отправляем приветственное сообщение и переводим в состояние ожидания сообщения
    await message.answer(
        SUPPORT_WELCOME_MESSAGE,
        reply_markup=keyboards.support_keyboard()
    )
    await state.set_state(SupportStates.waiting_for_message)

# Обработка сообщения от пользователя для поддержки
@support_router.message(StateFilter(SupportStates.waiting_for_message))
async def handle_support_message(message: Message, bot: Bot, state: FSMContext):
    """Обработка сообщения для поддержки"""
    if not SUPPORT_ENABLED or not SUPPORT_CHAT_ID:
        await message.answer("❌ Поддержка временно недоступна.")
        await state.clear()
        return
    
    user_id = message.from_user.id
    user_name = message.from_user.full_name
    user_message = message.text or message.caption or "Пустое сообщение"
    
    # Сохраняем данные в состоянии
    await state.update_data(user_id=user_id, user_name=user_name, message_text=user_message)
    
    try:
        # Отправляем тикет в чат поддержки
        ticket_text = SUPPORT_TICKET_TEMPLATE.format(
            user_name=user_name,
            user_id=user_id,
            message=user_message
        )
        
        await bot.send_message(
            SUPPORT_CHAT_ID,
            ticket_text,
            parse_mode="Markdown",
            reply_markup=keyboards.admin_support_keyboard(user_id)
        )
        
        # Отправляем подтверждение пользователю
        await message.answer(
            "✅ Ваше сообщение отправлено в поддержку!\n"
            "Мы свяжемся с вами в ближайшее время.",
            reply_markup=keyboards.main_menu_keyboard()
        )
        
        # Очищаем состояние
        await state.clear()
        
    except Exception as e:
        logging.error(f"Error sending support message: {e}", exc_info=True)
        await message.answer(
            "❌ Произошла ошибка при отправке сообщения. Попробуйте позже.",
            reply_markup=keyboards.main_menu_keyboard()
        )
        await state.clear()

# Обработка нажатия на кнопку "Ответить" администратором
@support_router.callback_query(F.data.startswith("reply_to_"))
async def reply_to_user(callback_query: CallbackQuery, state: FSMContext):
    """Обработка нажатия на кнопку 'Ответить' администратором"""
    # Проверяем, что это администратор
    if callback_query.from_user.id not in SUPPORT_ADMIN_IDS:
        await callback_query.answer("У вас нет прав для ответа на обращения.")
        return
    
    # Извлекаем ID пользователя из callback_data
    user_id = int(callback_query.data.split("_")[2])
    
    # Сохраняем ID пользователя в состоянии
    await state.update_data(reply_to_user_id=user_id)
    await state.set_state(SupportStates.waiting_for_reply)
    
    await callback_query.message.reply(
        f"Введите ответ для пользователя (ID: {user_id}):"
    )
    await callback_query.answer()

# Обработка ответа администратора
@support_router.message(StateFilter(SupportStates.waiting_for_reply))
async def send_reply_to_user(message: Message, bot: Bot, state: FSMContext):
    """Отправка ответа пользователю от администратора"""
    # Получаем данные из состояния
    data = await state.get_data()
    user_id = data.get("reply_to_user_id")
    
    if not user_id:
        await message.answer("❌ Ошибка: ID пользователя не найден.")
        await state.clear()
        return
    
    reply_text = message.text or message.caption or "Пустое сообщение"
    
    try:
        # Отправляем ответ пользователю
        await bot.send_message(
            user_id,
            SUPPORT_REPLY_TEMPLATE.format(message=reply_text),
            parse_mode="Markdown"
        )
        
        # Отправляем подтверждение администратору
        await message.answer(f"✅ Ответ отправлен пользователю (ID: {user_id}).")
        
        # Очищаем состояние
        await state.clear()
        
    except Exception as e:
        logging.error(f"Error sending reply to user: {e}", exc_info=True)
        await message.answer(f"❌ Ошибка отправки ответа пользователю (ID: {user_id}).")
        await state.clear()

# Обработка кнопки "Отмена" в поддержке
@support_router.callback_query(F.data == "cancel_support")
async def cancel_support(callback_query: CallbackQuery, state: FSMContext):
    """Отмена обращения в поддержку"""
    await state.clear()
    await callback_query.message.edit_text(
        "❌ Обращение в поддержку отменено.",
        reply_markup=keyboards.main_menu_keyboard()
    )
    await callback_query.answer()

# Обработка кнопки "Закрыть обращение"
@support_router.callback_query(F.data.startswith("close_ticket_"))
async def close_ticket(callback_query: CallbackQuery):
    """Закрытие тикета поддержки администратором"""
    # Проверяем, что это администратор
    if callback_query.from_user.id not in SUPPORT_ADMIN_IDS:
        await callback_query.answer("У вас нет прав для закрытия обращений.")
        return
    
    # Извлекаем ID пользователя из callback_data
    user_id = int(callback_query.data.split("_")[2])
    
    # Отмечаем тикет как закрытый (в реальном приложении здесь может быть обновление БД)
    await callback_query.message.edit_text(
        f"{callback_query.message.text}\n\n✅ Обращение закрыто.",
        reply_markup=None
    )
    
    # Отправляем уведомление пользователю
    try:
        await callback_query.bot.send_message(
            user_id,
            "✅ Ваше обращение в поддержку было закрыто.\n"
            "Если у вас остались вопросы, вы можете создать новое обращение.",
            reply_markup=keyboards.main_menu_keyboard()
        )
    except Exception as e:
        logging.error(f"Error notifying user about ticket closure: {e}", exc_info=True)
    
    await callback_query.answer("Обращение закрыто.")

# Команда для администраторов - статистика поддержки
@support_router.message(Command("support_stats"))
async def cmd_support_stats(message: Message):
    """Статистика обращений в поддержку (только для администраторов)"""
    if message.from_user.id not in SUPPORT_ADMIN_IDS:
        return
    
    # Здесь можно добавить логику для сбора статистики из базы данных
    # Например, количество обращений за день/неделю/месяц
    
    await message.answer(
        "📊 *Статистика обращений в поддержку*\n\n"
        "Функция в разработке.",
        parse_mode="Markdown"
    ) 