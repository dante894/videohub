import requests

from app.core.logger import logger


class NetworkDiagnostics:

    @staticmethod
    def public_ip(proxy=None):

        try:
            r = requests.get(
                "https://api.ipify.org?format=json",
                proxies={"http": proxy, "https": proxy} if proxy else None,
                timeout=10,
            )

            return r.json().get("ip")

        except Exception as e:
            logger.warning(f"No se pudo obtener IP: {e}")
            return None

    @staticmethod
    def geo(proxy=None):

        try:
            r = requests.get(
                "https://ipinfo.io/json",
                proxies={"http": proxy, "https": proxy} if proxy else None,
                timeout=10,
            )

            data = r.json()

            return {
                "ip": data.get("ip"),
                "country": data.get("country"),
                "city": data.get("city"),
                "org": data.get("org"),
            }

        except Exception as e:
            logger.warning(f"No se pudo obtener geolocalización: {e}")
            return {}

    @staticmethod
    def check_proxy(proxy):

        try:
            ip = NetworkDiagnostics.public_ip(proxy)

            if ip:
                logger.info(f"Proxy OK: {ip}")
                return True

            return False

        except Exception as e:
            logger.warning(f"Proxy FAIL: {e}")
            return False