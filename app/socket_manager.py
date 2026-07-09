from flask import session
from flask_socketio import SocketIO, join_room

# async_mode="threading" avoids requiring eventlet/gevent monkey-patching,
# which conflicts with yt-dlp's own use of threads/ssl.
socketio = SocketIO(cors_allowed_origins="*", async_mode="threading")


@socketio.on("connect")
def _on_connect():
    """Cada visitante entra a una 'room' propia (su uid de sesión), así
    los eventos de progreso/descarga se le mandan solo a él y no a todos
    los que tengan la página abierta al mismo tiempo."""
    uid = session.get("uid")
    if uid:
        join_room(uid)
