from flask import Flask
from pathlib import Path

from app.config import HOST, PORT, FLASK_SECRET_KEY, YTDLP_COOKIES_FILE
from app.core.logger import logger
from app.socket_manager import socketio
from app.web.routes import web


def _diagnosticar_cookies():
    """Log de arranque, temporal, para depurar por qué CookieManager no
    encuentra el archivo de cookies en producción aunque la config parezca
    correcta. Se puede borrar una vez resuelto."""

    logger.info(f"[DIAG] YTDLP_COOKIES_FILE = {YTDLP_COOKIES_FILE!r}")

    secrets_dir = Path("/etc/secrets")

    if not secrets_dir.exists():
        logger.warning("[DIAG] La carpeta /etc/secrets ni siquiera existe en este contenedor.")
        return

    try:
        contenido = list(secrets_dir.iterdir())
    except Exception as e:
        logger.warning(f"[DIAG] No se pudo listar /etc/secrets: {e}")
        return

    if not contenido:
        logger.warning("[DIAG] /etc/secrets existe pero está VACÍA. El Secret File no se está montando.")
        return

    logger.info(f"[DIAG] Archivos reales dentro de /etc/secrets: {[p.name for p in contenido]}")

    for p in contenido:
        try:
            size = p.stat().st_size
            logger.info(f"[DIAG]   - {p} ({size} bytes)")
        except Exception:
            pass


_diagnosticar_cookies()


app = Flask(__name__)
app.config["SECRET_KEY"] = FLASK_SECRET_KEY

socketio.init_app(app)
app.register_blueprint(web)


if __name__ == "__main__":

    

    # Iniciar Flask + SocketIO
    #
    # allow_unsafe_werkzeug=True: usamos async_mode="threading" a propósito
    # (ver app/socket_manager.py) para no chocar con los hilos/SSL que usa
    # yt-dlp. Eso hace que Flask-SocketIO use el servidor de desarrollo de
    # Werkzeug incluso en producción; para esta escala (un solo servicio,
    # sin balanceo entre múltiples workers) es aceptable. Si el proyecto
    # crece mucho, lo ideal sería migrar a async_mode="eventlet" o correr
    # con gunicorn+eventlet detrás de un proxy.
    socketio.run(
        app,
        host=HOST,
        port=PORT,
        debug=False,
        allow_unsafe_werkzeug=True,
    )