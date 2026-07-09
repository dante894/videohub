from dataclasses import dataclass


@dataclass
class VideoInfo:

    title: str

    uploader: str

    duration: int

    thumbnail: str

    url: str

    qualities: list