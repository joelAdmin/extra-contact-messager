from abc import ABC, abstractmethod

from models.contact import Contact


class ContactRepository(ABC):

    @abstractmethod
    def save(self, contact: Contact) -> str:
        ...

    @abstractmethod
    def find_by_sender(
        self, client_id: str, sender_id: str
    ) -> Contact | None:
        ...

    @abstractmethod
    def list_by_client(
        self, client_id: str, limit: int = 50
    ) -> list[Contact]:
        ...


class MongoContactRepository(ContactRepository):

    def __init__(self, db):
        self.collection = db["contacts"]

    def save(self, contact: Contact) -> str:
        doc = contact.__dict__.copy()
        doc.pop("_id", None)
        result = self.collection.insert_one(doc)
        return str(result.inserted_id)

    def find_by_sender(
        self, client_id: str, sender_id: str
    ) -> Contact | None:
        doc = self.collection.find_one(
            {"client_id": client_id, "sender_id": sender_id}
        )
        return Contact(**doc) if doc else None

    def list_by_client(
        self, client_id: str, limit: int = 50
    ) -> list[Contact]:
        docs = (
            self.collection.find({"client_id": client_id})
            .sort("fecha_captura", -1)
            .limit(limit)
        )
        return [Contact(**d) for d in docs]
