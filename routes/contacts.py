from flask import Blueprint, current_app, jsonify, request

from auth import token_required
from utils import serialize

contacts_bp = Blueprint("contacts", __name__, url_prefix="/api/contacts")


@contacts_bp.route("", methods=["GET"])
@token_required
def listar_contactos():
    client_id = request.args.get("client_id")
    limit = request.args.get("limit", 50, type=int)

    repo = current_app.config["contact_repo"]
    contactos = repo.find_all(client_id=client_id, limit=limit)
    return jsonify({"data": serialize(contactos), "total": len(contactos)})


@contacts_bp.route("/<contact_id>", methods=["GET"])
@token_required
def obtener_contacto(contact_id):
    repo = current_app.config["contact_repo"]
    contacto = repo.find_by_id(contact_id)
    if not contacto:
        return jsonify({"error": "Contacto no encontrado"}), 404
    return jsonify({"data": serialize(contacto)})


@contacts_bp.route("/<contact_id>", methods=["PUT"])
@token_required
def actualizar_contacto(contact_id):
    repo = current_app.config["contact_repo"]
    existente = repo.find_by_id(contact_id)
    if not existente:
        return jsonify({"error": "Contacto no encontrado"}), 404

    data = request.get_json()
    if not data:
        return jsonify({"error": "Datos requeridos"}), 400

    campos_editables = {"estado", "etiquetas", "notificado", "metadata"}
    update_data = {k: v for k, v in data.items() if k in campos_editables}
    if not update_data:
        return jsonify({"error": "No hay campos editables"}), 400

    repo.update(contact_id, update_data)
    return jsonify({"message": "Contacto actualizado"})


@contacts_bp.route("/<contact_id>", methods=["DELETE"])
@token_required
def eliminar_contacto(contact_id):
    repo = current_app.config["contact_repo"]
    if not repo.find_by_id(contact_id):
        return jsonify({"error": "Contacto no encontrado"}), 404
    repo.delete(contact_id)
    return jsonify({"message": "Contacto eliminado"})
