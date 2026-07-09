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
    socketio.run(
        app,
        host=HOST,
        port=PORT,
        debug=False
    )