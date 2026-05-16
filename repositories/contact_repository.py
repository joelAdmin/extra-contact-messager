from abc import ABC, abstractmethod
from typing import List, Optional

from bson import ObjectId

from models.contact import Contact


class ContactRepository(ABC):

    @abstractmethod
    def save(self, contact: Contact) -> str:
        ...

    @abstractmethod
    def find_by_sender(
        self, client_id: str, sender_id: str
    ) -> Optional[Contact]:
        ...

    @abstractmethod
    def find_by_id(self, contact_id: str) -> Optional[Contact]:
        ...

    @abstractmethod
    def find_all(
        self, client_id: Optional[str] = None, limit: int = 50
    ) -> List[Contact]:
        ...

    @abstractmethod
    def list_by_client(
        self, client_id: str, limit: int = 50
    ) -> List[Contact]:
        ...

    @abstractmethod
    def update(self, contact_id: str, data: dict) -> bool:
        ...

    @abstractmethod
    def delete(self, contact_id: str) -> bool:
        ...


class MongoContactRepository(ContactRepository):

    def __init__(self, db):
        self.collection = db["contacts"]

    def save(self, contact: Contact) -> str:
        existing = self.collection.find_one(
            {"client_id": contact.client_id, "sender_id": contact.sender_id}
        )
        if existing:
            update = {"$set": {}, "$push": {}}
            update["$set"]["numero_telefono"] = contact.numero_telefono
            update["$set"]["nombre_usuario"] = contact.nombre_usuario
            update["$set"]["estado"] = contact.estado
            update["$set"]["notificado"] = contact.notificado
            update["$set"]["fuente"] = contact.fuente
            update["$set"]["etiquetas"] = contact.etiquetas or []
            update["$set"]["metadata"] = contact.metadata or {}
            if contact.conversacion:
                update["$push"]["conversacion"] = {"$each": contact.conversacion}
            else:
                del update["$push"]
            self.collection.update_one({"_id": existing["_id"]}, update)
            return str(existing["_id"])

        doc = contact.__dict__.copy()
        doc.pop("_id", None)
        if not doc.get("conversacion"):
            doc.pop("conversacion", None)
        if not doc.get("etiquetas"):
            doc.pop("etiquetas", None)
        if not doc.get("metadata"):
            doc.pop("metadata", None)
        result = self.collection.insert_one(doc)
        return str(result.inserted_id)

    def find_by_sender(
        self, client_id: str, sender_id: str
    ) -> Optional[Contact]:
        doc = self.collection.find_one(
            {"client_id": client_id, "sender_id": sender_id}
        )
        return Contact(**doc) if doc else None

    def find_by_id(self, contact_id: str) -> Optional[Contact]:
        doc = self.collection.find_one({"_id": ObjectId(contact_id)})
        return Contact(**doc) if doc else None

    def find_all(
        self, client_id: Optional[str] = None, limit: int = 50
    ) -> List[Contact]:
        filtro = {}
        if client_id:
            filtro["client_id"] = client_id
        docs = (
            self.collection.find(filtro)
            .sort("fecha_captura", -1)
            .limit(limit)
        )
        return [Contact(**d) for d in docs]

    def list_by_client(
        self, client_id: str, limit: int = 50
    ) -> List[Contact]:
        return self.find_all(client_id=client_id, limit=limit)

    def update(self, contact_id: str, data: dict) -> bool:
        result = self.collection.update_one(
            {"_id": ObjectId(contact_id)}, {"$set": data}
        )
        return result.matched_count > 0

    def delete(self, contact_id: str) -> bool:
        result = self.collection.delete_one({"_id": ObjectId(contact_id)})
        return result.deleted_count > 0
