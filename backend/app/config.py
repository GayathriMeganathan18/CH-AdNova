"""
Settings are read from the environment variables the `backend` service in
docker-compose.yml already sets - nothing new was added to the compose file.
See PHASE1_README.md / RUNBOOK.md for what each variable means.
"""
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # ClickHouse
    #
    # docker-compose.yml's backend service sets CLICKHOUSE_HTTP_PORT=8123
    # explicitly (the container-internal port, not the host-mapped one you
    # reach from your laptop), so the plain env var name is safe to use
    # directly here - it doesn't pick up the .env-level host-mapping value.
    # For ClickHouse Cloud, set CLICKHOUSE_HOST to your Cloud hostname,
    # CLICKHOUSE_HTTP_PORT=8443, and CLICKHOUSE_SECURE=true.
    clickhouse_host: str = "clickhouse"
    clickhouse_http_port: int = 8123
    clickhouse_db: str = "ch_adnova"
    clickhouse_user: str = "ch_adnova_admin"
    clickhouse_password: str = "root"
    clickhouse_secure: bool = False

    # Langfuse
    langfuse_host: str = "http://langfuse:3000"  # internal: backend -> Langfuse API calls
    langfuse_public_host: str = "http://localhost:3001"  # browser-facing: trace links a user clicks
    langfuse_public_key: str = ""
    langfuse_secret_key: str = ""
    langfuse_project_id: str = ""  # from Settings in the Langfuse UI - needed to build trace links

    # ClickStack / OpenTelemetry
    otel_service_name: str = "ch-adnova-backend"
    otel_exporter_otlp_endpoint: str = ""
    otel_exporter_otlp_protocol: str = "http/protobuf"
    clickstack_host: str = "http://clickstack:8080"  
    clickstack_ingestion_key: str = ""
    clickstack_url: str = ""  

    # MongoDB (investigation trace store)
    #
    # mongo_uri takes priority when set - a MongoDB Atlas connection string
    # (mongodb+srv://user:pass@cluster.mongodb.net) bakes in auth/TLS/SRV
    # lookup that can't be expressed as separate host+port fields. Local
    # Docker Compose leaves this blank and falls back to mongo_host/mongo_port.
    mongo_uri: str = ""
    mongo_host: str = "mongodb"
    mongo_port: int = 27017
    mongo_db: str = "ch_adnova_investigations"

    # LLM (used only for narrative text - never for arithmetic; see agents/)
    anthropic_api_key: str = ""
    anthropic_model: str = "claude-sonnet-4-6"

    # Investigation defaults
    default_baseline_days: int = 7
    significance_threshold_pct: float = 8.0   
    concentration_threshold_pct: float = 40.0


    monitor_enabled: bool = True
    monitor_interval_seconds: int = 60
    monitor_strategy: str = "pct_deviation"
    monitor_baseline_days: int = 7

    # CORS - comma-separated browser origins allowed to call this API.
    # Local Vite dev server by default; add your deployed frontend's origin
    # (e.g. https://ch-adnova.vercel.app) in production. "*" still works if
    # set explicitly (matches FastAPI CORSMiddleware's own wildcard).
    allowed_origins: str = "http://localhost:5173"

    @property
    def allowed_origins_list(self) -> list[str]:
        return [o.strip() for o in self.allowed_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
