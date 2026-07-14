from app.downloader.engine import VideoDownloader
from app.services.queue_service import QueueService
from app.socket_manager import socketio
from app.core.logger import logger


class DownloadService:

    def __init__(self):
        self.engine = VideoDownloader()
        self.queue = QueueService()
        self.queue.start(self.process_download)

    def analyze(self, url):
        return self.engine.get_info(url)

    def enqueue(self, url, quality="1080", audio=False, user=None,
                on_complete=None, on_error=None):
        """Agrega una tarea de descarga a la cola.

        on_complete(filepath) y on_error(mensaje) son callbacks opcionales,
        usados por ejemplo por el bot de Telegram para enviar el archivo
        resultante al chat correspondiente cuando termina.
        """
        task = {
            "url": url,
            "quality": quality,
            "audio": audio,
            "user": user,
            "on_complete": on_complete,
            "on_error": on_error,
        }
        self.queue.add(task)

    def process_download(self, task):
        url = task["url"]
        try:
            filename = self.engine.download(
                url,
                quality=task.get("quality", "1080"),
                audio=task.get("audio", False),
                progress_callback=self._on_progress,
            )
            socketio.emit("download_complete", {"url": url, "file": filename})

            if task.get("on_complete"):
                task["on_complete"](filename)

        except Exception as e:
            logger.exception(e)
            socketio.emit("download_error", {"url": url, "error": str(e)})

            if task.get("on_error"):
                task["on_error"](str(e))

    def _on_progress(self, d):
        status = d.get("status")

        if status == "downloading":
            socketio.emit("progress", {
                "percent": (d.get("_percent_str") or "0%").strip(),
                "speed": (d.get("_speed_str") or "N/A").strip(),
                "eta": (d.get("_eta_str") or "N/A").strip(),
            })
        elif status == "finished":
            socketio.emit("progress", {
                "percent": "100%",
                "speed": "-",
                "eta": "0s",
            })

    def download_now(self, url, quality="1080", audio=False):
        """
        Descarga el archivo de forma síncrona (sin cola).
        Devuelve la ruta del archivo descargado.
        """
        return self.engine.download(
        url,
        quality=quality,
        audio=audio,
        progress_callback=None,
    )