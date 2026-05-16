#!/usr/bin/env python3
import os
import sys
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
from pymongo import MongoClient
from pymongo.server_api import ServerApi


def conectar_mongodb():
    load_dotenv()
    uri = os.getenv("MONGODB_URI")
    if not uri:
        print("❌ MONGODB_URI no está definida en .env")
        sys.exit(1)
    client = MongoClient(uri, server_api=ServerApi("1"))
    db_name = os.getenv("MONGODB_DB_NAME", "plataforma_bots")
    db = client[db_name]
    client.admin.command("ping")
    print("[✓] Conectado a MongoDB Atlas\n")
    return db


def crear_o_actualizar_cliente(db):
    print("=== Registrar Cliente en MongoDB ===\n")

    client_id = input("client_id [default]: ").strip() or "default"
    nombre_empresa = input("nombre_empresa: ").strip()
    email = input("email (opcional): ").strip()
    plan = input("plan [free]: ").strip() or "free"

    print("\n--- Facebook ---")
    page_id = input("page_id: ").strip()
    page_name = input("page_name (opcional): ").strip()
    page_access_token = input("page_access_token: ").strip()
    verify_token = input("verify_token: ").strip()

    print("\n--- Telegram (opcional) ---")
    tg_token = input("bot_token: ").strip()
    tg_chat_id = input("chat_id: ").strip()

    print("\n--- Mensajes del Bot ---")
    msg_bienvenida = input("mensaje_bienvenida (Enter = default): ").strip()
    msg_confirmacion = input("mensaje_confirmacion (Enter = default): ").strip()

    ahora = datetime.utcnow()

    data = {
        "client_id": client_id,
        "nombre_empresa": nombre_empresa,
        "email": email or None,
        "plan": plan,
        "activo": True,
        "fecha_registro": ahora,
        "facebook_config": {
            "page_id": page_id,
            "page_name": page_name,
            "page_access_token": page_access_token,
            "verify_token": verify_token,
            "webhook_verified": False,
            "ultima_verificacion": None,
        },
        "notificaciones": {
            "telegram": {
                "bot_token": tg_token,
                "chat_id": tg_chat_id,
                "activo": bool(tg_token and tg_chat_id),
                "ultimo_envio": None,
            },
            "whatsapp": {"numero": "", "activo": False},
            "email": {"email": "", "activo": False},
        },
        "bot_config": {
            "mensaje_bienvenida": (
                msg_bienvenida
                or "¡Hola! Por favor comparte tu número telefónico para ayudarte mejor."
            ),
            "mensaje_confirmacion": (
                msg_confirmacion
                or "✅ ¡Excelente! Hemos recibido tu número. En breve un asesor te contactará."
            ),
            "mensaje_sin_respuesta": (
                "No logramos identificar tu número. Por favor escríbelo en formato 3101234567"
            ),
            "idioma": "es",
            "zona_horaria": "America/Bogota",
            "respuesta_automatica": True,
            "tiempo_espera_respuesta": 0,
        },
        "estadisticas": {
            "total_contactos": 0,
            "total_conversaciones": 0,
            "contactos_mes_actual": 0,
            "ultimo_contacto": None,
            "fecha_actualizacion": ahora,
        },
        "facturacion": {
            "metodo_pago": "pending",
            "ultimo_pago": None,
            "proximo_pago": None,
            "estado": "activo",
        },
        "metadata": {
            "creado_por": "setup_client.py",
            "notas": "",
            "tags": [],
        },
    }

    db.clients.update_one(
        {"client_id": client_id},
        {"$set": data, "$setOnInsert": {"fecha_registro": ahora}},
        upsert=True,
    )

    print(f"\n✅ Cliente '{client_id}' insertado correctamente")
    print(f"   page_id: {page_id}")
    print(f"   webhook_verified: False")
    print(f"   Telegram: {'✓' if tg_token and tg_chat_id else '✗ no configurado'}")


if __name__ == "__main__":
    db = conectar_mongodb()
    crear_o_actualizar_cliente(db)
