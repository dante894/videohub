from pathlib import Path
from yt_dlp import YoutubeDL

from app.config import MAX_VIDEO_HEIGHT

QUALITY_HEIGHTS = {
    "1080": 1080,
    "720": 720,
    "480": 480,
    "360": 360,
}


class VideoDownloader:

    def __init__(self, download_path="downloads"):
        self.download_path = Path(download_path)
        self.download_path.mkdir(exist_ok=True)

    def get_info(self, url):
        options = {
            "quiet": True,
            "skip_download": True,
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
            }
        else:
            options = {
                "outtmpl": str(self.download_path / "%(title)s.%(ext)s"),
                "format": (
                    f"bestvideo[height<={height}]+bestaudio/"
                    f"best[height<={height}]"
                ),
                "merge_output_format": "mp4",
                "progress_hooks": [hook],
                "quiet": True,
            }

        with YoutubeDL(options) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)

        if audio:
            # FFmpegExtractAudio cambia la extensión final a mp3
            filename = str(Path(filename).with_suffix(".mp3"))

        return filename
