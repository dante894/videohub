import shutil
from pathlib import Path

from app.config import YTDLP_COOKIES_FILE
from app.core.logger import logger

WRITABLE_PATH = Path("/tmp/videohub_cookies.txt")


class CookieManager:

    def __init__(self):
        self.cookiefile = self._prepare()

def _prepare(self):

    logger.info("=" * 60)
    logger.info("COOKIE MANAGER")
    logger.info("=" * 60)

    logger.info("YTDLP_COOKIES_FILE = %s", YTDLP_COOKIES_FILE)

    if not YTDLP_COOKIES_FILE:
        logger.warning("No hay cookies configuradas.")
        return None

    source = Path(YTDLP_COOKIES_FILE)

    logger.info("Ruta absoluta: %s", source.resolve())

    logger.info("Existe?: %s", source.exists())

    if not source.exists():
        logger.warning("No existe el archivo de cookies: %s", source)
        return None

    try:
        size = source.stat().st_size
        logger.info("Tamaño: %.2f KB", size / 1024)

    except Exception:
        logger.exception("No se pudo leer el tamaño del archivo")

    try:

        shutil.copyfile(source, WRITABLE_PATH)

        logger.info("Cookies copiadas correctamente")
        logger.info("Destino: %s", WRITABLE_PATH)

        return str(WRITABLE_PATH)

    except Exception as e:

        logger.exception("Error copiando cookies")

        return str(source)

        if not YTDLP_COOKIES_FILE:
            logger.warning("No hay cookies configuradas.")
            return None

        source = Path(YTDLP_COOKIES_FILE)

        if not source.exists():
            logger.warning(f"No existe el archivo de cookies: {source}")
            return None

        try:
            shutil.copyfile(source, WRITABLE_PATH)
            logger.info("Cookies copiadas a /tmp correctamente")
            return str(WRITABLE_PATH)

        except Exception as e:
            logger.exception(f"Error copiando cookies: {e}")
            return str(source)

    def get(self):
        return self.cookiefile

    def available(self):
        return self.cookiefile is not None