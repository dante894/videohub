from pathlib import Path
from dotenv import load_dotenv
import os

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent


def _env(key, default=""):
    """Como os.getenv, pero trata '' (variable creada pero vacía, algo
    común en paneles como Render/Railway) igual que si no existiera."""
    value = os.getenv(key)
    if value is None or value.strip() == "":
        return default
    return value.strip()


def _int_env(key, default):
    value = _env(key, "")
    return int(value) if value else default


def _float_env(key, default):
    value = _env(key, "")
    return float(value) if value else default


APP_NAME = _env("APP_NAME", "VideoHub")

HOST = _env("HOST", "0.0.0.0")

PORT = _int_env("PORT", 5000)

DOWNLOAD_PATH = _env("DOWNLOAD_PATH", "downloads")

DATABASE_URL = _env("DATABASE_URL", "sqlite:///videohub.db")

TELEGRAM_TOKEN = _env("TELEGRAM_TOKEN", None)

# --- Límites y plan PRO ---

# Descargas gratuitas permitidas por día (por usuario de Telegram)
FREE_DAILY_LIMIT = _int_env("FREE_DAILY_LIMIT", 3)

# Descargas permitidas por día para usuarios PRO (ya no ilimitadas)
PRO_DAILY_LIMIT = _int_env("PRO_DAILY_LIMIT", 10)

# Calidad máxima permitida (en píxeles de altura)
MAX_VIDEO_HEIGHT = _int_env("MAX_VIDEO_HEIGHT", 1080)

# Precio del plan PRO en pesos argentinos (ARS) y duración en días
PRO_PRICE_ARS = _float_env("PRO_PRICE_ARS", 3000)
PRO_DURATION_DAYS = _int_env("PRO_DURATION_DAYS", 30)

# Mercado Pago
MERCADOPAGO_ACCESS_TOKEN = _env("MERCADOPAGO_ACCESS_TOKEN", "")

# Clave para firmar la cookie de sesión de Flask (identifica a cada
# visitante anónimo del sitio web para aplicar su límite diario).
# En producción, poné un valor largo y random en el .env.
FLASK_SECRET_KEY = _env("FLASK_SECRET_KEY", "cambia-esta-clave-en-produccion")

# URL pública donde corre este Flask (para que Mercado Pago mande el webhook
# y para las páginas de retorno). En local con ngrok sería algo como
# https://xxxx.ngrok-free.app — NO puede ser localhost, MP no le llega.
PUBLIC_BASE_URL = _env("PUBLIC_BASE_URL", "http://localhost:5000")

# Límite de Telegram para que un bot envíe archivos (API estándar)
TELEGRAM_MAX_FILE_MB = _int_env("TELEGRAM_MAX_FILE_MB", 50)

# Ruta a un cookies.txt exportado de una cuenta real de YouTube (formato
# Netscape). Ayuda a esquivar el bloqueo "Sign in to confirm you're not
# a bot" que YouTube aplica seguido a IPs de datacenter (Render, Railway,
# etc). En Render: subilo como "Secret File" y queda en /etc/secrets/<nombre>.
YTDLP_COOKIES_FILE = _env("YTDLP_COOKIES_FILE", "")

# Proxy opcional para yt-dlp (formato http://user:pass@host:puerto o
# socks5://host:puerto). Sirve para esquivar videos geobloqueados a un
# país distinto al del servidor (p. ej. contenido restringido a
# Argentina corriendo el bot desde EE.UU./Render). Requiere contratar un
# servicio de proxy con salida en el país que necesites; dejalo vacío si
# no tenés uno.
YTDLP_PROXY = _env("YTDLP_PROXY", "")
