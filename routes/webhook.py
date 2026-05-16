from datetime import datetime

from flask import Blueprint, current_app, request

from models.contact import Contact
from services.messenger import MessengerService
from services.notifications import NotificationService
from utils import extraer_numero_telefono

webhook_bp = Blueprint("webhook", __name__)


@webhook_bp.route("/webhook", methods=["GET"])
def verificar_webhook():
    mode = request.args.get("hub.mode")
    token = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")

    client_repo = current_app.config["client_repo"]
    db = current_app.config["db"]

    client = client_repo.find_by_verify_token(token)
    if client and mode == "subscribe":
        fb = client.facebook_config
        if not fb.get("webhook_verified"):
            db.clients.update_one(
                {"client_id": client.client_id},
                {
                    "$set": {
                        "facebook_config.webhook_verified": True,
                        "facebook_config.ultima_verificacion": datetime.utcnow(),
                    }
                },
            )
        print(f"[✓] Webhook verified for client {client.client_id}")
        return challenge, 200

    return "Verification failed", 403


@webhook_bp.route("/webhook", methods=["POST"])
def recibir_mensajes():
    data = request.get_json()

    if data.get("object") != "page":
        return "OK", 200

    client_repo = current_app.config["client_repo"]
    contact_repo = current_app.config["contact_repo"]
    user_repo = current_app.config["user_repo"]
    db = current_app.config["db"]

    for entry in data.get("entry", []):
        page_id = entry.get("id")
        client = client_repo.find_by_page_id(page_id)

        if not client:
            print(f"[!] No client found for page_id: {page_id}")
            continue

        fb_config = client.facebook_config
        notif_config = client.notificaciones
        bot_msgs = client.bot_config

        messenger = MessengerService(fb_config["page_access_token"])
        notifier = NotificationService(
            telegram_bot_token=(
                notif_config["telegram"]["bot_token"]
                if notif_config.get("telegram", {}).get("activo")
                else None
            ),
            telegram_chat_id=(
                notif_config["telegram"]["chat_id"]
                if notif_config.get("telegram", {}).get("activo")
                else None
            ),
        )

        for messaging_event in entry.get("messaging", []):
            sender_id = messaging_event.get("sender", {}).get("id")
            recipient_id = messaging_event.get("recipient", {}).get("id")

            if sender_id == recipient_id:
                continue

            message = messaging_event.get("message", {})
            if not message.get("text"):
                continue

            texto_usuario = message["text"]
            ahora = datetime.utcnow()

            numero = extraer_numero_telefono(texto_usuario)

            if numero:
                profile = messenger.get_user_profile(sender_id)
                nombre = profile.get("name") if profile else None

                conversacion = [
                    {
                        "mensaje": texto_usuario,
                        "fecha": ahora,
                        "tipo": "entrante",
                    }
                ]

                contact = Contact(
                    client_id=client.client_id,
                    sender_id=sender_id,
                    numero_telefono=numero,
                    nombre_usuario=nombre,
                    fuente="messenger",
                    estado="nuevo",
                    notificado=False,
                    conversacion=conversacion,
                    etiquetas=[],
                    metadata={"locale": "es_CO"},
                )
                contact_repo.save(contact)

                user_repo.mark_responded(client.client_id, sender_id)

                notifier.send_telegram_alert(numero, sender_id)

                msg_confirmacion = bot_msgs.get(
                    "mensaje_confirmacion",
                    f"✅ ¡Excelente! Hemos recibido tu número {numero}. "
                    f"En breve un asesor te contactará.",
                )
                messenger.send_message(sender_id, msg_confirmacion)

                db.clients.update_one(
                    {"client_id": client.client_id},
                    {
                        "$inc": {
                            "estadisticas.total_contactos": 1,
                            "estadisticas.contactos_mes_actual": 1,
                        },
                        "$set": {
                            "estadisticas.ultimo_contacto": ahora,
                            "estadisticas.fecha_actualizacion": ahora,
                        },
                    },
                )
                print(f"[+] Lead saved: {sender_id} - {numero}")

            else:
                if not user_repo.is_responded(client.client_id, sender_id):
                    msg_bienvenida = bot_msgs.get(
                        "mensaje_bienvenida",
                        "¡Gracias por contactarnos! Por favor comparte "
                        "tu número telefónico para poder ayudarte mejor.",
                    )
                    messenger.send_message(sender_id, msg_bienvenida)
                    user_repo.mark_responded(client.client_id, sender_id)
                    print(f"[!] Asked for number from: {sender_id}")
                else:
                    print(
                        f"[!] User {sender_id} already responded, ignoring"
                    )

    return "OK", 200
