from telegram import Update
from telegram.ext import ContextTypes

from app.config import FREE_DAILY_LIMIT, PRO_PRICE_ARS, PRO_DURATION_DAYS
from app.telegram.service import download_service, usage_service
from app.telegram.keyboards import pro_offer_keyboard, pro_payment_keyboard
from app.services.payment_service import create_pro_preference
from app.core.logger import logger


def tg_key(user_id):
    """Clave genérica para usage_service/payment_service a partir de un
    user_id de Telegram, para no mezclarse con las claves del sitio web."""
    return f"tg:{user_id}"


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Bienvenido a VideoHub\n\n"
        "Envíame un enlace de YouTube, Instagram o TikTok y te lo descargo "
        "directo, en la mejor calidad disponible (máximo 1080p).\n\n"
        f"🆓 Plan gratuito: {FREE_DAILY_LIMIT} descargas por día.\n"
        "💎 Usa /pro para descargas ilimitadas.\n"
        "📊 Usa /status para ver cuántas descargas te quedan hoy."
    )


async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if usage_service.is_pro(tg_key(user_id)):
        until = usage_service.pro_until(tg_key(user_id))
        await update.message.reply_text(
            f"💎 Eres usuario PRO (activo hasta {until}).\nDescargas ilimitadas."
        )
        return

    remaining = usage_service.remaining_today(tg_key(user_id))
    used = FREE_DAILY_LIMIT - remaining

    await update.message.reply_text(
        "🆓 Plan gratuito\n"
        f"Descargas usadas hoy: {used}/{FREE_DAILY_LIMIT}\n"
        f"Te quedan: {remaining}\n\n"
        "Usa /pro para descargas ilimitadas.",
        reply_markup=pro_offer_keyboard(),
    )


async def receive_url(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Descarga directo al recibir el link, sin preguntar calidad:
    siempre la mejor disponible, con tope de 1080p (ver engine.py)."""
    url = update.message.text.strip()
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id

    logger.info("URL recibida de %s: %s", user_id, url)

    if not url.startswith("http"):
        await update.message.reply_text(
            "❌ Eso no parece un enlace válido. Envíame un link de YouTube, "
            "Instagram o TikTok."
        )
        return

    if not usage_service.can_download(tg_key(user_id)):
        await update.message.reply_text(
            f"🚫 Alcanzaste el límite de {FREE_DAILY_LIMIT} descargas gratuitas de hoy.\n"
            "Vuelve mañana o hazte PRO para descargas ilimitadas 👇",
            reply_markup=pro_offer_keyboard(),
        )
        return

    usage_service.register_download(tg_key(user_id))

    await update.message.reply_text(
        "⬇️ Descargando en la mejor calidad disponible (máximo 1080p)... "
        "te lo mando acá apenas esté listo."
    )

    download_service.enqueue(
        url=url,
        quality="1080",
        audio=False,
        user=str(user_id),
        on_complete=lambda filepath: _deliver_file(chat_id, filepath, False),
        on_error=lambda err: _notify_error(chat_id, err),
    )


async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Único botón que queda es el de 'Hazte PRO'."""
    query = update.callback_query
    await query.answer()

    if query.data == "buy_pro":
        await send_pro_link(update, context)


async def send_pro_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Genera un link de pago de Mercado Pago para este usuario y se lo envía.
    Cuando Mercado Pago confirme el pago (webhook en Flask), se activa el PRO
    automáticamente y se le avisa por Telegram."""
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id

    try:
        checkout_url = create_pro_preference(tg_key(user_id))
    except Exception as e:
        logger.exception(e)
        await context.bot.send_message(
            chat_id=chat_id,
            text="❌ No pude generar el link de pago en este momento. Intenta más tarde.",
        )
        return

    await context.bot.send_message(
        chat_id=chat_id,
        text=(
            f"💎 VideoHub PRO — ${PRO_PRICE_ARS:.0f} ARS\n"
            f"Descargas ilimitadas durante {PRO_DURATION_DAYS} días.\n\n"
            "Toca el botón para pagar con Mercado Pago. En cuanto se acredite "
            "el pago, te activo el PRO automáticamente y te aviso por acá."
        ),
        reply_markup=pro_payment_keyboard(checkout_url),
    )


def _deliver_file(chat_id, filepath, is_audio):
    from app.telegram.bot import send_file_sync
    send_file_sync(chat_id, filepath, is_audio)


def _notify_error(chat_id, error):
    from app.telegram.bot import send_message_sync
    send_message_sync(chat_id, f"❌ Error al descargar:\n{error}")
