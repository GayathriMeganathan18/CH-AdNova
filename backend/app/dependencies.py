from functools import lru_cache
from app.config import Settings, get_settings
from app.observability.langfuse_tracer import LangfuseTracer, get_tracer
from app.observability.llm_client import LLMClient, get_llm_client
from app.repositories.anomaly_store import AnomalyStore
from app.repositories.anomaly_store import get_anomaly_store as get_anomaly_store_singleton
from app.repositories.clickhouse_repo import ClickHouseRepository, get_repository
from app.repositories.investigation_store import InvestigationStore, get_store
from app.services.investigation_service import InvestigationService

def get_repo() -> ClickHouseRepository:
    return get_repository(get_settings())

def get_llm() -> LLMClient:
    return get_llm_client(get_settings())

def get_langfuse_tracer() -> LangfuseTracer:
    return get_tracer(get_settings())

def get_investigation_store() -> InvestigationStore:
    return get_store(get_settings())

def get_anomaly_store() -> AnomalyStore:
    return get_anomaly_store_singleton(get_settings())

@lru_cache
def get_investigation_service() -> InvestigationService:
    settings = get_settings()
    return InvestigationService(
        settings=settings,
        repo=get_repo(),
        llm=get_llm(),
        tracer=get_langfuse_tracer(),
        store=get_investigation_store(),
    )
