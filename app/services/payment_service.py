import mercadopago

from app.config import (
    MERCADOPAGO_ACCESS_TOKEN,
    PRO_PRICE_ARS,
    PRO_DURATION_DAYS,
    PUBLIC_BASE_URL,
)
from app.core.logger import logger

_sdk = None


def _get_sdk():
    global _sdk
    if _sdk is None:
        if not MERCADOPAGO_ACCESS_TOKEN:
            raise RuntimeError(
                "Falta MERCADOPAGO_ACCESS_TOKEN en el .env. "
                "Consíguelo en https://www.mercadopago.com.ar/developers/panel/app"
            )
        _sdk = mercadopago.SDK(MERCADOPAGO_ACCESS_TOKEN)
    return _sdk


def create_pro_preference(user_key, back_base_url=None):
    """Crea una preferencia de pago (Checkout Pro) para que el usuario
    pague el plan PRO. Devuelve la URL a la que hay que mandarlo a pagar.

    user_key viaja en external_reference para poder identificar, cuando
    llegue el webhook, a quién hay que activarle el PRO. Debe venir ya
    formado, p. ej. "tg:123456789" (Telegram) o "web:<uuid-de-sesion>"
    (sitio web).
    """
    sdk = _get_sdk()

    base_url = back_base_url or PUBLIC_BASE_URL

    preference_data = {
        "items": [
            {
                "title": f"VideoHub PRO ({PRO_DURATION_DAYS} días)",
                "quantity": 1,
                "unit_price": float(PRO_PRICE_ARS),
                "currency_id": "ARS",
            }
        ],
        "external_reference": str(user_key),
        "notification_url": f"{PUBLIC_BASE_URL}/webhook/mercadopago",
        "back_urls": {
            "success": f"{base_url}/pago/exitoso",
            "failure": f"{base_url}/pago/fallido",
            "pending": f"{base_url}/pago/pendiente",
        },
        "auto_return": "approved",
    }

    result = sdk.preference().create(preference_data)
    preference = result.get("response", {})

    if "init_point" not in preference and "sandbox_init_point" not in preference:
        logger.error("Respuesta inesperada de Mercado Pago: %s", result)
        raise RuntimeError("Mercado Pago no devolvió un link de pago válido.")

    # Si el access token es de prueba (TEST-...), Mercado Pago solo habilita
    # el sandbox_init_point; con credenciales reales se usa init_point.
    if MERCADOPAGO_ACCESS_TOKEN.startswith("TEST-"):
        return preference.get("sandbox_init_point", preference.get("init_point"))

    return preference.get("init_point", preference.get("sandbox_init_point"))


def get_payment(payment_id):
    """Consulta el estado real de un pago en Mercado Pago (nunca confiar
    ciegamente en lo que manda el webhook, siempre reconsultar)."""
    sdk = _get_sdk()
    result = sdk.payment().get(payment_id)
    return result.get("response", {})
