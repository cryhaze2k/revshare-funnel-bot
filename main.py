# main.py

import asyncio
import logging

from aiohttp import web
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.client.default import DefaultBotProperties
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application

from config import BOT_TOKEN, BASE_URL
from handlers import user_flow, admin
import db

# --- Глобальная настройка ---

# Настройка логирования для вывода информации в консоль
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Пути для вебхука и веб-приложения
WEBHOOK_PATH = f"/webhook/{BOT_TOKEN}"
WEBHOOK_URL = f"{BASE_URL}{WEBHOOK_PATH}"
WEBAPP_PATH = "/web_app"

# Создаем объекты бота, диспетчера и хранилища
storage = MemoryStorage()
default_properties = DefaultBotProperties(parse_mode="HTML")
bot = Bot(token=BOT_TOKEN, default=default_properties)
dp = Dispatcher(storage=storage)

# Подключаем роутеры из папки handlers
dp.include_router(admin.router)
dp.include_router(user_flow.router)

# --- Логика запуска и остановки ---

async def on_startup(bot_instance: Bot):
    """Действия при старте: инициализация БД и установка вебхука."""
    logging.info("Initializing database...")
    db.init_db()
    logging.info(f"Setting webhook to {WEBHOOK_URL}")
    await bot_instance.set_webhook(WEBHOOK_URL, drop_pending_updates=True)

async def on_shutdown(bot_instance: Bot):
    """Действия при остановке: удаляем вебхук."""
    logging.warning('Shutting down..')
    await bot_instance.delete_webhook()

# Регистрируем функции запуска и остановки
dp.startup.register(on_startup)
dp.shutdown.register(on_shutdown)

# --- Настройка веб-приложения ---

# Создаем объект веб-приложения. Gunicorn будет искать именно его.
app = web.Application()

# Создаем обработчик для вебхуков
webhook_requests_handler = SimpleRequestHandler(
    dispatcher=dp,
    bot=bot,
)

# Регистрируем обработчик в приложении для обработки запросов от Telegram
webhook_requests_handler.register(app, path=WEBHOOK_PATH)

# Настраиваем остальные части aiogram для работы с веб-приложением
setup_application(app, dp, bot=bot)

# Добавляем маршрут для обслуживания статических файлов нашего Web App (для геолокации)
app.router.add_static(WEBAPP_PATH, path='web_app', name='webapp')

# Этот блок нужен для локального запуска без Gunicorn (например, на вашем компьютере)
if __name__ == '__main__':
    logging.info("Starting web server for local development...")
    web.run_app(app, host="0.0.0.0", port=8080)