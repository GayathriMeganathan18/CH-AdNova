from pymongo import MongoClient
from app.config import Settings

class AnomalyStore:
    def __init__(self, settings: Settings):
        client = (
            MongoClient(settings.mongo_uri)
            if settings.mongo_uri
            else MongoClient(host=settings.mongo_host, port=settings.mongo_port)
        )
        self._collection = client[settings.mongo_db]["anomalies"]

    def save(self, anomaly_id: str, record: dict) -> None:
        self._collection.update_one(
            {"_id": anomaly_id}, {"$set": record}, upsert=True
        )

    def get(self, anomaly_id: str) -> dict | None:
        return self._collection.find_one({"_id": anomaly_id})

    def attach_investigation(
        self, anomaly_id: str, investigation_id: str, root_cause_summary: str, executive_summary: str
    ) -> None:
        self._collection.update_one(
            {"_id": anomaly_id},
            {"$set": {
                "investigation_id": investigation_id,
                "root_cause_summary": root_cause_summary,
                "executive_summary": executive_summary,
                "status": "investigated",
            }},
        )

    def list_recent(
        self,
        limit: int = 50,
        metric: str | None = None,
        severity: str | None = None,
        is_anomalous: bool | None = None,
        status: str | None = None,
        start_date: str | None = None,
        end_date: str | None = None,
    ) -> list[dict]:
        query: dict = {}
        if metric:
            query["metric"] = metric
        if severity:
            query["severity"] = severity
        if is_anomalous is not None:
            query["is_anomalous"] = is_anomalous
        if status:
            query["status"] = status
        if start_date or end_date:
            date_query: dict = {}
            if start_date:
                date_query["$gte"] = start_date
            if end_date:
                date_query["$lte"] = end_date
            query["target_date"] = date_query
        return list(
            self._collection.find(query).sort("detected_at", -1).limit(limit)
        )


_store_singleton: AnomalyStore | None = None

def get_anomaly_store(settings: Settings) -> AnomalyStore:
    global _store_singleton
    if _store_singleton is None:
        _store_singleton = AnomalyStore(settings)
    return _store_singleton
