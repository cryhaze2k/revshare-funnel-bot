# keyboards.py
from aiogram.types import InlineKeyboardButton, WebAppInfo
from aiogram.utils.keyboard import InlineKeyboardBuilder
from config import BASE_URL

def get_verify_keyboard():
    """Клавиатура для запроса верификации через Web App. [cite: 463]"""
    builder = InlineKeyboardBuilder()
    web_app = WebAppInfo(url=f"{BASE_URL}/web_app") # URL нашего веб-приложения
    builder.add(InlineKeyboardButton(text="✅ Verify Location", web_app=web_app))
    return builder.as_markup()

def get_next_keyboard(text: str = "Next ➡️"):
    """Клавиатура с кнопкой 'Next'. [cite: 424]"""
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(text=text, callback_data="next_step"))
    return builder.as_markup()

def get_final_keyboard(button_text: str):
    """Финальная кнопка для перехода на платформу (сначала как callback). [cite: 444, 446]"""
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(text=button_text, callback_data="open_platform"))
    return builder.as_markup()

def get_url_keyboard(button_text: str, url: str):
    """Кнопка с прямой ссылкой. [cite: 430]"""
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(text=button_text, url=url))
    return builder.as_markup()

def get_admin_keyboard():
    """Интерактивная админ-панель (опционально, но улучшает UX). [cite: 508]"""
    builder = InlineKeyboardBuilder()
    builder.button(text="📊 Статистика", callback_data="admin_stats")
    builder.button(text="✏️ Изменить ссылку", callback_data="admin_set_link")
    builder.button(text="📢 Рассылка", callback_data="admin_broadcast")
    builder.adjust(1) # Все кнопки в один столбец
    return builder.as_markup()