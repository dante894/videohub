from pathlib import Path
from dotenv import load_dotenv
import os

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

APP_NAME = os.getenv("APP_NAME", "VideoHub")

HOST = os.getenv("HOST", "0.0.0.0")

PORT = int(os.getenv("PORT", "5000"))

DOWNLOAD_PATH = os.getenv("DOWNLOAD_PATH", "downloads")

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///videohub.db")

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")

# --- Límites y plan PRO ---

# Descargas gratuitas permitidas por día (por usuario de Telegram)
FREE_DAILY_LIMIT = int(os.getenv("FREE_DAILY_LIMIT", "3"))

# Calidad máxima permitida (en píxeles de altura)
MAX_VIDEO_HEIGHT = int(os.getenv("MAX_VIDEO_HEIGHT", "1080"))

# Precio del plan PRO en pesos argentinos (ARS) y duración en días
PRO_PRICE_ARS = float(os.getenv("PRO_PRICE_ARS", "3000"))
PRO_DURATION_DAYS = int(os.getenv("PRO_DURATION_DAYS", "30"))

# Mercado Pago
MERCADOPAGO_ACCESS_TOKEN = os.getenv("MERCADOPAGO_ACCESS_TOKEN", "")

# Clave para firmar la cookie de sesión de Flask (identifica a cada
# visitante anónimo del sitio web para aplicar su límite diario).
# En producción, poné un valor largo y random en el .env.
FLASK_SECRET_KEY = os.getenv("FLASK_SECRET_KEY", "cambia-esta-clave-en-produccion")

# URL pública donde corre este Flask (para que Mercado Pago mande el webhook
# y para las páginas de retorno). En local con ngrok sería algo como
# https://xxxx.ngrok-free.app — NO puede ser localhost, MP no le llega.
PUBLIC_BASE_URL = os.getenv("PUBLIC_BASE_URL", "http://localhost:5000")

# Límite de Telegram para que un bot envíe archivos (API estándar)
TELEGRAM_MAX_FILE_MB = int(os.getenv("TELEGRAM_MAX_FILE_MB", "50"))
