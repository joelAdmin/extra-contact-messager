from dataclasses import dataclass
from typing import Any, Optional
from datetime import datetime
from bson import ObjectId


@dataclass
class Client:
    client_id: str
    nombre_empresa: str
    email: Optional[str]
    plan: str
    activo: bool
    facebook_config: dict
    notificaciones: dict
    bot_config: dict
    fecha_registro: datetime
    fecha_vencimiento: Optional[datetime] = None
    estadisticas: Optional[dict] = None
    facturacion: Optional[dict] = None
    metadata: Optional[dict] = None
    _id: Optional[ObjectId] = None
