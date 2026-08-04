from pymongo import MongoClient
from app.config import Settings

class InvestigationStore:
    def __init__(self, settings: Settings):
        self._client = (
            MongoClient(settings.mongo_uri)
            if settings.mongo_uri
            else MongoClient(host=settings.mongo_host, port=settings.mongo_port)
        )
        self._collection = self._client[settings.mongo_db]["investigations"]

    def ping(self) -> bool:
        try:
            self._client.admin.command("ping")
            return True
        except Exception:
            return False

    def save(self, investigation_id: str, result: dict) -> None:
        self._collection.update_one(
            {"_id": investigation_id}, {"$set": result}, upsert=True
        )

    def get(self, investigation_id: str) -> dict | None:
        return self._collection.find_one({"_id": investigation_id})

    def list_recent(self, limit: int = 20) -> list[dict]:
        return list(
            self._collection.find({}, {"agent_log": 0, "explorations": 0})
            .sort("created_at", -1)
            .limit(limit)
        )


_store_singleton: InvestigationStore | None = None

def get_store(settings: Settings) -> InvestigationStore:
    global _store_singleton
    if _store_singleton is None:
        _store_singleton = InvestigationStore(settings)
    return _store_singleton
