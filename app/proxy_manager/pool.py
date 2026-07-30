from app.config import (
    YTDLP_PROXY,
    YTDLP_PROXY_AR,
    YTDLP_PROXY_US,
    YTDLP_PROXY_EU,
)

from .proxy import Proxy


POOL = []

if YTDLP_PROXY:
    POOL.append(
        Proxy(
            "DEFAULT",
            YTDLP_PROXY,
            "DEFAULT",
        )
    )

if YTDLP_PROXY_AR:
    POOL.append(
        Proxy(
            "AR",
            YTDLP_PROXY_AR,
            "Argentina",
        )
    )

if YTDLP_PROXY_US:
    POOL.append(
        Proxy(
            "US",
            YTDLP_PROXY_US,
            "USA",
        )
    )

if YTDLP_PROXY_EU:
    POOL.append(
        Proxy(
            "EU",
            YTDLP_PROXY_EU,
            "Europa",
        )
    )