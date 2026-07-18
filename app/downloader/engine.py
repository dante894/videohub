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
