from threading import Thread

from flask import Flask

from app.config import HOST, PORT, FLASK_SECRET_KEY
from app.socket_manager import socketio
from app.web.routes import web
from app.telegram.bot import run as run_bot

app = Flask(__name__)
app.config["SECRET_KEY"] = FLASK_SECRET_KEY

socketio.init_app(app)
app.register_blueprint(web)


if __name__ == "__main__":

    # Iniciar el bot de Telegram en segundo plano
    telegram_thread = Thread(
        target=run_bot,
        daemon=True,
        name="TelegramBot"
    )
    telegram_thread.start()

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