from app.agents.common import AgentDeps, timed_agent

def run(state: dict, deps: AgentDeps) -> dict:
    with timed_agent(state, deps, "MetricAttributionAgent", {"flagged_count": len(state.get("flagged_dimensions", []))}) as rec:
        flagged = state.get("flagged_dimensions", [])
        attribution = sorted(
            (f["top_contributor"] for f in flagged if f["top_contributor"]),
            key=lambda v: abs(v["delta"]),
            reverse=True,
        )
        rec["sql_statements"] = []  # pure aggregation of already-fetched exploration results
        rec["reasoning"] = (
            f"{len(attribution)} dimension(s) flagged as significant contributors: "
            + ", ".join(f"{a['dimension']}={a['value']} ({a['share_of_total_delta_pct']:+.1f}%)" for a in attribution)
            if attribution else "No dimension crossed the significance threshold - anomaly may be broad-based rather than concentrated."
        )
        rec["confidence"] = 0.85 if attribution else 0.4
        state["attribution"] = attribution

    return state
