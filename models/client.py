from dataclasses import dataclass
from typing import Optional
from bson import ObjectId


@dataclass
class Client:
    client_id: str
    email: Optional[str]
    facebook_config: dict
    telegram_config: Optional[dict]
    activo: bool
    plan: str
    _id: Optional[ObjectId] = None
