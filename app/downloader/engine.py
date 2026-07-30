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

<<<<<<< HEAD
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
=======
            if RetryStrategy.should_retry(e):
                logger.info("Intentando otros proxies...")
                return self._download_with_proxy(ctx, hook, url)
>>>>>>> e320f02e5d5d374d21667f2b5487fcac82b0ba10

            raise

    def _download_with_proxy(self, ctx, hook, url):
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
                ctx.proxy = proxy.url
                ctx.proxy_name = proxy.name
                options = OptionBuilder.build(ctx, self.download_path, hook=hook)

                filename, _info = DownloaderCore.download(url, options)

                logger.info(f"OK usando proxy {proxy.name}")
                self.proxy_manager.success(proxy)
                return filename

            except Exception as e:
                logger.warning(f"Falló proxy {proxy.name}: {e}")
                self.proxy_manager.failure(proxy)
                last_error = e

        raise last_error or RuntimeError(
            "No se pudo descargar con ninguno de los proxies disponibles."
        )
