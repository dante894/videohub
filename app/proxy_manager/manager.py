from app.proxy_manager.pool import POOL


class ProxyManager:

    def __init__(self):

        self.index = 0

    def all(self):

        return POOL

    def next(self):

        if not POOL:
            return None

        proxy = POOL[self.index]

        self.index = (self.index + 1) % len(POOL)

        return proxy

    def success(self, proxy):

        proxy.success()

    def failure(self, proxy):

        proxy.failure()