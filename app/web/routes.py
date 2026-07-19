import uuid
from pathlib import Path
from urllib.parse import urljoin
from flask import (
    Blueprint, jsonify, request, render_template, session, send_file, abort,
)

from app.services.registry import download_service as service, usage_service
from app.services.payment_service import create_pro_preference, get_payment
from app.socket_manager import socketio
from app.config import FREE_DAILY_LIMIT, PRO_DAILY_LIMIT, PRO_PRICE_ARS, PRO_DURATION_DAYS
from app.core.logger import logger
from app.config import PUBLIC_BASE_URL

web = Blueprint("web", __name__)

# file_id corto -> ruta real en disco, para poder ofrecer la descarga sin
# exponer paths del servidor. Se llena cuando termina una descarga.
READY_FILES = {}


def _web_key():
    """Identifica al visitante anónimo por cookie de sesión Flask. No es
    una cuenta de verdad (si borra cookies, cuenta como otro usuario),
    pero alcanza para aplicar el límite gratuito de forma razonable."""
    if "uid" not in session:
        session["uid"] = uuid.uuid4().hex
        session.permanent = True
    return f"web:{session['uid']}"


@web.route("/")
def index():
    _web_key()  # asegura que exista la cookie de sesión desde la primera carga
    return render_template("index.html")


@web.get("/api/status")
def api_status():
    key = _web_key()

    is_pro = usage_service.is_pro(key)

    return jsonify({
        "is_pro": is_pro,
        "pro_until": usage_service.pro_until(key) if is_pro else None,
        "remaining": usage_service.remaining_today(key),
        "daily_limit": FREE_DAILY_LIMIT,
        "pro_daily_limit": PRO_DAILY_LIMIT,
        "pro_price_ars": PRO_PRICE_ARS,
    })


@web.post("/analyze")
def analyze():
    url = (request.json or {}).get("url")

    if not url:
        return jsonify({"error": "URL requerida"}), 400

    try:
        info = service.analyze(url)
    except Exception as e:
        return jsonify({"error": str(e)}), 400

    return jsonify(info)


@web.post("/api/download")
def api_download():

    payload = request.json or {}

    url = payload.get("url")
    quality = payload.get("quality", "1080")
    audio = bool(payload.get("audio", False))

    if not url:
        return jsonify({"error": "URL requerida"}), 400

    try:

        filepath = service.download_now(
            url=url,
            quality=quality,
            audio=audio,
        )

        path = Path(filepath)

        file_id = uuid.uuid4().hex

        READY_FILES[file_id] = str(path)

        download_url = f"{PUBLIC_BASE_URL}/download/{file_id}"

        return jsonify({
            "success": True,
            "filename": path.name,
            "download_url": download_url,
        })

    except Exception as e:
        logger.exception(e)
        return jsonify({
            "success": False,
            "error": str(e),
            "type": type(e).__name__,
        }), 500


@web.post("/enqueue")
def enqueue():
    payload = request.json or {}
    url = payload.get("url")
    quality = payload.get("quality", "1080")
    audio = bool(payload.get("audio", False))

    if not url:
        return jsonify({"error": "URL requerida"}), 400

    key = _web_key()

    if not usage_service.can_download(key):
        limit = PRO_DAILY_LIMIT if usage_service.is_pro(key) else FREE_DAILY_LIMIT
        plan = "PRO" if usage_service.is_pro(key) else "gratuitas"
        return jsonify({
            "error": f"Alcanzaste el límite de {limit} descargas {plan} de hoy.",
            "limit_reached": True,
        }), 403

    usage_service.register_download(key)
    room = session["uid"]

    service.enqueue(
        url=url,
        quality=quality,
        audio=audio,
        user=key,
        on_complete=lambda filepath: _deliver_web_file(room, filepath),
        on_error=lambda err: socketio.emit("download_error", {"error": err}, room=room),
    )

    return jsonify({
        "success": True,
        "message": "Agregado a la cola",
        "remaining": usage_service.remaining_today(key),
    })


def _deliver_web_file(room, filepath):
    path = Path(filepath)
    file_id = uuid.uuid4().hex
    READY_FILES[file_id] = str(path)

    socketio.emit("download_complete", {
        "filename": path.name,
        "download_url": f"/download/{file_id}",
    }, room=room)


@web.get("/download/<file_id>")
def download_file(file_id):

    logger.info(f"DOWNLOAD solicitado: {file_id}")
    logger.info(f"READY_FILES = {READY_FILES}")

    filepath = READY_FILES.get(file_id)

    if not filepath:
        logger.warning("No existe file_id")
        abort(404)

    if not Path(filepath).exists():
        logger.warning("No existe archivo")
        abort(404)

    return send_file(filepath, as_attachment=True)


@web.post("/api/pro/checkout")
def pro_checkout():
    key = _web_key()

    try:
        # Usamos PUBLIC_BASE_URL (la variable de entorno) y no request.url_root:
        # Render entrega las peticiones a Flask por HTTP plano puertas adentro
        # aunque el usuario entre por HTTPS, así que request.url_root puede
        # devolver una URL que Mercado Pago rechaza.
        checkout_url = create_pro_preference(key)
    except Exception as e:
        logger.exception(e)
        return jsonify({
            "success": False,
            "error": str(e),
            "type": type(e).__name__,
        }), 500

    return jsonify({"success": True, "checkout_url": checkout_url})


@web.route("/webhook/mercadopago", methods=["GET", "POST"])
def mercadopago_webhook():
    """Mercado Pago llama acá cuando cambia el estado de un pago.
    Soporta tanto el formato viejo de IPN (?topic=payment&id=...) como
    el nuevo webhook (POST JSON con type/data.id)."""

    payment_id = None

    if request.args.get("topic") == "payment":
        payment_id = request.args.get("id")

    if not payment_id:
        data = request.get_json(silent=True) or {}
        if data.get("type") == "payment":
            payment_id = (data.get("data") or {}).get("id")

    if not payment_id:
        # Notificación de otro tipo (merchant_order, etc.), la ignoramos.
        return jsonify({"status": "ignored"}), 200

    try:
        payment = get_payment(payment_id)
    except Exception as e:
        logger.exception(e)
        return jsonify({"status": "error"}), 200

    logger.info("Webhook Mercado Pago: pago %s -> estado %s", payment_id, payment.get("status"))

    if payment.get("status") == "approved":
        user_key = payment.get("external_reference")

        if user_key:
            until = usage_service.set_pro(user_key, days=PRO_DURATION_DAYS)

            if user_key.startswith("tg:"):
                telegram_id = user_key.split(":", 1)[1]
                from app.telegram.bot import send_message_sync
                send_message_sync(
                    int(telegram_id),
                    f"🎉 ¡Pago aprobado! Ahora eres usuario PRO hasta el {until}. "
                    f"{PRO_DAILY_LIMIT} descargas por día 💎",
                )
            elif user_key.startswith("web:"):
                room = user_key.split(":", 1)[1]
                socketio.emit("pro_activated", {"pro_until": until}, room=room)

    return jsonify({"status": "ok"}), 200


@web.route("/pago/exitoso")
def pago_exitoso():
    return render_template("pago.html", estado="exitoso")


@web.route("/pago/fallido")
def pago_fallido():
    return render_template("pago.html", estado="fallido")


@web.route("/pago/pendiente")
def pago_pendiente():
    return render_template("pago.html", estado="pendiente")

@web.get("/ping")
def ping():
    return jsonify({
        "ok": True,
        "version": "api-download-v1"
    })


