from abc import ABC, abstractmethod
from typing import List, Optional

from models.client import Client
from utils import serialize


class ClientRepository(ABC):

    @abstractmethod
    def find_by_verify_token(self, token: str) -> Optional[Client]:
        ...

    @abstractmethod
    def find_by_page_id(self, page_id: str) -> Optional[Client]:
        ...

    @abstractmethod
    def find_by_id(self, client_id: str) -> Optional[Client]:
        ...

    @abstractmethod
    def find_all(self, limit: int = 50) -> List[Client]:
        ...

    @abstractmethod
    def create(self, data: dict) -> str:
        ...

    @abstractmethod
    def update(self, client_id: str, data: dict) -> bool:
        ...

    @abstractmethod
    def delete(self, client_id: str) -> bool:
        ...

    @abstractmethod
    def upsert(self, client: Client) -> str:
        ...


class MongoClientRepository(ClientRepository):

    def __init__(self, db):
        self.collection = db["clients"]

    def find_by_verify_token(self, token: str) -> Optional[Client]:
        doc = self.collection.find_one({"facebook_config.verify_token": token})
        return Client(**doc) if doc else None

    def find_by_page_id(self, page_id: str) -> Optional[Client]:
        doc = self.collection.find_one({"facebook_config.page_id": page_id})
        return Client(**doc) if doc else None

    def find_by_id(self, client_id: str) -> Optional[Client]:
        doc = self.collection.find_one({"client_id": client_id})
        return Client(**doc) if doc else None

    def find_all(self, limit: int = 50) -> List[Client]:
        docs = self.collection.find().limit(limit)
        return [Client(**d) for d in docs]

    def create(self, data: dict) -> str:
        result = self.collection.insert_one(data)
        return str(result.inserted_id)

    def update(self, client_id: str, data: dict) -> bool:
        result = self.collection.update_one(
            {"client_id": client_id}, {"$set": data}
        )
        return result.matched_count > 0

    def delete(self, client_id: str) -> bool:
        result = self.collection.delete_one({"client_id": client_id})
        return result.deleted_count > 0

    def upsert(self, client: Client) -> str:
        data = {k: v for k, v in client.__dict__.items() if k != "_id"}
        result = self.collection.update_one(
            {"client_id": client.client_id}, {"$set": data}, upsert=True
        )
        return str(result.upserted_id) if result.upserted_id else client.client_id
