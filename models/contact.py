from dataclasses import dataclass, field
from typing import Optional
from datetime import datetime
from bson import ObjectId


@dataclass
class Contact:
    client_id: str
    sender_id: str
    numero_telefono: str
    estado: str = "nuevo"
    fecha_captura: datetime = field(default_factory=datetime.utcnow)
    _id: Optional[ObjectId] = None
