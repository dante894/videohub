from telegram import InlineKeyboardButton, InlineKeyboardMarkup


def quality_keyboard(token):
    """Teclado para elegir la calidad de descarga. Máximo 1080p."""
    keyboard = [
        [
            InlineKeyboardButton("🎬 1080p", callback_data=f"dl|{token}|1080"),
            InlineKeyboardButton("🎬 720p", callback_data=f"dl|{token}|720"),
        ],
        [
            InlineKeyboardButton("🎬 480p", callback_data=f"dl|{token}|480"),
            InlineKeyboardButton("🎬 360p", callback_data=f"dl|{token}|360"),
        ],
        [
            InlineKeyboardButton("🎵 Solo audio (MP3)", callback_data=f"dl|{token}|audio"),
        ],
    ]
    return InlineKeyboardMarkup(keyboard)


def pro_offer_keyboard():
    """Botón para iniciar el proceso de pago (dispara el callback buy_pro,
    que genera el link de Mercado Pago y lo manda en un mensaje aparte)."""
    keyboard = [
        [InlineKeyboardButton("💎 Hazte PRO", callback_data="buy_pro")]
    ]
    return InlineKeyboardMarkup(keyboard)


def pro_payment_keyboard(checkout_url):
    """Botón que ya lleva directo al checkout de Mercado Pago."""
    keyboard = [
        [InlineKeyboardButton("💳 Pagar con Mercado Pago", url=checkout_url)]
    ]
    return InlineKeyboardMarkup(keyboard)
