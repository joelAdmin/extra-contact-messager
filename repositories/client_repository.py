from abc import ABC, abstractmethod
from typing import Optional

from models.client import Client


class ClientRepository(ABC):

    @abstractmethod
    def find_by_verify_token(self, token: str) -> Optional[Client]:
        ...

    @abstractmethod
    def find_by_page_id(self, page_id: str) -> Optional[Client]:
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

    def upsert(self, client: Client) -> str:
        data = {k: v for k, v in client.__dict__.items() if k != "_id"}
        result = self.collection.update_one(
            {"client_id": client.client_id}, {"$set": data}, upsert=True
        )
        return str(result.upserted_id) if result.upserted_id else client.client_id
