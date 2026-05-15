import os
import re

from flask import Flask, request

import config
from models.client import Client
from models.contact import Contact
from services.messenger import MessengerService
from services.notifications import NotificationService

config.load_environment()

DB_TYPE = os.getenv("DB_TYPE", "mongo")

if DB_TYPE == "mongo":
    db = config.get_database()
    from repositories.client_repository import MongoClientRepository
    from repositories.contact_repository import MongoContactRepository
    from repositories.user_repository import MongoUserRepository

    client_repo = MongoClientRepository(db)
    contact_repo = MongoContactRepository(db)
    user_repo = MongoUserRepository(db)

    default_client = Client(
        client_id=os.getenv("CLIENT_ID", "default"),
        email=os.getenv("EMAIL"),
        facebook_config={
            "page_access_token": os.getenv("FACEBOOK_PAGE_ACCESS_TOKEN"),
            "verify_token": os.getenv("VERIFY_TOKEN"),
            "page_id": os.getenv("PAGE_ID", ""),
            "phone_number_id": os.getenv("PHONE_NUMBER_ID", ""),
        },
        telegram_config=(
            {
                "bot_token": os.getenv("TELEGRAM_BOT_TOKEN"),
                "chat_id": os.getenv("MI_ID_TELEGRAM"),
            }
            if os.getenv("TELEGRAM_BOT_TOKEN")
            else None
        ),
        activo=True,
        plan=os.getenv("PLAN", "free"),
    )
    client_repo.upsert(default_client)
else:
    raise ValueError(f"Unsupported DB_TYPE: {DB_TYPE}. Available: mongo")

app = Flask(__name__)


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


@app.route("/webhook", methods=["GET"])
def verificar_webhook():
    mode = request.args.get("hub.mode")
    token = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")

    client = client_repo.find_by_verify_token(token)
    if client and mode == "subscribe":
        print(f"[✓] Webhook verified for client {client.client_id}")
        return challenge, 200

    return "Verification failed", 403


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

        messenger = MessengerService(
            client.facebook_config.get("page_access_token")
        )
        notifier = NotificationService(
            telegram_bot_token=(
                client.telegram_config.get("bot_token")
                if client.telegram_config
                else None
            ),
            telegram_chat_id=(
                client.telegram_config.get("chat_id")
                if client.telegram_config
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

            mensaje_texto = message["text"]
            numero = extraer_numero_telefono(mensaje_texto)

            if numero:
                contact = Contact(
                    client_id=client.client_id,
                    sender_id=sender_id,
                    numero_telefono=numero,
                )
                contact_repo.save(contact)
                user_repo.mark_responded(client.client_id, sender_id)
                notifier.send_telegram_alert(numero, sender_id)
                messenger.send_message(
                    sender_id,
                    f"✅ ¡Gracias! Hemos recibido tu número {numero}. "
                    f"En breve nos pondremos en contacto contigo.",
                )
                print(f"[+] Lead saved: {sender_id} - {numero}")
            else:
                if not user_repo.is_responded(
                    client.client_id, sender_id
                ):
                    messenger.send_message(
                        sender_id,
                        "¡Gracias por contactarnos! Por favor comparte "
                        "tu número telefónico para poder ayudarte mejor.",
                    )
                    user_repo.mark_responded(client.client_id, sender_id)
                    print(f"[!] Asked for number from: {sender_id}")
                else:
                    print(
                        f"[!] User {sender_id} already responded, ignoring"
                    )

    return "OK", 200


if __name__ == "__main__":
    if not os.getenv("FACEBOOK_PAGE_ACCESS_TOKEN"):
        print("⚠️  ERROR: FACEBOOK_PAGE_ACCESS_TOKEN not set")
    if not os.getenv("VERIFY_TOKEN"):
        print("⚠️  ERROR: VERIFY_TOKEN not set")

    print(f"🤖  Bot de Messenger iniciado (DB_TYPE={DB_TYPE})")
    app.run(port=5000, debug=True)
