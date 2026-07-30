import shutil
from pathlib import Path

from app.config import YTDLP_COOKIES_FILE
from app.core.logger import logger

WRITABLE_PATH = Path("/tmp/videohub_cookies.txt")


class CookieManager:

    def __init__(self):
        self.cookiefile = self._prepare()

    def _prepare(self):

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