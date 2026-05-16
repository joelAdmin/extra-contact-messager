from dataclasses import dataclass, field
from typing import List, Optional
from datetime import datetime
from bson import ObjectId


@dataclass
class Contact:
    client_id: str
    sender_id: str
    numero_telefono: str
    nombre_usuario: Optional[str] = None
    fuente: str = "messenger"
    estado: str = "nuevo"
    notificado: bool = False
    conversacion: Optional[List[dict]] = None
    etiquetas: Optional[List[str]] = None
    metadata: Optional[dict] = None
    fecha_captura: datetime = field(default_factory=datetime.utcnow)
    _id: Optional[ObjectId] = None
