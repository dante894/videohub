from pathlib import Path

from yt_dlp import YoutubeDL

from app.downloader.context import DownloadContext
from app.downloader.option import OptionBuilder
from app.downloader.core import DownloaderCore

from app.cookies.manager import CookieManager

from app.proxy_manager.manager import ProxyManager
from app.proxy_manager.pool import POOL

from app.retry.strategy import RetryStrategy

from app.diagnostic.network import NetworkDiagnostics

from app.core.logger import logger


class VideoDownloader:

    def __init__(self, download_path="downloads"):

        self.download_path = Path(download_path)
        self.download_path.mkdir(exist_ok=True)

        self.cookie_manager = CookieManager()
        self.proxy_manager = ProxyManager()

    def _build_context(self, url, quality="1080", audio=False):
        return DownloadContext(
            url=url,
            quality=str(quality),
            audio=audio,
            cookiefile=self.cookie_manager.get(),
        )

    def get_info(self, url):

        ctx = self._build_context(url)
        options = OptionBuilder.build(ctx, self.download_path)
        options["quiet"] = True
        options["skip_download"] = True

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

        try:
            diag = NetworkDiagnostics.geo()
            logger.info(f"Red actual: {diag}")
        except Exception as e:
            logger.warning(f"No se pudo obtener diagnóstico de red: {e}")

        ctx = self._build_context(url, quality=quality, audio=audio)
        options = OptionBuilder.build(ctx, self.download_path, hook=hook)

        try:
            filename, _info = DownloaderCore.download(url, options)
            return filename

        except Exception as e:
            logger.exception(e)

            if RetryStrategy.should_retry(e) and POOL:
                logger.info("Intentando otros proxies...")
                return self._download_with_proxy(ctx, hook, url)

            if RetryStrategy.should_retry(e) and not POOL:
                logger.warning(
                    "El error parece requerir un proxy distinto, pero no hay "
                    "ninguno configurado (YTDLP_PROXY / YTDLP_PROXY_AR / "
                    "YTDLP_PROXY_US / YTDLP_PROXY_EU en el .env). Se relanza "
                    "el error original de yt-dlp en vez de uno genérico."
                )

            raise
