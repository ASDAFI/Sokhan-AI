from collections import defaultdict

import pymongo

from sokhan.entry.base.documents import Document


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

    def insert_many_docs_into_collection(
        self,
        docs: list[Document],
        collection_name: str,
    ):
        if not docs:
            return

        self._db[collection_name].insert_many(
            [doc.to_mongo_dict() for doc in docs]
        )

    def insert_many_docs(self, docs: list[Document]):
        if not docs:
            return

        coll_map_docs = defaultdict(list)

        for doc in docs:
            coll_map_docs[doc.collection_name].append(doc)

        for collection_name, grouped_docs in coll_map_docs.items():
            self.insert_many_docs_into_collection(
                grouped_docs,
                collection_name,
            )

    def close(self):
        self._client.close()
