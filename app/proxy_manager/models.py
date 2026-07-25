from dataclasses import dataclass
from time import time


@dataclass
class Proxy:

    name: str
    url: str
    country: str

    enabled: bool = True

    failures: int = 0

    last_failure: float = 0

    last_success: float = 0

    cooldown: int = 300

    def available(self):

        if self.enabled:
            return True

        return (time() - self.last_failure) > self.cooldown