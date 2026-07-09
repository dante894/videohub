from dataclasses import dataclass
from datetime import datetime
from uuid import uuid4

@dataclass
class DownloadTask:

    id: str

    url: str

    quality: str = "best"

    audio: bool = False

    platform: str = "youtube"

    status: str = "waiting"

    created_at: datetime = datetime.now()

    @staticmethod
    def create(url, quality="best", audio=False):

        return DownloadTask(
            id=str(uuid4()),
            url=url,
            quality=quality,
            audio=audio
        )