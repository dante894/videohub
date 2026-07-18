import shutil
from pathlib import Path

from yt_dlp import YoutubeDL

from app.core.logger import logger

from app.config import (
    MAX_VIDEO_HEIGHT,
    YTDLP_COOKIES_FILE,
    YTDLP_PROXY,
    YTDLP_PROXY_AR,
    YTDLP_PROXY_US,
    YTDLP_PROXY_EU,
)

QUALITY_HEIGHTS = {
    "1080": 1080,
    "720": 720,
    "480": 480,
    "360": 360,
}

_WRITABLE_COOKIES_PATH = Path("/tmp/videohub_cookies.txt")

PROXIES = [
    ("DEFAULT", YTDLP_PROXY),
    ("AR", YTDLP_PROXY_AR),
    ("US", YTDLP_PROXY_US),
    ("EU", YTDLP_PROXY_EU),
]

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

    def _anti_bot_options(self, proxy=None):

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

        if proxy:
            options["proxy"] = proxy

        return options


    def _download_with_proxy(self, options, url):

    last_error = None

    for region, proxy in PROXIES:

        if not proxy:
            continue

        try:

            logger.info(f"Probando proxy {region}")

            opts = options.copy()
            opts.update(self._anti_bot_options(proxy))

            with YoutubeDL(opts) as ydl:

                info = ydl.extract_info(url, download=True)
                filename = ydl.prepare_filename(info)

            logger.info(f"Descarga OK usando {region}")

            return filename, info

        except Exception as e:

            logger.warning(f"{region} falló: {e}")
            last_error = e

    raise last_error

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

        except Exception as e:
        
            texto = str(e).lower()
        
            region_errors = (
                "not available in your country",
                "blocked",
                "geo",
                "country",
                "video unavailable",
                "403",
                "forbidden",
                "requested format is not available",
                "playability",
            )
        
            if any(x in texto for x in region_errors):
        
                logger.info("Intentando otros proxies...")
        
                filename, info = self._download_with_proxy(
                    options,
                    url,
                )
        
            else:
                raise
        
