from app.agents.common import AgentDeps, timed_agent

def run(state: dict, deps: AgentDeps) -> dict:
    with timed_agent(state, deps, "LangfuseTraceAgent", {}) as rec:
        deps.langfuse_trace.update(
            output={
                "executive_summary": state.get("executive_summary"),
                "overall_confidence": state.get("overall_confidence"),
                "root_cause_count": len(state.get("root_causes", [])),
            }
        )
        deps.tracer.flush()
        rec["sql_statements"] = []
        rec["reasoning"] = "Finalized and flushed the Langfuse trace for this investigation."
        rec["confidence"] = 1.0

    return state
