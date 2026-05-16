import os
import re
from datetime import datetime

from flask import Flask, request

import config
from models.contact import Contact
from services.messenger import MessengerService
from services.notifications import NotificationService

# ─── Cargar configuración del sistema ─────────────────────────────────
config.load_environment()

DB_TYPE = os.getenv("DB_TYPE", "mongo")

# ─── Inicializar repositorios según el motor de BD ─────────────────────
if DB_TYPE == "mongo":
    db = config.get_database()
    from repositories.client_repository import MongoClientRepository
    from repositories.contact_repository import MongoContactRepository
    from repositories.user_repository import MongoUserRepository

    client_repo = MongoClientRepository(db)
    contact_repo = MongoContactRepository(db)
    user_repo = MongoUserRepository(db)
else:
    raise ValueError(f"Unsupported DB_TYPE: {DB_TYPE}. Available: mongo")

app = Flask(__name__)


# ─── Utilidad: extraer número de teléfono del texto ───────────────────
def extraer_numero_telefono(texto):
    texto = texto.strip()

    patrones = [
        r"\+\d{1,3}[\s\-]?\d{3}[\s\-]?\d{3}[\s\-]?\d{4}",
        r"\(\d{3}\)[\s\-]?\d{3}[\s\-]?\d{4}",
        r"\d{3}[\s\-]\d{3}[\s\-]\d{4}",
        r"\d{3}[\s]\d{3}[\s]\d{4}",
        r"\d{10,15}",
        r"\d{11,15}",
    ]

    for patron in patrones:
        match = re.search(patron, texto)
        if match:
            numero_raw = match.group()
            numero_limpio = re.sub(r"\D", "", numero_raw)
            if 7 <= len(numero_limpio) <= 15:
                print(f"[DEBUG] Number found: {numero_raw} -> {numero_limpio}")
                return numero_limpio

    print(f"[DEBUG] No number found in: {texto[:50]}")
    return None


# ─── Endpoint: verificación del webhook (GET) ─────────────────────────
@app.route("/webhook", methods=["GET"])
def verificar_webhook():
    mode = request.args.get("hub.mode")
    token = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")

    client = client_repo.find_by_verify_token(token)
    if client and mode == "subscribe":
        # Marcar webhook como verificado
        fb = client.facebook_config
        if not fb.get("webhook_verified"):
            db.clients.update_one(
                {"client_id": client.client_id},
                {"$set": {
                    "facebook_config.webhook_verified": True,
                    "facebook_config.ultima_verificacion": datetime.utcnow(),
                }}
            )
        print(f"[✓] Webhook verified for client {client.client_id}")
        return challenge, 200

    return "Verification failed", 403


# ─── Endpoint: recibir mensajes (POST) ────────────────────────────────
@app.route("/webhook", methods=["POST"])
def recibir_mensajes():
    data = request.get_json()

    if data.get("object") != "page":
        return "OK", 200

    for entry in data.get("entry", []):
        page_id = entry.get("id")
        client = client_repo.find_by_page_id(page_id)

        if not client:
            print(f"[!] No client found for page_id: {page_id}")
            continue

        # ── Obtener configuración del cliente ──
        fb_config = client.facebook_config
        notif_config = client.notificaciones
        bot_msgs = client.bot_config

        # Inicializar servicios
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

            # Ignorar mensajes enviados por la propia página
            if sender_id == recipient_id:
                continue

            message = messaging_event.get("message", {})
            if not message.get("text"):
                continue

            texto_usuario = message["text"]
            ahora = datetime.utcnow()

            # ─── 1. Intentar extraer un número de teléfono ─────────
            numero = extraer_numero_telefono(texto_usuario)

            if numero:

                # ── Obtener perfil del usuario desde Facebook ──
                profile = messenger.get_user_profile(sender_id)
                nombre = profile.get("name") if profile else None

                # ── Armar el registro de conversación ──
                conversacion = [
                    {
                        "mensaje": texto_usuario,
                        "fecha": ahora,
                        "tipo": "entrante",
                    }
                ]

                # ── Guardar o actualizar el contacto en la BD ──
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

                # Marcar como respondido
                user_repo.mark_responded(client.client_id, sender_id)

                # Enviar alerta al administrador
                notifier.send_telegram_alert(numero, sender_id)

                # Confirmar al usuario con el mensaje configurado
                msg_confirmacion = bot_msgs.get(
                    "mensaje_confirmacion",
                    f"✅ ¡Excelente! Hemos recibido tu número {numero}. "
                    f"En breve un asesor te contactará.",
                )
                messenger.send_message(sender_id, msg_confirmacion)

                # Actualizar estadísticas del cliente
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
                    }
                )

                print(f"[+] Lead saved: {sender_id} - {numero}")

            else:
                # ── No se encontró número en el mensaje ──

                if not user_repo.is_responded(client.client_id, sender_id):

                    # Usar mensaje de bienvenida configurado
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


# ─── Punto de entrada ──────────────────────────────────────────────────
if __name__ == "__main__":
    print(f"🤖  Bot de Messenger iniciado (DB_TYPE={DB_TYPE})")
    app.run(port=5000, debug=True)
