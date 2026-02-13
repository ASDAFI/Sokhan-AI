from collections import defaultdict

import pymongo


class MongoDBClient:
    def __init__(
            self,
            host: str = "localhost",
            port: int = 27017,
            username: str = "user",
            password: str = "pass",
            db_name: str = "sokhan",
    ):
        self._client = pymongo.MongoClient(f"mongodb://{username}:{password}@{host}:{port}/?authSource=admin")
        self._db = self._client[db_name]

    def bulk_insert(self, collection_name: str, data: list[dict]) -> None:
        self._db[collection_name].insert_many(
            data
        )

    def close(self):
        self._client.close()


MONGO_CLIENT = MongoDBClient()
