import os

from flask import Flask

import config

# ─── Cargar configuración del sistema ─────────────────────────────────
config.load_environment()

DB_TYPE = os.getenv("DB_TYPE", "mongo")

# ─── Inicializar repositorios ─────────────────────────────────────────
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
app.config["db"] = db
app.config["client_repo"] = client_repo
app.config["contact_repo"] = contact_repo
app.config["user_repo"] = user_repo

# ─── Registrar blueprints ──────────────────────────────────────────────
from routes.webhook import webhook_bp
from routes.auth import auth_bp
from routes.clients import clients_bp
from routes.contacts import contacts_bp

app.register_blueprint(webhook_bp)
app.register_blueprint(auth_bp)
app.register_blueprint(clients_bp)
app.register_blueprint(contacts_bp)


# ─── Punto de entrada ──────────────────────────────────────────────────
if __name__ == "__main__":
    print(f"🤖  Bot de Messenger iniciado (DB_TYPE={DB_TYPE})")
    app.run(port=5000, debug=True)
