from time import time

from .pool import POOL


class ProxyManager:

    def __init__(self):

        self.index = 0

    def next(self):

        if not POOL:
            return None

        total = len(POOL)

        for _ in range(total):

            proxy = POOL[self.index]

            self.index = (self.index + 1) % total

            if proxy.available():
                return proxy

        return None

    def success(self, proxy):

        proxy.enabled = True

        proxy.failures = 0

        proxy.last_success = time()

    def failure(self, proxy):

        proxy.failures += 1

        proxy.enabled = False

        proxy.last_failure = time()


proxy_manager = ProxyManager()