import os
from datetime import datetime, timedelta
from functools import wraps

import jwt
from flask import current_app, jsonify, request


def create_token() -> str:
    now = datetime.utcnow()
    payload = {
        "sub": "admin",
        "iat": now,
        "exp": now + timedelta(hours=24),
    }
    return jwt.encode(payload, os.getenv("JWT_SECRET_KEY"), algorithm="HS256")


def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            return jsonify({"error": "Token requerido"}), 401
        token = auth_header.split(" ", 1)[1]
        try:
            jwt.decode(token, os.getenv("JWT_SECRET_KEY"), algorithms=["HS256"])
        except jwt.ExpiredSignatureError:
            return jsonify({"error": "Token expirado"}), 401
        except jwt.InvalidTokenError:
            return jsonify({"error": "Token inválido"}), 401
        return f(*args, **kwargs)
    return decorated
