import uuid
from datetime import datetime, timezone
from app.agents.common import AgentDeps
from app.agents.graph import build_graph
from app.config import Settings
from app.observability.langfuse_tracer import LangfuseTracer
from app.observability.llm_client import LLMClient
from app.repositories.clickhouse_repo import ClickHouseRepository
from app.repositories.investigation_store import InvestigationStore
from app.schemas.investigation import InvestigationRequest, InvestigationResult

class InvestigationService:
    def __init__(
        self,
        settings: Settings,
        repo: ClickHouseRepository,
        llm: LLMClient,
        tracer: LangfuseTracer,
        store: InvestigationStore,
    ):
        self._settings = settings
        self._repo = repo
        self._llm = llm
        self._tracer = tracer
        self._store = store

    def run_investigation(self, request: InvestigationRequest) -> InvestigationResult:
        investigation_id = str(uuid.uuid4())
        langfuse_trace = self._tracer.start_trace(
            name="ch-adnova-investigation",
            investigation_id=investigation_id,
            metadata={"metric": request.metric, "target_date": str(request.target_date)},
            input_data={
                "metric": request.metric,
                "target_date": str(request.target_date),
                "baseline_days": request.baseline_days,
            },
        )

        deps = AgentDeps(
            settings=self._settings,
            repo=self._repo,
            llm=self._llm,
            tracer=self._tracer,
            langfuse_trace=langfuse_trace,
        )

        initial_state = {
            "investigation_id": investigation_id,
            "metric": request.metric,
            "target_date": request.target_date,
            "baseline_days": request.baseline_days,
            "started_at": datetime.now(timezone.utc),
            "ruled_out": [],
            "agent_log": [],
        }

        graph = build_graph(deps)
        final_state = graph.invoke(initial_state, config={"recursion_limit": 25})
        actual_overall = final_state.get("_actual_overall") or {}
        funnel_volumes = (
            {k: actual_overall[k] for k in ("requests", "fills", "impressions", "clicks")}
            if actual_overall else None
        )

        result = InvestigationResult(
            investigation_id=investigation_id,
            request=request,
            trigger=final_state["trigger"],
            funnel_checks=final_state["funnel_checks"],
            funnel_volumes=funnel_volumes,
            explorations=final_state["explorations"],
            recursive_drilldowns=final_state.get("recursive_drilldowns", []),
            ruled_out=final_state.get("ruled_out", []),
            root_causes=final_state.get("root_causes", []),
            counterfactual=final_state.get("counterfactual"),
            recommendations=final_state.get("recommendations", []),
            executive_summary=final_state.get("executive_summary", ""),
            overall_confidence=final_state.get("overall_confidence", 0.0),
            agent_log=final_state.get("agent_log", []),
            langfuse_trace_url=self._tracer.trace_url(investigation_id),
            created_at=datetime.now(timezone.utc),
        )

        self._store.save(investigation_id, result.model_dump(mode="json"))
        return result
