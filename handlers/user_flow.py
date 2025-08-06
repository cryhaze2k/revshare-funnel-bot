# handlers/user_flow.py
import logging
import requests
from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery, WebAppInfo
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from config import BANNED_COUNTRIES, IPINFO_TOKEN, SCENARIOS
import db
import keyboards as kb

# Создаем роутер для этого файла
router = Router()

# Определяем состояния (шаги воронки)
class UserFlow(StatesGroup):
    step_1 = State()
    step_2 = State()
    step_3 = State()
    step_4 = State()
    final = State()

# --- Хендлеры для старта и верификации ---

@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    """
    Начало диалога. Запрашиваем верификацию геолокации.
    """
    await message.answer(
        "Welcome! To continue, please verify your location.",
        reply_markup=kb.get_verify_keyboard()
    )

@router.message(F.web_app_data)
async def process_webapp_data(message: Message, state: FSMContext, bot: Bot):
    """
    Обрабатываем данные, полученные от Web App (геолокация).
    """
    web_app_data = message.web_app_data.data
    logging.info(f"Received web_app_data: {web_app_data}") # Логируем для отладки

    if "error" in web_app_data:
        await message.answer("Could not determine your location. Please try again.")
        return

    # Данные приходят как 'lat:xx,lon:yy'
    try:
        lat, lon = web_app_data.split(',')
        lat = lat.split(':')[1]
        lon = lon.split(':')[1]
    except (IndexError, ValueError) as e:
        logging.error(f"Error parsing web_app_data: {e}")
        await message.answer("Invalid location data format. Please try again.")
        return

    # Определяем страну по IP, используя ipinfo.io
    # Примечание: для большей точности лучше использовать координаты, 
    # но ipinfo бесплатен для IP и прост в использовании.
    # Мы получим IP пользователя из запроса к Telegram API (если он доступен)
    # или используем IP, с которого пришел запрос на наш веб-сервер.
    # Для простоты, мы используем сторонний сервис, который по координатам даст нам IP/страну.
    # Однако, ipinfo.io не работает напрямую с lat/lon в бесплатных планах.
    # Поэтому мы используем IP пользователя. В реальном проекте, Web App передал бы IP.
    # Для демонстрации, мы будем использовать API ipinfo для определения по IP.
    # **ВАЖНО**: Этот метод не идеален, так как IP может быть от VPN.
    # Запрос на ipinfo.io
    try:
        response = requests.get(f'https://ipinfo.io/json?token={IPINFO_TOKEN}')
        response.raise_for_status()
        data = response.json()
        country_code = data.get("country")
    except requests.RequestException as e:
        logging.error(f"IPInfo API error: {e}")
        await message.answer("There was an error verifying your location. Please contact support.")
        return
        
    if not country_code:
        await message.answer("Could not determine your country. Please try again.")
        return

    # Проверка на запрещенные страны
    if country_code in BANNED_COUNTRIES:
        await message.answer("Sorry, our service is not available in your country.")
        return

    # Сохраняем пользователя и его страну в БД
    db.add_or_update_user(message.from_user.id, message.from_user.username, country_code)
    
    # Получаем нужный сценарий
    scenario = SCENARIOS.get(country_code, SCENARIOS["DEFAULT"])
    await state.update_data(scenario=scenario)
    
    # Переходим к первому шагу воронки
    await state.set_state(UserFlow.step_1)
    await message.answer(scenario["texts"]["step1"], reply_markup=kb.get_next_keyboard())


# --- Хендлеры для шагов воронки ---

@router.callback_query(F.data == "next_step", UserFlow.step_1)
async def go_to_step_2(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    scenario = data.get("scenario")
    await callback.message.edit_text(
        scenario["texts"]["step2"],
        reply_markup=kb.get_next_keyboard()
    )
    await state.set_state(UserFlow.step_2)
    await callback.answer()

@router.callback_query(F.data == "next_step", UserFlow.step_2)
async def go_to_step_3(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    scenario = data.get("scenario")
    await callback.message.edit_text(
        scenario["texts"]["step3"],
        reply_markup=kb.get_next_keyboard()
    )
    await state.set_state(UserFlow.step_3)
    await callback.answer()

@router.callback_query(F.data == "next_step", UserFlow.step_3)
async def go_to_step_4(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    scenario = data.get("scenario")
    await callback.message.edit_text(
        scenario["texts"]["step4"],
        reply_markup=kb.get_final_keyboard(scenario["texts"]["final_button"])
    )
    await state.set_state(UserFlow.step_4)
    await callback.answer()
    
# --- Хендлер для финальной кнопки ---

@router.callback_query(F.data == "open_platform", UserFlow.step_4)
async def open_platform(callback: CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    
    # Получаем страну пользователя из БД
    country_code = db.get_user_country(user_id)
    if not country_code:
        await callback.message.answer("Error: Could not find your data. Please restart the bot with /start.")
        await callback.answer()
        return

    # Получаем партнерскую ссылку
    affiliate_link = db.get_affiliate_link(country_code)
    
    # Логируем клик
    db.log_final_click(user_id)
    
    # Получаем текст кнопки из сценария
    data = await state.get_data()
    scenario = data.get("scenario")
    
    # Отправляем сообщение с прямой ссылкой
    await callback.message.edit_text(
        "Here is your personal link to the platform:",
        reply_markup=kb.get_url_keyboard(scenario["texts"]["final_button"], affiliate_link)
    )
    
    # Завершаем состояние FSM
    await state.clear()
    await callback.answer(text="Link generated!", show_alert=False)