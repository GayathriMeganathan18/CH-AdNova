from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import get_settings
from app.dependencies import get_anomaly_store, get_investigation_service, get_repo
from app.observability.otel_setup import setup_otel
from app.routers import analytics, chat, health, investigate, metrics, monitor, system
from app.services.monitor_service import init_monitor_service


@asynccontextmanager
async def lifespan(app: FastAPI):
    monitor_svc = init_monitor_service(
        repo=get_repo(),
        anomaly_store=get_anomaly_store(),
        investigation_service=get_investigation_service(),
        settings=get_settings(),
    )
    monitor_svc.start()
    yield
    monitor_svc.stop()


app = FastAPI(
    title="CH-AdNova",
    description="AI-powered root cause investigation platform for ad-metric anomalies",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=get_settings().allowed_origins_list,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(investigate.router)
app.include_router(metrics.router)
app.include_router(analytics.router)
app.include_router(monitor.router)
app.include_router(system.router)
app.include_router(chat.router)

setup_otel(app, get_settings())
