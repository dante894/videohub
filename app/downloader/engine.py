import shutil
from pathlib import Path
from yt_dlp import YoutubeDL

from app.config import MAX_VIDEO_HEIGHT, YTDLP_COOKIES_FILE
from app.core.logger import logger

QUALITY_HEIGHTS = {
    "1080": 1080,
    "720": 720,
    "480": 480,
    "360": 360,
}

# yt-dlp reescribe el archivo de cookies después de cada uso (para
# persistir cookies renovadas). Si YTDLP_COOKIES_FILE apunta a un Secret
# File de Render, ese archivo es de solo lectura, así que trabajamos
# siempre sobre una copia en un lugar donde sí se pueda escribir.
_WRITABLE_COOKIES_PATH = Path("/tmp/videohub_cookies.txt")


class VideoDownloader:

    def __init__(self, download_path="downloads"):
        self.download_path = Path(download_path)
        self.download_path.mkdir(exist_ok=True)
        self.cookies_file = self._prepare_cookies_file()

    def _prepare_cookies_file(self):
        if not YTDLP_COOKIES_FILE:
            return None

        source = Path(YTDLP_COOKIES_FILE)

        if not source.exists():
            logger.warning("YTDLP_COOKIES_FILE configurado pero no existe: %s", source)
            return None

        try:
            shutil.copyfile(source, _WRITABLE_COOKIES_PATH)
            return str(_WRITABLE_COOKIES_PATH)
        except Exception as e:
            logger.exception(e)
            # Si por algún motivo no se pudo copiar, probamos igual con el
            # original (puede fallar si yt-dlp necesita reescribirlo).
            return str(source)

    def _anti_bot_options(self):
        """Mitigaciones para el bloqueo "Sign in to confirm you're not a
        bot" que YouTube aplica seguido a IPs de datacenter (Render,
        Railway, etc):

        1) Forzar el cliente "android" de YouTube, que en general no pide
           esta verificación (a veces alcanza solo con esto).
        2) Si se configuró YTDLP_COOKIES_FILE (cookies.txt de una cuenta
           real), usarlas: es la mitigación más confiable.
        """
        options = {
            "extractor_args": {
                "youtube": {"player_client": ["android", "web", "ios"]}
            }
        }

        if self.cookies_file:
            options["cookiefile"] = self.cookies_file

        return options

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

    def download(self, url, quality="1080", audio=False, progress_callback=None):
        """Descarga el video en la calidad pedida (tope MAX_VIDEO_HEIGHT) o el audio en MP3."""

        def hook(d):
            if progress_callback:
                progress_callback(d)

        # Nunca se permite superar la calidad máxima configurada (1080p por defecto),
        # sin importar lo que pida el usuario.
        height = min(QUALITY_HEIGHTS.get(str(quality), MAX_VIDEO_HEIGHT), MAX_VIDEO_HEIGHT)

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
                    f"bestvideo[height<={height}]+bestaudio/"
                    f"best[height<={height}]/"
                    # Respaldo final: si el cliente de YouTube que estamos
                    # usando no expone NINGÚN formato <= height para este
                    # video puntual, mejor traer el mejor disponible que
                    # fallar directo. En la práctica casi nunca se llega
                    # a esta rama, porque YouTube casi siempre ofrece algo
                    # igual o menor a 1080p.
                    "bestvideo+bestaudio/best"
                ),
                "merge_output_format": "mp4",
                "progress_hooks": [hook],
                "quiet": True,
                **self._anti_bot_options(),
            }

        with YoutubeDL(options) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)

        if audio:
            # FFmpegExtractAudio cambia la extensión final a mp3
            filename = str(Path(filename).with_suffix(".mp3"))

        return filename
