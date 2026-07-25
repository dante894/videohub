import shutil
from pathlib import Path

from yt_dlp import YoutubeDL

from app.core.logger import logger
from app.proxy_manager.manager import proxy_manager
from app.proxy_manager.pool import POOL

from app.config import (
    MAX_VIDEO_HEIGHT,
    YTDLP_COOKIES_FILE,
)

QUALITY_HEIGHTS = {
    "1080": 1080,
    "720": 720,
    "480": 480,
    "360": 360,
}

# Errores típicos de geo-bloqueo / bloqueo anti-bot que justifican
# reintentar la descarga rotando de proxy.
REGION_ERRORS = (
    "not available in your country",
    "blocked",
    "geo",
    "country",
    "video unavailable",
    "403",
    "forbidden",
    "requested format is not available",
    "playability",
    "sign in to confirm",
)

_WRITABLE_COOKIES_PATH = Path("/tmp/videohub_cookies.txt")


class VideoDownloader:

    def __init__(self, download_path="downloads"):

        self.download_path = Path(download_path)
        self.download_path.mkdir(exist_ok=True)

        self.cookies_file = self._prepare_cookies_file()

    def _prepare_cookies_file(self):

        if not YTDLP_COOKIES_FILE:
            logger.warning("No hay archivo de cookies.")
            return None

        source = Path(YTDLP_COOKIES_FILE)

        if not source.exists():
            logger.warning("No existe %s", source)
            return None

        try:
            shutil.copyfile(source, _WRITABLE_COOKIES_PATH)
            return str(_WRITABLE_COOKIES_PATH)

        except Exception:
            logger.exception("No se pudieron copiar las cookies.")
            return str(source)

    def _anti_bot_options(self, proxy_url=None):

        options = {
            "extractor_args": {
                "youtube": {
                    "player_client": [
                        "android",
                        "web",
                        "ios",
                    ]
                }
            }
        }

        if self.cookies_file:
            options["cookiefile"] = self.cookies_file

        if proxy_url:
            options["proxy"] = proxy_url

        return options

    def _is_region_error(self, error):
        texto = str(error).lower()
        return any(x in texto for x in REGION_ERRORS)

    def _download_with_proxy(self, options, url):
        """Reintenta la descarga rotando por todos los proxies disponibles
        en el pool. Devuelve el filename resultante o relanza el último
        error si ninguno funcionó."""

        last_error = None

        if not POOL:
            logger.warning("No hay proxies configurados para reintentar.")
            raise RuntimeError("No hay proxies disponibles para reintentar.")

        for proxy in POOL:

            if not proxy.available():
                continue

            logger.info(f"Probando proxy {proxy.name} ({proxy.country})")

            try:
                opts = options.copy()
                opts.update(self._anti_bot_options(proxy.url))

                with YoutubeDL(opts) as ydl:
                    info = ydl.extract_info(url, download=True)
                    filename = ydl.prepare_filename(info)

                logger.info(f"OK usando proxy {proxy.name}")
                proxy_manager.success(proxy)
                return filename

            except Exception as e:
                logger.warning(f"Falló proxy {proxy.name}: {e}")
                proxy_manager.failure(proxy)
                last_error = e

        raise last_error or RuntimeError(
            "No se pudo descargar con ninguno de los proxies disponibles."
        )

    def get_info(self, url):

        options = {
            "quiet": True,
            "skip_download": True,
            **self._anti_bot_options(),
        }

        with YoutubeDL(options) as ydl:
            info = ydl.extract_info(url, download=False)

        return {
            "title": info.get("title"),
            "duration": info.get("duration"),
            "thumbnail": info.get("thumbnail"),
            "uploader": info.get("uploader"),
            "webpage_url": info.get("webpage_url"),
        }

    def download(
        self,
        url,
        quality="1080",
        audio=False,
        progress_callback=None,
    ):

        def hook(d):
            if progress_callback:
                progress_callback(d)

        height = min(
            QUALITY_HEIGHTS.get(str(quality), MAX_VIDEO_HEIGHT),
            MAX_VIDEO_HEIGHT,
        )

        if audio:

            options = {
                "outtmpl": str(self.download_path / "%(title)s.%(ext)s"),
                "format": "bestaudio/best",
                "postprocessors": [{
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "mp3",
                    "preferredquality": "192",
                }],
                "progress_hooks": [hook],
                "quiet": True,
                **self._anti_bot_options(),
            }

        else:

            options = {
                "outtmpl": str(self.download_path / "%(title)s.%(ext)s"),
                "format": (
                    f"bestvideo[height<={height}]"
                    "+bestaudio/"
                    f"best[height<={height}]/"
                    "bestvideo+bestaudio/best"
                ),
                "merge_output_format": "mp4",
                "progress_hooks": [hook],
                "quiet": True,
                **self._anti_bot_options(),
            }

        try:

            with YoutubeDL(options) as ydl:

                info = ydl.extract_info(
                    url,
                    download=True,
                )

                filename = ydl.prepare_filename(info)

            return filename

        except Exception as e:
            logger.exception(e)

            if self._is_region_error(e):
                logger.info("Intentando otros proxies...")
                return self._download_with_proxy(options, url)

            raise
