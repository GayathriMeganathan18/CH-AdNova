import time
from contextlib import contextmanager
from datetime import datetime, timezone
from dataclasses import dataclass
from opentelemetry import trace
from app.config import Settings
from app.observability.langfuse_tracer import LangfuseTracer
from app.observability.llm_client import LLMClient
from app.repositories.clickhouse_repo import ClickHouseRepository

_otel_tracer = trace.get_tracer("ch_adnova.agents")

@dataclass
class AgentDeps:
    settings: Settings
    repo: ClickHouseRepository
    llm: LLMClient
    tracer: LangfuseTracer
    langfuse_trace: object  


@contextmanager
def timed_agent(state: dict, deps: AgentDeps, agent_name: str, input_data: dict):
    started = datetime.now(timezone.utc)
    t0 = time.perf_counter()
    record = {"sql_statements": [], "reasoning": "", "confidence": None}
    with _otel_tracer.start_as_current_span(agent_name) as otel_span:
        with deps.tracer.agent_span(deps.langfuse_trace, agent_name, input_data) as span:
            try:
                yield record
            except Exception as exc:
                otel_span.record_exception(exc)
                otel_span.set_status(trace.Status(trace.StatusCode.ERROR, str(exc)))
                raise
            finally:
                duration_ms = (time.perf_counter() - t0) * 1000
                entry = {
                    "agent": agent_name,
                    "started_at": started.isoformat(),
                    "duration_ms": round(duration_ms, 2),
                    "sql_statements": record["sql_statements"],
                    "reasoning": record["reasoning"],
                    "confidence": record["confidence"],
                }
                state.setdefault("agent_log", []).append(entry)
                span.update(output=entry)
                otel_span.set_attribute("agent.duration_ms", duration_ms)
                otel_span.set_attribute("agent.sql_count", len(record["sql_statements"]))
                if record["confidence"] is not None:
                    otel_span.set_attribute("agent.confidence", record["confidence"])
