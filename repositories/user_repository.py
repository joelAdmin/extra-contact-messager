from abc import ABC, abstractmethod
from datetime import datetime


class UserRepository(ABC):

    @abstractmethod
    def is_responded(self, client_id: str, sender_id: str) -> bool:
        ...

    @abstractmethod
    def mark_responded(self, client_id: str, sender_id: str):
        ...


class MongoUserRepository(UserRepository):

    def __init__(self, db):
        self.collection = db["user_states"]

    def is_responded(self, client_id: str, sender_id: str) -> bool:
        doc = self.collection.find_one(
            {"client_id": client_id, "sender_id": sender_id}
        )
        return doc is not None

    def mark_responded(self, client_id: str, sender_id: str):
        self.collection.update_one(
            {"client_id": client_id, "sender_id": sender_id},
            {
                "$set": {
                    "client_id": client_id,
                    "sender_id": sender_id,
                    "responded_at": datetime.utcnow(),
                }
            },
            upsert=True,
        )
