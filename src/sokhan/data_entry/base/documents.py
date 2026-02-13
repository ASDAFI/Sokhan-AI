from datetime import datetime
from typing import TypeVar, Generic
from abc import ABC, abstractmethod
import uuid

from pydantic import BaseModel, UUID4, Field, AnyUrl

from sokhan.utils.db.mongo_client import MONGO_CLIENT

T = TypeVar("T", bound="Document")


class Document(BaseModel, Generic[T], ABC):
    id: UUID4 = Field(default_factory=uuid.uuid4)
    created_date: datetime = Field(default_factory=datetime.now)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Document):
            return False
        return self.id == other.id

    def __hash__(self) -> int:
        return hash(self.id)

    @property
    @abstractmethod
    def collection_name(self):
        pass

    @classmethod
    def from_dict(cls, data: dict) -> T:
        return cls(**data)

    @staticmethod
    def fix_data_types(data: dict) -> dict:
        out = {}
        for key, value in data.items():
            if isinstance(value, AnyUrl):
                out[key] = str(value)
            elif isinstance(value, uuid.UUID):
                out[key] = str(value)
            elif isinstance(value, datetime):
                out[key] = value.isoformat()
            else:
                out[key] = value
        return out

    def to_mongo_dict(self) -> dict:
        data = self.model_dump()
        data = self.fix_data_types(data)

        data["_id"] = str(data["id"])

        if "id" in data:
            data.pop("id")

        return data

    def save(self):
        MONGO_CLIENT.bulk_insert(self.collection_name, [self.to_mongo_dict()])
