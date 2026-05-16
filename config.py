import os
from dotenv import load_dotenv
from pymongo import MongoClient
from pymongo.server_api import ServerApi

_client = None
_db = None


def load_environment():
    load_dotenv()
    db_type = os.getenv("DB_TYPE", "mongo")
    if db_type == "mongo" and not os.getenv("MONGODB_URI"):
        raise ValueError("MONGODB_URI is required when DB_TYPE=mongo")
    if not os.getenv("JWT_SECRET_KEY"):
        raise ValueError("JWT_SECRET_KEY is required")
    if not os.getenv("API_KEY"):
        raise ValueError("API_KEY is required")


def get_database():
    global _client, _db
    if _db is None:
        uri = os.getenv("MONGODB_URI")
        _client = MongoClient(uri, server_api=ServerApi("1"))
        db_name = os.getenv("MONGODB_DB_NAME", "plataforma_bots")
        _db = _client[db_name]
        _client.admin.command("ping")
        print("[✓] Connected to MongoDB Atlas")
    return _db


def close_connection():
    global _client, _db
    if _client:
        _client.close()
        _client = None
        _db = None
