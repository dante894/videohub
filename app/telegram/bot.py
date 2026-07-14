import asyncio
from pathlib import Path

from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
)

from app.config import TELEGRAM_TOKEN, TELEGRAM_MAX_FILE_MB
from app.core.logger import logger

from app.telegram.handlers import (
    start,
    help_command,
    status,
    receive_url,
    button,
    send_pro_link,
)

# Referencias globales al bot y a su event loop, para poder enviarle
# mensajes/archivos desde el hilo trabajador de la cola de descargas.
_LOOP = None
_BOT = None


async def _setup_commands(application):
    """Registra el menú nativo de comandos de Telegram (aparece al tocar
    el botón '/' en el chat), con una descripción corta para cada uno."""
    await application.bot.set_my_commands([
        ("start", "Ver la guía de bienvenida"),
        ("pro", "Pasar al plan PRO"),
        ("status", "Ver cuántas descargas te quedan hoy"),
        ("help", "Cómo usar el bot"),
    ])


def run():
    global _LOOP, _BOT

    # Crear un event loop para este hilo
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    _LOOP = loop

    application = (
        Application.builder()
        .token(TELEGRAM_TOKEN)
        .post_init(_setup_commands)
        .build()
    )
    _BOT = application.bot

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("pro", send_pro_link))
    application.add_handler(CommandHandler("status", status))
    application.add_handler(CommandHandler("help", help_command))

    application.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, receive_url)
    )

    application.add_handler(CallbackQueryHandler(button))

    print("🤖 Bot iniciado")

    # stop_signals=None: run_polling() por defecto intenta registrar
    # manejadores de SIGINT/SIGTERM, pero esto corre en un hilo secundario
    # (main.py lo lanza con threading.Thread) y eso solo se puede hacer
    # desde el hilo principal de Python. Sin este parámetro, el hilo del
    # bot se cae apenas arranca.
    application.run_polling(close_loop=False, stop_signals=None)


def send_file_sync(chat_id, filepath, is_audio):
    """Llamado desde el hilo de la cola (no async) para entregar el archivo."""
    if _LOOP is None or _BOT is None:
        logger.error("El bot todavía no está listo para enviar archivos")
        return

    asyncio.run_coroutine_threadsafe(_send_file(chat_id, filepath, is_audio), _LOOP)


def send_message_sync(chat_id, text):
    if _LOOP is None or _BOT is None:
        logger.error("El bot todavía no está listo para enviar mensajes")
        return

    asyncio.run_coroutine_threadsafe(_BOT.send_message(chat_id=chat_id, text=text), _LOOP)


async def _send_file(chat_id, filepath, is_audio):
    path = Path(filepath)

    if not path.exists():
        await _BOT.send_message(chat_id=chat_id, text="❌ No encontré el archivo descargado.")
        return

    size_mb = path.stat().st_size / (1024 * 1024)

    if size_mb > TELEGRAM_MAX_FILE_MB:
        await _BOT.send_message(
            chat_id=chat_id,
            text=(
                f"⚠️ El archivo pesa {size_mb:.0f}MB y Telegram no permite que los "
                f"bots envíen archivos de más de {TELEGRAM_MAX_FILE_MB}MB.\n"
                "Prueba con una calidad más baja (720p o 480p)."
            ),
        )
        return

    try:
        with open(path, "rb") as f:
            if is_audio:
                await _BOT.send_audio(chat_id=chat_id, audio=f, filename=path.name)
            else:
                await _BOT.send_video(
                    chat_id=chat_id, video=f, filename=path.name, supports_streaming=True
                )
    except Exception as e:
        logger.exception(e)
        await _BOT.send_message(chat_id=chat_id, text=f"❌ No pude enviar el archivo:\n{e}")
