# handlers/admin.py
import asyncio
from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command, Filter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.exceptions import TelegramBadRequest

import db
from config import ADMIN_IDS
import keyboards as kb

router = Router()

# --- Фильтр для проверки, является ли пользователь админом ---
class AdminFilter(Filter):
    async def __call__(self, message: Message) -> bool:
        return message.from_user.id in ADMIN_IDS

# --- Состояния для админских действий ---
class AdminStates(StatesGroup):
    set_link_country = State()
    set_link_url = State()
    broadcast_message = State()

# --- Основные команды админа ---

@router.message(Command("admin"), AdminFilter())
async def cmd_admin_panel(message: Message):
    """
    Показывает админ-панель.
    """
    await message.answer("Админ-панель:", reply_markup=kb.get_admin_keyboard())

@router.callback_query(F.data == "admin_stats", AdminFilter())
async def show_stats(callback: CallbackQuery):
    """
    Показывает статистику.
    """
    stats = db.get_stats()
    
    users_by_country_str = "\n".join([f"  - {country}: {count}" for country, count in stats['users_by_country']])
    clicks_by_country_str = "\n".join([f"  - {country}: {count}" for country, count in stats['clicks_by_country']])
    
    stats_text = (
        f"📊 **Статистика Бота**\n\n"
        f"👤 **Всего пользователей:** {stats['total_users']}\n\n"
        f"🌍 **Пользователей по странам:**\n{users_by_country_str or 'Нет данных'}\n\n"
        f"🖱️ **Всего переходов по ссылкам:** {stats['total_clicks']}\n\n"
        f"📈 **Переходов по странам:**\n{clicks_by_country_str or 'Нет данных'}"
    )
    await callback.message.answer(stats_text, parse_mode="Markdown")
    await callback.answer()

# --- Логика изменения ссылки ---

@router.callback_query(F.data == "admin_set_link", AdminFilter())
async def set_link_start(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer("Введите код страны (например, CA, ES, DEFAULT):")
    await state.set_state(AdminStates.set_link_country)
    await callback.answer()

@router.message(AdminStates.set_link_country, AdminFilter())
async def set_link_country(message: Message, state: FSMContext):
    country_code = message.text.upper()
    await state.update_data(country_code=country_code)
    await message.answer(f"Отлично. Теперь введите новую ссылку для {country_code}:")
    await state.set_state(AdminStates.set_link_url)

@router.message(AdminStates.set_link_url, AdminFilter())
async def set_link_url(message: Message, state: FSMContext):
    new_url = message.text
    data = await state.get_data()
    country_code = data['country_code']
    
    if db.update_affiliate_link(country_code, new_url):
        await message.answer(f"✅ Ссылка для страны {country_code} успешно обновлена.")
    else:
        await message.answer(f"❌ Ошибка: страна {country_code} не найдена в базе. Используйте CA, ES или DEFAULT.")
    
    await state.clear()

# --- Логика рассылки ---

@router.callback_query(F.data == "admin_broadcast", AdminFilter())
async def broadcast_start(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer("Введите сообщение для рассылки всем пользователям:")
    await state.set_state(AdminStates.broadcast_message)
    await callback.answer()

@router.message(AdminStates.broadcast_message, AdminFilter())
async def process_broadcast(message: Message, state: FSMContext, bot: Bot):
    await state.clear()
    user_ids = db.get_all_user_ids()
    
    success_count = 0
    error_count = 0
    
    await message.answer(f"Начинаю рассылку для {len(user_ids)} пользователей...")
    
    for user_id in user_ids:
        try:
            # Копируем сообщение, чтобы сохранить форматирование, фото и т.д.
            await bot.copy_message(chat_id=user_id, from_chat_id=message.chat.id, message_id=message.message_id)
            success_count += 1
        except TelegramBadRequest as e:
            if "bot was blocked by the user" in e.message:
                db.set_user_inactive(user_id) # Деактивируем пользователя
                error_count += 1
            else:
                error_count += 1
        except Exception:
            error_count += 1
        await asyncio.sleep(0.1) # Небольшая задержка, чтобы не превышать лимиты Telegram
        
    await message.answer(
        f"✅ Рассылка завершена!\n"
        f"Успешно отправлено: {success_count}\n"
        f"Ошибок (включая заблокировавших): {error_count}"
    )