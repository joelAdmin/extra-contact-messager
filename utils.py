import re
from datetime import datetime
from bson import ObjectId


def extraer_numero_telefono(texto):
    texto = texto.strip()
    patrones = [
        r"\+\d{1,3}[\s\-]?\d{3}[\s\-]?\d{3}[\s\-]?\d{4}",
        r"\(\d{3}\)[\s\-]?\d{3}[\s\-]?\d{4}",
        r"\d{3}[\s\-]\d{3}[\s\-]\d{4}",
        r"\d{3}[\s]\d{3}[\s]\d{4}",
        r"\d{10,15}",
        r"\d{11,15}",
    ]
    for patron in patrones:
        match = re.search(patron, texto)
        if match:
            numero_raw = match.group()
            numero_limpio = re.sub(r"\D", "", numero_raw)
            if 7 <= len(numero_limpio) <= 15:
                return numero_limpio
    return None


def serialize(obj):
    if obj is None:
        return None
    if isinstance(obj, list):
        return [serialize(item) for item in obj]
    if hasattr(obj, "__dict__"):
        obj = obj.__dict__
    if isinstance(obj, dict):
        result = {}
        for k, v in obj.items():
            if k == "_id":
                result["id"] = serialize(v)
            else:
                result[k] = serialize(v)
        return result
    if isinstance(obj, ObjectId):
        return str(obj)
    if isinstance(obj, datetime):
        return obj.isoformat()
    return obj
