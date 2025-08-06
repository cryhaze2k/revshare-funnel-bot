# main.py

import asyncio
import logging
from aiohttp import web

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
# ИЗМЕНЕНИЕ: Добавили новый импорт
from aiogram.client.default import DefaultBotProperties

from config import BOT_TOKEN, BASE_URL
from handlers import user_flow, admin
import db

# Путь для вебхука
WEBHOOK_PATH = f"/webhook/{BOT_TOKEN}"
# Полный URL для установки вебхука
WEBHOOK_URL = f"{BASE_URL}{WEBHOOK_PATH}"

# Путь к статическим файлам веб-приложения
WEBAPP_PATH = "/web_app"

async def on_startup(bot: Bot):
    """
    Действия при старте бота: инициализация БД и установка вебхука.
    """
    # Инициализируем базу данных
    db.init_db()
    # Устанавливаем вебхук
    await bot.set_webhook(WEBHOOK_URL)
    logging.info(f"Webhook set to {WEBHOOK_URL}")

def main():
    """
    Основная функция для запуска бота.
    """
    # Настройка логирования
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

    # ИЗМЕНЕНИЕ: Создаем объект Bot новым способом
    default_properties = DefaultBotProperties(parse_mode="HTML")
    bot = Bot(token=BOT_TOKEN, default=default_properties)

    # Используем MemoryStorage для хранения состояний FSM
    dp = Dispatcher(storage=MemoryStorage())

    # Регистрируем действия при старте
    dp.startup.register(on_startup)

    # Подключаем роутеры из других файлов
    dp.include_router(admin.router)
    dp.include_router(user_flow.router) # Роутер пользователя должен идти после админа

    # Создаем приложение aiohttp
    app = web.Application()

    # Регистрируем хендлер для вебхуков Telegram
    webhook_requests_handler = SimpleRequestHandler(
        dispatcher=dp,
        bot=bot,
    )
    webhook_requests_handler.register(app, path=WEBHOOK_PATH)

    # Настраиваем приложение aiohttp и запускаем
    setup_application(app, dp, bot=bot)

    # Добавляем маршрут для обслуживания статических файлов Web App
    app.router.add_static(WEBAPP_PATH, path='web_app', name='webapp')

    # Запускаем веб-сервер
    # В production на Render.com это будет Gunicorn или аналогичный сервер
    logging.info("Starting web server...")
    web.run_app(app, host="0.0.0.0", port=8080) # Render обычно использует порт 8080 или 10000

if __name__ == "__main__":
    main()