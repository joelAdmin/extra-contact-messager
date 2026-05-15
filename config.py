import os
from dotenv import load_dotenv
from pymongo import MongoClient
from pymongo.server_api import ServerApi

_client = None
_db = None


def load_environment():
    load_dotenv()
    required = ["FACEBOOK_PAGE_ACCESS_TOKEN", "VERIFY_TOKEN"]
    db_type = os.getenv("DB_TYPE", "mongo")
    if db_type == "mongo":
        required.append("MONGODB_URI")
    missing = [v for v in required if not os.getenv(v)]
    if missing:
        raise ValueError(
            f"Missing required environment variables: {', '.join(missing)}"
        )


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
