import os

from flask import Blueprint, jsonify, request

from auth import create_token

auth_bp = Blueprint("auth", __name__, url_prefix="/api/auth")


@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json() or {}
    api_key = data.get("api_key", "")

    if api_key != os.getenv("API_KEY"):
        return jsonify({"error": "API key inválida"}), 401

    token = create_token()
    return jsonify({"token": token, "type": "Bearer", "expires_in": "24h"})
