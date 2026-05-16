from datetime import datetime

from flask import Blueprint, current_app, jsonify, request

from auth import token_required
from utils import serialize

clients_bp = Blueprint("clients", __name__, url_prefix="/api/clients")

CAMPOS_EDITABLES = [
    "nombre_empresa", "email", "plan", "activo",
    "facebook_config", "notificaciones", "bot_config",
    "fecha_vencimiento", "estadisticas", "facturacion", "metadata",
]


@clients_bp.route("", methods=["GET"])
@token_required
def listar_clientes():
    limit = request.args.get("limit", 50, type=int)
    repo = current_app.config["client_repo"]
    clientes = repo.find_all(limit=limit)
    return jsonify({"data": serialize(clientes), "total": len(clientes)})


@clients_bp.route("/<client_id>", methods=["GET"])
@token_required
def obtener_cliente(client_id):
    repo = current_app.config["client_repo"]
    cliente = repo.find_by_id(client_id)
    if not cliente:
        return jsonify({"error": "Cliente no encontrado"}), 404
    return jsonify({"data": serialize(cliente)})


@clients_bp.route("", methods=["POST"])
@token_required
def crear_cliente():
    data = request.get_json()
    if not data or not data.get("client_id"):
        return jsonify({"error": "client_id es requerido"}), 400
    if not data.get("facebook_config", {}).get("page_access_token"):
        return jsonify({"error": "facebook_config.page_access_token es requerido"}), 400

    data.setdefault("activo", True)
    data.setdefault("fecha_registro", datetime.utcnow())
    data.setdefault("estadisticas", {
        "total_contactos": 0, "total_conversaciones": 0,
        "contactos_mes_actual": 0, "ultimo_contacto": None,
        "fecha_actualizacion": datetime.utcnow(),
    })
    if not data.get("notificaciones"):
        data["notificaciones"] = {
            "telegram": {"bot_token": "", "chat_id": "", "activo": False, "ultimo_envio": None},
            "whatsapp": {"numero": "", "activo": False},
            "email": {"email": "", "activo": False},
        }
    if not data.get("bot_config"):
        data["bot_config"] = {
            "mensaje_bienvenida": "¡Hola! Por favor comparte tu número telefónico.",
            "mensaje_confirmacion": "✅ Hemos recibido tu número. Te contactaremos pronto.",
            "mensaje_sin_respuesta": "No logramos identificar tu número.",
            "idioma": "es", "zona_horaria": "America/Bogota",
            "respuesta_automatica": True, "tiempo_espera_respuesta": 0,
        }
    if not data.get("facturacion"):
        data["facturacion"] = {
            "metodo_pago": "pending", "ultimo_pago": None,
            "proximo_pago": None, "estado": "activo",
        }
    if not data.get("metadata"):
        data["metadata"] = {"creado_por": "api", "notas": "", "tags": []}

    repo = current_app.config["client_repo"]
    _id = repo.create(data)
    return jsonify({"message": "Cliente creado", "id": _id}), 201


@clients_bp.route("/<client_id>", methods=["PUT"])
@token_required
def actualizar_cliente(client_id):
    repo = current_app.config["client_repo"]
    existente = repo.find_by_id(client_id)
    if not existente:
        return jsonify({"error": "Cliente no encontrado"}), 404

    data = request.get_json()
    if not data:
        return jsonify({"error": "Datos requeridos"}), 400

    update_data = {k: v for k, v in data.items() if k in CAMPOS_EDITABLES}
    if not update_data:
        return jsonify({"error": "No hay campos editables"}), 400

    repo.update(client_id, update_data)
    return jsonify({"message": "Cliente actualizado"})


@clients_bp.route("/<client_id>", methods=["DELETE"])
@token_required
def eliminar_cliente(client_id):
    repo = current_app.config["client_repo"]
    if not repo.find_by_id(client_id):
        return jsonify({"error": "Cliente no encontrado"}), 404
    repo.delete(client_id)
    return jsonify({"message": "Cliente eliminado"})


@clients_bp.route("/<client_id>/stats", methods=["GET"])
@token_required
def estadisticas_cliente(client_id):
    repo = current_app.config["client_repo"]
    cliente = repo.find_by_id(client_id)
    if not cliente:
        return jsonify({"error": "Cliente no encontrado"}), 404

    contact_repo = current_app.config["contact_repo"]
    total_contactos = len(contact_repo.find_all(client_id=client_id, limit=0))

    stats = serialize(cliente.estadisticas) if cliente.estadisticas else {}
    stats["total_en_bd"] = total_contactos
    return jsonify({"data": stats})
