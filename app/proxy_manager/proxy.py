from dataclasses import dataclass
from datetime import datetime


@dataclass
class Proxy:

    name: str

    url: str

    country: str

    enabled: bool = True

    failures: int = 0

    last_failure: datetime | None = None

    successes: int = 0

    priority: int = 100

    def available(self):

        return self.enabled

    def success(self):

        self.successes += 1

        self.failures = 0

    def failure(self):

        self.failures += 1

        self.last_failure = datetime.utcnow()