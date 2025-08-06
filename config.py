# config.py
import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
IPINFO_TOKEN = os.getenv("IPINFO_TOKEN")
BASE_URL = os.getenv("BASE_URL")

# Преобразуем строку с ID администраторов в список целых чисел
ADMIN_IDS_STR = os.getenv("ADMIN_IDS", "")
ADMIN_IDS = [int(admin_id) for admin_id in ADMIN_IDS_STR.split(',') if admin_id]

# Список запрещенных стран [cite: 396, 469]
BANNED_COUNTRIES = ["RU"] 

# Сценарии для разных стран [cite: 408, 677, 703]
# Фактические тексты должны быть предоставлены заказчиком [cite: 666]
SCENARIOS = {
    "CA": {
        "lang": "en",
        "currency": "CAD$",
        "texts": {
            "step1": "Step 1/4: Welcome! This service will guide you through the setup process. Please follow the instructions carefully.",
            "step2": "Step 2/4: Great. Now, make sure you are in a supported region and have a stable connection.",
            "step3": "Step 3/4: Almost there. Our platform offers various features. Remember to use it responsibly.",
            "step4": "Step 4/4: All set! Click the button below to access the platform.",
            "final_button": "Open Platform"
        }
    },
    "ES": {
        "lang": "es",
        "currency": "€",
        "texts": {
            "step1": "Paso 1/4: ¡Bienvenido! Este servicio te guiará a través del proceso de configuración. Sigue las instrucciones.",
            "step2": "Paso 2/4: Genial. Ahora, asegúrate de estar en una región compatible y tener una conexión estable.",
            "step3": "Paso 3/4: Casi listo. Nuestra plataforma ofrece varias funciones. Recuerda usarla de manera responsable.",
            "step4": "Paso 4/4: ¡Todo listo! Haz clic en el botón de abajo para acceder a la plataforma.",
            "final_button": "Abrir Plataforma"
        }
    },
    # Можно добавить другие страны по аналогии
    "DEFAULT": {
        "lang": "en",
        "currency": "$",
        "texts": {
            "step1": "Step 1/4: Welcome! This service will guide you through the setup process. Please follow the instructions carefully.",
            "step2": "Step 2/4: Great. Now, make sure you are in a supported region and have a stable connection.",
            "step3": "Step 3/4: Almost there. Our platform offers various features. Remember to use it responsibly.",
            "step4": "Step 4/4: All set! Click the button below to access the platform.",
            "final_button": "Open Platform"
        }
    }
}