from app.core.logger import logger


REGION_ERRORS = [
    "not available in your country",
    "video unavailable",
    "blocked",
    "geo",
    "country",
]

BOT_ERRORS = [
    "sign in to confirm you're not a bot",
    "confirm you are not a bot",
    "please sign in",
]

NETWORK_ERRORS = [
    "403",
    "forbidden",
    "proxyerror",
    "timed out",
    "connection reset",
]


class RetryStrategy:

    @staticmethod
    def classify(error: Exception):

        text = str(error).lower()

        if any(x in text for x in REGION_ERRORS):
            return "region"

        if any(x in text for x in BOT_ERRORS):
            return "bot"

        if any(x in text for x in NETWORK_ERRORS):
            return "network"

        return "unknown"

    @staticmethod
    def should_retry(error: Exception):

        kind = RetryStrategy.classify(error)

        logger.warning(f"Error clasificado como: {kind}")

        return kind in {"region", "bot", "network"}