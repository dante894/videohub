from dataclasses import dataclass
from typing import Optional


@dataclass
class DownloadContext:

    url: str

    quality: str = "1080"

    audio: bool = False

    proxy: Optional[str] = None

    proxy_name: Optional[str] = None

    cookiefile: Optional[str] = None

    player_client: str = "android"

    attempt: int = 1

    max_attempts: int = 5