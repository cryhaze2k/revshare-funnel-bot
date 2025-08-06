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

# --- Global Setup ---

# Configure logging to print info messages
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Webhook and Web App paths
WEBHOOK_PATH = f"/webhook/{BOT_TOKEN}"
WEBHOOK_URL = f"{BASE_URL}{WEBHOOK_PATH}"
WEBAPP_PATH = "/web_app"

# Create Bot, Dispatcher, and Storage instances
storage = MemoryStorage()
default_properties = DefaultBotProperties(parse_mode="HTML")
bot = Bot(token=BOT_TOKEN, default=default_properties)
dp = Dispatcher(storage=storage)

# Include routers from the 'handlers' directory
dp.include_router(admin.router)
dp.include_router(user_flow.router)


# --- Startup and Shutdown Logic ---

# CORRECTION: Removed the 'bot_instance' argument.
# The function will now use the global 'bot' object defined above.
async def on_startup():
    """Actions on startup: initialize DB and set webhook."""
    logging.info("Initializing database...")
    db.init_db()
    logging.info(f"Setting webhook to {WEBHOOK_URL}")
    await bot.set_webhook(WEBHOOK_URL, drop_pending_updates=True)

# CORRECTION: Removed the 'bot_instance' argument.
async def on_shutdown():
    """Actions on shutdown: delete webhook."""
    logging.warning('Shutting down..')
    await bot.delete_webhook()

# Register the startup and shutdown functions
dp.startup.register(on_startup)
dp.shutdown.register(on_shutdown)


# --- Web Application Setup ---

# Create the web application instance. Gunicorn will look for this.
app = web.Application()

# Create a webhook handler
webhook_requests_handler = SimpleRequestHandler(
    dispatcher=dp,
    bot=bot,
)

# Register the handler in the app to process requests from Telegram
webhook_requests_handler.register(app, path=WEBHOOK_PATH)

# Set up the rest of the aiogram components for the web app
setup_application(app, dp, bot=bot)

# Add a route to serve the static files for our Web App (for geolocation)
app.router.add_static(WEBAPP_PATH, path='web_app', name='webapp')

# This block is for local testing without Gunicorn
if __name__ == '__main__':
    logging.info("Starting web server for local development...")
    web.run_app(app, host="0.0.0.0", port=8080)